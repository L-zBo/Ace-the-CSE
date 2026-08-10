#!/usr/bin/env python3
"""用官方真题 + 答案解析 PDF 双向校验，解决「答案与解析矛盾」。

问题：120 道题的 answer 字段与解析结论对不上（PDF 抽取整块串行所致），
光凭解析改答案是"推导"不是"证据"。

之前失败的做法：直接拿题干去「答案解析」PDF 里搜 —— 命中率 4/120，
因为解析 PDF 普遍不重复完整题干，只按题号列答案。

本脚本的做法（双向校验，两步都过才采信）：
  1. 到**真题** PDF 里按题干原文定位，确认该题在原卷中的题号 == 库里的题号
     —— 这一步锁定「我们说的第 N 题就是原卷第 N 题」
  2. 再到同一套的**答案解析** PDF 的同一年份分节里，取第 N 题的【答案】
     —— 题号已被第 1 步锚定，这里取到的答案才可信

任一步不过就跳过，不猜。

用法：
  python scripts/resolve_answer_conflicts.py            # 预览
  python scripts/resolve_answer_conflicts.py --apply    # 落盘
输出：reports/answer_resolution.json
"""
import glob
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

APPLY = '--apply' in sys.argv

PLACEHOLDER = ['OCR 抽取失败', 'OCR抽取失败', 'OCR 提取失败',
               '题目缺失', '暂缺', '正在全力以赴征集']
CONCLUSION = re.compile(r'故正确答案为\s*([A-D]+)\s*[。.]?')
YEAR_MARK = re.compile(r'(20\d\d)\s*年\s*(\d{0,2})\s*月?\s*全国事业单位联考')

CRLF = chr(13) + chr(10)


def norm(s):
    return re.sub(r'\s+', '', str(s or ''))


def flat_answer(a):
    """多选题 answer 存成 ['A','B']，这里拍平成 'AB' 再与 PDF 结论比对。

    不这么做的话，脚本第二次跑会把已修正的数组又判成「需修正」，不幂等。
    """
    if isinstance(a, list):
        return ''.join(str(x) for x in a)
    return str(a or '')


def dump(arr, trailing):
    t = json.dumps(arr, ensure_ascii=False, indent=2).replace(chr(10), CRLF)
    return (t + CRLF if trailing else t).encode('utf-8')


def pdf_text(path, cache):
    if path not in cache:
        try:
            d = pymupdf.open(path)
            cache[path] = '\n'.join(pg.get_text() for pg in d)
            d.close()
        except Exception:
            cache[path] = ''
    return cache[path]


def split_sections(text):
    """按「20XX 年 X 月全国事业单位联考」切分，返回 [(year, month, 正文), ...]"""
    marks = [(m.start(), m.group(1), m.group(2)) for m in YEAR_MARK.finditer(text)]
    out = []
    for i, (pos, y, mo) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out.append((y, mo, text[pos:end]))
    return out


def collect_conflicts():
    out = []
    for path in sorted(glob.glob('src/data/xingce/*/*.json')):
        base = os.path.basename(path)[:-5]
        for q in json.load(io.open(path, encoding='utf-8')):
            if any(p in str(q.get('content') or '') for p in PLACEHOLDER):
                continue
            exp = str(q.get('explanation') or '')
            ans = flat_answer(q.get('answer'))
            hits = CONCLUSION.findall(exp)
            if len(hits) == 1 and ans and hits[0] != ans:
                out.append({
                    'json': path.replace('\\', '/'), 'paper': base,
                    'id': q.get('id'), 'num': int(q.get('id', '0').rsplit('-', 1)[-1]),
                    'answer_field': ans, 'exp_says': hits[0],
                    'stem': norm(q.get('content'))[:20],
                })
    return out


def find_num_in_section(sec_norm, sec_raw, stem):
    """在分节正文里定位题干，返回它前面最近的题号。"""
    i = sec_norm.find(stem)
    if i < 0:
        return None
    # 往前找最近的「数字．」或「数字、」
    head = sec_norm[max(0, i - 12):i]
    m = None
    for mm in re.finditer(r'(\d{1,3})[.．、]', head):
        m = mm
    return int(m.group(1)) if m else None


def main():
    conflicts = collect_conflicts()
    inst = [c for c in conflicts if c['paper'].startswith('institution')]
    print(f'答案冲突总数 {len(conflicts)}，其中事业编 {len(inst)}')

    cache = {}
    results = []
    stats = Counter()

    for c in conflicts:
        c['official'] = None
        c['evidence'] = None
        m = re.match(r'institution_(\d{4})_([a-e])$', c['paper'])
        if not m:
            stats['skip_not_institution'] += 1
            results.append(c)
            continue
        year, cls = m.group(1), m.group(2).upper()

        q_pdfs = [p.replace('\\', '/') for p in
                  glob.glob(f'material/**/{cls}类/职测/*真题.pdf', recursive=True)]
        a_pdfs = [p.replace('\\', '/') for p in
                  glob.glob(f'material/**/{cls}类/职测/*真题答案解析.pdf', recursive=True)]
        if not q_pdfs or not a_pdfs:
            stats['skip_no_pdf'] += 1
            results.append(c)
            continue

        # 第 1 步：在真题 PDF 里锁定题号
        qt = pdf_text(q_pdfs[0], cache)
        hit_sec = None
        for y, mo, sec in split_sections(qt):
            if y != year:
                continue
            n = find_num_in_section(norm(sec), sec, c['stem'])
            if n is not None:
                hit_sec = (y, mo, n)
                break
        if hit_sec is None:
            stats['step1_stem_not_found'] += 1
            results.append(c)
            continue
        if hit_sec[2] != c['num']:
            stats['step1_num_mismatch'] += 1
            c['evidence'] = f'真题PDF中该题为第{hit_sec[2]}题，与库里第{c["num"]}题不符'
            results.append(c)
            continue

        # 第 2 步：在解析 PDF 的同年同月分节里取第 N 题答案
        at = pdf_text(a_pdfs[0], cache)
        got = None
        for y, mo, sec in split_sections(at):
            if y != hit_sec[0] or (hit_sec[1] and mo and mo != hit_sec[1]):
                continue
            mm = re.search(rf'(?m)^\s*{c["num"]}\s*[.．、]\s*【答案】\s*([A-D]+)', sec)
            if mm:
                got = mm.group(1)
                break
        if got is None:
            stats['step2_answer_not_found'] += 1
            results.append(c)
            continue

        c['official'] = got
        c['evidence'] = f'真题PDF {year}年{hit_sec[1]}月第{c["num"]}题题干匹配；解析PDF同节【答案】{got}'
        stats['resolved'] += 1
        results.append(c)

    os.makedirs('reports', exist_ok=True)
    json.dump(results, io.open('reports/answer_resolution.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    ok = [c for c in results if c['official']]
    need_fix = [c for c in ok if c['official'] != c['answer_field']]
    already = [c for c in ok if c['official'] == c['answer_field']]
    print(f'\n双向校验通过 {len(ok)} 道：')
    print(f'  官方答案 != 库里 answer  -> 需修正 {len(need_fix)} 道')
    print(f'  官方答案 == 库里 answer  -> 解析是串来的，answer 本来就对 {len(already)} 道')
    print('\n未解决原因：')
    for k, v in stats.most_common():
        if k != 'resolved':
            print(f'  {k:28} {v}')

    if need_fix:
        print('\n需修正样例：')
        for c in need_fix[:6]:
            print(f'  {c["id"]}  {c["answer_field"]} -> {c["official"]}   ({c["evidence"]})')

    if APPLY and need_fix:
        by_json = defaultdict(list)
        for c in need_fix:
            by_json[c['json']].append(c)
        changed = 0
        for path, items in by_json.items():
            raw = io.open(path, 'rb').read()
            arr = json.loads(raw.decode('utf-8'))
            trailing = raw.endswith(CRLF.encode())
            assert dump(arr, trailing) == raw, path
            idx = {q.get('id'): q for q in arr}
            for c in items:
                q = idx.get(c['id'])
                if q is not None:
                    off = c['official']
                    q['answer'] = list(off) if len(off) > 1 else off
                    changed += 1
            io.open(path, 'wb').write(dump(arr, trailing))
        print(f'\n已写盘：修正 {changed} 道')
    else:
        print('\n预览模式，未写盘。加 --apply 落盘。')


if __name__ == '__main__':
    main()
