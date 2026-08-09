#!/usr/bin/env python3
"""用官方「答案及解析」PDF 复核答案与解析矛盾的题。

背景：122 道题的 answer 字段与解析结论对不上（PDF 抽取整块串行所致）。
光凭解析改答案是"推导"不是"证据"，所以回到 material/ 下的官方答案解析 PDF，
按题干原文定位，抽出官方给的答案。

只产出证据报告，不直接改数据 —— 改不改、怎么改由人决定。

用法：python scripts/verify_answers_from_pdf.py [--limit N]
输出：reports/answer_conflicts_evidence.json
"""
import glob
import io
import json
import os
import re
import sys

import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

LIMIT = None
for i, a in enumerate(sys.argv):
    if a == '--limit' and i + 1 < len(sys.argv):
        LIMIT = int(sys.argv[i + 1])

PLACEHOLDER = ['OCR 抽取失败', 'OCR抽取失败', 'OCR 提取失败',
               '题目缺失', '暂缺', '正在全力以赴征集']
CONCLUSION = re.compile(r'故正确答案为\s*([A-D]+)\s*[。.]?')

PROVINCE_CN = {
    'guangdong': '广东', 'chongqing': '重庆', 'shenzhen': '深圳', 'xinjiang': '新疆',
    'fujian': '福建', 'shanghai': '上海', 'jiangsu': '江苏', 'shandong': '山东',
    'tianjin': '天津', 'anhui': '安徽', 'hebei': '河北', 'neimenggu': '内蒙古',
    'zhejiang': '浙江', 'jiangxi': '江西', 'sichuan': '四川', 'hainan': '海南',
    'hunan': '湖南', 'hubei': '湖北', 'henan': '河南', 'shanxi': '山西',
    'shaanxi': '陕西', 'gansu': '甘肃', 'qinghai': '青海', 'ningxia': '宁夏',
    'jilin': '吉林', 'liaoning': '辽宁', 'heilongjiang': '黑龙江', 'yunnan': '云南',
    'guizhou': '贵州', 'guangxi': '广西',
}


def norm(s):
    return re.sub(r'\s+', '', str(s or ''))


def collect_conflicts():
    out = []
    for path in sorted(glob.glob('src/data/xingce/*/*.json')):
        base = path.replace('\\', '/').split('/')[-1][:-5]
        for q in json.load(io.open(path, encoding='utf-8')):
            if any(p in str(q.get('content') or '') for p in PLACEHOLDER):
                continue
            exp = str(q.get('explanation') or '')
            ans = str(q.get('answer') or '')
            hits = CONCLUSION.findall(exp)
            if len(hits) == 1 and ans and hits[0] != ans:
                out.append({
                    'json': path.replace('\\', '/'), 'paper': base,
                    'id': q.get('id'), 'num': q.get('id', '').rsplit('-', 1)[-1],
                    'answer_field': ans, 'explanation_says': hits[0],
                    'stem': norm(q.get('content'))[:22],
                    'stem_full': str(q.get('content') or '')[:80],
                })
    return out


def candidate_pdfs(paper, all_pdfs):
    year = re.search(r'(\d{4})', paper)
    year = year.group(1) if year else ''
    c = [p for p in all_pdfs if ('答案' in p or '解析' in p)]
    if paper.startswith('national'):
        c = [p for p in c if '国考' in p or '国家' in p]
    elif paper.startswith('institution'):
        c = [p for p in c if '事业' in p]
    else:
        m = re.match(r'provincial_(\w+?)_(\d{4})', paper)
        cn = PROVINCE_CN.get(m.group(2 - 1)) if m else None
        if cn:
            c = [p for p in c if cn in p]
    # 年份优先，但跨年合集（如 2018-2024）也要保留
    return [p for p in c if year in p or re.search(r'\d{4}年-\d{4}年', p)]


def main():
    conflicts = collect_conflicts()
    if LIMIT:
        conflicts = conflicts[:LIMIT]
    print(f'待复核冲突题 {len(conflicts)} 道')

    all_pdfs = [p.replace('\\', '/') for p in glob.glob('material/**/*.pdf', recursive=True)]
    cache = {}
    resolved = 0
    for c in conflicts:
        cands = candidate_pdfs(c['paper'], all_pdfs)
        c['official'] = None
        c['source_pdf'] = None
        for pdf in cands:
            if pdf not in cache:
                try:
                    d = pymupdf.open(pdf)
                    cache[pdf] = norm('\n'.join(pg.get_text() for pg in d))
                    d.close()
                except Exception:
                    cache[pdf] = ''
            t = cache[pdf]
            i = t.find(c['stem'])
            if i < 0:
                continue
            seg = t[i:i + 1500]
            m = (re.search(r'【答案】\s*([A-D]+)', seg)
                 or re.search(r'正确答案[是为：:]\s*([A-D]+)', seg)
                 or re.search(r'答案[：:]\s*([A-D]+)', seg))
            if m:
                c['official'] = m.group(1)
                c['source_pdf'] = pdf
                resolved += 1
                break
    os.makedirs('reports', exist_ok=True)
    json.dump(conflicts, io.open('reports/answer_conflicts_evidence.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    agree_exp = sum(1 for c in conflicts if c['official'] and c['official'] == c['explanation_says'])
    agree_field = sum(1 for c in conflicts if c['official'] and c['official'] == c['answer_field'])
    other = sum(1 for c in conflicts if c['official'] and c['official'] not in
                (c['explanation_says'], c['answer_field']))
    print(f'官方 PDF 定位成功 {resolved}/{len(conflicts)}')
    print(f'  官方答案 == 解析结论（说明 answer 字段错）：{agree_exp}')
    print(f'  官方答案 == answer 字段（说明解析是串来的）：{agree_field}')
    print(f'  三者都不同：{other}')
    print('明细 -> reports/answer_conflicts_evidence.json')


if __name__ == '__main__':
    main()
