#!/usr/bin/env python3
"""把 sourceLabel 里的拼音省份改成中文，并补上空的 sourceLabel。

背景：省考题的 sourceLabel 全库写成「2024年省考heilongjiang行测第114题」，
拼音直接暴露在答题页页眉（QuestionHeader）和新的跨卷关联提示里，用户看到的
就是这串洋文。另有 15 道题 sourceLabel 是空的。

省份中文名读 src/lib/regions.json —— 与前端 src/lib/regionNames.ts 同一份
真相源，不在脚本里另抄一份。

安全约束：
  - 只动 sourceLabel 这一个展示字段，不碰 id / answer / content
  - 拼音按整词替换（前后不得再接字母），长的先替换，避免部分匹配
  - 补空值时只用「同文件其它题的卷标签 + 本题题号」，卷标签不唯一就跳过报告，
    绝不自己拼「N年X考行测」这种模板
  - 写盘前做字节级格式校验，格式对不上直接中止

用法：
  python scripts/fix_source_label_region.py            # 预览
  python scripts/fix_source_label_region.py --apply    # 落盘
"""
import glob
import io
import json
import os
import re
import sys
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

APPLY = '--apply' in sys.argv

with open('src/lib/regions.json', encoding='utf-8') as _f:
    PROVINCES = json.load(_f)['provinces']

# 长拼音先替换：避免 shanxi 抢在 shanghai 之类的前面造成部分匹配
_ORDERED = sorted(PROVINCES.items(), key=lambda kv: -len(kv[0]))
PINYIN_RE = re.compile(
    '(?<![A-Za-z])(' + '|'.join(re.escape(k) for k, _ in _ORDERED) + ')(?![A-Za-z])',
    re.IGNORECASE,
)
QNO_IN_LABEL_RE = re.compile(r'第\d+题')
QNO_IN_ID_RE = re.compile(r'(\d+)$')


def dump(arr, trailing_newline=True):
    """按题库既有格式序列化：CRLF + indent=2，结尾换行按原文件而定。"""
    crlf = chr(13) + chr(10)
    text = json.dumps(arr, ensure_ascii=False, indent=2).replace(chr(10), crlf)
    if trailing_newline:
        text += crlf
    return text.encode('utf-8')


def to_chinese(label):
    return PINYIN_RE.sub(lambda m: PROVINCES[m.group(1).lower()], label)


def paper_label_of(source_label):
    """去掉「第N题」剩下的卷标签。没有题号标记则返回 None。"""
    if not source_label or not QNO_IN_LABEL_RE.search(source_label):
        return None
    return QNO_IN_LABEL_RE.sub('', source_label, count=1)


def main():
    stats = Counter()
    unfilled = []
    changed_files = 0

    for path in sorted(glob.glob('src/data/*/*/*.json')):
        raw = io.open(path, 'rb').read()
        arr = json.loads(raw.decode('utf-8'))
        if not isinstance(arr, list):
            continue
        trailing = raw.endswith(chr(13).encode() + chr(10).encode())
        if dump(arr, trailing) != raw:
            print(f'[中止] {path} 的格式与预期不符，未做任何修改')
            sys.exit(1)

        # 先把本文件已有的卷标签收齐，供补空值使用（拼音已折算成中文再收）
        templates = Counter()
        for q in arr:
            if not isinstance(q, dict):
                continue
            tpl = paper_label_of(to_chinese(q.get('sourceLabel') or ''))
            if tpl:
                templates[tpl] += 1

        dirty = False
        for q in arr:
            if not isinstance(q, dict):
                continue
            label = q.get('sourceLabel') or ''

            if not label:
                stats['empty'] += 1
                if len(templates) != 1:
                    unfilled.append(
                        f'{path}#{q.get("id")} 卷标签不唯一（{len(templates)} 种），未补')
                    stats['empty_skipped'] += 1
                    continue
                m = QNO_IN_ID_RE.search(q.get('id') or '')
                if not m:
                    unfilled.append(f'{path}#{q.get("id")} id 末尾无题号，未补')
                    stats['empty_skipped'] += 1
                    continue
                tpl = next(iter(templates))
                # 题号按同卷惯例去掉前导零，「007」显示成「第7题」
                q['sourceLabel'] = f'{tpl}第{int(m.group(1))}题'
                stats['empty_filled'] += 1
                dirty = True
                continue

            fixed = to_chinese(label)
            if fixed != label:
                q['sourceLabel'] = fixed
                stats['pinyin_fixed'] += 1
                dirty = True

        if dirty:
            changed_files += 1
            if APPLY:
                with open(path, 'wb') as f:
                    f.write(dump(arr, trailing))

    mode = '已落盘' if APPLY else '预览（加 --apply 落盘）'
    print(f'== sourceLabel 修复 · {mode} ==')
    print(f'拼音改中文 {stats["pinyin_fixed"]} 道')
    print(f'空 sourceLabel {stats["empty"]} 道 -> 补上 {stats["empty_filled"]} 道，'
          f'跳过 {stats["empty_skipped"]} 道')
    print(f'涉及文件 {changed_files} 个')
    for line in unfilled:
        print(f'  [未补] {line}')


if __name__ == '__main__':
    main()
