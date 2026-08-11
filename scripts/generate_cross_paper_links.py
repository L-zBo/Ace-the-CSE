#!/usr/bin/env python3
"""生成跨卷同题关联 src/data/index/cross-paper-links.json。

背景：全库审计里 `dup_cross_paper` 有 2000 多组 —— 同一道题在不同年份、
不同省份的卷子里重复出现。这不是缺陷（真题本来就跨省共用题池），
把它做成「这道题在 X 年 Y 卷也考过」的关联提示，脏数据就变成了功能。

## 为什么不能直接用审计那份名单

审计的 `dup_cross_paper` 用题干前 80 字做指纹，误判很多：

- 图形推理题的题干是模板句（「从所给的四个选项中选择最合适的一个填入
  问号处」246 处、「把下面的六个图形分为两类」186 处），选项还都是
  `[见图]` —— 这些题靠图区分，文本上完全一样，但根本不是同一道题
- 资料分析题的「能够从上述资料中推出的是」151 处，同理
- 占位题「题干OCR抽取失败」52 处

所以这里自己算一份严格指纹，宁可漏，不可错报 —— 关联提示报错了，
用户点过去发现是另一道题，比不给提示更糟。

## 指纹口径

signature = 规范化题干 + 排序后的规范化选项内容

规范化 = 只保留中日韩汉字与字母数字（丢掉空白、标点、页码残留）。
选项排序是因为跨卷同题的选项顺序可能不同（PDF 双栏排版按列读的老问题）。

## 准入门槛（任一不满足就不参与关联）

1. 不是占位题（口径与 src/lib/placeholder.ts 一致）
2. 规范化题干长度 >= 10
3. 选项里最长的一个 > 2 字符 —— 排除 `A/B/C/D` 裸字母选项（图形题）
4. 选项内容总长 >= 20 —— 排除 `[见图]`、`图形选项`、空选项
5. 题干 + 选项总长 >= 40 —— 兜底，信息量太少的一律不认

用法：python scripts/generate_cross_paper_links.py
改题库后需要和 generate_question_index.py 一起重跑。
"""

import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

DATA_DIR = 'src/data'
OUT_DIR = 'src/data/index'
OUT_FILE = os.path.join(OUT_DIR, 'cross-paper-links.json')

# marker 唯一真相源，与 src/lib/placeholder.ts 共用
with open('src/lib/markers.json', encoding='utf-8') as _f:
    _M = json.load(_f)
OCR_MARKERS = _M['placeholderMarkers']
SHORT_PLACEHOLDERS = _M['sourcePlaceholderShort']

MIN_STEM = 10
MIN_OPT_TOTAL = 20
MIN_TOTAL = 40
MIN_OPT_MAXLEN = 2

NON_WORD = re.compile(r'[^0-9A-Za-z一-鿿]')
# sourceLabel 形如「2020年事业编行测（a）第1题」；也有「…第101题（同年另一卷）」
# 这种题号不在末尾的，所以取最后一处「第N题」，剩下的拼回卷标签。
QNO_RE = re.compile(r'第(\d+)题')


def norm(s):
    return NON_WORD.sub('', s or '')


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
    """对齐 placeholder.ts 的 isPlaceholderQuestion：题干坏，或 >=2 个选项坏。"""
    if is_placeholder_text(q.get('content')):
        return True
    opts = q.get('options') or []
    if not opts:
        return False
    bad = sum(1 for o in opts if is_placeholder_text((o or {}).get('content')))
    return bad >= 2


def iter_questions():
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
                if not isinstance(arr, list):
                    continue
                paper_key = f'{subject}/{category}/{filename[:-5]}'
                for q in arr:
                    if isinstance(q, dict):
                        yield paper_key, q


def signature(q):
    """返回 (signature, 拒绝原因)。signature 为 None 表示不参与关联。"""
    if is_placeholder_question(q):
        return None, '占位题'
    stem = norm(q.get('content'))
    if len(stem) < MIN_STEM:
        return None, '题干过短'
    opts = [norm((o or {}).get('content')) for o in (q.get('options') or [])]
    if opts and max(len(o) for o in opts) <= MIN_OPT_MAXLEN:
        return None, '裸字母选项'
    opt_total = sum(len(o) for o in opts)
    if opt_total < MIN_OPT_TOTAL:
        return None, '选项信息不足'
    if len(stem) + opt_total < MIN_TOTAL:
        return None, '总信息不足'
    return stem + '##' + '|'.join(sorted(opts)), None


def split_label(source_label, paper_key):
    """把 sourceLabel 拆成（卷标签, 题号）。抽不到题号就返回 0。"""
    label = (source_label or '').strip()
    hits = list(QNO_RE.finditer(label))
    if hits:
        m = hits[-1]
        paper = (label[:m.start()] + label[m.end():]).strip()
        return paper or paper_key, int(m.group(1))
    return label or paper_key, 0


def main():
    buckets = defaultdict(list)
    rejected = Counter()
    total = 0

    for paper_key, q in iter_questions():
        total += 1
        sig, reason = signature(q)
        if sig is None:
            rejected[reason] += 1
            continue
        paper_label, qno = split_label(q.get('sourceLabel'), paper_key)
        buckets[sig].append({
            'id': q.get('id') or '',
            'paperKey': paper_key,
            'paperLabel': paper_label,
            'qno': qno,
            'year': q.get('year') or 0,
        })

    paper_labels = []
    label_idx = {}
    groups = []
    dropped_same_paper = 0

    for members in buckets.values():
        # 同一份卷里指纹相同的属残留重复题（另一类缺陷），每卷只留题号最小的一道，
        # 免得关联列表里出现「本卷第 7 题也考过」这种自指噪声。
        by_paper = {}
        for m in members:
            cur = by_paper.get(m['paperKey'])
            if cur is None or m['qno'] < cur['qno']:
                if cur is not None:
                    dropped_same_paper += 1
                by_paper[m['paperKey']] = m
            else:
                dropped_same_paper += 1
        if len(by_paper) < 2:
            continue

        rows = sorted(by_paper.values(), key=lambda m: (m['year'], m['paperKey'], m['qno']))
        group = []
        for m in rows:
            if not m['id']:
                continue
            idx = label_idx.get(m['paperLabel'])
            if idx is None:
                idx = len(paper_labels)
                label_idx[m['paperLabel']] = idx
                paper_labels.append(m['paperLabel'])
            group.append([m['id'], idx, m['qno']])
        if len(group) >= 2:
            groups.append(group)

    os.makedirs(OUT_DIR, exist_ok=True)
    payload = {
        '_meta': ('自动生成，请勿手动编辑；生成命令 '
                  'python scripts/generate_cross_paper_links.py'),
        '_rule': ('指纹 = 规范化题干 + 排序后的规范化选项；'
                  '占位题、裸字母选项、[见图] 类图形题一律不参与'),
        'paperLabels': paper_labels,
        # 每组是同一道题的多处出现，元素为 [题目id, paperLabels下标, 题号]
        'groups': groups,
    }
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, separators=(',', ':'))

    linked = sum(len(g) for g in groups)
    size = os.path.getsize(OUT_FILE)
    print(f'扫描 {total} 题，参与关联 {total - sum(rejected.values())} 题')
    print('  排除：' + '、'.join(f'{k} {v}' for k, v in rejected.most_common()))
    print(f'跨卷同题 {len(groups)} 组，涉及 {linked} 道题，卷标签 {len(paper_labels)} 个')
    if dropped_same_paper:
        print(f'  同卷内指纹重复 {dropped_same_paper} 道（属残留重复题，每卷只保留题号最小的）')
    print(f'写入 {OUT_FILE}  {size / 1024:.0f} KB')


if __name__ == '__main__':
    main()
