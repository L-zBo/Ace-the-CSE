#!/usr/bin/env python3
"""补回缺失的选项（库里只剩 A、C，B 和 D 整条没了）。

现象：`institution_2020_c` 第 161/162 题 label 序列是 ['A','C']，B 和 D
在抽取时整条丢失。用户看到的是一道只有两个选项的类比推理题。

证据链：
  1. 在官方真题 PDF 里按**题干原文**定位（不靠题号 —— 这两道题库里的编号
     161/162 和原卷的 61/62 本来就对不上）
  2. 解析出该处的 A/B/C/D 四个选项
  3. **要求库里现存的每个选项都与 PDF 逐字一致** —— 这一步证明定位到的
     就是这道题，而不是隔壁题
  4. 才把缺的那几个补进去，已有的一个不动

用法：
  python scripts/fill_missing_options.py            # 预览
  python scripts/fill_missing_options.py --apply    # 落盘
输出：reports/missing_options.json
"""
import glob
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import repair_explanations_from_pdf as R  # 复用 PDF 定位 / 分节 / 缓存
# 注意：R 在 import 时已经把 sys.stdout 换成 UTF-8 wrapper，这里不能再包一层
# —— 二次包裹会让先被回收的那个 wrapper 关掉底层 buffer，print 直接抛
# ValueError: I/O operation on closed file。

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

APPLY = '--apply' in sys.argv
CRLF = chr(13) + chr(10)
LABELS = ['A', 'B', 'C', 'D']
OPT = re.compile(r'([A-D])\s*[、．.]\s*')
PLACEHOLDER = ['OCR 抽取失败', 'OCR抽取失败', 'OCR 提取失败',
               '题目缺失', '暂缺', '正在全力以赴征集']


def dump(arr, trailing):
    t = json.dumps(arr, ensure_ascii=False, indent=2).replace(chr(10), CRLF)
    return (t + CRLF if trailing else t).encode('utf-8')


def parse_after(ntext, pos):
    """从归一化文本的 pos 处往后切出 A/B/C/D 四个选项。"""
    seg = ntext[pos:pos + 400]
    hits = list(OPT.finditer(seg))
    start = None
    for i in range(len(hits) - 3):
        if [hits[i + k].group(1) for k in range(4)] == LABELS:
            start = i
            break
    if start is None:
        return None
    out = {}
    for k in range(4):
        i = start + k
        end = hits[i + 1].start() if i + 1 < len(hits) else len(seg)
        body = seg[hits[i].end():end].strip()
        # D 后面没有下一个标号可截，会一路吃进下一题（"…电脑：开关：电灯63.考场：考试：考官"）。
        # 在「题号 + 中文」这种边界上切断。
        body = re.split(r'\d{1,3}\s*[.．、](?=[一-龥])', body)[0].strip()
        if not body:
            return None
        out[hits[i].group(1)] = body
    return out


def main():
    cache = {}
    stats = Counter()
    records = []
    fixes = defaultdict(list)

    for path in sorted(glob.glob('src/data/xingce/*/*.json')):
        path = path.replace('\\', '/')
        paper = path.split('/')[-1][:-5]
        arr = json.load(io.open(path, encoding='utf-8'))
        targets = []
        for q in arr:
            if not isinstance(q, dict):
                continue
            if any(x in str(q.get('content') or '') for x in PLACEHOLDER):
                continue
            opts = q.get('options') or []
            labels = [o.get('label') for o in opts if isinstance(o, dict)]
            # 只处理「标号是 ABCD 的真子集」的情况；两选项的判断题不在此列
            if 1 <= len(labels) < 4 and set(labels) < set(LABELS) \
                    and len(labels) == len(set(labels)) and len(labels) >= 2:
                targets.append(q)
        if not targets:
            continue
        stats['target'] += len(targets)

        qp, _ = R.find_pdfs(paper)
        if not qp:
            stats['no_pdf'] += len(targets)
            continue

        for q in targets:
            rec = {'id': q.get('id'), 'have': [o.get('label') for o in q['options']]}
            stem = R.norm(q.get('content'))
            if len(stem) < 6:
                rec['verdict'] = 'stem_too_short'
                stats['stem_too_short'] += 1
                records.append(rec)
                continue
            got = None
            for p in qp:
                for sec in R.sections(paper, R.pdf_text(p, cache)):
                    ns = R.norm(sec)
                    i = ns.find(stem[:24])
                    if i < 0:
                        continue
                    parsed = parse_after(ns, i + len(stem[:24]))
                    if parsed:
                        got = (os.path.basename(p), parsed)
                        break
                if got:
                    break
            if not got:
                rec['verdict'] = 'not_found'
                stats['not_found'] += 1
                records.append(rec)
                continue

            pdfname, parsed = got
            # 现存选项必须与 PDF 逐字一致，否则说明定位错了
            bad = [o['label'] for o in q['options']
                   if R.norm(o.get('content')) != R.norm(parsed.get(o['label']))]
            if bad:
                rec['verdict'] = 'existing_mismatch'
                rec['mismatch'] = bad
                stats['existing_mismatch'] += 1
                records.append(rec)
                continue

            add = [{'label': L, 'content': parsed[L]} for L in LABELS
                   if L not in rec['have']]
            rec.update({'verdict': 'fill', 'pdf': pdfname, 'add': add})
            stats['fill'] += 1
            records.append(rec)
            fixes[path].append((q.get('id'), add))

    os.makedirs('reports', exist_ok=True)
    json.dump(records, io.open('reports/missing_options.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    print(f'选项不全的题 {stats["target"]} 道，可补 {stats["fill"]} 道')
    for k in ('no_pdf', 'stem_too_short', 'not_found', 'existing_mismatch'):
        if stats[k]:
            print(f'  未补 {k:18} {stats[k]}')
    for r in records:
        if r.get('verdict') == 'fill':
            print(f'  {r["id"]}  现有 {r["have"]}  补 ' +
                  ' / '.join(f'{a["label"]}．{a["content"]}' for a in r['add']))

    if APPLY and fixes:
        n = 0
        for path, items in fixes.items():
            raw = io.open(path, 'rb').read()
            arr = json.loads(raw.decode('utf-8'))
            trailing = raw.endswith(CRLF.encode())
            assert dump(arr, trailing) == raw, path
            idx = {q.get('id'): q for q in arr}
            for qid, add in items:
                q = idx.get(qid)
                if q is None:
                    continue
                q['options'] = sorted(q['options'] + add,
                                      key=lambda o: LABELS.index(o['label']))
                n += 1
            io.open(path, 'wb').write(dump(arr, trailing))
        print(f'\n已写盘：补齐 {n} 道题的选项')
    else:
        print('\n预览模式，未写盘。加 --apply 落盘。')


if __name__ == '__main__':
    main()
