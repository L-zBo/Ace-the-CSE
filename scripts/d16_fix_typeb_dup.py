#!/usr/bin/env python3
"""D-16 L-10c 修 lib 散点 dup ID（Type B）

L-10b 处理整批合并 7 个事业编文件（115 题 shift）后，剩 11 个散点 dup
分两类：

类型 1 — 事业编同年两套卷的零星 dup（3 文件 5 题）
  shuliang/institution_2020_a.json: q046/q047
  yanyu/institution_2021_b.json:    q037
  shuliang/institution_2022_a.json: q046/q047
  两份都是合法真题，按 L-10b 同策略：第二份 +100 shift

类型 2 — 省考 D-13 sim 救援残留脏数据（3 文件 6 题）
  provincial_hubei_2023.json:     q008/q105
  provincial_sichuan_2023.json:   q001/q003
  provincial_zhejiang_2021.json:  q001/q029
  第二份 stem 是数据片段（不是真题），answer/explanation 从 keep
  复制过来 → 第二份是垃圾，删除
"""
import argparse
import json
import re
from pathlib import Path

# 类型 1: 第二份 +100 shift
B_SHIFT = [
    'src/data/xingce/shuliang/institution_2020_a.json',
    'src/data/xingce/yanyu/institution_2021_b.json',
    'src/data/xingce/shuliang/institution_2022_a.json',
]

# 类型 2: 删除第二份
B_DELETE = [
    'src/data/xingce/changshi/provincial_hubei_2023.json',
    'src/data/xingce/changshi/provincial_sichuan_2023.json',
    'src/data/xingce/ziliao/provincial_zhejiang_2021.json',
]

ID_RE = re.compile(r'^(.*-)(\d+)$')


def shift_qn(qid: str, offset: int = 100) -> str:
    m = ID_RE.match(qid)
    if not m:
        raise ValueError(f'无法解析 ID: {qid}')
    prefix, qn = m.group(1), int(m.group(2))
    return f'{prefix}{qn + offset:03d}'


def shift_source_label(label: str, offset: int = 100) -> str:
    if not label:
        return label
    m = re.search(r'第\s*(\d+)\s*题', label)
    if not m:
        return label + '（同年另一卷）'
    new_qn = int(m.group(1)) + offset
    return re.sub(r'第\s*\d+\s*题', f'第{new_qn}题（同年另一卷）', label, count=1)


def process_shift(f: str, apply: bool) -> int:
    """同 ID 第二份 +100 shift"""
    p = Path(f)
    data = json.loads(p.read_text(encoding='utf-8'))
    seen = {}
    n = 0
    for i, q in enumerate(data):
        qid = q.get('id', '')
        if qid in seen:
            old_id = q['id']
            new_id = shift_qn(old_id)
            old_label = q.get('sourceLabel', '')
            new_label = shift_source_label(old_label)
            print(f'  SHIFT [{i}] {old_id} -> {new_id}')
            if apply:
                q['id'] = new_id
                if old_label:
                    q['sourceLabel'] = new_label
            n += 1
        else:
            seen[qid] = i
    if apply and n:
        p.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )
    print(f'  {f}: shift {n} 题')
    return n


def process_delete(f: str, apply: bool) -> int:
    """同 ID 第二份删除（脏数据）"""
    p = Path(f)
    data = json.loads(p.read_text(encoding='utf-8'))
    seen = {}
    to_drop = []
    for i, q in enumerate(data):
        qid = q.get('id', '')
        if qid in seen:
            stem = (q.get('content', '') or '')[:50].replace('\n', ' ')
            print(f'  DROP [{i}] {qid}  stem={stem}')
            to_drop.append(i)
        else:
            seen[qid] = i
    if apply and to_drop:
        new_data = [q for i, q in enumerate(data) if i not in set(to_drop)]
        p.write_text(
            json.dumps(new_data, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )
    print(f'  {f}: drop {len(to_drop)} 题')
    return len(to_drop)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    total_shift = 0
    total_drop = 0
    print('=== 类型 1: 事业编散点 dup (+100 shift) ===')
    for f in B_SHIFT:
        total_shift += process_shift(f, args.apply)

    print('\n=== 类型 2: 省考脏数据残留 (delete) ===')
    for f in B_DELETE:
        total_drop += process_delete(f, args.apply)

    mode = 'APPLY' if args.apply else 'DRY-RUN'
    print(f'\n[{mode}] shift {total_shift} 题 + drop {total_drop} 题')
    if not args.apply:
        print('要落盘加 --apply')


if __name__ == '__main__':
    main()
