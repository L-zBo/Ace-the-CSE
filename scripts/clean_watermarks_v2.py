#!/usr/bin/env python3
"""清除解析/题干里残留的第三方引流水印。

这些是 PDF 页眉页脚被一起抽进来的碎片，用户在解析面板能直接看到，
例如「获取试卷更新，请关注公众号：gwyeasy…」。

安全约束：
  - 只删**精确字面量**，不做关键词匹配。
    题库里有大量含「关注」「公众号」的正常内容（如「呼吁社会关注老年人的
    精神和心理需求」），关键词匹配会误删。
  - 删除后把残留的多余空行收敛，但不动其余文字。
  - 页码碎片（`- 32 -`）不删：裸数字有可能是正文，风险大于收益。

用法：
  python scripts/clean_watermarks_v2.py            # 预览
  python scripts/clean_watermarks_v2.py --apply    # 落盘
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

# 按长的在前排，避免短的先匹配掉一半
PATTERNS = [
    r'获取试卷更新，请关注公众号：gwyeasy（公务员考试挺简单）[,，]\s*一个上岸考生分享经验和答疑的平台。',
    r'获取试卷更新，请关注',
    r'来源：[A-Z]\s*整理：杨柳（微信：gwy288）',
    r'整理：杨柳（微信：gwy288）',
    r'公众号：樱有尽有，获取',
    r'公众号：樱有尽有',
    r'（认准淘宝：[^）]{0,12}，微信：[^）]{0,12}，公众号：[^）]{0,12}）',
    r'杨柳（微信：gwy288，淘宝：杨柳真题）温馨提示：[^\n]{0,80}',
    # 上传者批注里的联系方式：只摘掉「杨柳（微信：xxx）」这段，保留后面的
    # 「注：此题有争议…」正文——那对做题的人是有用信息，不能连带删掉。
    r'杨柳\s*[（【\(]\s*微信：\s*gwy\d+\s*[）】\)]',
    r'[（\(]\s*微信：\s*gwy\d+\s*[）\)]',
    r'公考事业编学习资料加微信\s*AS73982',
    r'老师微信：\s*AS73982',
    r'^\s*20\d\d\s*国考《行测》（[^）]{2,10}）解析\s*$',
    # 山东 2025 那套 PDF 的页脚：客服电话 + 波浪线页码。
    # 波浪线页码只删 `~ 12 ~` 这种带波浪线的形式，裸数字仍然不碰
    # （裸数字有可能是正文，风险大于收益，见文件头说明）。
    r'全国服务电话[：:]\s*400-6353-\d{3}',
    r'~\s{0,4}\d{1,3}\s{0,4}~',
    r'上岸真题库\s*更多真题：https://www\.saztk\.com/\S*',
]
FIELDS = ('content', 'explanation', 'material', 'originalExplanation')

# 选项里的水印后面常跟着页码碎片（如「… - 2 - 获取试卷更新…」），
# 摘掉水印后再把选项尾部残留的页码去掉。只对选项做，正文不动。
PAGE_TAIL = re.compile(r'\s*-\s*\d{1,3}\s*-\s*$')


def dump(arr, trailing):
    crlf = chr(13) + chr(10)
    text = json.dumps(arr, ensure_ascii=False, indent=2).replace(chr(10), crlf)
    if trailing:
        text += crlf
    return text.encode('utf-8')


def clean(text):
    out = text
    for pat in PATTERNS:
        out = re.sub(pat, '', out, flags=re.MULTILINE)
    # 收敛因删除留下的空白：连续 3+ 空行压成 2 行，行尾空格去掉
    out = re.sub(r'[ \t]+(?=\n)', '', out)
    out = re.sub(r'\n{3,}', '\n\n', out)
    return out


def main():
    hits = Counter()
    changed_q = 0
    changed_files = 0
    samples = []

    for path in sorted(glob.glob('src/data/*/*/*.json')):
        raw = io.open(path, 'rb').read()
        arr = json.loads(raw.decode('utf-8'))
        if not isinstance(arr, list):
            continue
        trailing = raw.endswith(chr(13).encode() + chr(10).encode())
        if dump(arr, trailing) != raw:
            print(f'[中止] {path} 格式与预期不符，未做任何修改')
            sys.exit(1)

        dirty = False
        for q in arr:
            if not isinstance(q, dict):
                continue
            touched = False
            for f in FIELDS:
                v = q.get(f)
                if not isinstance(v, str) or not v:
                    continue
                for pat in PATTERNS:
                    n = len(re.findall(pat, v, flags=re.MULTILINE))
                    if n:
                        hits[pat] += n
                nv = clean(v)
                if nv != v:
                    if len(samples) < 3 and f == 'explanation':
                        samples.append((q.get('id'), v, nv))
                    q[f] = nv
                    touched = True
            for opt in (q.get('options') or []):
                if not isinstance(opt, dict):
                    continue
                v = opt.get('content')
                if not isinstance(v, str) or not v:
                    continue
                for pat in PATTERNS:
                    n = len(re.findall(pat, v, flags=re.MULTILINE))
                    if n:
                        hits[pat] += n
                cleaned = clean(v)
                if cleaned == v:
                    continue  # 这个选项本来就没水印，连空白都不动
                nv = PAGE_TAIL.sub('', cleaned.strip())
                if nv != v:
                    opt['content'] = nv
                    touched = True

            if touched:
                changed_q += 1
                dirty = True

        if dirty:
            changed_files += 1
            if APPLY:
                io.open(path, 'wb').write(dump(arr, trailing))

    print('命中次数：')
    for pat, n in hits.most_common():
        print(f'  ×{n:5}  {pat[:60]}')
    print(f'\n受影响题目 {changed_q}，文件 {changed_files}')
    for qid, before, after in samples:
        print(f'\n--- {qid}')
        print('  前:', repr(before[:180]))
        print('  后:', repr(after[:180]))
    print('\n' + ('已写盘。' if APPLY else '预览模式，未写盘。加 --apply 落盘。'))


if __name__ == '__main__':
    main()
