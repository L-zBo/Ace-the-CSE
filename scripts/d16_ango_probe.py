"""D-16 L-0a 探查 ANGO-S1 数据集：年份/省份/卷别分布 + 事业编覆盖"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ANGO_FILE = Path('data/ango_cache/test_dataset.json')
OUT = Path('data/ango_cache/probe.md')


def main():
    data = json.loads(ANGO_FILE.read_text(encoding='utf-8'))
    n = len(data)

    year_c = Counter()
    region_c = Counter()
    paper_type_c = Counter()  # 国考/省考/事业编/选调...
    has_material = 0
    has_image_marker = 0
    has_formula = 0

    sample_inst_sources = []
    history_total = 0
    history_year_c = Counter()
    history_region_c = Counter()
    history_paper_type_c = Counter()

    # 拆 source 用的关键词
    KW_PAPER = [
        ('事业单位', '事业'),
        ('事业编', '事业'),
        ('选调', '选调'),
        ('公务员', '公务员'),
        ('村官', '村官'),
        ('政法干警', '政法'),
        ('三支一扶', '三支一扶'),
        ('教师', '教师'),
        ('军转', '军转'),
        ('辅警', '辅警'),
    ]

    REGIONS = [
        '北京', '天津', '河北', '山西', '内蒙古', '内蒙',
        '辽宁', '吉林', '黑龙江', '上海', '江苏', '浙江',
        '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南',
        '广东', '广西', '海南', '重庆', '四川', '贵州', '云南',
        '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆',
        '国家', '联考', '多省', '深圳', '广州', '厦门', '南京',
    ]

    def parse_source(src: str):
        # 年份
        m = re.search(r'(20\d{2}|19\d{2})', src or '')
        year = m.group(1) if m else None
        # 省份
        region = None
        for r in REGIONS:
            if r in src:
                region = r
                break
        # 卷别
        paper_type = None
        for kw, label in KW_PAPER:
            if kw in src:
                paper_type = label
                break
        return year, region, paper_type

    for item in data:
        # 主 item 用的是最新出现的 source
        src = item.get('source', '') or ''
        y, r, t = parse_source(src)
        if y: year_c[y] += 1
        if r: region_c[r] += 1
        if t: paper_type_c[t] += 1

        opts = item.get('options', '') or ''
        if item.get('material'): has_material += 1
        if '[' in opts and '图' in opts: has_image_marker += 1
        if item.get('formulas', 0): has_formula += 1

        if t == '事业':
            sample_inst_sources.append(src)

        # history
        for h in item.get('history', []) or []:
            history_total += 1
            hsrc = h.get('source', '') or ''
            hy, hr, ht = parse_source(hsrc)
            if hy: history_year_c[hy] += 1
            if hr: history_region_c[hr] += 1
            if ht: history_paper_type_c[ht] += 1
            if ht == '事业':
                sample_inst_sources.append(hsrc)

    out = []
    out.append(f'# ANGO-S1 数据探查')
    out.append('')
    out.append(f'- 主题题数: **{n}**')
    out.append(f'- history 总条数（同题不同年份）: **{history_total}**')
    out.append(f'- 主题 + history 合计: **{n + history_total}**')
    out.append(f'- 含 material（材料/资料分析题）: {has_material}')
    out.append(f'- 含 [图...] 标记: {has_image_marker}')
    out.append(f'- 含公式: {has_formula}')
    out.append('')
    out.append('## 主题 source — 年份分布 top 20')
    for y, c in sorted(year_c.items(), key=lambda x: -x[1])[:20]:
        out.append(f'  - {y}: {c}')
    out.append('')
    out.append('## 主题 source — 省份分布 top 30')
    for r, c in sorted(region_c.items(), key=lambda x: -x[1])[:30]:
        out.append(f'  - {r}: {c}')
    out.append('')
    out.append('## 主题 source — 卷别分布')
    for t, c in sorted(paper_type_c.items(), key=lambda x: -x[1]):
        out.append(f'  - {t}: {c}')
    out.append('')
    out.append('## history source — 年份分布 top 20')
    for y, c in sorted(history_year_c.items(), key=lambda x: -x[1])[:20]:
        out.append(f'  - {y}: {c}')
    out.append('')
    out.append('## history source — 省份分布 top 30')
    for r, c in sorted(history_region_c.items(), key=lambda x: -x[1])[:30]:
        out.append(f'  - {r}: {c}')
    out.append('')
    out.append('## history source — 卷别分布')
    for t, c in sorted(history_paper_type_c.items(), key=lambda x: -x[1]):
        out.append(f'  - {t}: {c}')
    out.append('')
    out.append('## 事业编联考 source 样本 top 30')
    seen = set()
    for s in sample_inst_sources:
        if s not in seen:
            seen.add(s)
            out.append(f'  - {s}')
            if len(seen) >= 30:
                break

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('\n'.join(out), encoding='utf-8')
    print(f'[ANGO probe] wrote {OUT}')
    print(f'  unique 主题 = {n}, history = {history_total}, 合计 = {n+history_total}')
    print(f'  paper_type top: {dict(paper_type_c.most_common(10))}')
    print(f'  history paper_type top: {dict(history_paper_type_c.most_common(10))}')


if __name__ == '__main__':
    main()
