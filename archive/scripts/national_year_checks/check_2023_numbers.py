#!/usr/bin/env python3
"""检查 2023 国考题号分布"""
import json

modules = ['changshi', 'yanyu', 'shuliang', 'panduan', 'ziliao']
level = 'fushengjia'

print("=" * 60)
print(f"2023 国考 {level} 题号分布")
print("=" * 60)

for mod in modules:
    try:
        with open(f'src/data/xingce/{mod}/national_2023_{level}.json', encoding='utf-8') as f:
            data = json.load(f)

        # 提取题号
        numbers = []
        for q in data:
            num = int(q['id'].split('-')[-1])
            numbers.append(num)

        numbers.sort()
        print(f"\n{mod}:")
        print(f"  题数: {len(numbers)}")
        print(f"  题号范围: {min(numbers)} - {max(numbers)}")
        if len(numbers) <= 50:
            print(f"  题号: {numbers}")
    except Exception as e:
        print(f"\n{mod}: 错误 - {e}")

print("\n" + "=" * 60)
print("标准题号分布（副省级 135 题）:")
print("  常识: 1-20")
print("  言语: 21-60")
print("  数量: 61-75")
print("  判断: 76-115")
print("  资料: 116-135")
