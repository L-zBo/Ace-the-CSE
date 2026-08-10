#!/usr/bin/env python3
"""把多选题的 answer 从拼接字符串规范化成数组。

问题：库里有 36 道多选题的 answer 存成 'BC' / 'ABD' / 'ABCD' 这样的拼接串，
但前端代码（OptionList / QuestionPageClient / ExamSessionClient）判定多选
一律走 `Array.isArray(answer)` 分支：

    const answerSet = Array.isArray(answer) ? new Set(answer) : new Set([answer]);
    const isCorrect = Array.isArray(q.answer) ? q.answer.includes(sel) : q.answer === sel;

字符串 'ABCD' 会变成 Set{'ABCD'}，`has('A')` 为 false —— 结果是这些题
**提交后正确选项一个都不高亮，判分也永远算错**。

规范化成 ['A','B','C','D'] 后，既有代码的多选分支就能正常工作。

注意：这里只改 answer 的存储形态，不动 type 字段，也不实现多选作答交互
（当前 UI 仍是单选，选中任一正确选项即算对，这是既有语义）。

用法：
  python scripts/normalize_multi_answers.py            # 预览
  python scripts/normalize_multi_answers.py --apply    # 落盘
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
CRLF = chr(13) + chr(10)


def dump(arr, trailing):
    t = json.dumps(arr, ensure_ascii=False, indent=2).replace(chr(10), CRLF)
    return (t + CRLF if trailing else t).encode('utf-8')


def main():
    stats = Counter()
    samples = []
    files = 0

    for path in sorted(glob.glob('src/data/*/*/*.json')):
        raw = io.open(path, 'rb').read()
        arr = json.loads(raw.decode('utf-8'))
        if not isinstance(arr, list):
            continue
        trailing = raw.endswith(CRLF.encode())
        if dump(arr, trailing) != raw:
            print(f'[中止] {path} 格式与预期不符')
            sys.exit(1)

        dirty = False
        for q in arr:
            a = q.get('answer')
            if not isinstance(a, str):
                continue
            # 只处理纯字母且长度 >1 的（'AB'、'ABCD'），不碰申论的长答案
            if len(a) < 2 or not re.fullmatch(r'[A-Z]{2,6}', a):
                continue
            labels = [o.get('label') for o in (q.get('options') or [])
                      if isinstance(o, dict)]
            new = list(a)
            # 拆出来的每个字母都必须是本题真实存在的选项，否则不动
            if labels and not all(x in labels for x in new):
                stats['skip_label_missing'] += 1
                continue
            q['answer'] = new
            stats['normalized'] += 1
            if len(samples) < 5:
                samples.append((q.get('id'), a, new))
            dirty = True

        if dirty:
            files += 1
            if APPLY:
                io.open(path, 'wb').write(dump(arr, trailing))

    print(f'规范化 {stats["normalized"]} 道，涉及 {files} 个文件')
    if stats['skip_label_missing']:
        print(f'跳过（拆出的字母不在选项里）：{stats["skip_label_missing"]}')
    for qid, old, new in samples:
        print(f'   {qid}: {old!r} -> {new}')
    print('\n' + ('已写盘。' if APPLY else '预览模式，未写盘。加 --apply 落盘。'))


if __name__ == '__main__':
    main()
