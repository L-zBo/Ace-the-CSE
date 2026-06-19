"""D-16 L-7b 死链 questionImage 分析 + 修复

L-7a 给 26 占位题补 questionImage 后，全库扫发现 139 个 questionImage
字段是死链（绝大多数是非占位的图形题）。本工具：
  1. 找替代命名能修的（q049 vs q49）
  2. 找完全缺失的（目录都没有 / PNG 真不存在）
"""
import argparse
import json
import re
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true', help='应用可修复的改名')
    ap.add_argument('--drop-missing', action='store_true',
                    help='删除完全缺失的 questionImage 字段（防 UI 误导）')
    args = ap.parse_args()

    broken = []
    all_libs = list(Path('src/data/xingce').rglob('*.json'))
    for f in all_libs:
        data = json.loads(f.read_text(encoding='utf-8'))
        for q in data:
            url = q.get('questionImage')
            if not url:
                continue
            path = Path('public') / url.lstrip('/')
            if path.exists():
                continue
            broken.append((f, q, url, path))

    fixable = []
    totally_missing = []
    for f, q, url, path in broken:
        parent = path.parent
        qn_m = re.search(r'q(\d+)\.png$', path.name)
        if not qn_m or not parent.exists():
            totally_missing.append((f, q, url))
            continue
        qn = int(qn_m.group(1))
        candidates = []
        for fmt in ('02d', '03d', 'd'):
            cand = parent / f'q{qn:{fmt}}.png'
            if cand != path and cand.exists():
                candidates.append(cand)
        if candidates:
            rel = candidates[0].as_posix().replace('public/', '', 1)
            new_url = '/' + rel
            fixable.append((f, q, url, new_url))
        else:
            totally_missing.append((f, q, url))

    print(f'死链总 {len(broken)}')
    print(f'  可改名修复 = {len(fixable)}')
    print(f'  完全缺失 = {len(totally_missing)}')

    if fixable:
        print('\n=== 可改名样本 ===')
        for f, q, old, new in fixable[:5]:
            print(f'  {q["id"]}\n    {old} -> {new}')

    # apply 改名
    if args.apply and fixable:
        # 按文件聚合，每个文件读一次写一次
        by_file = {}
        for f, q, old, new in fixable:
            by_file.setdefault(str(f), []).append((q['id'], new))
        n_changed = 0
        for fp, updates in by_file.items():
            data = json.loads(Path(fp).read_text(encoding='utf-8'))
            id_to_new = dict(updates)
            for q in data:
                if q.get('id') in id_to_new and q.get('questionImage'):
                    q['questionImage'] = id_to_new[q['id']]
                    n_changed += 1
            Path(fp).write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
        print(f'\n[APPLY] 已修 {n_changed} 个 questionImage URL')

    # drop missing
    if args.drop_missing and totally_missing:
        by_file = {}
        for f, q, url in totally_missing:
            by_file.setdefault(str(f), set()).add(q['id'])
        n_dropped = 0
        for fp, ids in by_file.items():
            data = json.loads(Path(fp).read_text(encoding='utf-8'))
            for q in data:
                if q.get('id') in ids and 'questionImage' in q:
                    del q['questionImage']
                    n_dropped += 1
            Path(fp).write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
        print(f'\n[DROP] 已删 {n_dropped} 个死链 questionImage 字段')


if __name__ == '__main__':
    main()
