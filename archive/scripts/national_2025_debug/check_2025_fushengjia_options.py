#!/usr/bin/env python3
"""找出 2025 国考副省级选项不全的题目"""
import json

print("=" * 70)
print("2025 国考副省级 - 选项不全题目详情")
print("=" * 70)

for mod in ['changshi', 'yanyu', 'shuliang', 'panduan', 'ziliao']:
    path = f'src/data/xingce/{mod}/national_2025_fushengjia.json'

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    incomplete = []
    for q in data:
        opts = len(q.get('options', []))
        if opts < 4:
            incomplete.append({
                'id': q['id'],
                'num': int(q['id'].split('-')[-1]),
                'opts': opts,
                'content': q.get('content', '')[:100],
                'options': q.get('options', [])
            })

    if incomplete:
        print(f"\n{mod}: {len(incomplete)} 题选项不全")
        for item in incomplete:
            print(f"  题号 {item['num']}: {item['opts']} 个选项")
            print(f"    内容: {item['content']}...")
            if item['options']:
                print(f"    现有选项: {[o['label'] for o in item['options']]}")
