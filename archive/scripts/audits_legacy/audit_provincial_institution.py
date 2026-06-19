#!/usr/bin/env python3
"""审计省考和事业编数据"""
import json
import glob

print("=" * 70)
print("省考和事业编数据审计")
print("=" * 70)

# 统计省考
provincial_files = glob.glob('src/data/xingce/*/provincial_*.json')
provincial_count = 0
provincial_by_province = {}

for f in provincial_files:
    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)
        provincial_count += len(data)

        # 提取省份
        filename = f.replace('\\', '/').split('/')[-1]
        parts = filename.replace('provincial_', '').replace('.json', '').split('_')
        if len(parts) >= 2:
            province = parts[0]
            year = parts[1]
            key = f"{province}_{year}"
            if key not in provincial_by_province:
                provincial_by_province[key] = 0
            provincial_by_province[key] += len(data)

print(f"\n省考数据:")
print(f"  总文件数: {len(provincial_files)}")
print(f"  总题数: {provincial_count}")
print(f"  覆盖省份年份: {len(provincial_by_province)}")

# 统计事业编
institution_files = glob.glob('src/data/xingce/*/institution_*.json')
institution_count = 0
institution_by_year_type = {}

for f in institution_files:
    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)
        institution_count += len(data)

        # 提取年份和类型
        filename = f.replace('\\', '/').split('/')[-1]
        parts = filename.replace('institution_', '').replace('.json', '').split('_')
        if len(parts) >= 2:
            year = parts[0]
            type_code = parts[1].upper()
            key = f"{year}_{type_code}"
            if key not in institution_by_year_type:
                institution_by_year_type[key] = 0
            institution_by_year_type[key] += len(data)

print(f"\n事业编数据:")
print(f"  总文件数: {len(institution_files)}")
print(f"  总题数: {institution_count}")
print(f"  覆盖年份类型: {len(institution_by_year_type)}")

# 按年份统计事业编
by_year = {}
for key in institution_by_year_type:
    year = key.split('_')[0]
    if year not in by_year:
        by_year[year] = []
    by_year[year].append(key.split('_')[1])

print(f"\n事业编按年份:")
for year in sorted(by_year.keys()):
    types = sorted(by_year[year])
    print(f"  {year}: {', '.join(types)} 类")

print("\n" + "=" * 70)
print(f"总计: 省考 {provincial_count} 题 + 事业编 {institution_count} 题 = {provincial_count + institution_count} 题")
print("=" * 70)
