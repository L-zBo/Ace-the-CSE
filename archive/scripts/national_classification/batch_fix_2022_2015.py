#!/usr/bin/env python3
"""批量修复 2022-2015 国考数据（level + 分类 + 去重）"""
import json
import glob
import os

def fix_year(year):
    """修复指定年份的国考数据"""
    print(f"\n{'='*70}")
    print(f"修复 {year} 国考")
    print('='*70)

    # 标准题数配置
    # 2022 年开始有行政执法类
    if year >= 2022:
        level_configs = {
            'fushengjia': {'changshi': 20, 'yanyu': 40, 'shuliang': 15, 'panduan': 40, 'ziliao': 20},
            'dishi': {'changshi': 20, 'yanyu': 40, 'shuliang': 10, 'panduan': 40, 'ziliao': 20},
            'xingzhengzhifa': {'changshi': 20, 'yanyu': 40, 'shuliang': 15, 'panduan': 40, 'ziliao': 20},
        }
    else:
        # 2021 及之前只有副省级和地市级
        level_configs = {
            'fushengjia': {'changshi': 20, 'yanyu': 40, 'shuliang': 15, 'panduan': 40, 'ziliao': 20},
            'dishi': {'changshi': 20, 'yanyu': 40, 'shuliang': 10, 'panduan': 40, 'ziliao': 20},
        }

    results = {}

    for level, expected_counts in level_configs.items():
        # 1. 读取所有数据
        all_questions = []
        for mod in ['changshi', 'yanyu', 'shuliang', 'panduan', 'ziliao']:
            path = f'src/data/xingce/{mod}/national_{year}_{level}.json'
            if not os.path.exists(path):
                continue

            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for q in data:
                    all_questions.append(q)

        if not all_questions:
            continue

        # 2. 去重（按题号）
        seen = {}
        unique_questions = []
        for q in all_questions:
            num = int(q['id'].split('-')[-1])
            if num not in seen:
                seen[num] = q
                unique_questions.append(q)

        # 3. 按题号排序
        unique_questions.sort(key=lambda x: int(x['id'].split('-')[-1]))

        # 4. 计算题号范围
        ranges = {}
        start = 1
        for mod in ['changshi', 'yanyu', 'shuliang', 'panduan', 'ziliao']:
            count = expected_counts[mod]
            ranges[mod] = (start, start + count - 1)
            start += count

        # 5. 重新分配到正确的模块
        new_modules = {mod: [] for mod in ['changshi', 'yanyu', 'shuliang', 'panduan', 'ziliao']}

        for q in unique_questions:
            num = int(q['id'].split('-')[-1])

            # 找到应该属于哪个模块
            target_mod = None
            for mod, (s, e) in ranges.items():
                if s <= num <= e:
                    target_mod = mod
                    break

            if not target_mod:
                continue

            # 更新 category、id 和 level
            q['category'] = target_mod
            id_parts = q['id'].split('-')
            id_parts[2] = target_mod
            q['id'] = '-'.join(id_parts)
            q['level'] = level

            new_modules[target_mod].append(q)

        # 6. 保存
        level_result = {}
        for mod in new_modules:
            path = f'src/data/xingce/{mod}/national_{year}_{level}.json'
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(new_modules[mod], f, ensure_ascii=False, indent=2)

            actual = len(new_modules[mod])
            expected = expected_counts[mod]
            level_result[mod] = {'actual': actual, 'expected': expected}

        results[level] = level_result

    # 7. 输出结果
    for level, mods in results.items():
        total_actual = sum(m['actual'] for m in mods.values())
        total_expected = sum(m['expected'] for m in mods.values())
        status = "[OK]" if total_actual == total_expected else f"({total_actual}/{total_expected})"

        print(f"\n  {level}: {status}")
        for mod, counts in mods.items():
            if counts['actual'] != counts['expected']:
                print(f"    [WARN] {mod}: {counts['actual']}/{counts['expected']}")

    return results

# 批量修复 2022-2015
print("=" * 70)
print("批量修复 2022-2015 国考数据")
print("=" * 70)

all_results = {}
for year in range(2022, 2014, -1):  # 2022, 2021, ..., 2015
    results = fix_year(year)
    all_results[year] = results

# 最终总结
print("\n" + "=" * 70)
print("修复总结")
print("=" * 70)

for year in sorted(all_results.keys(), reverse=True):
    print(f"\n{year} 年:")
    for level, mods in all_results[year].items():
        total_actual = sum(m['actual'] for m in mods.values())
        total_expected = sum(m['expected'] for m in mods.values())
        status = "[OK] 100%" if total_actual == total_expected else f"[WARN] {total_actual}/{total_expected}"
        print(f"  {level}: {status}")

print("\n修复完成！")
