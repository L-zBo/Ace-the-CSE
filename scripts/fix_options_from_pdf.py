#!/usr/bin/env python3
"""用官方真题 PDF 整组重建「题干与选项不配套」的选项。

现象：甘肃 2022 第 19 题题干在问「算盘、八卦……下列有关说法错误的有几项」，
四个选项却是「某培训机构举行报名即可获赠名师签名的活动……」——
整组选项都是另一道题的。

fix_option_crosstalk.py 处理的是「选项里串进一段别的题」，靠「本题至少 2 个
未受污染的选项与 PDF 一致」来互证。整组都错时那条路走不通，因为一个能对上
的选项都没有。

这里换一条更强的锚：**按题干原文在真题 PDF 里定位**。
  1. 官方真题 PDF 按单调递增的题号链切块
  2. 找出正文包含库里题干前 24 字的那个块，且**全篇只能有一个**这样的块
     （同一道题在同一份 PDF 里只应出现一次；出现多次说明卷别混了，不动）
  3. 从该块解析 A/B/C/D 四个选项，要求四个齐全、都不为空、都不含
     整组外来标号
  4. 只有当库里选项与 PDF 至少差 2 个位置时才整组替换 —— 差 0~1 个属于
     标点/尾巴噪声，那是 fix_option_crosstalk 的活儿，这里不越界

题干本身就是锚，所以不需要题号对齐；库里题号错位的卷（浙江那种多卷合并）
也能修。

用法：
  python scripts/fix_options_from_pdf.py            # 预览
  python scripts/fix_options_from_pdf.py --apply    # 落盘
输出：reports/options_from_pdf.json
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
LABELS = ['A', 'B', 'C', 'D']

PLACEHOLDER = ['OCR 抽取失败', 'OCR抽取失败', 'OCR 提取失败',
               '题目缺失', '暂缺', '正在全力以赴征集']
QNUM = re.compile(r'(?m)^[ \t]*(\d{1,3})[ \t]*(?:[、．.][ \t]*|[ \t]+|$)')
OPT = re.compile(r'(?:(?<=\s)|^)([A-D])\s*[、．.]\s*')
FOREIGN = re.compile(r'(?<=[\s）)】。，、；:：.．])([A-D])\s*[、．.]\s*')
YEAR_MARK = re.compile(r'(20\d\d)\s*年\s*(\d{0,2})\s*月?\s*全国事业单位联考')
JUNK = re.compile(
    r'公考事业编学习资料加微信\s*AS73982|老师微信：\s*AS73982|事业单位联考真题'
    r'|获取试卷更新[^\n]*|整理：杨柳[^\n]*|公众号：[^\n]*'
    r'|^[ \t]*[·・]?[ \t]*\d{1,4}[ \t]*[·・]?[ \t]*$'
    r'|^[ \t]*-[ \t]*\d{1,3}[ \t]*-[ \t]*$', re.M)
PAGE_TAIL = re.compile(r'[\s]*(?:[·・]\s*\d{1,4}\s*[·・]|-\s*\d{1,3}\s*-|~\s*\d{1,3}\s*~)\s*$')

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
            cache[path] = '\n'.join(pg.get_text(sort=True) for pg in d)
            d.close()
        except Exception:
            cache[path] = ''
    return cache[path]


def question_pdfs(paper):
    year = re.search(r'(\d{4})', paper).group(1)
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
    allp = [p.replace('\\', '/') for p in
            glob.glob('material/【省考】2000-2025真题pdf/**/*.pdf', recursive=True)]
    same = [p for p in allp if cn in p and year in p
            and ('行测' in p or '思维能力测验' in p)]
    return [p for p in same if '答案' not in p and '解析' not in p]


def sections(paper, text):
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
    """只认单调递增成链的题号，避开页码等噪声。返回 [(题号, 块正文), ...]"""
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
    out = []
    for i, (n, m) in enumerate(best):
        end = best[i + 1][1].start() if i + 1 < len(best) else len(sec)
        out.append((n, sec[m.end():end]))
    return out


def parse_options(block):
    clean = JUNK.sub('', block)
    hits = list(OPT.finditer(clean))
    start = None
    for i in range(len(hits) - 3):
        if [hits[i + k].group(1) for k in range(4)] == LABELS:
            start = i
            break
    if start is None:
        return None
    out = []
    for k in range(4):
        i = start + k
        end = hits[i + 1].start() if i + 1 < len(hits) else len(clean)
        body = re.sub(r'\s+', ' ', clean[hits[i].end():end]).strip()
        body = PAGE_TAIL.sub('', body).strip()
        # 末选项后面没有标号可截，会一路吃到下一题 / 下一段材料。
        # 在「题号+中文」、材料小节号「（四）」、页脚「第24页」处断开。
        body = re.split(r'\d{1,3}\s*[.．、](?=[一-龥])', body)[0].strip()
        body = re.split(r'（[一二三四五六七八九十]{1,2}）|第\s*\d+\s*页', body)[0].strip()
        if not body or len({m.group(1) for m in FOREIGN.finditer(body)}) >= 2:
            return None
        out.append({'label': LABELS[k], 'content': body})
    # 兜底：某个选项明显比同题其余选项长出一大截，多半还是吞了后文
    lens = sorted(len(norm(o['content'])) for o in out)
    med = lens[len(lens) // 2] or 1
    if lens[-1] > med * 3 + 40:
        return None
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
        pdfs = None
        blocks = None

        for q in arr:
            if not isinstance(q, dict):
                continue
            if any(x in str(q.get('content') or '') for x in PLACEHOLDER):
                continue
            db = [o for o in (q.get('options') or []) if isinstance(o, dict)]
            if len(db) != 4 or [o.get('label') for o in db] != LABELS:
                continue
            # 图形题的选项本来就是占位（选项内容在题图里），不能拿 PDF 里
            # 抽出来的裸字母 "A"/"B" 去覆盖 —— 那是把好数据改坏。
            if any(m in str(o.get('content') or '')
                   for o in db for m in ('[见图]', '[图形选项]')):
                continue
            stem = norm(q.get('content'))
            if len(stem) < 24:
                continue
            stats['scanned'] += 1

            if pdfs is None:
                pdfs = question_pdfs(paper)
                blocks = []
                for p in pdfs:
                    for sec in sections(paper, pdf_text(p, cache)):
                        blocks.extend((os.path.basename(p), n, b)
                                      for n, b in ordered_blocks(sec))
            if not pdfs:
                stats['no_pdf'] += 1
                continue

            probe = stem[:24]
            # 题干必须**贴着块首**出现，且块本身不能过大。
            # 只要求「块里含题干」会踩坑：题号链断掉时会出现一个吞掉十几道题
            # 的巨块，五道不同的题都「唯一命中」同一个块，拿到同一组选项。
            hit = []
            for src, n, b in blocks:
                nb = norm(b)
                if len(nb) > 1200:
                    continue
                i = nb.find(probe)
                if 0 <= i < 40:
                    hit.append((src, n, b))
            if len(hit) != 1:
                stats['not_unique' if hit else 'not_found'] += 1
                continue
            src, num, block = hit[0]
            parsed = parse_options(block)
            if not parsed:
                stats['unparsable'] += 1
                continue
            # PDF 里也是图形题：四个选项抽出来只剩裸字母。
            # 不能按总长度判 —— 「①②/①③/②③/②④」这种组合题选项也很短，
            # 但那是真内容，按长度一刀切会把它们一起误杀。
            if all(re.fullmatch(r'[A-D]', norm(o['content'])) for o in parsed):
                stats['pdf_is_figure'] += 1
                continue

            diff = sum(1 for a, b in zip(db, parsed)
                       if norm(a.get('content')) != norm(b['content']))
            if diff < 2:
                # 只差一两处、且库里的值就是「PDF 的值 + 一条尾巴」时，
                # 按 PDF 裁掉尾巴。北京 2023 第 10 题的 D 选项就是
                # 「一夫当关，万夫莫开」后面粘着下一题的整段题干。
                trimmed = []
                for a, b in zip(db, parsed):
                    na, nb = norm(a.get('content')), norm(b['content'])
                    if na != nb and nb and na.startswith(nb) and len(na) > len(nb) + 4:
                        trimmed.append({'label': a['label'], 'content': b['content']})
                    else:
                        trimmed.append({'label': a['label'],
                                        'content': a.get('content', '')})
                if any(norm(x['content']) != norm(o.get('content'))
                       for x, o in zip(trimmed, db)):
                    stats['trim'] += 1
                    records.append({'paper': paper, 'id': q.get('id'), 'pdfNum': num,
                                    'pdf': src, 'diff': diff, 'mode': 'trim',
                                    'old': [o.get('content', '')[:70] for o in db],
                                    'new': [o['content'][:70] for o in trimmed]})
                    fixes[path].append({'id': q.get('id'),
                                        'old': [dict(o) for o in db],
                                        'new': trimmed})
                else:
                    stats['ok_or_minor'] += 1
                continue

            stats['mismatch'] += 1
            records.append({'paper': paper, 'id': q.get('id'), 'pdfNum': num,
                            'pdf': src, 'diff': diff,
                            'old': [o.get('content', '')[:70] for o in db],
                            'new': [o['content'][:70] for o in parsed]})
            fixes[path].append({'id': q.get('id'),
                                'old': [dict(o) for o in db], 'new': parsed})

    os.makedirs('reports', exist_ok=True)
    json.dump(records, io.open('reports/options_from_pdf.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    print(f'扫描 {stats["scanned"]} 道；整组重建 {stats["mismatch"]} 道，'
          f'裁掉尾巴 {stats["trim"]} 道')
    for k in ('no_pdf', 'not_found', 'not_unique', 'unparsable',
              'pdf_is_figure', 'ok_or_minor'):
        if stats[k]:
            print(f'  {k:14} {stats[k]}')
    for r in records[:5]:
        print(f'  {r["id"]}  差 {r["diff"]} 个  [{r["pdf"][:34]} 第{r["pdfNum"]}题]')
        print(f'      旧 {r["old"][0][:56]!r}')
        print(f'      新 {r["new"][0][:56]!r}')

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
                cur = [o for o in (q.get('options') or []) if isinstance(o, dict)]
                if [norm(o.get('content')) for o in cur] != \
                        [norm(o.get('content')) for o in f['old']]:
                    continue
                q['options'] = f['new']
                n += 1
            io.open(path, 'wb').write(dump(arr, trailing))
        print(f'\n已写盘：重建 {n} 道题的选项，涉及 {len(fixes)} 个文件')
    else:
        print('\n预览模式，未写盘。加 --apply 落盘。')


if __name__ == '__main__':
    main()
