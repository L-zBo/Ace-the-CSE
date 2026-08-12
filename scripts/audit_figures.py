#!/usr/bin/env python3
"""图片题审计：输出嫌疑清单 + 一致性报告。

只读扫描，不修改任何文件。产出：
  - reports/audit_figures.json  机器可读明细
  - reports/audit_figures.md    人工浏览摘要

产物早先直接落在仓库根（audit_report.json/md），跟其他审计报告不在一处，
每跑一次就在根目录多两个文件。现在统一进 reports/。
"""
import os, sys, json, glob, re
from collections import defaultdict
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_ROOT = os.path.join(ROOT, 'public', 'img', 'questions')
DATA_ROOT = os.path.join(ROOT, 'src', 'data', 'xingce')

MIN_H = 80            # 低于此像素视为过小
MIN_W = 120
MAX_H = 1800          # 过高可能截多了
MAX_WH_RATIO = 12     # 宽高比异常
# 图形推理题本就大量留白，白比单独不算问题；只有在"既矮又空"时才视为疑似空白条
SHORT_AND_WHITE_H = 200
SHORT_AND_WHITE_RATIO = 0.95
NEAR_WHITE = 245

FIG_MARKERS = ('[见图]', '[图形选项]', '见图', '如图', '下图', '上图',
               '图中', '图示', '问号处', '如下图', '如下所示')


def near_white_ratio(im: Image.Image) -> float:
    g = im.convert('L')
    w, h = g.size
    if w * h == 0:
        return 1.0
    step = max(1, (w * h) // 20000)
    px = list(g.getdata())[::step]
    white = sum(1 for v in px if v >= NEAR_WHITE)
    return white / len(px)


def iter_questions():
    # exam_key 直接取 JSON 文件名（不带扩展名），天然等于 png 目录名：
    #   src/data/xingce/panduan/provincial_jiangsu_2020.json -> provincial_jiangsu_2020
    #   src/data/xingce/changshi/national_2025_dishi.json    -> national_2025_dishi
    # 这比从 id 解析更稳：provincial 的 id 把 region 放在第 2 段
    # (`provincial-jiangsu-xingce-panduan-2020-066`), 旧实现用 parts[4:-1]
    # 切不到 region, 生成 `provincial_2020_2020` 与 png 目录对不上 ->
    # 全部 provincial 题被误判为孤儿。
    for p in glob.glob(os.path.join(DATA_ROOT, '*', '*.json')):
        try:
            qs = json.load(open(p, encoding='utf-8'))
        except Exception:
            continue
        key = os.path.splitext(os.path.basename(p))[0]
        for q in qs:
            qid = q.get('id', '')
            parts = qid.split('-')
            if len(parts) < 4:
                continue
            tail = parts[-1]
            try:
                qn = int(tail)
            except ValueError:
                continue
            text = q.get('content', '') + ' ' + ' '.join(
                (o.get('content', '') if isinstance(o, dict) else str(o))
                for o in q.get('options', [])
            )
            has_img = any(m in text for m in FIG_MARKERS) or bool(q.get('questionImage'))
            empty_options = (q.get('type') in ('single_choice', 'multi_choice')
                             and len(q.get('options', [])) == 0)
            yield key, qn, has_img, qid, empty_options


def main():
    # 1) index: what JSON says
    declared = defaultdict(dict)   # exam -> {qn: (has_img, qid, empty_opts)}
    empty_opts_list = []
    for key, qn, has_img, qid, empty in iter_questions():
        # 同一 exam 下多个科目 JSON 可能共用题号（panduan q071-080 与
        # ziliao q071-080 同号不同科目），但 png 只有一份，只要任一
        # 科目声明有图就不该视为孤儿：True 优先。
        prev = declared[key].get(qn)
        if prev is None or (has_img and not prev[0]):
            declared[key][qn] = (has_img, qid)
        if empty:
            empty_opts_list.append({'exam': key, 'qn': qn, 'qid': qid})

    # 2) scan images
    issues = []
    orphans = []
    missing = []

    for exam_dir in sorted(glob.glob(os.path.join(IMG_ROOT, '*'))):
        exam = os.path.basename(exam_dir)
        decl = declared.get(exam, {})
        png_files = glob.glob(os.path.join(exam_dir, 'q*.png'))
        present = {}
        for png in png_files:
            m = re.search(r'q(\d+)\.png$', png.replace(os.sep, '/'))
            if not m:
                continue
            qn = int(m.group(1))
            present[qn] = png

        # orphans: png 存在但 JSON 没声明 [见图]
        for qn, png in present.items():
            if qn not in decl:
                orphans.append((exam, qn, png, 'no_json_entry'))
            elif not decl[qn][0]:
                orphans.append((exam, qn, png, 'json_no_seejian'))

        # missing: JSON 说有图但 png 不在
        for qn, (has_img, qid) in decl.items():
            if has_img and qn not in present:
                missing.append((exam, qn, qid))

        # quality: 扫所有 png
        for qn, png in present.items():
            try:
                with Image.open(png) as im:
                    w, h = im.size
                    wr = near_white_ratio(im)
            except Exception as e:
                issues.append({'exam': exam, 'qn': qn, 'path': png,
                               'flag': 'open_failed', 'detail': str(e)})
                continue
            flags = []
            if h < MIN_H:
                flags.append(f'too_short(h={h})')
            if w < MIN_W:
                flags.append(f'too_narrow(w={w})')
            if h > MAX_H:
                flags.append(f'too_tall(h={h})')
            if w and h:
                r = max(w / h, h / w)
                if r > MAX_WH_RATIO:
                    flags.append(f'bad_ratio({w}x{h})')
            if wr >= SHORT_AND_WHITE_RATIO and h <= SHORT_AND_WHITE_H:
                flags.append(f'short_and_blank({w}x{h},white={wr:.0%})')
            if flags:
                issues.append({'exam': exam, 'qn': qn, 'path': png,
                               'w': w, 'h': h, 'white': round(wr, 3),
                               'flag': ','.join(flags)})

    report = {
        'summary': {
            'total_exams': len(declared),
            'quality_issues': len(issues),
            'orphans': len(orphans),
            'missing': len(missing),
            'empty_options': len(empty_opts_list),
        },
        'issues': issues,
        'orphans': [{'exam': e, 'qn': q, 'path': p, 'reason': r}
                    for e, q, p, r in orphans],
        'missing': [{'exam': e, 'qn': q, 'qid': qid}
                    for e, q, qid in missing],
        'empty_options': empty_opts_list,
    }
    out_json = os.path.join(ROOT, 'reports', 'audit_figures.json')
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    json.dump(report, open(out_json, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)

    # markdown
    md = ['# 图片题审计报告', '', '## 汇总', '']
    for k, v in report['summary'].items():
        md.append(f'- {k}: **{v}**')
    md.append('')

    by_exam_issue = defaultdict(list)
    for it in issues:
        by_exam_issue[it['exam']].append(it)
    md.append('## 质量嫌疑（按试卷）')
    for exam in sorted(by_exam_issue, key=lambda k: -len(by_exam_issue[k])):
        its = by_exam_issue[exam]
        md.append(f'\n### {exam}  ({len(its)}条)')
        for it in sorted(its, key=lambda x: x['qn']):
            md.append(f"- q{it['qn']:03d}  {it['flag']}"
                      + (f"  [{it.get('w')}x{it.get('h')}, white={it.get('white')}]" if 'w' in it else ''))

    md.append('\n## 缺图（JSON 声明有图但 png 缺失）')
    by_exam_miss = defaultdict(list)
    for m in report['missing']:
        by_exam_miss[m['exam']].append(m['qn'])
    for exam in sorted(by_exam_miss):
        md.append(f"- {exam}: {sorted(by_exam_miss[exam])}")

    md.append('\n## 孤儿图（png 存在但 JSON 未声明[见图]）')
    by_exam_orph = defaultdict(list)
    for o in report['orphans']:
        by_exam_orph[o['exam']].append((o['qn'], o['reason']))
    for exam in sorted(by_exam_orph):
        md.append(f"- {exam}: {sorted(by_exam_orph[exam])}")

    md.append('\n## 选项为空的题（数据完整性）')
    from collections import defaultdict as _dd
    by_exam_eo = _dd(list)
    for it in empty_opts_list:
        by_exam_eo[it['exam']].append(it['qn'])
    for exam in sorted(by_exam_eo):
        md.append(f"- {exam}: {sorted(by_exam_eo[exam])}")

    out_md = os.path.join(ROOT, 'reports', 'audit_figures.md')
    open(out_md, 'w', encoding='utf-8').write('\n'.join(md))

    print(f'Done. summary={report["summary"]}')
    print(f'  -> {out_json}')
    print(f'  -> {out_md}')


if __name__ == '__main__':
    main()
