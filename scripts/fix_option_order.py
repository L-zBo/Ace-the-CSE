#!/usr/bin/env python3
"""按 label 重排选项数组。

背景：PDF 双栏 2×2 排版被按列读取，导致 1,941 道题的选项数组顺序是
A,C,B,D 之类。label 与内容的配对是完好的，只是数组顺序错，而
OptionList.tsx 按数组顺序渲染，用户看到的选项就是乱序的。

安全约束（不满足就跳过并报告，绝不猜）：
  - 只重排，不改任何 label / content 文本
  - 重排前后 (label, content) 的集合必须完全一致
  - label 有重复的题跳过（排序有歧义）

用法：
  python scripts/fix_option_order.py            # 预览
  python scripts/fix_option_order.py --apply    # 落盘
"""
import glob
import io
import json
import os
import sys
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

APPLY = '--apply' in sys.argv


def dump(arr, trailing_newline=True):
    """按题库既有格式序列化：CRLF + indent=2，结尾换行按原文件而定。

    全库实测只有两种形态：CRLF+indent2 带结尾换行 1175 个、不带 205 个。
    """
    crlf = chr(13) + chr(10)
    text = json.dumps(arr, ensure_ascii=False, indent=2).replace(chr(10), crlf)
    if trailing_newline:
        text += crlf
    return text.encode('utf-8')


def main():
    stats = Counter()
    skipped = []
    changed_files = 0

    for path in sorted(glob.glob('src/data/*/*/*.json')):
        raw = io.open(path, 'rb').read()
        arr = json.loads(raw.decode('utf-8'))
        if not isinstance(arr, list):
            continue
        # 题库 JSON 统一是 CRLF + indent=2 + 结尾换行。先确认按这个格式重新序列化
        # 能得到字节完全一致的结果，否则说明格式假设不成立，宁可中止也不要
        # 让 411 个文件产生满屏无关 diff。
        trailing = raw.endswith(chr(13).encode() + chr(10).encode())
        if dump(arr, trailing) != raw:
            print(f'[中止] {path} 的格式与预期不符，未做任何修改')
            sys.exit(1)

        dirty = False
        for q in arr:
            if not isinstance(q, dict):
                continue
            opts = q.get('options')
            if not isinstance(opts, list) or len(opts) < 2:
                continue
            if not all(isinstance(o, dict) and o.get('label') for o in opts):
                continue

            labels = [o['label'] for o in opts]
            if labels == sorted(labels):
                continue

            stats['out_of_order'] += 1
            if len(set(labels)) != len(labels):
                skipped.append(f'{path}#{q.get("id")} label 重复 {labels}')
                stats['skipped_dup_label'] += 1
                continue

            before = sorted(
                (o['label'], json.dumps(o, ensure_ascii=False, sort_keys=True))
                for o in opts
            )
            new_opts = sorted(opts, key=lambda o: o['label'])
            after = sorted(
                (o['label'], json.dumps(o, ensure_ascii=False, sort_keys=True))
                for o in new_opts
            )
            # 不变量：只允许顺序变化，内容一个字都不能动
            assert before == after, f'{path}#{q.get("id")} 重排改动了内容'

            q['options'] = new_opts
            stats['fixed'] += 1
            dirty = True

        if dirty:
            changed_files += 1
            if APPLY:
                io.open(path, 'wb').write(dump(arr, trailing))

    print(f'选项乱序题目：{stats["out_of_order"]}')
    print(f'  已重排：{stats["fixed"]}')
    print(f'  跳过（label 重复）：{stats["skipped_dup_label"]}')
    print(f'涉及文件：{changed_files}')
    for s in skipped[:10]:
        print('   跳过', s)
    print('\n' + ('已写盘。' if APPLY else '预览模式，未写盘。加 --apply 落盘。'))


if __name__ == '__main__':
    main()
