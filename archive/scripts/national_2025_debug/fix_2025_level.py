#!/usr/bin/env python3
"""修复 2025 国考 level 字段"""
import json
import glob

files = sorted(glob.glob('src/data/xingce/*/national_2025_*.json'))

for f in files:
    # 从文件名提取 level
    # Windows 路径用反斜杠，需要统一处理
    filename = f.replace('\\', '/').split('/')[-1]  # national_2025_fushengjia.json
    level = filename.replace('national_2025_', '').replace('.json', '')

    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 修复 level 字段
    modified = 0
    for q in data:
        if q.get('level') != level:
            q['level'] = level
            modified += 1

    if modified > 0:
        with open(f, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        print(f"[OK] {f}: 修复 {modified}/{len(data)} 条 level 字段")
    else:
        print(f"[SKIP] {f}: 无需修复")

print("\n修复完成！")
