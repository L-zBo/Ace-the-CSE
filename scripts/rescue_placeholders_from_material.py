#!/usr/bin/env python3
"""用 material/ 下的官方真题 PDF 复原「不可作答」的占位题。

背景：库里 55 道题的题干是占位符（「OCR 抽取失败」「题目缺失」之类），
历次救援只翻过公开网站，一直没系统性回到本机 material/ 的 2555 份官方 PDF。
实测这些卷子（北京 2023、新疆 2023、吉林 2024、甘肃 2024、内蒙 2023…）
在 material/ 里真题和答案解析都齐，文本层也完整。

铁规矩：题干、选项、答案、来源证据四者成链才准入库。所以：

  1. **先证明编号对齐**：抽本卷若干道非占位题，要求「PDF 里第 N 题的正文
     包含库里第 N 题题干前 12 字」。命中 >= 3 且无冲突，才认为 PDF 的题号
     体系和库里一致。不做这步，题号错一位就会把整卷补错。
  2. 再对每个占位题号取 PDF 块，切出题干与 A/B/C/D 四个选项
  3. 到同套的答案解析 PDF 里取该题号的答案
  4. 题干非空 + 恰好 4 个选项且标号为 ABCD + 答案在 A-D 内，四者齐全才产出

任何一步不过就不动。产出全部先落报告，`--apply` 才写库。

用法：
  python scripts/rescue_placeholders_from_material.py            # 预览
  python scripts/rescue_placeholders_from_material.py --apply    # 落盘
输出：reports/placeholder_rescue.json
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
CRLF = chr(13) + chr(10)

# 题号：行首数字，后面可跟顿号/点，也可能只跟空格（北京卷就是 "1  正文"）
QNUM = re.compile(r'(?m)^[ \t]*(\d{1,3})[ \t]*[、．.]?[ \t]+(?=\S)')
OPT = re.compile(r'(?:(?<=\s)|^)([A-D])\s*[、．.]\s*')
ANSWER_PAT = [
    r'(?m)^\s*{n}\s*[.．、]\s*【答案】\s*([A-D]+)',
    r'(?m)^\s*{n}\s*[.．、]\s*答案[：:]\s*([A-D]+)',
    r'(?m)^\s*{n}\s*[.．、]?\s+【答案】\s*([A-D]+)',
    r'【\s*{n}\s*】\s*【?答案】?\s*[：:]?\s*([A-D]+)',
]
JUNK = re.compile(
    r'公考事业编学习资料加微信\s*AS73982|老师微信：\s*AS73982|事业单位联考真题'
    r'|获取试卷更新[^\n]*|整理：杨柳[^\n]*|公众号：[^\n]*'
    r'|^[ \t]*[·・]?[ \t]*第?\s*\d{1,4}\s*页?[ \t]*[·・]?[ \t]*$'
    r'|^[ \t]*-[ \t]*\d{1,3}[ \t]*-[ \t]*$', re.M)

PROVINCE_CN = {
    'beijing': '北京', 'xinjiang': '新疆', 'jilin': '吉林', 'gansu': '甘肃',
    'neimenggu': '内蒙古', 'shandong': '山东',
}


def norm(s):
    return re.sub(r'\s+', '', str(s or ''))


def dump(arr, trailing):
    t = json.dumps(arr, ensure_ascii=False, indent=2).replace(chr(10), CRLF)
    return (t + CRLF if trailing else t).encode('utf-8')


def load_markers():
    """占位判定与 src/lib/placeholder.ts 保持同一份真相源。"""
    m = json.load(io.open('src/lib/markers.json', encoding='utf-8'))
    return m['placeholderMarkers'], m['sourcePlaceholderShort']


OCR_MARKERS, SHORT_PLACEHOLDERS = load_markers()


def is_placeholder_text(s):
    s = str(s or '')
    if not s:
        return False
    if any(m in s for m in OCR_MARKERS):
        return True
    if '题目正在全力以赴征集' in s:
        return True
    t = s.strip()
    return any(t == p or t == p + '。' or t == p + '.' for p in SHORT_PLACEHOLDERS)


def is_placeholder(q):
    """等价于 placeholder.ts 的 isUnanswerable（占位题且无兜底图）。"""
    if q.get('questionImage'):
        return False
    if is_placeholder_text(q.get('content')):
        return True
    opts = q.get('options') or []
    if not opts:
        return False
    bad = sum(1 for o in opts
              if isinstance(o, dict) and is_placeholder_text(o.get('content')))
    return bad >= 2


def pdf_text(path, cache):
    if path not in cache:
        try:
            d = pymupdf.open(path)
            cache[path] = '\n'.join(pg.get_text(sort=True) for pg in d)
            d.close()
        except Exception:
            cache[path] = ''
    return cache[path]


def find_pdfs(paper):
    """paper 文件名 -> (真题 PDF 列表, 答案解析 PDF 列表)"""
    year = re.search(r'(\d{4})', paper).group(1)
    if paper.startswith('institution'):
        m = re.match(r'institution_\d{4}_([a-e])$', paper)
        cls = m.group(1).upper() if m else ''
        q = glob.glob(f'material/**/{cls}类/职测/*真题.pdf', recursive=True)
        a = glob.glob(f'material/**/{cls}类/职测/*真题答案解析.pdf', recursive=True)
        return ([p.replace('\\', '/') for p in q],
                [p.replace('\\', '/') for p in a])

    m = re.match(r'provincial_([a-z]+)_(\d{4})', paper)
    cn = PROVINCE_CN.get(m.group(1)) if m else None
    if not cn:
        return [], []
    allp = [p.replace('\\', '/') for p in
            glob.glob('material/【省考】2000-2025真题pdf/**/*.pdf', recursive=True)]
    same = [p for p in allp if cn in p and year in p and '行测' in p]
    a = [p for p in same if '答案' in p or '解析' in p]
    return [p for p in same if p not in a], a


def split_blocks(text):
    text = JUNK.sub('', text)
    marks = list(QNUM.finditer(text))
    out = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.setdefault(int(m.group(1)), []).append(text[m.end():end])
    return out


YEAR_MARK = re.compile(r'(20\d\d)\s*年\s*(\d{0,2})\s*月?\s*全国事业单位联考')


def sections(paper, text):
    """事业编 PDF 是 2018-2024 多年合集，必须按年份切开。

    不切的话，「第 70 题」在整册里有 7 个（每年一个），随手取第一个就等于
    把 2018 年的题当成 2022 年的题补进库 —— 那是编数据。
    """
    if not paper.startswith('institution'):
        return [text]
    year = re.search(r'(\d{4})', paper).group(1)
    marks = [(m.start(), m.group(1)) for m in YEAR_MARK.finditer(text)]
    out = []
    for i, (pos, y) in enumerate(marks):
        if y != year:
            continue
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out.append(text[pos:end])
    return out


def check_alignment(blocks, arr):
    """用非占位题验证 PDF 题号与库里题号是同一套编号。"""
    hit = miss = 0
    for q in arr:
        if is_placeholder(q):
            continue
        try:
            n = int(str(q.get('id', '')).rsplit('-', 1)[-1])
        except ValueError:
            continue
        if n not in blocks:
            continue
        probe = norm(q.get('content'))[:12]
        if len(probe) < 8:
            continue
        if any(probe in norm(b) for b in blocks[n]):
            hit += 1
        else:
            miss += 1
        if hit >= 6:
            break
    return hit, miss


def parse_block(block):
    """块 -> (题干, [{label, content}])。切不出 4 个 ABCD 选项就返回 None。"""
    hits = list(OPT.finditer(block))
    if len(hits) < 4:
        return None
    # 取最后一组连续 A→B→C→D
    start = None
    for i in range(len(hits) - 3):
        if [hits[i + k].group(1) for k in range(4)] == ['A', 'B', 'C', 'D']:
            start = i
            break
    if start is None:
        return None
    stem = re.sub(r'\s+', ' ', block[:hits[start].start()]).strip()
    opts = []
    for k in range(4):
        i = start + k
        end = hits[i + 1].start() if i + 1 < len(hits) else len(block)
        body = re.sub(r'\s+', ' ', block[hits[i].end():end]).strip()
        opts.append({'label': hits[i].group(1), 'content': body})
    if not stem or any(not o['content'] for o in opts):
        return None
    return stem, opts


def find_answer(text, n):
    """取第 n 题答案。【答案】标记与「故正确答案为」两路都取，都有就必须一致。

    只信一路的话，PDF 抽取跨题串行时很容易取到隔壁题的结论 —— 这正是库里
    120 道「答案与解析矛盾」的成因，不能在补题时再犯一遍。
    """
    tagged = None
    for pat in ANSWER_PAT:
        m = re.search(pat.format(n=n), text)
        if m:
            tagged = m.group(1)
            break

    concluded = None
    for m in re.finditer(rf'(?m)^\s*{n}\s*[、.．]?\s+', text):
        seg = text[m.end():m.end() + 4000]
        nxt = re.search(rf'(?m)^\s*{n + 1}\s*[、.．]?\s+', seg)
        if nxt:
            seg = seg[:nxt.start()]
        got = re.search(r'故正确答案为\s*([A-D]+)|正确答案[是为：:]\s*([A-D]+)', seg)
        if got:
            concluded = got.group(1) or got.group(2)
            break

    if tagged and concluded and tagged != concluded:
        return None
    return tagged or concluded


def main():
    stats = Counter()
    records = []
    fixes = defaultdict(list)
    cache = {}

    for path in sorted(glob.glob('src/data/xingce/*/*.json')):
        path = path.replace('\\', '/')
        paper = path.split('/')[-1][:-5]
        arr = json.load(io.open(path, encoding='utf-8'))
        ph = [q for q in arr if isinstance(q, dict) and is_placeholder(q)]
        if not ph:
            continue
        stats['placeholder'] += len(ph)

        qp, ap = find_pdfs(paper)
        if not qp:
            stats['no_question_pdf'] += len(ph)
            records.append({'paper': paper, 'verdict': 'no_question_pdf',
                            'count': len(ph)})
            continue

        picked = None
        for p in qp:
            for sec in sections(paper, pdf_text(p, cache)):
                blocks = split_blocks(sec)
                hit, miss = check_alignment(blocks, arr)
                if hit >= 3 and miss == 0:
                    picked = (p, blocks, hit)
                    break
            if picked:
                break
        if not picked:
            stats['align_failed'] += len(ph)
            records.append({'paper': paper, 'verdict': 'align_failed',
                            'count': len(ph), 'pdfs': [os.path.basename(x) for x in qp]})
            continue

        p, blocks, hit = picked
        atext = ''
        for x in ap:
            for sec in sections(paper, pdf_text(x, cache)):
                atext += sec + '\n'

        for q in ph:
            n = int(str(q.get('id', '')).rsplit('-', 1)[-1])
            rec = {'paper': paper, 'id': q.get('id'), 'num': n,
                   'pdf': os.path.basename(p), 'align_hits': hit}
            cands = blocks.get(n) or []
            parsedList = [r for r in (parse_block(b) for b in cands) if r]
            # 同一年份分节里第 N 题应当只有一处。出现多处说明切块串了，宁可不补。
            if len(parsedList) != 1:
                if any(is_placeholder_text(norm(b)) for b in cands):
                    # 官方 PDF 在这一题上写的就是「暂缺」
                    rec['verdict'] = 'pdf_also_placeholder'
                elif not parsedList:
                    rec['verdict'] = 'no_block_or_options'
                else:
                    rec['verdict'] = 'ambiguous_block'
                stats[rec['verdict']] += 1
                records.append(rec)
                continue
            parsed = parsedList[0]
            stem, opts = parsed
            # PDF 自己就是残卷的情况（吉林 2024 那份文件名直接写着「暂缺10题左右」，
            # 缺的题在 PDF 里同样是「题目正在全力以赴征集」+ 四个「缺失」）。
            # 把占位符从 PDF 搬回库里不是复原，是自欺。
            bad_opt = sum(1 for o in opts if is_placeholder_text(o['content']))
            if is_placeholder_text(stem) or bad_opt >= 2:
                rec['verdict'] = 'pdf_also_placeholder'
                stats['pdf_also_placeholder'] += 1
                records.append(rec)
                continue
            ans = find_answer(atext, n) if atext else None
            if not ans or len(ans) > 4:
                rec['verdict'] = 'no_answer'
                rec['stem'] = stem[:60]
                stats['no_answer'] += 1
                records.append(rec)
                continue
            labels = [o['label'] for o in opts]
            if any(c not in labels for c in ans):
                rec['verdict'] = 'answer_label_mismatch'
                stats['answer_label_mismatch'] += 1
                records.append(rec)
                continue
            rec.update({'verdict': 'rescue', 'stem': stem, 'options': opts,
                        'answer': ans,
                        'answerPdf': os.path.basename(ap[0]) if ap else ''})
            stats['rescue'] += 1
            records.append(rec)
            fixes[path].append(rec)

    os.makedirs('reports', exist_ok=True)
    json.dump(records, io.open('reports/placeholder_rescue.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    print(f'占位题 {stats["placeholder"]} 道')
    print(f'四要素齐全可复原：{stats["rescue"]} 道')
    for k in ('no_question_pdf', 'align_failed', 'no_block_or_options',
              'ambiguous_block', 'pdf_also_placeholder', 'no_answer',
              'answer_label_mismatch'):
        if stats[k]:
            print(f'  未复原 {k:24} {stats[k]}')
    for items in list(fixes.values())[:2]:
        for r in items[:3]:
            print(f'  {r["id"]}  答案 {r["answer"]}')
            print(f'      题干 {r["stem"][:70]}')
            for o in r['options']:
                print(f'      {o["label"]}. {o["content"][:50]}')

    if APPLY and fixes:
        n = 0
        for path, items in fixes.items():
            raw = io.open(path, 'rb').read()
            arr = json.loads(raw.decode('utf-8'))
            trailing = raw.endswith(CRLF.encode())
            assert dump(arr, trailing) == raw, path
            idx = {q.get('id'): q for q in arr}
            for r in items:
                q = idx.get(r['id'])
                if q is None:
                    continue
                q['content'] = r['stem']
                q['options'] = r['options']
                q['answer'] = r['answer'] if len(r['answer']) == 1 else list(r['answer'])
                q['sourceEvidence'] = f'{r["pdf"]} 第{r["num"]}题；答案取自 {r["answerPdf"]}'
                n += 1
            io.open(path, 'wb').write(dump(arr, trailing))
        print(f'\n已写盘：复原 {n} 道')
    else:
        print('\n预览模式，未写盘。加 --apply 落盘。')


if __name__ == '__main__':
    main()
