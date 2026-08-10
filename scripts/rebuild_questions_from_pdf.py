#!/usr/bin/env python3
"""整题重建：库里这道题的题干在官方真题 PDF 里压根不存在，而 PDF 在该题号上
有一道完整的题。

典型：北京 2023 第 4 题在库里是「①治国有常，利民为本②君子务本…」——
那其实是第 1 题的选项被拆成了一道独立的题，把真正的第 4 题挤没了。
官方 PDF 第 4 题是「党的二十大报告指出，健全就业公共服务体系……」，
题干、四个选项、解析全都在。

准入条件（全部满足才重建）：
  1. 库里题干（前 20 字）在本卷**任何一份**官方真题 PDF 里都找不到
  2. PDF 在该题号上的块是完整的：题干 ≥ 20 字 + A/B/C/D 四个非空选项
  3. 该 PDF 块的题干不是本卷里**其他**任何一道库内题的题干
     —— 否则重建就会造出一道重复题
  4. 同卷答案解析 PDF 能给出该题号的答案（结论唯一）

第 3 条是关键护栏：很多卷的 PDF 是网友回忆版，措辞与库里不同，
单看「找不到」会把大量正常题误判成假题。要求 PDF 那道题在库里也确实
缺席，才说明是库里丢了题而不是版本差异。

用法：
  python scripts/rebuild_questions_from_pdf.py            # 预览
  python scripts/rebuild_questions_from_pdf.py --apply    # 落盘
输出：reports/rebuild_questions.json
"""
import glob
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fix_options_from_pdf as F          # 复用 PDF 定位 / 切块 / 选项解析
# F 在 import 时把 sys.stdout 换成了 UTF-8 wrapper；下面 R 还会再换一个。
# 这里必须留住 F 那个 wrapper 的引用 —— 不留的话它先被 GC，析构时会关掉
# 底层 buffer，之后所有 print 都抛 ValueError: I/O operation on closed file。
_KEEP_WRAPPER = sys.stdout
import repair_explanations_from_pdf as R  # 复用答案解析 PDF 定位

APPLY = '--apply' in sys.argv
CRLF = chr(13) + chr(10)
MIN_STEM = 20

# PDF 那边也不干净的信号：残卷占位、页脚水印
JUNK_STEM = ['正在全力以赴征集', '题目缺失', '暂缺', '认准淘宝', '通关达人资料库',
             '获取试卷更新', '公众号：', '智库，获取']


def dump(arr, trailing):
    t = json.dumps(arr, ensure_ascii=False, indent=2).replace(chr(10), CRLF)
    return (t + CRLF if trailing else t).encode('utf-8')


def block_stem(block, opts_start):
    return re.sub(r'\s+', ' ', block[:opts_start]).strip()


def main():
    cache = {}
    stats = Counter()
    records = []
    fixes = defaultdict(list)

    # 先按试卷把库内所有题干收集起来（跨模块，同一套卷分散在多个 json 里）
    paper_files = defaultdict(list)
    for path in sorted(glob.glob('src/data/xingce/*/*.json')):
        path = path.replace('\\', '/')
        paper_files[path.split('/')[-1][:-5]].append(path)

    for paper, paths in sorted(paper_files.items()):
        pdfs = F.question_pdfs(paper)
        if not pdfs:
            continue
        blocks = []
        pdf_all = ''
        for p in pdfs:
            for sec in F.sections(paper, F.pdf_text(p, cache)):
                pdf_all += F.norm(sec)
                blocks.extend((os.path.basename(p), n, b)
                              for n, b in F.ordered_blocks(sec))
        if not blocks:
            continue
        by_num = {}
        for src, n, b in blocks:
            by_num.setdefault(n, (src, b))

        db = []
        for path in paths:
            for q in json.load(io.open(path, encoding='utf-8')):
                if isinstance(q, dict):
                    db.append((path, q))
        db_stems = {F.norm(q.get('content'))[:20] for _p, q in db
                    if len(F.norm(q.get('content'))) >= 20}

        _, apdfs = R.find_pdfs(paper)
        atext = ''
        for p in apdfs:
            for sec in R.sections(paper, R.pdf_text(p, cache)):
                atext += sec + '\n'

        # 逐个模块文件先验证题号对齐：本文件里题干能在 PDF **同号块**里找到的
        # 比例够高，才说明这份文件的编号体系和 PDF 一致，后面「第 N 题对不上」
        # 才能解释成这道题坏了。
        aligned = {}
        for path in paths:
            hit = tot = 0
            for p2, q in db:
                if p2 != path:
                    continue
                s = F.norm(q.get('content'))
                if len(s) < MIN_STEM:
                    continue
                n2 = int(str(q.get('id', '0')).rsplit('-', 1)[-1])
                if n2 not in by_num:
                    continue
                tot += 1
                if s[:20] in F.norm(by_num[n2][1]):
                    hit += 1
            aligned[path] = tot >= 8 and hit / tot >= 0.7

        for path, q in db:
            stem = F.norm(q.get('content'))
            num = int(str(q.get('id', '0')).rsplit('-', 1)[-1])
            stats['scanned'] += 1
            if len(stem) < MIN_STEM:
                # 题干本来就短（类比推理「睡眠不足：血压升高」才 11 字），
                # 「在 PDF 里搜不到」不能当成它是假题的证据。
                stats['db_stem_too_short'] += 1
                continue
            if not aligned.get(path):
                # 这个模块文件的题号跟 PDF 对不齐（多卷合并、模块切分不同），
                # 那么「第 N 题对不上」是编号问题而不是这道题坏了，不能拿
                # PDF 的第 N 题去覆盖它 —— 实测会把数量题换成常识题。
                stats['file_not_aligned'] += 1
                continue
            if stem[:20] in pdf_all:
                # 题干在 PDF 里能搜到就算正常。曾试过再收紧成「必须在自己的
                # 题号块里」，结果把一批题号只是排布不同的正常题批量换成了
                # 别的题（模块切分与 PDF 编号本就不一定一致），已撤销。
                continue
            if num not in by_num:
                stats['pdf_no_block'] += 1
                continue

            src, block = by_num[num]
            parsed = F.parse_options(block)
            if not parsed:
                stats['pdf_block_unparsable'] += 1
                continue
            clean = F.JUNK.sub('', block)
            hits = list(F.OPT.finditer(clean))
            first = next((h for i, h in enumerate(hits)
                          if [hits[i + k].group(1) for k in range(4)]
                          == F.LABELS and i + 3 < len(hits)), None)
            if first is None:
                stats['pdf_block_unparsable'] += 1
                continue
            new_stem = block_stem(clean, first.start())
            if len(F.norm(new_stem)) < MIN_STEM:
                stats['pdf_stem_too_short'] += 1
                continue
            # PDF 那份也是残卷（「题目正在全力以赴征集」），或者切出来的其实是
            # 页脚水印 —— 拿这种东西覆盖一道真题是倒退。
            if any(x in new_stem for x in JUNK_STEM):
                stats['pdf_stem_is_junk'] += 1
                continue
            # 重建是为了把被截断的题干补全，新题干只会更长；明显更短说明切错了
            if len(F.norm(new_stem)) < len(stem) * 0.6:
                stats['pdf_stem_shorter'] += 1
                continue
            if F.norm(new_stem)[:20] in db_stems:
                # PDF 那道题库里已经有了，说明只是措辞对不上，不是丢题
                stats['pdf_stem_already_in_db'] += 1
                continue
            ans = None
            if atext:
                blk = {n: b for n, b in F.ordered_blocks(atext)}.get(num)
                if blk:
                    hs = set(R.CONCLUSION.findall(blk)) | \
                         {m.group(2) for m in R.MARK_HEAD.finditer(blk)}
                    if len(hs) == 1:
                        ans = hs.pop()
            if not ans:
                stats['no_answer'] += 1
                continue

            stats['rebuild'] += 1
            records.append({'paper': paper, 'id': q.get('id'), 'num': num,
                            'pdf': src,
                            'old_stem': str(q.get('content'))[:90],
                            'new_stem': new_stem[:120],
                            'new_options': [o['content'][:50] for o in parsed],
                            'old_answer': q.get('answer'), 'new_answer': ans})
            fixes[path].append({'id': q.get('id'), 'stem': new_stem,
                                'options': parsed, 'answer': ans,
                                'evidence': f'{src} 第{num}题'})
    os.makedirs('reports', exist_ok=True)
    json.dump(records, io.open('reports/rebuild_questions.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    print(f'扫描 {stats["scanned"]} 道；可整题重建 {stats["rebuild"]} 道')
    for k in ('db_stem_too_short', 'file_not_aligned', 'pdf_no_block',
              'pdf_block_unparsable', 'pdf_stem_too_short', 'pdf_stem_is_junk',
              'pdf_stem_shorter', 'pdf_stem_already_in_db', 'no_answer'):
        if stats[k]:
            print(f'  跳过 {k:24} {stats[k]}')
    for r in records[:6]:
        print(f'  {r["id"]}  答案 {r["old_answer"]} -> {r["new_answer"]}  [{r["pdf"][:30]}]')
        print(f'      旧题干 {r["old_stem"][:60]!r}')
        print(f'      新题干 {r["new_stem"][:60]!r}')

    if APPLY and fixes:
        n = 0
        for path, items in fixes.items():
            raw = io.open(path, 'rb').read()
            arr = json.loads(raw.decode('utf-8'))
            trailing = raw.endswith(CRLF.encode())
            assert dump(arr, trailing) == raw, path
            idx = {q.get('id'): q for q in arr if isinstance(q, dict)}
            for f in items:
                q = idx.get(f['id'])
                if q is None:
                    continue
                q['content'] = f['stem']
                q['options'] = f['options']
                q['answer'] = (f['answer'] if len(f['answer']) == 1
                               else list(f['answer']))
                q['sourceEvidence'] = f['evidence']
                # 旧解析只在「结论与新答案对得上」时留着。对不上说明那段解析
                # 本来就是别的题的，留着只会误导；题干都换了还留错解析更糟。
                exp = str(q.get('explanation') or '')
                concl = set(R.CONCLUSION.findall(exp))
                if exp and (len(concl) != 1 or concl.pop() != f['answer']):
                    q.pop('explanation', None)
                n += 1
            io.open(path, 'wb').write(dump(arr, trailing))
        print(f'\n已写盘：重建 {n} 道题，涉及 {len(fixes)} 个文件')
    else:
        print('\n预览模式，未写盘。加 --apply 落盘。')


if __name__ == '__main__':
    main()
