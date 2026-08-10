#!/usr/bin/env python3
"""国考 / 省考的答案冲突双向校验（事业编见 resolve_answer_conflicts.py）。

国考、省考的 PDF 是按年份单独成册（真题一份、答案及解析一份），
不像事业编那样是多年合集，所以不用做年份分节，但要按「卷种」配对
（副省级 / 地市级 / 行政执法；A 卷 / B 卷 / 乡镇 / 县级…）。

校验逻辑与事业编相同，两步都过才采信：
  1. 真题 PDF 里按题干定位，确认原卷题号 == 库里题号
  2. 同一套的答案解析 PDF 里取第 N 题的【答案】

用法：
  python scripts/resolve_answer_conflicts_gk.py            # 预览
  python scripts/resolve_answer_conflicts_gk.py --apply    # 落盘
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
CONCLUSION = re.compile(r'故正确答案为\s*([A-D]+)\s*[。.]?')

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

ANSWER_PAT = [
    r'(?m)^\s*{n}\s*[.．、]\s*【答案】\s*([A-D]+)',
    r'(?m)^\s*{n}\s*[.．、]\s*答案[：:]\s*([A-D]+)',
    r'{n}\s*[.．、]\s*【答案】\s*([A-D]+)',
    r'【\s*{n}\s*】\s*【?答案】?\s*[：:]?\s*([A-D]+)',
]


def answer_from_block(text, n):
    """省考解析常见格式：`N、本题考查…… 故正确答案为X。`（无【答案】标记）。

    定位第 N 题的块首，再在块内（到下一题号为止）取第一个「故正确答案为」。
    """
    for m in re.finditer(rf'(?m)^\s*{n}\s*[、.．]\s*', text):
        seg = text[m.end():m.end() + 4000]
        nxt = re.search(rf'(?m)^\s*{n + 1}\s*[、.．]\s*', seg)
        if nxt:
            seg = seg[:nxt.start()]
        got = re.search(r'故正确答案为\s*([A-D]+)', seg)
        if got:
            return got.group(1)
    return None


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


def collect():
    out = []
    for path in sorted(glob.glob('src/data/xingce/*/*.json')):
        base = os.path.basename(path)[:-5]
        if base.startswith('institution'):
            continue
        for q in json.load(io.open(path, encoding='utf-8')):
            if any(p in str(q.get('content') or '') for p in PLACEHOLDER):
                continue
            exp = str(q.get('explanation') or '')
            ans = flat_answer(q.get('answer'))
            hits = CONCLUSION.findall(exp)
            if len(hits) == 1 and ans and hits[0] != ans:
                out.append({'json': path.replace('\\', '/'), 'paper': base,
                            'id': q.get('id'),
                            'num': int(q.get('id', '0').rsplit('-', 1)[-1]),
                            'answer_field': ans, 'exp_says': hits[0],
                            'stem': norm(q.get('content'))[:20]})
    return out


def candidates(paper):
    """返回 (真题 PDF 列表, 答案 PDF 列表)"""
    year = re.search(r'(\d{4})', paper).group(1)
    if paper.startswith('national'):
        root = 'material/【国考】2000-2025真题pdf/2000-2025国考行测PDF'
        q = [p for p in glob.glob(f'{root}/行测-真题/*.pdf') if year in p]
        a = [p for p in glob.glob(f'{root}/行测-答案及解析/*.pdf') if year in p]
        lv = re.search(r'_(fushengjia|dishi|xingzhengzhifa)$', paper)
        if lv:
            kws = LEVEL_CN[lv.group(1)]
            q2 = [p for p in q if any(k in p for k in kws)]
            a2 = [p for p in a if any(k in p for k in kws)]
            q, a = (q2 or q), (a2 or a)
        return [p.replace('\\', '/') for p in q], [p.replace('\\', '/') for p in a]

    m = re.match(r'provincial_([a-z]+)_(\d{4})', paper)
    cn = PROVINCE_CN.get(m.group(1)) if m else None
    if not cn:
        return [], []
    all_p = [p.replace('\\', '/') for p in
             glob.glob('material/【省考】2000-2025真题pdf/**/*.pdf', recursive=True)]
    same = [p for p in all_p if cn in p and year in p and '行测' in p]
    a = [p for p in same if ('答案' in p or '解析' in p)]
    q = [p for p in same if p not in a]
    return q, a


def find_num(sec_norm, stem):
    i = sec_norm.find(stem)
    if i < 0:
        return None
    head = sec_norm[max(0, i - 12):i]
    m = None
    for mm in re.finditer(r'(\d{1,3})[.．、]', head):
        m = mm
    return int(m.group(1)) if m else None


def main():
    items = collect()
    print(f'国考/省考 答案冲突 {len(items)} 道')
    cache = {}
    stats = Counter()
    results = []

    for c in items:
        c['official'] = None
        c['evidence'] = None
        qs, as_ = candidates(c['paper'])
        if not qs or not as_:
            stats['no_pdf'] += 1
            results.append(c)
            continue

        # 第 1 步：真题 PDF 锁定题号
        matched_q = None
        for qp in qs:
            n = find_num(norm(pdf_text(qp, cache)), c['stem'])
            if n is None:
                continue
            if n != c['num']:
                stats['num_mismatch'] += 1
                c['evidence'] = f'真题PDF中为第{n}题，与库里第{c["num"]}题不符'
                matched_q = False
                break
            matched_q = qp
            break
        if not matched_q:
            if matched_q is None:
                stats['stem_not_found'] += 1
            results.append(c)
            continue

        # 第 2 步：答案 PDF 取第 N 题答案
        got = None
        for ap in as_:
            t = pdf_text(ap, cache)
            for pat in ANSWER_PAT:
                mm = re.search(pat.format(n=c['num']), t)
                if mm:
                    got = mm.group(1)
                    break
            if not got:
                got = answer_from_block(t, c['num'])
            if got:
                c['evidence'] = (f'真题 {os.path.basename(matched_q)[:26]} 第{c["num"]}题题干匹配；'
                                 f'答案 {os.path.basename(ap)[:26]} 【答案】{got}')
                break
        if not got:
            stats['answer_not_found'] += 1
            results.append(c)
            continue
        c['official'] = got
        stats['resolved'] += 1
        results.append(c)

    json.dump(results, io.open('reports/answer_resolution_gk.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    ok = [c for c in results if c['official']]
    need = [c for c in ok if c['official'] != c['answer_field']]
    same = [c for c in ok if c['official'] == c['answer_field']]
    print(f'\n双向校验通过 {len(ok)} 道：需修正 {len(need)}，answer 本来就对 {len(same)}')
    print('未解决：', dict((k, v) for k, v in stats.items() if k != 'resolved'))
    for c in need[:8]:
        print(f'  {c["id"]}  {c["answer_field"]} -> {c["official"]}')

    if APPLY and need:
        by = defaultdict(list)
        for c in need:
            by[c['json']].append(c)
        n = 0
        for path, its in by.items():
            raw = io.open(path, 'rb').read()
            arr = json.loads(raw.decode('utf-8'))
            trailing = raw.endswith(CRLF.encode())
            assert dump(arr, trailing) == raw, path
            idx = {q.get('id'): q for q in arr}
            for c in its:
                if idx.get(c['id']) is not None:
                    off = c['official']
                    # 多选答案存成数组，前端的 Array.isArray 分支才认
                    idx[c['id']]['answer'] = list(off) if len(off) > 1 else off
                    n += 1
            io.open(path, 'wb').write(dump(arr, trailing))
        print(f'\n已写盘：修正 {n} 道')
    else:
        print('\n预览模式，未写盘。加 --apply 落盘。')


if __name__ == '__main__':
    main()
