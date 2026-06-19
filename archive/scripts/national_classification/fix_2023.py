#!/usr/bin/env python3
"""修复 2023 国考题目分类"""
import json

def fix_year(year, expected_counts):
    """
    按题号重新分配模块
    expected_counts: {'changshi': 20, 'yanyu': 40, 'shuliang': 15, 'panduan': 40, 'ziliao': 20}
    """
    for level in ['fushengjia', 'dishi', 'xingzhengzhifa']:
        print(f"\n{'='*60}")
        print(f"修复 {year} {level}")
        print('='*60)

        # 1. 读取所有数据
        all_questions = []
        for mod in ['changshi', 'yanyu', 'shuliang', 'panduan', 'ziliao']:
            path = f'src/data/xingce/{mod}/national_{year}_{level}.json'
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for q in data:
                        q['_original_module'] = mod
                        all_questions.append(q)
            except FileNotFoundError:
                continue

        if not all_questions:
            print(f"  [SKIP] 无数据")
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

        # 4. 标准题号范围
        ranges = {
            'changshi': (1, expected_counts['changshi']),
            'yanyu': (expected_counts['changshi'] + 1,
                     expected_counts['changshi'] + expected_counts['yanyu']),
            'shuliang': (expected_counts['changshi'] + expected_counts['yanyu'] + 1,
                        expected_counts['changshi'] + expected_counts['yanyu'] + expected_counts['shuliang']),
            'panduan': (expected_counts['changshi'] + expected_counts['yanyu'] + expected_counts['shuliang'] + 1,
                       expected_counts['changshi'] + expected_counts['yanyu'] + expected_counts['shuliang'] + expected_counts['panduan']),
            'ziliao': (expected_counts['changshi'] + expected_counts['yanyu'] + expected_counts['shuliang'] + expected_counts['panduan'] + 1,
                      sum(expected_counts.values()))
        }

        # 5. 重新分配
        new_modules = {mod: [] for mod in ['changshi', 'yanyu', 'shuliang', 'panduan', 'ziliao']}

        for q in unique_questions:
            num = int(q['id'].split('-')[-1])

            # 找到应该属于哪个模块
            target_mod = None
            for mod, (start, end) in ranges.items():
                if start <= num <= end:
                    target_mod = mod
                    break

            if not target_mod:
                print(f"  [WARN] 题号 {num} 超出范围")
                continue

            # 更新 category 和 id
            q['category'] = target_mod
            id_parts = q['id'].split('-')
            id_parts[2] = target_mod
            q['id'] = '-'.join(id_parts)

            # 修复 level
            q['level'] = level

            new_modules[target_mod].append(q)

        # 6. 保存
        for mod in new_modules:
            path = f'src/data/xingce/{mod}/national_{year}_{level}.json'
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(new_modules[mod], f, ensure_ascii=False, indent=2)

            actual = len(new_modules[mod])
            expected = expected_counts[mod]
            status = "[OK]" if actual == expected else f"[WARN] 期望{expected}"
            print(f"  {status} {mod}: {actual} 题")

# 修复 2023
fix_year('2023', {
    'changshi': 20, 'yanyu': 40, 'shuliang': 15, 'panduan': 40, 'ziliao': 20
})

print("\n修复完成！")
