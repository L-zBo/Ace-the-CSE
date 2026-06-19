#!/usr/bin/env python3
"""为空选项题分类补全/标记，稳健原则：

- 判断题 → options=[正确,错误]
- 图形题（关键词匹配）→ options=[见图]×4
- 脏数据 → 打 meta.invalid=true，不动 options，交给前端过滤
- 其他（需 PDF 回填）不动，留给后续人工处理

用法: python scripts/fix_empty_options.py [--apply]
  默认 dry-run，打印将要做的改动；--apply 才写盘。
"""
import os, sys, json, glob, re, argparse
from collections import Counter

FIG_KW = ['图形', '问号处', '折叠', '多面体', '展开图', '立方体', '如图', '下图',
          '上图', '图中', '图案', '截面', '直观图', '旋转', '翻转', '平移',
          '拼合', '分为两类', '六个图形', '四个图形']

DIRTY_RE = re.compile(r'^[\d\s.,，、：:]*$')
DIRTY_MARKERS = ('暂缺', '缺失')


def classify(q):
    if q.get('type') not in ('single_choice', 'multi_choice'):
        return None
    if len(q.get('options', [])) != 0:
        return None
    c = (q.get('content') or '').strip()
    if c in DIRTY_MARKERS or not c or len(c) < 8 or DIRTY_RE.fullmatch(c):
        return 'dirty'
    if c.startswith('（判断题）') or c.startswith('(判断题)'):
        return 'tf'
    if any(k in c for k in FIG_KW):
        # 仅当对应 png 实存才视为可补 [见图]×4
        qn = int(q['id'].split('-')[-1])
        parts = q['id'].split('-')
        mid = parts[4:-1]
        key = '_'.join([q.get('source', ''), str(q.get('year', ''))] + mid) \
            if mid else f"{q.get('source','')}_{q.get('year','')}"
        png = os.path.join('public', 'img', 'questions', key,
                           f'q{qn:03d}.png')
        if os.path.exists(png):
            return 'fig'
        return None  # 有图形关键词但 png 缺失 → 留待 B 阶段回填
    return None


def fix(q, kind):
    if kind == 'tf':
        q['options'] = [
            {'label': 'A', 'content': '正确'},
            {'label': 'B', 'content': '错误'},
        ]
    elif kind == 'fig':
        q['options'] = [
            {'label': L, 'content': '[见图]'} for L in 'ABCD'
        ]
    elif kind == 'dirty':
        meta = q.get('meta') or {}
        meta['invalid'] = True
        meta['reason'] = 'empty_content_or_garbage'
        q['meta'] = meta
    return q


def main(apply: bool):
    stats = Counter()
    changes = []  # (path, count_tf, count_fig, count_dirty)

    for path in sorted(glob.glob('src/data/xingce/**/*.json', recursive=True)):
        qs = json.load(open(path, encoding='utf-8'))
        file_stats = Counter()
        touched = False
        for q in qs:
            kind = classify(q)
            if not kind:
                continue
            fix(q, kind)
            file_stats[kind] += 1
            stats[kind] += 1
            touched = True
        if touched:
            changes.append((path, dict(file_stats)))
            if apply:
                json.dump(qs, open(path, 'w', encoding='utf-8'),
                          ensure_ascii=False, indent=2)

    print(f'MODE: {"APPLY" if apply else "DRY-RUN"}')
    print(f'Totals: {dict(stats)}')
    print(f'Files touched: {len(changes)}')
    for p, s in changes[:20]:
        print(f'  {p.replace(os.sep,"/"):70s}  {s}')
    if len(changes) > 20:
        print(f'  ...余 {len(changes)-20} 个文件')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    main(ap.parse_args().apply)
