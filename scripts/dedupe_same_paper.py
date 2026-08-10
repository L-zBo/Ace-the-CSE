#!/usr/bin/env python3
"""清理同一份试卷文件里的重复题。

成因：浙江、深圳、江西、青海、北京这些省份同一年有 A/B/C 卷（或乡镇/县级/
省级、行测1/行测2），同一道题在不同卷里题号不同。入库时把多套卷合并进了
一个 JSON，「卷」这一维丢了，于是同一道题在同一份文件里出现两三次，
**而且各自的 answer 还不一样** —— 说明至少有一份是错的。

净重复量 190 道（把 questionImage 一并纳入签名，排除图形推理模板题的假阳性），
集中在浙江 2023(71)、浙江 2022(42)、深圳 2020(20)。

处理规则：

  1. 组内 answer 全一致 → 纯去重，保留第一份。信息零损失。
  2. 组内 answer 不一致 → 必须官方定夺。对每一份单独做双锚定：
     「这份的题号 N 在某套卷的真题 PDF 里正好就是这道题」→ 卷定下来了 →
     到同卷的答案解析 PDF 取第 N 题结论。
     各份解出来的官方答案必须彼此一致（同一道题跨卷答案当然应该一样），
     一致才采信；保留一份并写入官方答案，其余删除。
  3. 定不了卷、或各份解出来的官方答案互相打架 → 不动，进报告等人工。

删题是破坏性操作，所以只在 1（零损失）和 2（有官方证据）两种情况下做。

用法：
  python scripts/dedupe_same_paper.py            # 预览
  python scripts/dedupe_same_paper.py --apply    # 落盘
输出：reports/dedupe_same_paper.json
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
# 题号：可能是「12．」「12、」「12 正文」，也可能整行只有一个数字（浙江卷就是）
QNUM = re.compile(r'(?m)^[ \t]*(\d{1,3})[ \t]*(?:[、．.][ \t]*|[ \t]+|$)')
ANS = re.compile(r'故正确答案为\s*([A-D]+)|【答案】\s*([A-D]+)|正确答案[为是：:]\s*([A-D]+)'
                 r'|正确答案\s*([A-D]+)\s*】')

# 卷别标记，用来把真题 PDF 和它对应的答案解析 PDF 配上对
VOL_MARKS = ['A类', 'B类', 'C类', 'D类', 'E类', 'A卷', 'B卷', 'C卷',
             '副省级', '地市级', '行政执法', '乡镇', '县级', '省级', '市级', '区级',
             '行测1', '行测2', '思维能力测验', '选调']

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


def vol_key(path):
    b = os.path.basename(path)
    return frozenset(m for m in VOL_MARKS if m in b)


def pdf_pairs(paper):
    """返回 [(真题 PDF, 答案解析 PDF), ...]，按卷别配对。"""
    ym = re.search(r'(\d{4})', paper)
    year = ym.group(1) if ym else ''
    m = re.match(r'provincial_([a-z]+)_(\d{4})', paper)
    cn = PROVINCE_CN.get(m.group(1)) if m else None
    if not cn:
        return []
    allp = [p.replace('\\', '/') for p in
            glob.glob('material/【省考】2000-2025真题pdf/**/*.pdf', recursive=True)]
    same = [p for p in allp if cn in p and year in p
            and ('行测' in p or '思维能力测验' in p)]
    ans = [p for p in same if '答案' in p or '解析' in p]
    qs = [p for p in same if p not in ans]
    out = []
    for q in qs:
        k = vol_key(q)
        for a in ans:
            if vol_key(a) == k:
                out.append((q, a))
                break
    return out


_SPAN_CACHE = {}


def ordered_spans(text):
    """把整篇切成 {题号: 正文}，但只认**单调递增成链**的题号序列。

    为什么不能见到数字就当题号：PDF 里到处是页码、「/ 43」、年份、金额，
    随手取一个「3」会把第 3 题切到第 7 题解析的尾巴上（浙江 2022 实测踩过）。
    真题和解析的题号一定是 1,2,3,… 递增的，按最长递增链筛一遍，噪声自己就掉了。
    """
    key = id(text)
    if key in _SPAN_CACHE:
        return _SPAN_CACHE[key]
    ms = [(int(m.group(1)), m) for m in QNUM.finditer(text)]
    best = []
    for s in range(min(40, len(ms))):
        chain = [ms[s]]
        last = ms[s][0]
        for n, m in ms[s + 1:]:
            # 允许跳号（PDF 缺题很常见），但不许倒退、不许一步跨太远
            if last < n <= last + 4:
                chain.append((n, m))
                last = n
        if len(chain) > len(best):
            best = chain
    out = {}
    for i, (n, m) in enumerate(best):
        end = best[i + 1][1].start() if i + 1 < len(best) else len(text)
        out.setdefault(n, text[m.end():end])
    _SPAN_CACHE[key] = out
    return out


def span(text, n):
    return ordered_spans(text).get(n)


def answer_for(atext, n, q):
    """从答案解析全文里取第 n 题的答案。

    优先认「【解析12—正确答案C】」这种显式标记（浙江 2022 之后的排版）；
    否则用单调链切出来的第 n 题区间，在区间内找结论。
    """
    for pat in (rf'【\s*解析\s*{n}\s*[—\-－]\s*正确答案\s*([A-D]+)\s*】',
                rf'【\s*{n}\s*[—\-－]\s*正确答案\s*([A-D]+)\s*】'):
        m = re.search(pat, atext)
        if m:
            return m.group(1)
    seg = span(atext, n)
    if not seg:
        return None
    m = ANS.search(seg[:2500])
    return next((g for g in m.groups() if g), None) if m else None


def official_for(pairs, num, q, cache):
    """双锚定：题号 num 在哪套卷的真题里正好是这道题，就取那套卷解析里的答案。"""
    probe = norm(q.get('content'))[:20]
    if len(probe) < 12:
        return None, None
    for qpdf, apdf in pairs:
        seg = span(pdf_text(qpdf, cache), num)
        if not seg or probe not in norm(seg):
            continue
        got = answer_for(pdf_text(apdf, cache), num, q)
        if got:
            return got, os.path.basename(qpdf)
    return None, None


PAGE_FRAG = re.compile(r'[-—~～]\s*\d{1,3}\s*[-—~～]')
KEEP = re.compile(r'[^一-鿿A-Za-z0-9①-⑳]')


def sig_text(s):
    """比对用的归一化：抹掉页码碎片和全部标点。

    同一道题的两份抄件常常只差一个「（　）。」或者中间夹了个「-2-」页码，
    逐字比对会认成两道不同的题（审计里那 64 组就是这么漏掉的）。
    只留汉字/字母/数字/圈号来比，不同的题在这个粒度下也不会撞。
    """
    return KEEP.sub('', PAGE_FRAG.sub('', str(s or '')))


def opt_sig(q):
    """选项签名。同样只比汉字/字母/数字，抹掉尾巴上粘的 `）。）。` 之类垃圾。"""
    return tuple(sig_text(o.get('content')) for o in (q.get('options') or [])
                 if isinstance(o, dict))


def junk_score(q):
    """选项里的垃圾量：同签名下越长越可能是粘了尾巴。"""
    return sum(len(norm(o.get('content'))) for o in (q.get('options') or [])
               if isinstance(o, dict))


SECTION_JUNK = re.compile(r'部分包括|请根据题目要求|第[一二三四五六]部分|本部分|请开始答题'
                          r'|[一二三四五六][.．、]\s*(言语|数量|判断|资料|常识)')


def opt_badness(q):
    """这份抄件的选项有多脏 —— 用来在一组重复里挑最干净的那份留下。

    两种脏法：整条选项其实是章节导语（「二. 言语理解与表达：本部分包括…」），
    或者尾巴上挂着抽取残留的孤立数字（「傣族 3」）。
    """
    opts = [norm(o.get('content')) for o in (q.get('options') or [])
            if isinstance(o, dict)]
    if not opts:
        return 99
    lens = sorted(len(x) for x in opts)
    med = lens[len(lens) // 2] or 1
    bad = 0
    for c in opts:
        if SECTION_JUNK.search(c):
            bad += 2
        if len(c) > med * 3 + 20:
            bad += 1
        if re.search(r'[^\d]\d{1,3}$', c) and len(c) > 2:
            bad += 1
    return bad


def cluster(bucket):
    """题干与题图相同的一堆题里，把「选项至多差一处」的并成一组。

    审计里剩下的那批就卡在这：同一道题的两份抄件，一份的 D 选项被章节导语
    顶掉了，另一份的 B 选项尾巴上多个「3」。逐字比选项配不上对，
    但它们确确实实是同一道题。
    """
    sigs = [opt_sig(q) for q in bucket]
    n = len(bucket)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            a, b = sigs[i], sigs[j]
            if len(a) != len(b) or not a:
                continue
            diff = sum(1 for x, y in zip(a, b) if x != y)
            if diff <= 1:
                parent[find(i)] = find(j)
    out = defaultdict(list)
    for i, q in enumerate(bucket):
        out[find(i)].append(q)
    return [v for v in out.values() if len(v) > 1]


def main():
    cache = {}
    stats = Counter()
    records = []
    plans = defaultdict(list)   # path -> [(保留的 id, 官方答案 or None, [要删的 id])]

    for path in sorted(glob.glob('src/data/xingce/*/*.json')):
        path = path.replace('\\', '/')
        paper = path.split('/')[-1][:-5]
        arr = json.load(io.open(path, encoding='utf-8'))
        groups = defaultdict(list)
        for q in arr:
            if not isinstance(q, dict):
                continue
            if any(x in str(q.get('content') or '') for x in PLACEHOLDER):
                continue
            key = (sig_text(q.get('content')), str(q.get('questionImage') or ''))
            if len(key[0]) > 20:
                groups[key].append(q)
        dups = [g for bucket in groups.values() if len(bucket) > 1
                for g in cluster(bucket)]
        if not dups:
            continue

        pairs = None
        for grp in dups:
            ids = [q.get('id') for q in grp]
            answers = {flat_answer(q.get('answer')) for q in grp}
            rec = {'paper': paper, 'ids': ids,
                   'answers': [flat_answer(q.get('answer')) for q in grp]}
            stats['group'] += 1

            if len(answers) == 1:
                # 答案都一样，纯去重。选项垃圾最少的优先，再看解析谁全。
                best = min(grp, key=lambda x: (opt_badness(x), junk_score(x),
                                               -len(str(x.get('explanation') or ''))))
                rec['verdict'] = 'pure_dup'
                rec['keep'] = best.get('id')
                stats['pure_dup'] += 1
                stats['removed'] += len(grp) - 1
                records.append(rec)
                plans[path].append((best.get('id'), None,
                                    [i for i in ids if i != best.get('id')]))
                continue

            if pairs is None:
                pairs = pdf_pairs(paper)
            if not pairs:
                rec['verdict'] = 'no_pdf_pair'
                stats['no_pdf_pair'] += 1
                records.append(rec)
                continue

            resolved = {}
            for q in grp:
                num = int(str(q.get('id', '0')).rsplit('-', 1)[-1])
                off, src = official_for(pairs, num, q, cache)
                if off:
                    resolved[q.get('id')] = (off, src)
            offs = {v[0] for v in resolved.values()}
            if not offs:
                rec['verdict'] = 'unresolved'
                stats['unresolved'] += 1
                records.append(rec)
                continue
            if len(offs) > 1:
                # 同一道题跨卷答案不该不一样，出现了就说明定位有问题
                rec['verdict'] = 'official_conflict'
                rec['resolved'] = {k: v[0] for k, v in resolved.items()}
                stats['official_conflict'] += 1
                records.append(rec)
                continue

            official = offs.pop()
            # 保留选项最干净的那份，答案统一写成官方结论 —— 反正答案要被
            # 官方值覆盖，就没必要为了迁就某份的 answer 而留下脏选项。
            keep = min(grp, key=lambda x: (opt_badness(x), junk_score(x),
                                           -len(str(x.get('explanation') or '')))).get('id')
            rec.update({'verdict': 'resolved', 'official': official, 'keep': keep,
                        'evidence': {k: v[1] for k, v in resolved.items()}})
            stats['resolved'] += 1
            stats['removed'] += len(grp) - 1
            records.append(rec)
            plans[path].append((keep, official, [i for i in ids if i != keep]))

    os.makedirs('reports', exist_ok=True)
    json.dump(records, io.open('reports/dedupe_same_paper.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    print(f'同卷重复组 {stats["group"]}，可删除多余份 {stats["removed"]} 道')
    print(f'  答案一致、纯去重      {stats["pure_dup"]} 组')
    print(f'  答案打架、官方已定夺  {stats["resolved"]} 组')
    for k in ('no_pdf_pair', 'unresolved', 'official_conflict'):
        if stats[k]:
            print(f'  未处理 {k:20} {stats[k]} 组')
    shown = 0
    for r in records:
        if r['verdict'] == 'resolved' and shown < 6:
            print(f'  {r["paper"]}  {r["ids"]} answers={r["answers"]}'
                  f' -> 保留 {r["keep"].rsplit("-", 1)[-1]}，官方 {r["official"]}')
            shown += 1

    if APPLY and plans:
        removed = fixed = 0
        for path, items in plans.items():
            raw = io.open(path, 'rb').read()
            arr = json.loads(raw.decode('utf-8'))
            trailing = raw.endswith(CRLF.encode())
            assert dump(arr, trailing) == raw, path
            drop = set()
            idx = {q.get('id'): q for q in arr if isinstance(q, dict)}
            for keep, official, gone in items:
                drop.update(gone)
                if official and idx.get(keep) is not None:
                    idx[keep]['answer'] = (official if len(official) == 1
                                           else list(official))
                    fixed += 1
            new = [q for q in arr if not (isinstance(q, dict) and q.get('id') in drop)]
            removed += len(arr) - len(new)
            io.open(path, 'wb').write(dump(new, trailing))
        print(f'\n已写盘：删除重复 {removed} 道，纠正保留份答案 {fixed} 道，'
              f'涉及 {len(plans)} 个文件')
    else:
        print('\n预览模式，未写盘。加 --apply 落盘。')


if __name__ == '__main__':
    main()
