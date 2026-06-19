#!/usr/bin/env python3
"""为 26 条确认图形题的孤儿图片添加 JSON questionImage 引用；删除 1 条误判。"""
import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 确认为图形题的（exam, qid）→ 添加 questionImage
TO_LINK = [
    ("national_2021", 75), ("national_2021_fushengjia", 80),
    ("national_2024_dishi", 77), ("national_2024_fushengjia", 80),
    ("national_2024_xingzhengzhifa", 76),
    ("national_2025_dishi", 81), ("national_2025_fushengjia", 86),
    ("national_2025_xingzhengzhifa", 82), ("national_2025_xingzhengzhifa", 90),
    ("provincial_anhui_2020", 85), ("provincial_hebei_2020", 77),
    ("provincial_henan_2021", 108),
    ("provincial_jiangsu_2020", 90), ("provincial_jiangsu_2021", 90),
    ("provincial_jiangsu_2022", 86),
    ("provincial_jiangsu_2024", 88), ("provincial_jiangsu_2024", 89),
    ("provincial_shanghai_2020", 33), ("provincial_shanghai_2020", 43),
    ("provincial_shanghai_2020", 62), ("provincial_shanghai_2020", 66),
    ("provincial_shanghai_2021", 29), ("provincial_shanghai_2021", 30),
    ("provincial_shanghai_2021", 65),
    ("provincial_sichuan_2020", 55),
    ("provincial_zhejiang_2022", 80),
]

# 误判，需删除图片
TO_DELETE = [
    ("national_2021", 89),  # 定义判断，"决策树...图解法" 无图
]

linked = 0
for exam, qn in TO_LINK:
    jp = f'src/data/xingce/panduan/{exam}.json'
    if not os.path.exists(jp):
        print(f'  [SKIP] {jp} 不存在'); continue
    qs = json.load(open(jp, encoding='utf-8'))
    img_path = f'/img/questions/{exam}/q{qn:03d}.png'
    disk = 'public' + img_path
    if not os.path.exists(disk):
        print(f'  [SKIP] 图片不存在 {disk}'); continue
    for q in qs:
        if int(q['id'].split('-')[-1]) == qn:
            q['questionImage'] = img_path
            linked += 1
            print(f'  链接 {exam} Q{qn}')
            break
    json.dump(qs, open(jp, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)

deleted = 0
for exam, qn in TO_DELETE:
    p = f'public/img/questions/{exam}/q{qn:03d}.png'
    if os.path.exists(p):
        os.remove(p)
        deleted += 1
        print(f'  删除误判 {p}')

print(f'\n总计：链接 {linked} 张，删除 {deleted} 张')
