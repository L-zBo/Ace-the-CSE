#!/usr/bin/env python3
"""删除明确非图形题的孤儿图片；列出可疑需人工确认的。"""
import json, glob, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

FIGURE_KW = ['图形','问号处','下列四','立方体','四面体','六面体','展开图','多面体',
             '折叠','拼合','平移','旋转','翻转','图①','图②','图1','图2',
             '下图','上图','直观图','立体图','下列图','下面图','如图','图中',
             '图(','图（','以下图','下列各图','下面的图']

refs = set()
for fp in glob.glob('src/data/xingce/*/*.json'):
    for q in json.load(open(fp, encoding='utf-8')):
        if 'questionImage' in q:
            refs.add(q['questionImage'].replace(os.sep, '/'))

deleted = 0
kept = []
for fp in glob.glob('public/img/questions/*/q*.png'):
    norm = fp.replace(os.sep, '/')
    rel = '/' + norm.split('public/', 1)[1]
    if rel in refs:
        continue
    # 查 content
    parts = rel.split('/')
    exam = parts[-2]; qn = int(parts[-1].replace('q', '').replace('.png', ''))
    jp = f'src/data/xingce/panduan/{exam}.json'
    if not os.path.exists(jp):
        continue
    qs = json.load(open(jp, encoding='utf-8'))
    target = next((q for q in qs if int(q['id'].split('-')[-1]) == qn), None)
    if not target:
        continue
    c = target.get('content', '')
    if any(k in c for k in FIGURE_KW):
        kept.append((rel, c[:60]))
    else:
        os.remove(fp)
        deleted += 1

print(f'删除非图形题孤儿图片 {deleted} 张')
print(f'保留 {len(kept)} 张疑似图形题（待人工审核）:')
for r in kept:
    print('  ', r)
