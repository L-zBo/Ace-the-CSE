#!/usr/bin/env python3
"""生成轻量题目索引 src/data/index/question-index.json。

背景：旧的 questionLoader.ts 用 1381 条静态 import 把整个题库拉进 bundle，
导致单个客户端 chunk 62.5 MB、dev 进程常驻 6 GB。

索引只保留列表页/筛选/统计需要的元数据，正文（content/options/explanation/material）
一律不进索引，改由 questionLoader 按试卷 dynamic import() 懒加载。

体积优化的关键观察：subject / category / source / level / year / region
都是「试卷级」属性（实测仅 1 处例外），所以拆成 papers 表 + questions 表，
避免每道题重复存这些字符串。

用法：python scripts/generate_question_index.py
"""

import io
import json
import os
import sys
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

DATA_DIR = 'src/data'
OUT_DIR = 'src/data/index'
OUT_FILE = os.path.join(OUT_DIR, 'question-index.json')

# marker 唯一真相源，与 src/lib/placeholder.ts 共用
with open('src/lib/markers.json', encoding='utf-8') as _f:
    _M = json.load(_f)
OCR_MARKERS = _M['placeholderMarkers']
SHORT_PLACEHOLDERS = _M['sourcePlaceholderShort']

# 索引里只存短答案（行测客观题）。申论答案是长文且不自动判分，不进索引。
MAX_ANSWER_LEN = 12

FLAG_UNANSWERABLE = 1
FLAG_HAS_IMAGE = 2


def is_short_placeholder(s):
    t = (s or '').strip()
    if not t:
        return False
    return any(t == p or t == p + '。' or t == p + '.' for p in SHORT_PLACEHOLDERS)


def is_placeholder_text(s):
    """对齐 placeholder.ts 的 isPlaceholderText。"""
    if not s:
        return False
    if any(m in s for m in OCR_MARKERS):
        return True
    if '题目正在全力以赴征集' in s:
        return True
    return is_short_placeholder(s)


def is_placeholder_question(q):
    """对齐 placeholder.ts 的 isPlaceholderQuestion：题干坏，或 ≥2 个选项坏。"""
    if is_placeholder_text(q.get('content')):
        return True
    opts = q.get('options') or []
    if not opts:
        return False
    bad = sum(1 for o in opts if is_placeholder_text((o or {}).get('content')))
    return bad >= 2


def is_unanswerable(q):
    """对齐 placeholder.ts 的 isUnanswerable：占位题且无兜底图。"""
    return is_placeholder_question(q) and not q.get('questionImage')


def main():
    papers = []
    questions = []
    stats = Counter()
    overrides = 0

    for subject in ('xingce', 'shenlun'):
        subject_dir = os.path.join(DATA_DIR, subject)
        if not os.path.isdir(subject_dir):
            continue
        for category in sorted(os.listdir(subject_dir)):
            cat_dir = os.path.join(subject_dir, category)
            if not os.path.isdir(cat_dir):
                continue
            for filename in sorted(os.listdir(cat_dir)):
                if not filename.endswith('.json'):
                    continue
                path = os.path.join(cat_dir, filename)
                with open(path, encoding='utf-8') as f:
                    arr = json.load(f)
                if not arr or not isinstance(arr, list):
                    continue

                stem = filename[:-5]
                key = f'{subject}/{category}/{stem}'
                head = arr[0]
                paper_idx = len(papers)
                papers.append({
                    'k': key,
                    's': head.get('subject') or subject,
                    'c': head.get('category') or category,
                    'o': head.get('source'),
                    'l': head.get('level'),
                    'y': head.get('year'),
                    'r': head.get('region'),
                })
                stats['papers'] += 1

                for q in arr:
                    if not isinstance(q, dict):
                        continue
                    stats['questions'] += 1
                    flags = 0
                    if is_unanswerable(q):
                        flags |= FLAG_UNANSWERABLE
                        stats['unanswerable'] += 1
                    if q.get('questionImage'):
                        flags |= FLAG_HAS_IMAGE

                    ans = q.get('answer')
                    if isinstance(ans, list):
                        # 多选题答案存成 ['A','B']，索引层原样保留，
                        # 前端统计走 Array.isArray 分支才不会判错。
                        ans_s = ([str(x) for x in ans]
                                 if all(isinstance(x, str) and len(x) <= MAX_ANSWER_LEN
                                        for x in ans)
                                 else '')
                    else:
                        ans_s = ans if isinstance(ans, str) and len(ans) <= MAX_ANSWER_LEN else ''

                    row = [q.get('id', ''), paper_idx, ans_s, flags]
                    # 极少数题目的 category 与所在目录不一致，单独带覆盖值，
                    # 避免筛选时把它归错类（实测全库 1 处）。
                    qc = q.get('category')
                    if qc and qc != papers[paper_idx]['c']:
                        row.append(qc)
                        overrides += 1
                    questions.append(row)

    os.makedirs(OUT_DIR, exist_ok=True)
    payload = {
        '_meta': '自动生成，请勿手动编辑；生成命令 python scripts/generate_question_index.py',
        'flags': {'unanswerable': FLAG_UNANSWERABLE, 'hasImage': FLAG_HAS_IMAGE},
        'papers': papers,
        'questions': questions,
    }
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, separators=(',', ':'))

    size = os.path.getsize(OUT_FILE)
    print(f'试卷 {stats["papers"]}  题目 {stats["questions"]}  '
          f'不可作答 {stats["unanswerable"]}  category 覆盖 {overrides}')
    print(f'索引写入 {OUT_FILE}  {size / 1048576:.2f} MB')


if __name__ == '__main__':
    main()
