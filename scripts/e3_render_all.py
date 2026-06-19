"""批量渲染各 PDF 关键页（覆盖 audit 不可作答题号段）"""
import fitz, json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
idx = json.loads((ROOT/'data'/'e1_vision'/'pdf_index.json').read_text(encoding='utf-8'))

# (paperKey, [题号近似页范围 0-indexed])
TARGETS = {
    'provincial_gansu_2024': [2, 3, 8, 9],         # q018-020 changshi + q054 yanyu + q069-070 shuliang + q078/087 panduan
    'provincial_hunan_2023': [4, 5, 7],            # q039,056,066 散布
    'provincial_hebei_2022': [6, 9, 13],           # q060 yanyu, q094 panduan
    'provincial_ningxia_2024': [5, 6],             # q052-055 yanyu
    'provincial_qinghai_2024': [5, 6, 11],         # q050,060 yanyu, q090 panduan
    'provincial_hunan_2024': [4],                  # q040 yanyu
    'provincial_shandong_2022': [1, 2],            # q008-009 changshi
    'provincial_hainan_2024': [13, 14],            # q110 ziliao
    'provincial_guangdong_2023': [10],             # q089 changshi
    'provincial_guangdong_2024': [4],              # q031 shuliang
    'provincial_yunnan_2023': [6],                 # q055 changshi
    'institution_2022_b': [40, 41, 42],            # q034 (取 2022B 段位)
    'institution_2022_c': [80, 81],                # q050 (2022C 段位)
    'provincial_beijing_2023': [16],               # q111 panduan
    'provincial_neimenggu_2023': [2],              # q018 changshi
    'provincial_jilin_2024': [10],                 # q077 panduan (已有)
}

os.makedirs('data/e1_vision/png_e3', exist_ok=True)

for pk, pages in TARGETS.items():
    pdf = idx.get(pk)
    if not pdf:
        print(f'NIL  {pk}')
        continue
    try:
        doc = fitz.open(str(ROOT/pdf))
    except Exception as e:
        print(f'ERR  {pk}: {e}')
        continue
    print(f'OK   {pk}: {len(doc)} pages')
    mat = fitz.Matrix(5.0, 5.0)
    for i in pages:
        if 0 <= i < len(doc):
            try:
                pix = doc[i].get_pixmap(matrix=mat)
                pix.save(f'data/e1_vision/png_e3/{pk.replace("provincial_","").replace("institution_","inst_")}__p{i+1:03d}.png')
            except Exception:
                pass
    doc.close()
print('done')
