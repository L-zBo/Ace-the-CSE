#!/usr/bin/env python3
"""审计 2024 国考行测数据"""
import json
import glob

files = sorted(glob.glob('src/data/xingce/*/national_2024_*.json'))

print("=" * 70)
print("2024 国考行测数据审计")
print("=" * 70)

total_by_level = {}
for f in files:
    module = f.replace('\\', '/').split('/')[-2]
    filename = f.replace('\\', '/').split('/')[-1]
    level = filename.replace('national_2024_', '').replace('.json', '')

    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)
        count = len(data)
        opt_less_4 = sum(1 for q in data if len(q.get('options', [])) < 4)
        levels_in_data = set(q.get('level', 'unknown') for q in data)

        print(f"\n{module}/{level}:")
        print(f"  题数: {count}")
        print(f"  level字段: {levels_in_data}")
        if opt_less_4 > 0:
            print(f"  [!] 选项<4: {opt_less_4}/{count}")

        # 统计总数
        if level not in total_by_level:
            total_by_level[level] = 0
        total_by_level[level] += count

print("\n" + "=" * 70)
print("各级别总题数:")
for level, cnt in sorted(total_by_level.items()):
    print(f"  {level}: {cnt} 题")

print("\n标准题数:")
print("  副省级(fushengjia): 135 题")
print("  地市级(dishi): 130 题")
print("  行政执法(xingzhengzhifa): 130 题")
