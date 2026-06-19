#!/usr/bin/env python3
import json

with open('src/data/xingce/ziliao/national_2023_xingzhengzhifa.json', encoding='utf-8') as f:
    data = json.load(f)

numbers = sorted([int(q['id'].split('-')[-1]) for q in data])
print(f"xingzhengzhifa 资料题号: {numbers}")
print(f"题数: {len(numbers)}")
print(f"应该是: 116-135 (20题)")
missing = sorted(set(range(116, 136)) - set(numbers))
print(f"缺失: {missing}")
