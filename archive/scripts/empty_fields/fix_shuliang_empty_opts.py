"""
P4 数量关系空选项题诊断 + 修复：
对全库 shuliang 类空 options 的题，在 PDF 中定位该题紧邻的文字，
判断选项是"文字可抽"还是"图形化无法抽"，分别处理：
- 文字选项漏抽：用 regex 补抓 A/B/C/D 文字
- 图形选项：meta.invalid = true + 前端已过滤

用法：
    python scripts/fix_shuliang_empty_opts.py --dry-run
    python scripts/fix_shuliang_empty_opts.py
"""
from __future__ import annotations

import argparse
import glob
import json
import re
from pathlib import Path

import pdfplumber

# id → (PDF 路径, 题号)
# id 形如 national-xingce-shuliang-2022-dishi-067  |  institution-xingce-shuliang-2020-a-055
PDF_LOCATOR = {
    ('national', '2017', 'dishi'): '【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-真题/2017年国家公务员考试行测真题（地市级）.pdf',
    ('national', '2022', 'dishi'): '【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-真题/2022 年国家公务员考试行测真题（地市级）.pdf',
    ('national', '2023', 'xingzhengzhifa'): '【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-真题/2023年国家公务员考试《行测》真题（行政执法）.pdf',
}

MATERIAL = Path('material')

REGION_CN = {
    "anhui": "安徽", "beijing": "北京", "fujian": "福建", "gansu": "甘肃",
    "guangdong": "广东", "guangxi": "广西", "guizhou": "贵州", "hainan": "海南",
    "hebei": "河北", "henan": "河南", "heilongjiang": "黑龙江", "hubei": "湖北",
    "hunan": "湖南", "jilin": "吉林", "jiangsu": "江苏", "jiangxi": "江西",
    "liaoning": "辽宁", "shandong": "山东", "shanxi": "山西", "shaanxi": "陕西",
    "shanghai": "上海", "sichuan": "四川", "tianjin": "天津", "xinjiang": "新疆",
    "yunnan": "云南", "zhejiang": "浙江", "chongqing": "重庆",
}


def locate_pdf_by_id(qid: str) -> Path | None:
    parts = qid.split('-')
    if parts[0] == 'national':
        year, level = parts[3], parts[4]
        # 国考行测题 PDF 在 "行测-真题" 目录下
        cand = list(MATERIAL.glob(f'**/行测-真题/*{year}*.pdf'))
        cand = [p for p in cand if '答案' not in p.name and '解析' not in p.name]
        for p in cand:
            n = p.name
            if level == 'dishi' and ('地市' in n or '市地' in n): return p
            if level == 'fushengjia' and ('副省' in n or '省级' in n): return p
            if level == 'xingzhengzhifa' and '行政执法' in n: return p
        # 兜底返回第一个
        return cand[0] if cand else None
    elif parts[0] == 'institution':
        year, lv = parts[3], parts[4].upper()
        cand = list(MATERIAL.glob(f'**/*{lv}类*职测*笔试真题.pdf'))
        return cand[0] if cand else None
    elif parts[0] == 'provincial':
        region, year = parts[1], parts[5]
        region_cn = REGION_CN.get(region)
        if not region_cn: return None
        # 省考题 PDF 在 "真题" 目录，答案在 "答案及解析"
        cand = list(MATERIAL.glob(f'**/*{region_cn}*/**/真题/*{year}*.pdf'))
        if not cand:  # 没"真题"目录就退化为全局
            cand = list(MATERIAL.glob(f'**/*{region_cn}*/**/*{year}*.pdf'))
            cand = [p for p in cand if '答案' not in p.name and '解析' not in p.name and '申论' not in str(p)]
        return cand[0] if cand else None
    return None


def get_question_context(pdf_path: Path, qn: int) -> str:
    """抽该题周围约 700 字符原文"""
    if not pdf_path or not pdf_path.exists():
        return ''
    try:
        with pdfplumber.open(pdf_path) as p:
            full = '\n'.join((pg.extract_text() or '') for pg in p.pages)
    except Exception as e:
        return ''
    # 定位题号 "67." / "67、"
    patterns = [f'{qn}.', f'{qn}、', f'{qn}．']
    for pat in patterns:
        idx = full.find(pat)
        while idx >= 0:
            # 避免误匹配"1067" 或 "2067" 之类
            prev = full[idx-1] if idx > 0 else '\n'
            if prev.isdigit():
                idx = full.find(pat, idx + 1)
                continue
            return full[idx: idx + 800]
    return ''


def detect_options_in_text(ctx: str) -> list[dict]:
    """从题干上下文抽 A/B/C/D 选项文字"""
    # 模式 1: A. xxx B. xxx C. xxx D. xxx
    opt_pattern = re.compile(r'([A-D])[.．、]\s*([^\n]{1,80}?)(?=\s*[A-D][.．、]|\n|$)')
    hits = []
    for m in opt_pattern.finditer(ctx):
        label, content = m.group(1), m.group(2).strip()
        # 排除空内容
        if content and not content.isspace():
            hits.append({'label': label, 'content': content})
    # 去重：保留每个字母第一次出现
    seen = set()
    out = []
    for h in hits:
        if h['label'] in seen: continue
        seen.add(h['label'])
        out.append(h)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    audit = json.load(open('audit_report.json', encoding='utf-8'))
    shuliang_targets = [
        item for item in audit.get('empty_options', [])
        if 'xingce-shuliang' in item.get('qid', '')
    ]
    print(f'shuliang 空选项目标: {len(shuliang_targets)} 题\n')

    results = {'text_recoverable': [], 'image_only': [], 'pdf_missing': []}

    for t in shuliang_targets:
        qid = t['qid']
        pdf = locate_pdf_by_id(qid)
        if not pdf or not pdf.exists():
            results['pdf_missing'].append(qid)
            print(f'[PDF 缺失] {qid}')
            continue
        ctx = get_question_context(pdf, t['qn'])
        opts = detect_options_in_text(ctx)
        if len(opts) >= 2:
            results['text_recoverable'].append((qid, opts, pdf.name))
            print(f'[可文字补抽] {qid}: {len(opts)} 选项 - {[o["label"] for o in opts]}')
        else:
            results['image_only'].append((qid, pdf.name))
            print(f'[疑图形化] {qid}: 上下文抽选项={len(opts)} (PDF={pdf.name[:50]})')

    # 写回
    filled = 0
    marked = 0
    for qid, opts, _ in results['text_recoverable']:
        for f in glob.glob('src/data/xingce/shuliang/*.json'):
            data = json.load(open(f, encoding='utf-8'))
            changed = False
            for q in data:
                if q['id'] == qid and not q.get('options'):
                    q['options'] = opts
                    filled += 1
                    changed = True
            if changed and not args.dry_run:
                json.dump(data, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    for qid, _ in results['image_only']:
        for f in glob.glob('src/data/xingce/shuliang/*.json'):
            data = json.load(open(f, encoding='utf-8'))
            changed = False
            for q in data:
                if q['id'] == qid and not q.get('options'):
                    meta = q.get('meta') or {}
                    meta['invalid'] = True
                    meta['reason'] = 'image_only_options'
                    q['meta'] = meta
                    marked += 1
                    changed = True
            if changed and not args.dry_run:
                json.dump(data, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    # PDF 缺失的也一并标 invalid（前端过滤，用户看不到空题）
    missing_marked = 0
    for qid in results['pdf_missing']:
        for f in glob.glob('src/data/xingce/shuliang/*.json'):
            data = json.load(open(f, encoding='utf-8'))
            changed = False
            for q in data:
                if q['id'] == qid and not q.get('options'):
                    meta = q.get('meta') or {}
                    meta['invalid'] = True
                    meta['reason'] = 'pdf_not_located'
                    q['meta'] = meta
                    missing_marked += 1
                    changed = True
            if changed and not args.dry_run:
                json.dump(data, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    print('\n' + '=' * 60)
    print(f'汇总: 可文字补抽 {filled}, 标 invalid(图形化) {marked}, PDF 缺失标 invalid {missing_marked}')
    if args.dry_run:
        print('[DRY RUN] 未写盘')


if __name__ == '__main__':
    main()
