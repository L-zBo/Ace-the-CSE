#!/usr/bin/env python3
"""用官方 PDF 核实跨卷同题的少数派答案。

背景：同一道真题在多套卷里出现，答案本该一样。`audit_cross_paper_answers.py`
找出 229 组矛盾，其中 75 组有明确多数派（如 10 个省写 C、1 个省写 B）。

**多数派只是线索，不是证据。** 项目铁规矩要求证据链完整，所以这里对每道
少数派可疑题都回官方 PDF 走双向校验，只有官方答案与多数派一致才改。

## 双向校验

1. **编号对齐**：在真题 PDF 里定位第 N 题，要求库内题干的连续子串命中该块。
   这一步证明「库里的第 N 题 == 官方卷的第 N 题」。只对题号不校题干的话，
   编号一偏就把隔壁题的答案抄过来了（吉林 020 当年就是这么补错的）。
2. **取官方答案**：在解析 PDF 里定位同一题号，抽「故正确答案为X」这类结论。

两步都过才采信。

## 一个必须说清的前提

`material/` 里那些「答案及解析」PDF 是**培训机构整理版，不是官方发布的标准答案**，
不同机构会给出相反答案。实测例子：2020 年联考「情商班」那道接语选择题，
宁夏那份写「正确答案 C，正确率 26%，易错项 B」，安徽那份写「正确答案 B，
正确率 60%，易错项 C」—— 两家机构互相打脸。

**而库内答案本来就是从这些 PDF 提取的。** 所以「PDF 与库内一致」是同义反复，
不构成独立证据。真正有价值的信号只有一个：

> 库内值 ≠ 本卷 PDF 值，且本卷 PDF 值 == 其他省同题的多数派

这说明当初从这份 PDF 提取时**抄错了**，且有跨省同题佐证。这类才改。

## 决策

| 情形 | 动作 |
|---|---|
| 本卷 PDF == 多数派，且 != 库内现值 | **改** —— 提取错误，三重印证 |
| 本卷 PDF == 库内现值 | 不改 —— 提取没错，是跨机构版本分歧，改了等于拿一家覆盖另一家 |
| 本卷 PDF 是第三个值 | 不改，落报告等人工 |
| 抽不出 / 编号对不齐 | 不改，落报告 |

## 护栏（都是真摔过的）

- 事业编 PDF 是 2018-2024 七年合集，必须先按年份分节，否则「第 32 题」有七个
- 题号只认单调递增成链的，避开页码噪声
- 题干校验要求**连续子串**命中，不能用字符出现率（图形题题干高度模板化，
  换个数字照样 90 分）
- 同卷有多份解析 PDF 时，答案必须一致，打架就弃权
- 解析块里必须出现「{答案字母} 项」的逐项分析，防止定位串到隔壁题
- 题干短于 15 字的一律跳过，锚不住
- 写盘带字节级格式校验

用法：
  python scripts/fix_cross_paper_answers.py            # 预览
  python scripts/fix_cross_paper_answers.py --apply    # 落盘
"""

import glob
import io
import json
import os
import re
import sys
from collections import Counter

import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

APPLY = '--apply' in sys.argv
CRLF = chr(13) + chr(10)

CONFLICTS = 'reports/cross_paper_answer_conflicts.json'
OUT_REPORT = 'reports/cross_paper_answer_resolution.json'

# 题干太短锚不住，直接放弃
MIN_STEM = 15
# 题干探针长度：从规范化题干里取连续子串去 PDF 块里找
PROBE_LEN = 18

# ---- 以下 PDF 定位 / 切块逻辑与 fix_options_from_pdf.py 同源，保持一致 ----

QNUM = re.compile(r'(?m)^[ \t]*(\d{1,3})[ \t]*(?:[、．.][ \t]*|[ \t]+|$)')
YEAR_MARK = re.compile(r'(20\d\d)\s*年\s*(\d{0,2})\s*月?\s*全国事业单位联考')

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

# 答案抽取。正则来源：scripts/fix_provincial_answers.py 积累的各省 PDF 格式，
# 按可靠性排序 —— 头部标记 > 结论句 > 裸答案。
ANS_HEAD = re.compile(
    r'【\s*(?:解析\s*)?\d{1,3}\s*[—\-－–]\s*正确答案\s*([A-D]+)\s*】')
ANS_PATTERNS = [
    re.compile(r'故正确答案?[为选是]?[:：]?\s*([A-D]+)(?=[\s，,。.、\)）])'),
    re.compile(r'因此[，,]?\s*选择\s*([A-D]+)(?:\s*选项)?(?=[\s。.，,])'),
    re.compile(r'【\s*答案\s*】\s*([A-D]+)(?=[\s。.，,\n】])'),
    re.compile(r'(?:正确答案|参考答案|答案)[：:]\s*([A-D]+)(?=[\s，。、\)）（(\n])'),
    re.compile(r'(?:正确答案|参考答案|答案)\s*[是为][：:]?\s*([A-D]+)(?=[\s，。、\)）\n])'),
]

_pdf_cache = {}


def norm(s):
    """只留中日韩汉字与字母数字，丢掉空白标点页码残留。"""
    return re.sub(r'[^0-9A-Za-z一-鿿]', '', str(s or ''))


def dump(arr, trailing):
    t = json.dumps(arr, ensure_ascii=False, indent=2).replace(chr(10), CRLF)
    return (t + CRLF if trailing else t).encode('utf-8')


def pdf_text(path):
    if path not in _pdf_cache:
        try:
            doc = pymupdf.open(path)
            _pdf_cache[path] = '\n'.join(pg.get_text(sort=True) for pg in doc)
            doc.close()
        except Exception as exc:
            print(f'  [警告] 读不了 {path}: {exc}')
            _pdf_cache[path] = ''
    return _pdf_cache[path]


def _all_pdfs():
    if '_all' not in _pdf_cache:
        _pdf_cache['_all'] = [p.replace(os.sep, '/')
                              for p in glob.glob('material/**/*.pdf', recursive=True)]
    return _pdf_cache['_all']


def _is_answer_pdf(path):
    return '答案' in path or '解析' in path


def paper_pdfs(paper, want_answer):
    """按试卷 key 找 PDF。want_answer=True 取解析卷，False 取真题卷。"""
    ym = re.search(r'(\d{4})', paper)
    if not ym:
        return []
    year = ym.group(1)

    if paper.startswith('institution'):
        m = re.match(r'institution_\d{4}_([a-e])$', paper)
        cls = m.group(1).upper() if m else ''
        cand = [p for p in _all_pdfs()
                if f'/{cls}类/职测/' in p and '真题' in p]
    elif paper.startswith('national'):
        cand = [p for p in _all_pdfs()
                if '【国考】' in p and year in p and '行测' in p]
        lv = re.search(r'_(fushengjia|dishi|xingzhengzhifa)$', paper)
        if lv:
            kws = LEVEL_CN[lv.group(1)]
            narrowed = [p for p in cand if any(k in p for k in kws)]
            cand = narrowed or cand
    else:
        m = re.match(r'provincial_([a-z]+)_(\d{4})', paper)
        cn = PROVINCE_CN.get(m.group(1)) if m else None
        if not cn:
            return []
        cand = [p for p in _all_pdfs()
                if '【省考】' in p and cn in p and year in p
                and ('行测' in p or '思维能力测验' in p)]

    return [p for p in cand if _is_answer_pdf(p) == want_answer]


def sections(paper, text):
    """事业编 PDF 是多年合集，必须按年份切开再定位题号。"""
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
    return out or [text]


def ordered_blocks(sec):
    """只认单调递增成链的题号，避开页码等噪声。返回 {题号: 块正文}。"""
    ms = [(int(m.group(1)), m) for m in QNUM.finditer(sec)]
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
        end = best[i + 1][1].start() if i + 1 < len(best) else len(sec)
        out[n] = sec[m.end():end]
    return out


def stem_hits(stem_norm, block_text):
    """库内题干的连续子串是否出现在 PDF 块里。

    用连续子串而不是字符重合率 —— 图形题题干高度模板化，
    按出现率算换个数字照样 90 分，会把 16 个正方体那题当成 17 个的。
    """
    blob = norm(block_text)
    if not blob:
        return False
    # 开头 / 三分之一处 / 中间 三个探针，命中任一即可（容忍 PDF 首尾噪声）
    starts = [0, len(stem_norm) // 3, len(stem_norm) // 2]
    for st in starts:
        probe = stem_norm[st:st + PROBE_LEN]
        if len(probe) >= PROBE_LEN and probe in blob:
            return True
    return False


def locate_block(paper, qno, want_answer):
    """在指定类型的 PDF 里找第 qno 题的块。返回 [(pdf路径, 块正文), ...]。"""
    found = []
    for pdf in paper_pdfs(paper, want_answer):
        text = pdf_text(pdf)
        if not text:
            continue
        for sec in sections(paper, text):
            blocks = ordered_blocks(sec)
            if qno in blocks:
                found.append((pdf, blocks[qno]))
    return found


def extract_answer(block, head_window):
    """从解析块里抽答案。头部标记优先，其次结论句。"""
    m = ANS_HEAD.search(head_window)
    if m:
        return m.group(1), 'head'
    for rgx in ANS_PATTERNS:
        m = rgx.search(block)
        if m:
            return m.group(1), rgx.pattern[:14]
    return '', ''


def load_questions(ids):
    """一次遍历题库，取出关心的题（题干、当前答案、所在文件）。

    answer 必须从题库实时读，不能用冲突报告里的快照 —— 否则落盘后再跑一遍，
    脚本仍拿着旧值，会报出同样的「可改」清单，看着像没生效。
    """
    out = {}
    for path in sorted(glob.glob('src/data/*/*/*.json')):
        with open(path, encoding='utf-8') as f:
            arr = json.load(f)
        if not isinstance(arr, list):
            continue
        for q in arr:
            if isinstance(q, dict) and q.get('id') in ids:
                ans = q.get('answer')
                out[q['id']] = {
                    'content': q.get('content') or '',
                    'answer': (''.join(str(x) for x in ans)
                               if isinstance(ans, list) else str(ans or '')),
                    'file': path.replace(os.sep, '/'),
                }
    return out


def main():
    with open(CONFLICTS, encoding='utf-8') as f:
        data = json.load(f)
    majority = [c for c in data['conflicts'] if c['verdict'] == 'majority']

    todo = []
    for c in majority:
        by_id = {m['id']: m for m in c['members']}
        for qid in c['suspects']:
            m = by_id[qid]
            todo.append({
                'id': qid,
                'file': m['file'],
                'qno': m['qno'],
                'current': m['answer'],
                'majority': c['majorityAnswer'],
                'votes': c['votes'],
                'paperLabel': m['paperLabel'],
            })

    qinfo = load_questions({t['id'] for t in todo})
    stats = Counter()
    resolved = []

    for t in todo:
        paper = os.path.basename(t['file'])[:-5]
        info = qinfo.get(t['id'])
        t['paper'] = paper
        if not info:
            t['status'] = 'question_not_found'
            stats['question_not_found'] += 1
            resolved.append(t)
            continue

        # 用题库实时值覆盖报告里的快照，保证重复运行幂等
        t['current'] = info['answer']
        stem_norm = norm(info['content'])
        if len(stem_norm) < MIN_STEM:
            t['status'] = 'stem_too_short'
            stats['stem_too_short'] += 1
            resolved.append(t)
            continue

        # ---- 第一步：真题 PDF 编号对齐 ----
        aligned_pdf = None
        for pdf, block in locate_block(paper, t['qno'], want_answer=False):
            if stem_hits(stem_norm, block):
                aligned_pdf = pdf
                break
        # 有些解析卷本身重复题干，真题卷缺失时退而求其次
        if not aligned_pdf:
            for pdf, block in locate_block(paper, t['qno'], want_answer=True):
                if stem_hits(stem_norm, block):
                    aligned_pdf = pdf
                    break
        if not aligned_pdf:
            t['status'] = 'no_stem_anchor'
            stats['no_stem_anchor'] += 1
            resolved.append(t)
            continue
        t['alignedPdf'] = aligned_pdf

        # ---- 第二步：解析 PDF 取答案。多份就必须互相一致 ----
        votes = {}
        for pdf, block in locate_block(paper, t['qno'], want_answer=True):
            ans, how = extract_answer(block, block[:120])
            if not ans:
                continue
            # 解析块必须逐项分析到答案那一项，否则多半是定位串到隔壁题了
            if not re.search(rf'{re.escape(ans[0])}\s*项', block):
                continue
            votes.setdefault(ans, []).append(f'{pdf} ({how})')

        if not votes:
            t['status'] = 'no_official_answer'
            stats['no_official_answer'] += 1
            resolved.append(t)
            continue
        if len(votes) > 1:
            t['status'] = 'pdf_disagree'
            t['pdfVotes'] = {k: v for k, v in votes.items()}
            stats['pdf_disagree'] += 1
            resolved.append(t)
            continue

        official = next(iter(votes))
        t['official'] = official
        t['officialSource'] = votes[official]

        # ---- 第三步：决策 ----
        if official == t['majority'] and official != t['current']:
            t['status'] = 'fix'
            stats['fix'] += 1
        elif official == t['current']:
            t['status'] = 'pdf_matches_current'
            stats['pdf_matches_current'] += 1
        elif official == t['majority'] and official == t['current']:
            t['status'] = 'already_correct'
            stats['already_correct'] += 1
        else:
            t['status'] = 'pdf_third_value'
            stats['pdf_third_value'] += 1
        resolved.append(t)

    # ---- 落盘 ----
    fixes = [t for t in resolved if t['status'] == 'fix']
    changed_files = 0
    if APPLY and fixes:
        by_file = {}
        for t in fixes:
            by_file.setdefault(t['file'], []).append(t)
        for path, items in sorted(by_file.items()):
            raw = io.open(path, 'rb').read()
            arr = json.loads(raw.decode('utf-8'))
            trailing = raw.endswith(CRLF.encode())
            if dump(arr, trailing) != raw:
                print(f'[中止] {path} 格式与预期不符，未做任何修改')
                sys.exit(1)
            wanted = {t['id']: t for t in items}
            for q in arr:
                if isinstance(q, dict) and q.get('id') in wanted:
                    q['answer'] = wanted[q['id']]['official']
            with open(path, 'wb') as f:
                f.write(dump(arr, trailing))
            changed_files += 1

    os.makedirs('reports', exist_ok=True)
    with open(OUT_REPORT, 'w', encoding='utf-8') as f:
        json.dump({
            '_meta': ('跨卷同题少数派答案的官方 PDF 复核结果；'
                      '生成命令 python scripts/fix_cross_paper_answers.py'),
            'stats': dict(stats),
            'items': resolved,
        }, f, ensure_ascii=False, indent=2)

    mode = '已落盘' if APPLY else '预览（加 --apply 落盘）'
    print(f'== 跨卷同题少数派答案复核 · {mode} ==')
    print(f'待核 {len(todo)} 道')
    for key, label in [
        ('fix', '本卷 PDF == 多数派 != 库内 -> 提取错误，可改'),
        ('pdf_matches_current', '本卷 PDF == 库内 -> 提取没错，属跨机构版本分歧'),
        ('pdf_third_value', '本卷 PDF 给出第三个值 -> 需人工'),
        ('pdf_disagree', '同卷多份解析 PDF 答案打架 -> 弃权'),
        ('already_correct', '已经是对的'),
        ('no_stem_anchor', '真题 PDF 里锚不到题干'),
        ('no_official_answer', '解析 PDF 抽不出答案'),
        ('stem_too_short', '题干过短，放弃'),
        ('question_not_found', '题库里找不到'),
    ]:
        if stats[key]:
            print(f'  {label}: {stats[key]}')
    if APPLY:
        print(f'改写文件 {changed_files} 个')
    print(f'明细 -> {OUT_REPORT}')


if __name__ == '__main__':
    main()
