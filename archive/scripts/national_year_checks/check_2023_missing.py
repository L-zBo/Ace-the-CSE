#!/usr/bin/env python3
"""检查 2023 国考缺失的题号"""
import json

for level in ['fushengjia', 'dishi', 'xingzhengzhifa']:
    print(f"\n{'='*60}")
    print(f"2023 {level} 缺失题号")
    print('='*60)

    # 收集所有题号
    all_numbers = set()
    for mod in ['changshi', 'yanyu', 'shuliang', 'panduan', 'ziliao']:
        path = f'src/data/xingce/{mod}/national_2023_{level}.json'
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for q in data:
                    num = int(q['id'].split('-')[-1])
                    all_numbers.add(num)
        except:
            pass

    # 检查缺失
    if level == 'fushengjia':
        expected = set(range(1, 136))  # 1-135
    else:
        expected = set(range(1, 131))  # 1-130

    missing = sorted(expected - all_numbers)
    total = len(all_numbers)
    expected_total = len(expected)

    print(f"  实际题数: {total}")
    print(f"  期望题数: {expected_total}")
    if missing:
        print(f"  缺失题号: {missing}")
    else:
        print(f"  [OK] 无缺失")
