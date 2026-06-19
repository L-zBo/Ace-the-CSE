#!/usr/bin/env python3
"""审计国考行测题数分布"""
import json
import glob
from collections import defaultdict

# 统计国考行测题数
national_files = sorted(glob.glob('src/data/xingce/*/national_*.json'))
stats = defaultdict(lambda: defaultdict(int))
options_stats = defaultdict(lambda: {'total': 0, 'less_than_4': 0})

for f in national_files:
    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)
        for q in data:
            year = q.get('year', 'unknown')
            level = q.get('level', 'unknown')
            module = q.get('module', 'unknown')
            key = f'{year}_{level}'
            stats[key][module] += 1
            stats[key]['total'] += 1

            # 统计选项数
            options = q.get('options', [])
            options_stats[key]['total'] += 1
            if len(options) < 4:
                options_stats[key]['less_than_4'] += 1

# 按年份排序输出
print("=" * 60)
print("国考行测题数分布")
print("=" * 60)
for key in sorted(stats.keys(), reverse=True):
    total = stats[key]['total']
    print(f'\n{key}: 总计 {total} 题')
    for mod, cnt in sorted(stats[key].items()):
        if mod != 'total':
            print(f'  {mod}: {cnt}')

    # 选项统计
    opt_stat = options_stats[key]
    if opt_stat['less_than_4'] > 0:
        pct = opt_stat['less_than_4'] / opt_stat['total'] * 100
        print(f'  [!] 选项<4: {opt_stat["less_than_4"]}/{opt_stat["total"]} ({pct:.1f}%)')

print("\n" + "=" * 60)
print("标准题数参考（国考行测）")
print("=" * 60)
print("副省级/行政执法: 135 题")
print("  常识: 20, 言语: 40, 数量: 15, 判断: 40, 资料: 20")
print("地市级: 130 题")
print("  常识: 20, 言语: 40, 数量: 10, 判断: 40, 资料: 20")
