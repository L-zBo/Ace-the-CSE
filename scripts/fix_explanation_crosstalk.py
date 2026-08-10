#!/usr/bin/env python3
"""截掉解析尾部串进来的邻题内容。

PDF 抽取时整块串行，导致一道题的 explanation 尾部粘着后面若干题的解析，
形如：

    ……故正确答案为 B。
    81.  【答案】D
    【解析】根据提问方式中的……

用户在解析面板会直接看到别人的题。

保守规则（三条同时满足才切，否则跳过）：
  1. 解析里出现 ≥2 次「故正确答案为」
  2. **首个**结论与本题 answer 字段一致 —— 不一致说明这题本身答案存疑，
     属于需要回源人工核的另一类问题，不在这里动
  3. 首个结论之后的尾巴确实长得像「另一道题」（含 `NN. 【答案】` /
     `【NN—正确答案` / `NN. 【解析】` 这类题号标记）

用法：
  python scripts/fix_explanation_crosstalk.py            # 预览
  python scripts/fix_explanation_crosstalk.py --apply    # 落盘
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

CONCLUSION = re.compile(r'故正确答案为\s*([A-D]+)\s*[。.]?')
# 尾巴里出现这些，才认定是「另一道题」
NEXT_Q = re.compile(r'(\d{1,3}\s*[.．、]\s*【\s*(答案|解析)|【\s*\d{1,3}\s*[—\-－]\s*正确答案)')
PLACEHOLDER = ['OCR 抽取失败', 'OCR抽取失败', 'OCR 提取失败',
               '题目缺失', '暂缺', '正在全力以赴征集']


def dump(arr, trailing):
    crlf = chr(13) + chr(10)
    text = json.dumps(arr, ensure_ascii=False, indent=2).replace(chr(10), crlf)
    if trailing:
        text += crlf
    return text.encode('utf-8')


def main():
    stats = Counter()
    samples = []
    changed_files = 0

    for path in sorted(glob.glob('src/data/xingce/*/*.json')):
        raw = io.open(path, 'rb').read()
        arr = json.loads(raw.decode('utf-8'))
        trailing = raw.endswith(chr(13).encode() + chr(10).encode())
        if dump(arr, trailing) != raw:
            print(f'[中止] {path} 格式与预期不符')
            sys.exit(1)

        dirty = False
        for q in arr:
            exp = str(q.get('explanation') or '')
            _a = q.get('answer')
            # 多选题 answer 是 ['A','B']，拍平成 'AB' 才能跟解析结论比
            ans = ''.join(str(x) for x in _a) if isinstance(_a, list) else str(_a or '')
            if any(p in str(q.get('content') or '') for p in PLACEHOLDER):
                continue
            hits = list(CONCLUSION.finditer(exp))
            if len(hits) < 2:
                continue
            stats['multi'] += 1

            if hits[0].group(1) != ans:
                stats['skip_answer_mismatch'] += 1
                continue

            cut = hits[0].end()
            tail = exp[cut:]
            # 尾巴里还有第二个「故正确答案为」，本身就证明那是另一道题的解析
            # （一道题不会有两个结论）。再加一道防线：尾巴太短可能只是重述，跳过。
            if len(tail.strip()) < 60 and not NEXT_Q.search(tail):
                stats['skip_tail_unclear'] += 1
                continue

            new = exp[:cut].rstrip()
            if new != exp:
                if len(samples) < 3:
                    samples.append((q.get('id'), len(exp), len(new), tail[:90]))
                q['explanation'] = new
                stats['truncated'] += 1
                dirty = True

        if dirty:
            changed_files += 1
            if APPLY:
                io.open(path, 'wb').write(dump(arr, trailing))

    print(f'解析含多个结论的题：{stats["multi"]}')
    print(f'  已截断：{stats["truncated"]}')
    print(f'  跳过（首个结论与 answer 不符，留待人工）：{stats["skip_answer_mismatch"]}')
    print(f'  跳过（尾巴不像另一道题）：{stats["skip_tail_unclear"]}')
    print(f'涉及文件：{changed_files}')
    for qid, a, b, tail in samples:
        print(f'\n  {qid}: {a} -> {b} 字')
        print(f'    删掉的尾巴开头: {tail!r}')
    print('\n' + ('已写盘。' if APPLY else '预览模式，未写盘。加 --apply 落盘。'))


if __name__ == '__main__':
    main()
