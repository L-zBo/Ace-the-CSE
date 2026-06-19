"""E-1 vision 救援：逐题用 lib explanation 最特异关键词反向定位 PDF 页。

D-16 末 99 题里筛出 11 题真 A 类（PDF 有题，OCR 部分失败）。每题手工挑选
2-4 个最特异关键词（避开「【答案】」「正确答案」这种模板词），扫整本 PDF
找到 kw 命中最多的页。institution paperKey 一年两场合并，必须逐题搜，
不能信整段校准。
"""

import json
import os
import sys

import fitz  # PyMuPDF

sys.stdout.reconfigure(encoding='utf-8')
fitz.TOOLS.mupdf_display_errors(False)

PDF_INDEX = json.load(open('data/e1_vision/pdf_index.json', 'r', encoding='utf-8'))

# (paperKey, qn, module, distinctive_keywords)
CANDIDATES = [
    ('institution_2021_a', '045', 'changshi',
     ['清代因袭明代', '宪纲条例', '钦定合规']),
    ('institution_2021_a', '094', 'ziliao',
     ['2018 年进口额正增长', '电信、计算机和信息服务', '2018 年我国计算机和信息服务进口额']),
    ('institution_2021_c', '014', 'changshi',
     ['根据板块构造学说', '板块构造学说']),
    ('institution_2021_c', '059', 'shuliang',
     ['S 省本级', '财政科学技术支出 84.25', '占当年全省财政公共预算支出', '1.79%']),
    ('institution_2021_c', '078', 'panduan',
     ['对于流感相当于滑坡', '流感相当于滑坡']),
    ('institution_2020_c', '060', 'panduan',
     ['现期平均数计算', '快递业务收入', '快递业务量']),
    ('institution_2022_c', '049', 'shuliang',
     ['水质实验室', '烧杯和三角瓶', '烧杯与三角瓶']),
    ('provincial_shanxi_2023', '069', 'changshi',
     ['甲乙两地间的纵横道路网', '铺设的电缆长度最短', '电缆经过丙地的概率']),
    ('provincial_guangdong_2024', '031', 'shuliang',
     ['题干出现图形', '判定为图形数阵', '观察图形发现']),
    ('provincial_shenzhen_2023', '015', 'yanyu',
     ['一带一路', '六大国际经济合作走廊', '六廊']),
    ('provincial_tianjin_2023', '006', 'yanyu',
     ['小林因病入院需挂瓶输液', '容量300 毫升', '药液滴速']),
]


def main():
    print(f'=== 逐题反向搜 ({len(CANDIDATES)} 题) ===\n')
    final_locs = []
    for pk, qn, mod, kws in CANDIDATES:
        pdf = PDF_INDEX[pk]
        doc = fitz.open(pdf)
        page_hits = {}
        for i in range(len(doc)):
            text = doc[i].get_text()
            hits = sum(1 for k in kws if k in text)
            if hits > 0:
                page_hits[i] = hits
        doc.close()
        if not page_hits:
            print(f'  ❌ {pk:30s} q{qn} 全 PDF 无命中')
            final_locs.append({'paperKey': pk, 'qn': qn, 'module': mod, 'page': None})
            continue
        sorted_pages = sorted(page_hits.items(), key=lambda x: (-x[1], x[0]))
        best_page, best_hits = sorted_pages[0]
        final_locs.append({
            'paperKey': pk, 'qn': qn, 'module': mod,
            'page': best_page, 'kw_hits': best_hits, 'total_kws': len(kws),
        })
        multi = f' (+{len(sorted_pages) - 1} 其他)' if len(sorted_pages) > 1 else ''
        print(f'  ✓ {pk:30s} q{qn} ({mod:8s}) -> p{best_page} '
              f'(kw命中 {best_hits}/{len(kws)}){multi}')

    out_path = 'data/e1_vision/a_final_v2.json'
    json.dump(final_locs, open(out_path, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    print(f'\n保存 -> {out_path}')
    ok = [l for l in final_locs if l.get('page') is not None]
    print(f'定位成功 {len(ok)}/{len(final_locs)}')


if __name__ == '__main__':
    main()
