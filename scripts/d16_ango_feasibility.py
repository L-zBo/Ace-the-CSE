"""D-16 L-0c 评估 ANGO 救援可行性：lib 占位题 (region,year,qn) ∩ ANGO source (region,year,qn)"""
import glob
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

MARKERS = [
    '[题干 OCR 抽取失败-D11]',
    '[选项 OCR 抽取失败-D11]',
    '[题干/选项 OCR 抽取失败-D11]',
    '[暂缺]',
]

REGION_LIB2ZH = {
    'beijing': '北京', 'tianjin': '天津', 'shanghai': '上海', 'chongqing': '重庆',
    'hebei': '河北', 'shanxi': '山西', 'liaoning': '辽宁', 'jilin': '吉林',
    'heilongjiang': '黑龙江', 'jiangsu': '江苏', 'zhejiang': '浙江', 'anhui': '安徽',
    'fujian': '福建', 'jiangxi': '江西', 'shandong': '山东', 'henan': '河南',
    'hubei': '湖北', 'hunan': '湖南', 'guangdong': '广东', 'guangxi': '广西',
    'hainan': '海南', 'sichuan': '四川', 'guizhou': '贵州', 'yunnan': '云南',
    'shaanxi': '陕西', 'gansu': '甘肃', 'qinghai': '青海', 'ningxia': '宁夏',
    'xinjiang': '新疆', 'neimenggu': '内蒙古', 'xizang': '西藏',
    'shenzhen': '深圳', 'guangzhou': '广州',
}


def is_bad(q):
    content = q.get('content', '') or ''
    if any(m in content for m in MARKERS): return True
    for o in q.get('options', []) or []:
        c = (o.get('content', '') or '') if isinstance(o, dict) else str(o)
        if any(m in c for m in MARKERS): return True
    return False


def parse_lib_paperkey(stem: str):
    if stem.startswith('provincial_'):
        parts = stem.split('_')
        region_en = parts[1]
        try: year = int(parts[2])
        except: return None, None, None
        level = parts[3].upper() if len(parts) > 3 else None
        region_zh = REGION_LIB2ZH.get(region_en)
        return region_zh, year, level
    return None, None, None


def parse_ango_source(src: str):
    if not src: return None, None, None
    m_year = re.search(r'(20\d{2}|19\d{2})', src)
    year = int(m_year.group(1)) if m_year else None
    region = None
    for r in REGION_LIB2ZH.values():
        if r in src:
            region = r
            break
    m_qn = re.search(r'第(\d+)题', src)
    qn = int(m_qn.group(1)) if m_qn else None
    return year, region, qn


def main():
    # === lib 占位题：(region_zh, year, qn) ===
    lib_keys = []  # (region_zh, year, qn, file_stem, qid)
    region_year_pairs = Counter()
    for mod in ['panduan', 'changshi', 'shuliang', 'ziliao', 'yanyu']:
        for fp in sorted(glob.glob(f'src/data/xingce/{mod}/*.json')):
            stem = Path(fp).stem
            region_zh, year, _ = parse_lib_paperkey(stem)
            if not (region_zh and year): continue
            lib = json.loads(Path(fp).read_text(encoding='utf-8'))
            for q in lib:
                if not is_bad(q): continue
                qid = q.get('id', '')
                tail = qid.rsplit('-', 1)[-1]
                try: qn = int(tail)
                except: continue
                lib_keys.append((region_zh, year, qn, f'{mod}/{stem}', qid))
                region_year_pairs[(region_zh, year)] += 1

    print(f'[lib placeholders 省考] {len(lib_keys)} 题')
    print('top (region,year):')
    for k, c in region_year_pairs.most_common(20):
        print(f'  {k}: {c}')

    # === ANGO 索引：(region_zh, year, qn) → 题目数据 ===
    ango = json.loads(Path('data/ango_cache/test_dataset.json').read_text(encoding='utf-8'))
    ango_idx = defaultdict(list)  # (region, year, qn) → list of (entry_index, in_history)
    ango_region_year = Counter()

    for i, item in enumerate(ango):
        # 主 entry
        src = item.get('source', '') or ''
        y, r, qn = parse_ango_source(src)
        if r and y:
            ango_region_year[(r, y)] += 1
            if qn is not None:
                ango_idx[(r, y, qn)].append((i, -1))
        # history
        for hi, h in enumerate(item.get('history', []) or []):
            hsrc = h.get('source', '') or ''
            hy, hr, hqn = parse_ango_source(hsrc)
            if hr and hy:
                ango_region_year[(hr, hy)] += 1
                if hqn is not None:
                    ango_idx[(hr, hy, hqn)].append((i, hi))

    print(f'\n[ANGO] (region,year,qn) 索引: {len(ango_idx)} 条')

    # === 评估覆盖 ===
    matched = []
    region_year_unmatched = Counter()
    for region_zh, year, qn, paperkey, qid in lib_keys:
        if (region_zh, year, qn) in ango_idx:
            matched.append((region_zh, year, qn, paperkey, qid))
        else:
            region_year_unmatched[(region_zh, year)] += 1

    print(f'\n[潜在救援] lib 占位 ∩ ANGO (region,year,qn) 命中: {len(matched)} / {len(lib_keys)}')
    print('未命中分布 (region,year) top 20:')
    for k, c in region_year_unmatched.most_common(20):
        in_ango = ango_region_year.get(k, 0)
        print(f'  {k}: lib缺{c} / ango有{in_ango}')

    # 输出报告
    out = []
    out.append('# D-16 L-0c ANGO 救援可行性评估')
    out.append('')
    out.append(f'- lib 省考占位题: **{len(lib_keys)}**')
    out.append(f'- ANGO (region,year,qn) 唯一键: **{len(ango_idx)}**')
    out.append(f'- 命中（key 完全匹配，待 sim 二次校验）: **{len(matched)}**')
    out.append('')
    out.append('## 命中题清单')
    for r, y, qn, pk, qid in sorted(matched):
        out.append(f'  - {pk}  q{qn:03d}  → ANGO ({r}, {y}, qn={qn})  id={qid}')
    out.append('')
    out.append('## 未命中 (region,year) ANGO 有 vs 没有')
    for k, c in region_year_unmatched.most_common():
        in_ango = ango_region_year.get(k, 0)
        sign = '✓' if in_ango > 0 else '✗'
        out.append(f'  - {sign} {k}: lib缺 {c} / ango 有 {in_ango} 题')

    Path('data/ango_cache/ango_feasibility.md').write_text(
        '\n'.join(out), encoding='utf-8'
    )
    print(f'\n[report] data/ango_cache/ango_feasibility.md')


if __name__ == '__main__':
    main()
