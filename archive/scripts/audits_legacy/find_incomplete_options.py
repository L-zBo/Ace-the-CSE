#!/usr/bin/env python3
"""找出所有选项不全的题目"""
import json
import glob

print("=" * 70)
print("收集选项不全的题目")
print("=" * 70)

incomplete_questions = []

files = sorted(glob.glob('src/data/xingce/*/national_*.json'))

for f in files:
    parts = f.replace('\\', '/').split('/')
    module = parts[-2]
    filename = parts[-1]

    name_parts = filename.replace('national_', '').replace('.json', '').split('_')
    if len(name_parts) != 2:
        continue

    year = int(name_parts[0])
    level = name_parts[1]

    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)

        for q in data:
            options = q.get('options', [])
            if len(options) < 4:
                incomplete_questions.append({
                    'year': year,
                    'level': level,
                    'module': module,
                    'id': q['id'],
                    'num': int(q['id'].split('-')[-1]),
                    'opt_count': len(options),
                    'content': q.get('content', '')[:80],
                })

print(f"\n找到 {len(incomplete_questions)} 题选项不全")

# 按年份、级别分组
by_year_level = {}
for q in incomplete_questions:
    key = f"{q['year']}_{q['level']}"
    if key not in by_year_level:
        by_year_level[key] = []
    by_year_level[key].append(q)

print("\n按年份级别分组:")
for key in sorted(by_year_level.keys(), reverse=True):
    questions = by_year_level[key]
    print(f"\n{key}: {len(questions)} 题")

    # 按选项数分组
    by_opt = {}
    for q in questions:
        opt_count = q['opt_count']
        if opt_count not in by_opt:
            by_opt[opt_count] = []
        by_opt[opt_count].append(q['num'])

    for opt_count in sorted(by_opt.keys()):
        nums = sorted(by_opt[opt_count])
        print(f"  {opt_count}选项: {len(nums)} 题 - 题号 {nums[:10]}{'...' if len(nums) > 10 else ''}")

# 保存到文件
with open('incomplete_options.json', 'w', encoding='utf-8') as f:
    json.dump(incomplete_questions, f, ensure_ascii=False, indent=2)

print(f"\n已保存到 incomplete_options.json")
