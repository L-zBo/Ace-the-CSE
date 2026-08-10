#!/usr/bin/env python3
"""修复「选项正文里串进了别的题的整组选项」。

现象（PDF 抽取跨题串行所致）：

    "D": "在国外合法设立但尚未在我国民政部门登记的某环保基金会 B、建设一支听党
          指挥、能打胜仗、作风优良的人民军队 D、确保到 2020 年全面实现机..."

前半截是本题 D 的真实内容，后面整段是另一道题的选项串进来的。

为什么不能靠「截断」：截断点是猜的。第一版脚本截断后拿结果回 PDF 里搜，
命中就采信 —— 那是假证据，同一套卷里任何一段文字都能搜到，证明不了它属于
这道题。实测截出来一堆 `A．畜牧业是其支柱产业`、`88 325` 这种垃圾。

现在的做法（双锚定 + 同题互证）：
  1. 在官方**真题** PDF 里按行首题号切块，取第 N 题的块
  2. 要求该块正文包含库里题干前 16 字 —— 题号和题干双锚，锁定就是这道题
  3. 解析该块的 A/B/C/D 四个选项
  4. **要求该题至少 2 个未受污染的选项与 PDF 完全一致** —— 这一步证明我们
     解析出来的这组选项确实和库里这道题对得上，而不是错位到了隔壁题
  5. 满足以上全部，才用 PDF 的内容替换被污染的那个选项

任何一步不过就不动，进报告等人工。宁可留着脏数据，也不写进去一个编的。

用法：
  python scripts/fix_option_crosstalk.py            # 预览 + 出报告
  python scripts/fix_option_crosstalk.py --apply    # 落盘
输出：reports/option_crosstalk.json
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

# 选项标号：前面必须是空白或收尾标点，避免误伤正文里的 "A."
LABEL = re.compile(r'(?<=[\s）)】。，、；:：.．])([A-D])\s*[、．.]\s*')
# PDF 块内解析用（行首或空白起头都算）
PDF_LABEL = re.compile(r'(?:(?<=\s)|^)([A-D])\s*[、．.]\s*')
QNUM = re.compile(r'(?m)^\s*(\d{1,3})\s*[、．.]\s*')
YEAR_MARK = re.compile(r'(20\d\d)\s*年\s*(\d{0,2})\s*月?\s*全国事业单位联考')

# PDF 页眉页脚水印，抽块时先剔掉（按行匹配，故加 re.M）
JUNK = re.compile(
    r'公考事业编学习资料加微信\s*AS73982|老师微信：\s*AS73982|事业单位联考真题'
    r'|获取试卷更新[^\n]*|整理：杨柳[^\n]*|公众号：[^\n]*'
    r'|^[ \t]*[·・]?[ \t]*\d{1,4}[ \t]*[·・]?[ \t]*$|^[ \t]*-[ \t]*\d{1,3}[ \t]*-[ \t]*$',
    re.M)
# 选项正文尾巴上粘的页码（`… 登录 · 13 ·`），单独再刮一遍
PAGE_TAIL = re.compile(r'[\s]*(?:[·・]\s*\d{1,4}\s*[·・]|-\s*\d{1,3}\s*-)\s*$')

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


def norm(s):
    return re.sub(r'\s+', '', str(s or ''))


def dump(arr, trailing):
    t = json.dumps(arr, ensure_ascii=False, indent=2).replace(chr(10), CRLF)
    return (t + CRLF if trailing else t).encode('utf-8')


def pdf_text(path, cache):
    if path not in cache:
        try:
            d = pymupdf.open(path)
            # sort=True 让多栏排版按阅读顺序输出，减少跨栏串行
            cache[path] = '\n'.join(pg.get_text(sort=True) for pg in d)
            d.close()
        except Exception:
            cache[path] = ''
    return cache[path]


def question_pdfs(paper):
    """paper 文件名 -> 该套卷的官方**真题** PDF 候选（不含答案解析）。"""
    ym = re.search(r'(\d{4})', paper)
    year = ym.group(1) if ym else ''

    if paper.startswith('institution'):
        m = re.match(r'institution_\d{4}_([a-e])$', paper)
        cls = m.group(1).upper() if m else ''
        return [p.replace('\\', '/') for p in
                glob.glob(f'material/**/{cls}类/职测/*真题.pdf', recursive=True)]

    if paper.startswith('national'):
        root = 'material/【国考】2000-2025真题pdf/2000-2025国考行测PDF'
        q = [p.replace('\\', '/') for p in
             glob.glob(f'{root}/行测-真题/*.pdf') if year in p]
        lv = re.search(r'_(fushengjia|dishi|xingzhengzhifa)$', paper)
        if lv:
            kws = LEVEL_CN[lv.group(1)]
            q = [p for p in q if any(k in p for k in kws)] or q
        return q

    m = re.match(r'provincial_([a-z]+)_(\d{4})', paper)
    cn = PROVINCE_CN.get(m.group(1)) if m else None
    if not cn:
        return []
    all_p = [p.replace('\\', '/') for p in
             glob.glob('material/【省考】2000-2025真题pdf/**/*.pdf', recursive=True)]
    same = [p for p in all_p if cn in p and year in p and '行测' in p]
    return [p for p in same if '答案' not in p and '解析' not in p]


def sections(paper, text):
    """事业编 PDF 是多年合集，按年份切；其余整册就是一段。"""
    if not paper.startswith('institution'):
        return [text]
    year = re.search(r'(\d{4})', paper).group(1)
    marks = [(m.start(), m.group(1)) for m in YEAR_MARK.finditer(text)]
    if not marks:
        return [text]
    out = []
    for i, (pos, y) in enumerate(marks):
        if y != year:
            continue
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out.append(text[pos:end])
    return out or [text]


def split_blocks(sec):
    """按行首题号切块，返回 {题号: 块正文}。同号多次出现时保留最后一次。"""
    marks = list(QNUM.finditer(sec))
    out = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(sec)
        out[int(m.group(1))] = sec[m.end():end]
    return out


def parse_options(block):
    """从题块里解析 {label: 正文}。遇到下一个标号即截断。"""
    clean = JUNK.sub('', block)
    hits = list(PDF_LABEL.finditer(clean))
    out = {}
    for i, m in enumerate(hits):
        lab = m.group(1)
        end = hits[i + 1].start() if i + 1 < len(hits) else len(clean)
        body = re.sub(r'\s+', ' ', clean[m.end():end]).strip()
        body = PAGE_TAIL.sub('', body).strip()
        # 同一标号出现多次说明跨题串了，只认第一次
        if lab not in out and body:
            out[lab] = body
    return out


def polluted(content):
    """判定该选项正文是否串进了别的题的选项。"""
    if len({m.group(1) for m in LABEL.finditer(content)}) >= 2:
        return True
    # 正文以标号打头（选项 B 的内容是 `B．0.9`）同样是串行残留
    return bool(re.match(r'^\s*[A-D]\s*[、．.]\s*\S', content))


def main():
    cache = {}
    stats = Counter()
    records = []
    targets = defaultdict(list)   # paper -> [(json, question, 污染的 label 列表)]

    for path in sorted(glob.glob('src/data/*/*/*.json')):
        path = path.replace('\\', '/')
        paper = path.split('/')[-1][:-5]
        for q in json.load(io.open(path, encoding='utf-8')):
            if any(x in str(q.get('content') or '') for x in PLACEHOLDER):
                continue
            bad = [o.get('label') for o in (q.get('options') or [])
                   if isinstance(o, dict) and polluted(str(o.get('content') or ''))]
            if bad:
                targets[paper].append((path, q, bad))
                stats['question'] += 1
                stats['option'] += len(bad)

    fixes = []
    for paper, items in sorted(targets.items()):
        pdfs = question_pdfs(paper)
        if not pdfs:
            stats['no_pdf'] += len(items)
            for path, q, bad in items:
                records.append({'id': q.get('id'), 'labels': bad,
                                'verdict': 'no_pdf'})
            continue
        blocks_by_pdf = []
        for p in pdfs:
            for sec in sections(paper, pdf_text(p, cache)):
                blocks_by_pdf.append((p, split_blocks(sec)))

        for path, q, bad in items:
            num = int(str(q.get('id', '0')).rsplit('-', 1)[-1])
            stem = norm(q.get('content'))[:16]
            db = {o.get('label'): str(o.get('content') or '')
                  for o in (q.get('options') or []) if isinstance(o, dict)}
            rec = {'id': q.get('id'), 'labels': bad}

            picked = None
            for p, blocks in blocks_by_pdf:
                blk = blocks.get(num)
                if not blk or stem not in norm(blk):
                    continue
                opts = parse_options(blk)
                # 同题互证：至少 2 个未污染选项与 PDF 一模一样
                agree = sum(1 for lab, c in db.items()
                            if lab not in bad and lab in opts
                            and norm(c) == norm(opts[lab]))
                if agree >= 2:
                    picked = (p, opts, agree)
                    break
            if not picked:
                rec['verdict'] = 'no_anchor'
                stats['no_anchor'] += 1
                records.append(rec)
                continue

            p, opts, agree = picked
            # 兄弟选项长度上界：资料分析末题的 D 后面直接跟下一段材料，PDF 块里
            # 没有标号可截，抽出来会把整段材料吞进去。用同题其余选项的长度兜底。
            sib = [len(c) for lab, c in db.items() if lab not in bad and c]
            cap = max(60, (max(sib) if sib else 0) * 2 + 30)
            got = []
            for lab in bad:
                new = opts.get(lab)
                if not new or polluted(new) or norm(new) == norm(db[lab]):
                    continue
                if len(new) > cap:
                    stats['reject_too_long'] += 1
                    continue
                got.append({'json': path, 'id': q.get('id'), 'label': lab,
                            'old': db[lab], 'new': new})
            if not got:
                rec['verdict'] = 'anchored_but_pdf_also_dirty'
                rec['pdf'] = os.path.basename(p)
                stats['anchored_but_pdf_also_dirty'] += 1
                records.append(rec)
                continue
            fixes.extend(got)
            stats['fixed_option'] += len(got)
            stats['fixed_question'] += 1
            rec.update({'verdict': 'fix', 'agree': agree, 'pdf': os.path.basename(p),
                        'changes': [{'label': g['label'], 'old': g['old'][:120],
                                     'new': g['new'][:120]} for g in got]})
            records.append(rec)

    os.makedirs('reports', exist_ok=True)
    json.dump(records, io.open('reports/option_crosstalk.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    print(f'受污染题目 {stats["question"]} 道 / 选项 {stats["option"]} 条')
    print(f'可修复：{stats["fixed_question"]} 道 / {stats["fixed_option"]} 条选项')
    for k in ('no_pdf', 'no_anchor', 'anchored_but_pdf_also_dirty', 'reject_too_long'):
        if stats[k]:
            print(f'  未修 {k:28} {stats[k]} 道')
    for g in fixes[:8]:
        print(f'  {g["id"]} {g["label"]}')
        print(f'      旧 {g["old"][:70]!r}')
        print(f'      新 {g["new"][:70]!r}')

    if APPLY and fixes:
        by_json = defaultdict(list)
        for g in fixes:
            by_json[g['json']].append(g)
        n = 0
        for jp, items in by_json.items():
            raw = io.open(jp, 'rb').read()
            arr = json.loads(raw.decode('utf-8'))
            trailing = raw.endswith(CRLF.encode())
            assert dump(arr, trailing) == raw, jp
            idx = {q.get('id'): q for q in arr}
            for g in items:
                q = idx.get(g['id'])
                if not q:
                    continue
                for o in q.get('options') or []:
                    if isinstance(o, dict) and o.get('label') == g['label'] \
                            and str(o.get('content') or '') == g['old']:
                        o['content'] = g['new']
                        n += 1
            io.open(jp, 'wb').write(dump(arr, trailing))
        print(f'\n已写盘：修复 {n} 条选项，涉及 {len(by_json)} 个文件')
    else:
        print('\n预览模式，未写盘。加 --apply 落盘。')


if __name__ == '__main__':
    main()
