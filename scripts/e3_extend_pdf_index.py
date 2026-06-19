"""扩展 pdf_index.json，扫描 material 下 11 个新 paperKey 的 PDF"""
import json, re, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAT = ROOT / 'material'

PROV_ZH = {
    'anhui': ['安徽'], 'beijing': ['北京'], 'fujian': ['福建'], 'gansu': ['甘肃'],
    'guangdong': ['广东'], 'guangxi': ['广西'], 'guizhou': ['贵州'], 'hainan': ['海南'],
    'hebei': ['河北'], 'henan': ['河南'], 'heilongjiang': ['黑龙江'], 'hubei': ['湖北'],
    'hunan': ['湖南'], 'jilin': ['吉林'], 'jiangsu': ['江苏'], 'jiangxi': ['江西'],
    'liaoning': ['辽宁'], 'neimenggu': ['内蒙古'], 'ningxia': ['宁夏'], 'qinghai': ['青海'],
    'shandong': ['山东'], 'shanxi': ['山西'], 'shaanxi': ['陕西'], 'shanghai': ['上海'],
    'sichuan': ['四川'], 'shenzhen': ['深圳'], 'tianjin': ['天津'], 'xizang': ['西藏'],
    'xinjiang': ['新疆'], 'yunnan': ['云南'], 'zhejiang': ['浙江'], 'chongqing': ['重庆'],
}

NEW_TARGETS = [
    'institution_2022_b',
    'provincial_gansu_2024',
    'provincial_guangdong_2023',
    'provincial_hainan_2024',
    'provincial_hebei_2022',
    'provincial_hunan_2023',
    'provincial_hunan_2024',
    'provincial_ningxia_2024',
    'provincial_qinghai_2024',
    'provincial_xinjiang_2023',
    'provincial_yunnan_2023',
]


def scan_pdf(target):
    if target.startswith('institution_'):
        # 形如 institution_2022_b → B 类联考
        m = re.match(r'institution_(\d{4})_([a-z])$', target)
        if not m: return []
        yr, level = m.groups()
        results = []
        for p in MAT.rglob('*.pdf'):
            ps = str(p)
            if '事业编' not in ps and '事业单位' not in ps:
                continue
            if level.upper() == 'B' and '/B类/' in ps.replace('\\', '/') and '职测' in ps:
                results.append(p.relative_to(ROOT).as_posix())
        return results
    # provincial_PROV_YYYY
    m = re.match(r'provincial_([a-z_]+?)_(\d{4})$', target)
    if not m: return []
    prov_en, yr = m.groups()
    zh_list = PROV_ZH.get(prov_en, [])
    if not zh_list: return []
    results = []
    for p in MAT.rglob('*.pdf'):
        ps = str(p)
        name = p.name
        if '行测' not in name or '答案' in name or '解析' in name or '申论' in name:
            continue
        if yr not in name:
            continue
        if not any(zh in ps for zh in zh_list):
            continue
        results.append(p.relative_to(ROOT).as_posix())
    return results


def main():
    idx_path = ROOT / 'data' / 'e1_vision' / 'pdf_index.json'
    idx = json.loads(idx_path.read_text(encoding='utf-8'))
    added = 0
    for t in NEW_TARGETS:
        pdfs = scan_pdf(t)
        print(f'{t}: {len(pdfs)} candidate(s)')
        for p in pdfs:
            print(f'  - {p}')
        if pdfs:
            # 选最匹配的（优先非乡镇/非选调的标准卷）
            best = pdfs[0]
            for p in pdfs:
                if '乡镇' not in p and '选调' not in p and '区级' not in p:
                    best = p
                    break
            idx[t] = best
            added += 1
            print(f'  +use: {best}')
    if added:
        idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'\nadded {added} entries to pdf_index.json')

if __name__ == '__main__':
    main()
