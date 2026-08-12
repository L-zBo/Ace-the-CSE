#!/usr/bin/env python3
"""用官方答案解析 PDF 修复串题的 explanation。

现象两类，都是 PDF 抽取跨题串行留下的：
  - 一道题的 explanation 里挂着好几道题的解析（最狠的一条 19458 字、
    含 57 个「故正确答案为」，等于把整份答案表塞进了一道题）
  - explanation 只有一个结论，但和 answer 对不上

前一个脚本 resolve_answer_conflicts.py 解决的是「答案错了」；这个脚本
解决的是「答案对、解析串了」。两者互补，证据链也不同：

  1. 官方**真题** PDF 里第 N 题的正文含库里第 N 题题干前 12 字 —— 编号锚定
  2. 官方**答案解析** PDF 里第 N 题块的结论 == 库里 answer —— 说明库里
     answer 与官方一致，那么与之矛盾的现有 explanation 必然是串来的
  3. 用该块替换 explanation

两步锚定都过才替换。过不了就不动，进报告。绝不拿解析去反推答案 ——
那是推导不是证据。

用法：
  python scripts/repair_explanations_from_pdf.py            # 预览
  python scripts/repair_explanations_from_pdf.py --apply    # 落盘
输出：reports/explanation_repair.json
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

PLACEHOLDER = ['OCR 抽取失败', 'OCR抽取失败', 'OCR 提取失败',
               '题目缺失', '暂缺', '正在全力以赴征集']
CONCLUSION = re.compile(r'故正确答案为\s*([A-D]+)')
# 其余机构的结论句式。与 scripts/fix_cross_paper_answers.py 同源，
# 都要求结论后面跟标点或换行，避免把正文里的「答案是否正确」之类误抓成结论。
EXTRA_CONCLUSION = [
    re.compile(r'故正确答案?[为选是]?[:：]?\s*([A-D]+)(?=[\s，,。.、\)）])'),
    re.compile(r'因此[，,]?\s*选择\s*([A-D]+)(?:\s*选项)?(?=[\s。.，,])'),
    re.compile(r'【\s*答案\s*】\s*([A-D]+)(?=[\s。.，,\n】])'),
    re.compile(r'(?:正确答案|参考答案|答案)[：:]\s*([A-D]+)(?=[\s，。、\)）（(\n])'),
    re.compile(r'(?:正确答案|参考答案|答案)\s*[是为][：:]?\s*([A-D]+)(?=[\s，。、\)）\n])'),
    # 正确答案:【B】 / 正确答案是：【B】 —— 广西/海南/湖南/贵州的块首标记
    re.compile(r'(?:正确答案|参考答案|答案)\s*[是为]?\s*[：:]?\s*【\s*([A-D]+)\s*】'),
]
# 解析里挂着的别题标记，形如「【48—正确答案 D】」
FOREIGN_MARK = re.compile(r'【\s*(\d{1,3})\s*[—\-－]\s*正确答案')
QNUM = re.compile(r'(?m)^[ \t]*(\d{1,3})[ \t]*[、．.]?[ \t]*(?=\S)')
YEAR_MARK = re.compile(r'(20\d\d)\s*年\s*(\d{0,2})\s*月?\s*全国事业单位联考')
JUNK = re.compile(
    r'公考事业编学习资料加微信\s*AS73982|老师微信：\s*AS73982|事业单位联考真题'
    r'|获取试卷更新[^\n]*|整理：杨柳[^\n]*|公众号：[^\n]*', re.M)

PROVINCE_CN = {
    'guangdong': '广东', 'chongqing': '重庆', 'shenzhen': '深圳', 'xinjiang': '新疆',
    'fujian': '福建', 'shanghai': '上海', 'jiangsu': '江苏', 'shandong': '山东',
    'tianjin': '天津', 'anhui': '安徽', 'hebei': '河北', 'neimenggu': '内蒙古',
    'zhejiang': '浙江', 'jiangxi': '江西', 'sichuan': '四川', 'hainan': '海南',
    'hunan': '湖南', 'hubei': '湖北', 'henan': '河南', 'shanxi': '山西',
    'shaanxi': '陕西', 'gansu': '甘肃', 'qinghai': '青海', 'ningxia': '宁夏',
    'jilin': '吉林', 'liaoning': '辽宁', 'heilongjiang': '黑龙江', 'yunnan': '云南',
    'guizhou': '贵州', 'guangxi': '广西', 'beijing': '北京',
}
LEVEL_CN = {'fushengjia': ['副省级', '省级'], 'dishi': ['地市级', '市级'],
            'xingzhengzhifa': ['行政执法']}

MIN_LEN = 40        # 太短的块当没抽到
MAX_LEN = 3000      # 超过这个长度多半又串了，不采信


def norm(s):
    return re.sub(r'\s+', '', str(s or ''))


def flat_answer(a):
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
            cache[path] = '\n'.join(pg.get_text(sort=True) for pg in d)
            d.close()
        except Exception:
            cache[path] = ''
    return cache[path]


def find_pdfs(paper):
    """paper -> (真题 PDF, 答案解析 PDF)"""
    year = re.search(r'(\d{4})', paper).group(1)
    if paper.startswith('institution'):
        m = re.match(r'institution_\d{4}_([a-e])$', paper)
        cls = m.group(1).upper() if m else ''
        return ([p.replace('\\', '/') for p in
                 glob.glob(f'material/**/{cls}类/职测/*真题.pdf', recursive=True)],
                [p.replace('\\', '/') for p in
                 glob.glob(f'material/**/{cls}类/职测/*真题答案解析.pdf', recursive=True)])
    if paper.startswith('national'):
        root = 'material/【国考】2000-2025真题pdf/2000-2025国考行测PDF'
        q = [p.replace('\\', '/') for p in glob.glob(f'{root}/行测-真题/*.pdf') if year in p]
        a = [p.replace('\\', '/') for p in glob.glob(f'{root}/行测-答案及解析/*.pdf') if year in p]
        lv = re.search(r'_(fushengjia|dishi|xingzhengzhifa)$', paper)
        if lv:
            kws = LEVEL_CN[lv.group(1)]
            q = [p for p in q if any(k in p for k in kws)] or q
            a = [p for p in a if any(k in p for k in kws)] or a
        return q, a
    m = re.match(r'provincial_([a-z]+)_(\d{4})', paper)
    cn = PROVINCE_CN.get(m.group(1)) if m else None
    if not cn:
        return [], []
    allp = [p.replace('\\', '/') for p in
            glob.glob('material/【省考】2000-2025真题pdf/**/*.pdf', recursive=True)]
    same = [p for p in allp if cn in p and year in p and '行测' in p]
    a = [p for p in same if '答案' in p or '解析' in p]
    return [p for p in same if p not in a], a


def sections(paper, text):
    """事业编 PDF 是多年合集，必须按年份切开再用。"""
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


def split_blocks(text):
    """按题号切块，只认单调递增成链的题号序列。

    早先见到数字就当题号，页码、「/ 43」、金额都会被当成题号，把块切碎、
    切串（dedupe 脚本里实测把第 3 题切到第 7 题解析的尾巴上）。
    真题和解析的题号一定递增，取最长递增链后噪声自然掉光。
    """
    text = JUNK.sub('', text)
    ms = [(int(m.group(1)), m) for m in QNUM.finditer(text)]
    best = []
    for s in range(min(40, len(ms))):
        chain = [ms[s]]
        last = ms[s][0]
        for n, m in ms[s + 1:]:
            if last < n <= last + 4:
                chain.append((n, m))
                last = n
        if len(chain) > len(best):
            best = chain
    out = {}
    for i, (n, m) in enumerate(best):
        end = best[i + 1][1].start() if i + 1 < len(best) else len(text)
        out.setdefault(n, []).append(text[m.end():end])
    return out


MARK_HEAD = re.compile(r'【\s*(?:解析)?\s*(\d{1,3})\s*[—\-－]\s*正确答案\s*([A-D]+)\s*】')

# 第三类排版：题号裹在标记里，既不在行首、也不是「【N—正确答案X】」。
# 实测四种，按可靠性排序（带答案的排前面）：
#   第【2】题正确答案:【B】     广西 / 海南 / 湖南 2023
#   第2 题 …… 正确答案是：【B】 贵州 2023
#   【解析2—正确答案D】         河北 2024（MARK_HEAD 已放宽兼容）
#   【2】本题考查……            甘肃 2023，只有题号没有答案
# 这些卷用行首裸数字切块只能切出 10 来个噪声题号（范围里混着 0 和 832），
# 整卷等于没解析可用。
HEAD_PATTERNS = [
    re.compile(r'第\s*【\s*(\d{1,3})\s*】\s*题\s*正确答案\s*[:：]?\s*【?\s*[A-D]+\s*】?'),
    re.compile(r'(?m)^第\s*(\d{1,3})\s*题\s*$'),
    MARK_HEAD,
    re.compile(r'(?m)^【\s*(\d{1,3})\s*】\s*(?=\S)'),
]


def split_blocks_headed(text):
    """按「题目头标记」切块，覆盖 HEAD_PATTERNS 里的几种排版。

    每种格式单独匹配、取命中最多的一种，不混用 —— 混着切会把块切碎，
    一道题的解析被拆成好几段，反而全都短到过不了 MIN_LEN。
    """
    text = JUNK.sub('', text)
    best = []
    for rgx in HEAD_PATTERNS:
        ms = [m for m in rgx.finditer(text) if 1 <= int(m.group(1)) <= 200]
        if len(ms) > len(best):
            best = ms
    out = {}
    for i, mm in enumerate(best):
        end = best[i + 1].start() if i + 1 < len(best) else len(text)
        # 块首保留标记本身，块内的「正确答案:【X】」才能被结论正则抽到
        out.setdefault(int(mm.group(1)), []).append(text[mm.start():end])
    return out


def split_blocks_marked(text):
    """另一种解析 PDF 排版：每题以「【48—正确答案 D】」开头，题号不在行首。

    黑龙江 / 吉林 2024 这两套用的就是这个格式，按行首数字切块一个都切不出来。
    """
    text = JUNK.sub('', text)
    marks = list(MARK_HEAD.finditer(text))
    out = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        # 把「正确答案 X】」留在块首，后面统一按结论正则识别
        out.setdefault(int(m.group(1)), []).append(text[m.start():end])
    return out


def block_conclusions(t):
    """块内的答案结论。

    各家机构的解析 PDF 结论句式不统一，只认「故正确答案为X」会漏掉一大片 ——
    实测江苏 2022 整卷用的都是「因此，选择D 选项」，5 道题因此卡在「无结论」。
    这里的句式集与 scripts/fix_cross_paper_answers.py 保持一致。

    返回的是**去重前**的列表：调用方靠 set() 后是否仍为 1 个来判断块干不干净，
    所以同一结论被多个句式重复命中不影响判定，混进别题结论才会被拦下。
    """
    out = CONCLUSION.findall(t) + [m.group(2) for m in MARK_HEAD.finditer(t)]
    for rgx in EXTRA_CONCLUSION:
        out.extend(rgx.findall(t))
    return out


def collect(arr):
    """挑出解析可疑的题：多结论、唯一结论与 answer 矛盾，或解析里带着别的题号。"""
    out = []
    for q in arr:
        if not isinstance(q, dict):
            continue
        if any(x in str(q.get('content') or '') for x in PLACEHOLDER):
            continue
        exp = str(q.get('explanation') or '')
        ans = flat_answer(q.get('answer'))
        num = str(q.get('id', '')).rsplit('-', 1)[-1].lstrip('0')
        if not ans or not exp:
            continue
        # 解析开头挂着「【48—正确答案 D】」这种别题标记 —— 整段都是别人的题
        if any(t.lstrip('0') != num for t in FOREIGN_MARK.findall(exp)):
            out.append(q)
            continue
        hits = CONCLUSION.findall(exp)
        if not hits:
            continue
        if len(hits) >= 2 or hits[0] != ans:
            out.append(q)
    return out


def split_blocks_naive(text):
    """见到行首题号就切。噪声多，但有些卷的题号不成连续链（分模块重新编号、
    多卷合并），链式切法一个块都切不出来，这时退回来用它兜底。"""
    text = JUNK.sub('', text)
    marks = list(QNUM.finditer(text))
    out = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.setdefault(int(m.group(1)), []).append(text[m.end():end])
    return out


def align(blocks, arr):
    hit = miss = 0
    for q in arr:
        if not isinstance(q, dict):
            continue
        if any(x in str(q.get('content') or '') for x in PLACEHOLDER):
            continue
        try:
            n = int(str(q.get('id', '')).rsplit('-', 1)[-1])
        except ValueError:
            continue
        probe = norm(q.get('content'))[:12]
        if len(probe) < 10 or n not in blocks:
            continue
        if any(probe in norm(b) for b in blocks[n]):
            hit += 1
        else:
            miss += 1
        if hit >= 6:
            break
    return hit, miss


def well_indexed(ablocks):
    """解析 PDF 的题号是否完整连续覆盖整卷。

    题面校验（topical）是防串题的主力，但它要求解析块里复述题干或选项 ——
    相当一部分解析 PDF 根本不复述，比如广西 2023 第 110 题的库内题干只有
    「不能从上述资料中推出的是：」12 个字，解析块直接从「A 项：根据文字材料」
    开讲，题面永远对不上。

    这种情况下题号本身就是可靠锚定，但前提是题号序列可信：从 1 开始、
    数量够多、几乎无断号。再叠加另外两道已有的保障 ——
      · 真题 PDF 那步已确认「库内第 N 题 == 官方卷第 N 题」（stem_not_anchored）
      · 块结论必须等于库内 answer（answer_conflict）
    三者同时成立时放宽 topical 是安全的。
    """
    ks = sorted(ablocks)
    if len(ks) < 30 or ks[0] != 1:
        return False
    return len(ks) >= (ks[-1] - ks[0] + 1) * 0.9


def clean(block):
    t = re.sub(r'\n{3,}', '\n\n', block).strip()
    return t


def topical(block, q):
    """解析块必须和这道题的题面对得上。

    只靠「块内结论字母 == 库里 answer」筛远远不够 —— 四选一，随便一道题都有
    1/4 概率撞上。实测这么筛出来 8 道，6 道是别的题的解析（「令尊∶史稿」的
    题配上「口若悬河∶喋喋不休」的解析）。

    这里认两条：题干的 6 字片段至少命中 2 个；或者至少 2 个选项的开头 10 字
    出现在块里（题干很短的题 —— 「下列做法在日常生活中不可行的是：」——
    只能靠选项来对）。
    """
    nb = norm(block)
    stem = norm(q.get('content'))
    grams = {stem[i:i + 6] for i in range(0, max(1, len(stem) - 5), 3)}
    if sum(1 for g in grams if len(g) == 6 and g in nb) >= 2:
        return True
    n = 0
    for o in q.get('options') or []:
        c = norm(o.get('content') if isinstance(o, dict) else '')
        if len(c) >= 8 and c[:10] in nb:
            n += 1
    return n >= 2


def main():
    cache = {}
    stats = Counter()
    records = []
    fixes = defaultdict(list)

    for path in sorted(glob.glob('src/data/xingce/*/*.json')):
        path = path.replace('\\', '/')
        paper = path.split('/')[-1][:-5]
        arr = json.load(io.open(path, encoding='utf-8'))
        targets = collect(arr)
        if not targets:
            continue
        stats['target'] += len(targets)

        qp, ap = find_pdfs(paper)
        if not qp or not ap:
            stats['no_pdf'] += len(targets)
            records.append({'paper': paper, 'verdict': 'no_pdf', 'count': len(targets)})
            continue

        # 编号锚定：真题 PDF 的题号体系必须和库里一致
        qblocks = None
        splitter = split_blocks
        for fn in (split_blocks, split_blocks_naive):
            for p in qp:
                for sec in sections(paper, pdf_text(p, cache)):
                    b = fn(sec)
                    h, m = align(b, arr)
                    if h >= 3 and m == 0:
                        qblocks, splitter = b, fn
                        break
                if qblocks:
                    break
            if qblocks:
                break
        if not qblocks:
            stats['align_failed'] += len(targets)
            records.append({'paper': paper, 'verdict': 'align_failed',
                            'count': len(targets)})
            continue

        ablocks = {}
        for p in ap:
            for sec in sections(paper, pdf_text(p, cache)):
                for fn in (splitter, split_blocks_marked, split_blocks_headed):
                    for k, v in fn(sec).items():
                        ablocks.setdefault(k, []).extend(v)
        indexed = well_indexed(ablocks)

        for q in targets:
            n = int(str(q.get('id', '')).rsplit('-', 1)[-1])
            ans = flat_answer(q.get('answer'))
            rec = {'paper': paper, 'id': q.get('id'), 'num': n, 'answer': ans}

            probe = norm(q.get('content'))[:12]
            if len(probe) < 10 or n not in qblocks or \
                    not any(probe in norm(b) for b in qblocks[n]):
                rec['verdict'] = 'stem_not_anchored'
                stats['stem_not_anchored'] += 1
                records.append(rec)
                continue

            good = []
            # 细分每个候选块的淘汰原因，否则 no_clean_block 只是个黑盒，
            # 没法判断该改清洗、改长度阈值还是改题面校验。
            why = Counter()
            for b in ablocks.get(n, []):
                t = clean(b)
                hits = block_conclusions(t)
                uniq = set(hits)
                # 同一个结论可能既出现在块首标记里、又出现在正文「故正确答案为」，
                # 去重后仍是 1 个才算干净。
                if len(uniq) == 0:
                    why['无结论'] += 1
                    continue
                if len(uniq) > 1:
                    why['多结论(串题)'] += 1
                    continue
                if len(t) < MIN_LEN:
                    why['过短'] += 1
                    continue
                if len(t) > MAX_LEN:
                    why['过长'] += 1
                    continue
                if not topical(t, q) and not indexed:
                    why['题面对不上'] += 1
                    continue
                good.append((t, hits[0]))
            # 三个切块器可能对同一题号切出多个块（粒度不同或范围重叠）。
            # 结论一致时那只是同一段解析的不同切法，取最完整的；
            # 结论不一致才是真歧义，交给 ambiguous_block 拦下。
            if len(good) > 1 and len({c for _, c in good}) == 1:
                good = [max(good, key=lambda x: len(x[0]))]
            if len(good) != 1:
                rec['verdict'] = 'no_clean_block' if not good else 'ambiguous_block'
                if not ablocks.get(n):
                    why['解析PDF无此题号'] += 1
                rec['why'] = dict(why)
                stats[rec['verdict']] += 1
                for k, v in why.items():
                    stats[f'why:{k}'] += v
                records.append(rec)
                continue

            new, official = good[0]
            # 本脚本的定位是「答案对、解析串了」，docstring 第 2 步要求块结论
            # == 库里 answer —— 那才能推出「与之矛盾的现有 explanation 是串来的」。
            # 结论不一致时说明这是另一码事（多为跨机构版本分歧），改答案需要
            # 跨源佐证，不是这里该干的活，交给 fix_cross_paper_answers.py。
            #
            # 实测拦下的 3 道全是江苏 2022 的图形选项题：新旧解析都在完整论证
            # 同一道题，只是结论不同，且选项是图无法独立复核。
            if official != ans:
                rec['verdict'] = 'answer_conflict'
                rec['official_answer'] = official
                stats['answer_conflict'] += 1
                records.append(rec)
                continue

            if norm(new) == norm(q.get('explanation')) and official == ans:
                rec['verdict'] = 'same'
                stats['same'] += 1
                records.append(rec)
                continue

            rec.update({'verdict': 'repair', 'old_len': len(str(q.get('explanation') or '')),
                        'new_len': len(new), 'new_head': new[:100],
                        'official_answer': official})
            stats['repair'] += 1
            if official != ans:
                stats['answer_also_fixed'] += 1
            records.append(rec)
            fixes[path].append({'id': q.get('id'), 'old': str(q.get('explanation') or ''),
                                'new': new, 'old_answer': q.get('answer'),
                                'new_answer': official})

    os.makedirs('reports', exist_ok=True)
    json.dump(records, io.open('reports/explanation_repair.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    print(f'解析可疑题 {stats["target"]} 道')
    print(f'两步锚定通过、可用官方解析替换：{stats["repair"]} 道'
          f'（其中 {stats["answer_also_fixed"]} 道 answer 同时被官方结论纠正）')
    for k in ('no_pdf', 'align_failed', 'stem_not_anchored', 'no_clean_block',
              'ambiguous_block', 'answer_conflict', 'same'):
        if stats[k]:
            print(f'  未修 {k:20} {stats[k]}')
    shown = 0
    for items in fixes.values():
        for f in items:
            if shown >= 5:
                break
            print(f'  {f["id"]}  {len(f["old"])} 字 -> {len(f["new"])} 字')
            print(f'      新: {f["new"][:80]!r}')
            shown += 1

    if APPLY and fixes:
        n = 0
        for path, items in fixes.items():
            raw = io.open(path, 'rb').read()
            arr = json.loads(raw.decode('utf-8'))
            trailing = raw.endswith(CRLF.encode())
            assert dump(arr, trailing) == raw, path
            idx = {q.get('id'): q for q in arr}
            for f in items:
                q = idx.get(f['id'])
                if q is not None and str(q.get('explanation') or '') == f['old']:
                    q['explanation'] = f['new']
                    na = f['new_answer']
                    q['answer'] = na if len(na) == 1 else list(na)
                    n += 1
            io.open(path, 'wb').write(dump(arr, trailing))
        print(f'\n已写盘：修复 {n} 条解析，涉及 {len(fixes)} 个文件')
    else:
        print('\n预览模式，未写盘。加 --apply 落盘。')


if __name__ == '__main__':
    main()
