#!/usr/bin/env python3
import json

with open('src/data/xingce/yanyu/national_2019_fushengjia.json', encoding='utf-8') as f:
    data = json.load(f)

numbers = sorted([int(q['id'].split('-')[-1]) for q in data])
print(f"2019 副省言语题号: {numbers}")
print(f"题数: {len(numbers)}")
print(f"应该是: 21-60 (40题)")

expected = set(range(21, 61))
actual = set(numbers)
missing = sorted(expected - actual)
print(f"缺失: {missing}")
