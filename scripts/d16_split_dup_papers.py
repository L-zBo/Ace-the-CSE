#!/usr/bin/env python3
"""D-16 L-10b 修 lib 合并 bug — Type A 整批 dup 文件

D-10/D-11 时期事业编联考救援时把 7.25 + 10.24 两套同年同类卷的
题原样 append 到了同一 lib 文件，题号 q001-q020 完全重复 → 前端
按 ID lookup 只能看见 batch1，batch2 永远不可见。

修法：batch2 所有题号 +100（q001→q101），sourceLabel 加「另一卷」
后缀。同一文件内两套卷题 ID 不冲突，前端按 source/year/level 筛
能看到全部题。

慎重起见：默认 dry-run，需 --apply 才落盘。
"""
import argparse
import json
import re
from pathlib import Path

# Type A 文件 → batch2 起始索引
TYPE_A = {
    'src/data/xingce/changshi/institution_2020_a.json': 12,
    'src/data/xingce/changshi/institution_2020_c.json': 14,
    'src/data/xingce/panduan/institution_2020_c.json': 43,
    'src/data/xingce/yanyu/institution_2020_a.json': 21,
    'src/data/xingce/yanyu/institution_2020_c.json': 22,
    'src/data/xingce/yanyu/institution_2022_a.json': 36,
    'src/data/xingce/ziliao/institution_2022_a.json': 15,
}

ID_RE = re.compile(r'^(.*-)(\d+)$')


def shift_qn(qid: str, offset: int = 100) -> str:
    m = ID_RE.match(qid)
    if not m:
        raise ValueError(f'无法解析 ID: {qid}')
    prefix, qn = m.group(1), int(m.group(2))
    return f'{prefix}{qn + offset:03d}'


def shift_source_label(label: str, offset: int = 100) -> str:
    """sourceLabel 末尾「第 N 题」→ 「第 (N+100) 题（同年另一卷）」"""
    if not label:
        return label
    m = re.search(r'第\s*(\d+)\s*题', label)
    if not m:
        return label + '（同年另一卷）'
    new_qn = int(m.group(1)) + offset
    return re.sub(r'第\s*\d+\s*题', f'第{new_qn}题（同年另一卷）', label, count=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true', help='落盘修改（默认 dry-run）')
    args = ap.parse_args()

    total_shifted = 0
    total_skipped = 0
    for f, b2_start in TYPE_A.items():
        p = Path(f)
        data = json.loads(p.read_text(encoding='utf-8'))
        n_total = len(data)
        if b2_start >= n_total:
            print(f'!! {f}: batch2_start={b2_start} >= total={n_total}，跳过')
            continue

        # 收集 batch1 出现过的 ID，只 shift 与 batch1 撞 ID 的 batch2 题
        batch1_ids = {q.get('id') for q in data[:b2_start]}

        n_shift = 0
        n_skip = 0
        samples = []
        for i in range(b2_start, n_total):
            q = data[i]
            old_id = q.get('id', '')
            if old_id not in batch1_ids:
                n_skip += 1
                continue
            new_id = shift_qn(old_id)
            old_label = q.get('sourceLabel', '')
            new_label = shift_source_label(old_label)

            if not args.apply:
                if len(samples) < 2:
                    samples.append((i, old_id, new_id, old_label, new_label))
            else:
                q['id'] = new_id
                if old_label:
                    q['sourceLabel'] = new_label
            n_shift += 1

        if args.apply:
            p.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

        for i, oid, nid, ol, nl in samples:
            print(f'  [{i}] {oid} -> {nid}')
            print(f'       "{ol}" -> "{nl}"')
        print(f'{f}: batch2[{b2_start}:{n_total}] shift={n_shift} skip={n_skip}')
        total_shifted += n_shift
        total_skipped += n_skip

    mode = 'APPLY' if args.apply else 'DRY-RUN'
    print(f'\n[{mode}] 共处理 {len(TYPE_A)} 文件, shift {total_shifted} 题（跳过 {total_skipped} 非 dup 题）')
    if not args.apply:
        print('要落盘加 --apply')


if __name__ == '__main__':
    main()
