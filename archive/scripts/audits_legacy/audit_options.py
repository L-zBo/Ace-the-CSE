#!/usr/bin/env python3
"""审计全库选项完整性"""
import json
import glob

print("=" * 70)
print("全库选项完整性审计")
print("=" * 70)

# 统计各年份、各级别的选项情况
stats = {}

files = sorted(glob.glob('src/data/xingce/*/national_*.json'))

for f in files:
    parts = f.replace('\\', '/').split('/')
    module = parts[-2]
    filename = parts[-1]

    # 解析文件名: national_2025_fushengjia.json
    name_parts = filename.replace('national_', '').replace('.json', '').split('_')
    if len(name_parts) != 2:
        continue

    year = int(name_parts[0])
    level = name_parts[1]

    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)

        for q in data:
            options = q.get('options', [])
            opt_count = len(options)

            key = f"{year}_{level}"
            if key not in stats:
                stats[key] = {
                    'total': 0,
                    'opt_0': 0,
                    'opt_1': 0,
                    'opt_2': 0,
                    'opt_3': 0,
                    'opt_4': 0,
                }

            stats[key]['total'] += 1
            if opt_count == 0:
                stats[key]['opt_0'] += 1
            elif opt_count == 1:
                stats[key]['opt_1'] += 1
            elif opt_count == 2:
                stats[key]['opt_2'] += 1
            elif opt_count == 3:
                stats[key]['opt_3'] += 1
            elif opt_count == 4:
                stats[key]['opt_4'] += 1

# 输出结果
print("\n年份_级别 | 总题数 | 4选项 | <4选项 | 完整率")
print("-" * 70)

total_questions = 0
total_complete = 0
total_incomplete = 0

for key in sorted(stats.keys(), reverse=True):
    s = stats[key]
    complete = s['opt_4']
    incomplete = s['opt_0'] + s['opt_1'] + s['opt_2'] + s['opt_3']
    rate = complete / s['total'] * 100 if s['total'] > 0 else 0

    total_questions += s['total']
    total_complete += complete
    total_incomplete += incomplete

    status = "[OK]" if rate >= 95 else "[WARN]"
    print(f"{key:20} | {s['total']:6} | {complete:6} | {incomplete:7} | {rate:5.1f}% {status}")

    # 显示详细分布（如果有不完整的）
    if incomplete > 0:
        details = []
        if s['opt_0'] > 0:
            details.append(f"0选项:{s['opt_0']}")
        if s['opt_1'] > 0:
            details.append(f"1选项:{s['opt_1']}")
        if s['opt_2'] > 0:
            details.append(f"2选项:{s['opt_2']}")
        if s['opt_3'] > 0:
            details.append(f"3选项:{s['opt_3']}")
        if details:
            print(f"{'':20}   {', '.join(details)}")

print("-" * 70)
overall_rate = total_complete / total_questions * 100 if total_questions > 0 else 0
print(f"{'总计':20} | {total_questions:6} | {total_complete:6} | {total_incomplete:7} | {overall_rate:5.1f}%")

print("\n" + "=" * 70)
print(f"需要修复的题目数: {total_incomplete}")
print("=" * 70)
