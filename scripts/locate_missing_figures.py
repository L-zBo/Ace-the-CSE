#!/usr/bin/env python3
"""为缺图的题定位源 PDF。

背景：62 道题的 questionImage 指向磁盘上不存在的 PNG。要补图先得知道图在哪份
PDF 里 —— 而且不能想当然：实测 provincial_guangdong_2020 的那批图形题其实出自
《2020年广东选调生思维能力测验》，跟卷名标的《行测》不是同一份考试。

做法：按题干原文（去空白后的特征串）到候选 PDF 里搜，搜到才算数，不靠文件名猜。

用法：python scripts/locate_missing_figures.py
输出：reports/missing_figures_sources.json
"""
import glob
import io
import json
import os
import re
import sys
from collections import defaultdict

import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

PROVINCE_CN = {
    'guangdong': '广东', 'chongqing': '重庆', 'shenzhen': '深圳', 'xinjiang': '新疆',
    'fujian': '福建', 'shanghai': '上海', 'jiangsu': '江苏', 'shandong': '山东',
    'tianjin': '天津', 'anhui': '安徽', 'hebei': '河北', 'neimenggu': '内蒙古',
    'zhejiang': '浙江', 'jiangxi': '江西', 'sichuan': '四川', 'hainan': '海南',
    'hunan': '湖南', 'hubei': '湖北', 'henan': '河南', 'shanxi': '山西',
    'shaanxi': '陕西', 'gansu': '甘肃', 'qinghai': '青海', 'ningxia': '宁夏',
    'jilin': '吉林', 'liaoning': '辽宁', 'heilongjiang': '黑龙江', 'yunnan': '云南',
    'guizhou': '贵州', 'guangxi': '广西',
}


def norm(s):
    return re.sub(r'\s+', '', str(s or ''))


def stem_key(content):
    """取题干前段做特征串，剔除页码碎片等噪声。"""
    t = norm(content)
    t = re.sub(r'[-—]\d{1,3}[-—]', '', t)
    return t[:24]


def main():
    have = set()
    for p in glob.glob('public/img/questions/*/*.png'):
        p = p.replace('\\', '/')
        have.add((p.split('/')[-2], p.split('/')[-1]))

    # 收集缺图题
    missing = []
    for path in sorted(glob.glob('src/data/xingce/*/*.json')):
        for q in json.load(io.open(path, encoding='utf-8')):
            img = str(q.get('questionImage') or '')
            m = re.search(r'questions/([^/]+)/(q\d+\.png)', img)
            if not m or (m.group(1), m.group(2)) in have:
                continue
            missing.append({
                'json': path.replace('\\', '/'),
                'examKey': m.group(1),
                'png': m.group(2),
                'id': q.get('id'),
                'key': stem_key(q.get('content')),
                'content': str(q.get('content') or '')[:70],
            })
    print(f'缺图题 {len(missing)} 道，涉及 {len({x["examKey"] for x in missing})} 套卷')

    # 按卷聚合，为每套卷挑候选 PDF（按省份中文名 + 年份过滤路径）
    all_pdfs = [p.replace('\\', '/') for p in
                glob.glob('material/**/*.pdf', recursive=True)]
    print(f'material 下 PDF {len(all_pdfs)} 份')

    by_exam = defaultdict(list)
    for x in missing:
        by_exam[x['examKey']].append(x)

    text_cache = {}
    results = []
    for exam, items in sorted(by_exam.items()):
        mm = re.match(r'(provincial|national|institution)_(\w+?)_?(\d{4})', exam)
        year = re.search(r'(\d{4})', exam).group(1)
        cands = [p for p in all_pdfs if year in p]
        if exam.startswith('institution'):
            # 事业编真题 PDF 是「2018年-2024年…（C类）笔试真题.pdf」这种多年合集，
            # 文件名里根本没有 2020，按年份过滤会把它整份筛掉（实测 6 道图因此
            # 一直定位不到源）。改按类别目录挑。
            cls = exam.rsplit('_', 1)[-1].upper()
            cands = [p for p in all_pdfs
                     if f'/{cls}类/' in p and '职测' in p and '解析' not in p]
        elif mm and mm.group(1) == 'provincial':
            cn = PROVINCE_CN.get(mm.group(2))
            if cn:
                cands = [p for p in cands if cn in p]
        elif mm and mm.group(1) == 'national':
            cands = [p for p in cands if '国考' in p or '国家' in p]

        found = 0
        for it in items:
            hit = None
            for pdf in cands:
                if pdf not in text_cache:
                    try:
                        d = pymupdf.open(pdf)
                        text_cache[pdf] = norm('\n'.join(pg.get_text() for pg in d))
                        d.close()
                    except Exception:
                        text_cache[pdf] = ''
                if it['key'] and it['key'] in text_cache[pdf]:
                    hit = pdf
                    break
            it['pdf'] = hit
            if hit:
                found += 1
            results.append(it)
        print(f'  {exam:34} 缺 {len(items):2}  候选PDF {len(cands):3}  定位到 {found}')

    os.makedirs('reports', exist_ok=True)
    json.dump(results, io.open('reports/missing_figures_sources.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    ok = sum(1 for r in results if r.get('pdf'))
    print(f'\n合计定位到源 PDF：{ok}/{len(results)}')
    print('明细 -> reports/missing_figures_sources.json')


if __name__ == '__main__':
    main()
