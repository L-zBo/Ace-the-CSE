#!/usr/bin/env python3
"""修复 2019 国考题目分类"""
import json

def fix_year(year, expected_counts):
    for level in ['fushengjia', 'dishi']:
        print(f"\n{'='*60}")
        print(f"修复 {year} {level}")
        print('='*60)

        # 读取所有数据
        all_questions = []
        for mod in ['changshi', 'yanyu', 'shuliang', 'panduan', 'ziliao']:
            path = f'src/data/xingce/{mod}/national_{year}_{level}.json'
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_questions.extend(data)
            except:
                continue

        if not all_questions:
            continue

        # 去重
        seen = {}
        unique_questions = []
        for q in all_questions:
            num = int(q['id'].split('-')[-1])
            if num not in seen:
                seen[num] = q
                unique_questions.append(q)

        # 排序
        unique_questions.sort(key=lambda x: int(x['id'].split('-')[-1]))

        # 计算题号范围
        ranges = {}
        start = 1
        for mod in ['changshi', 'yanyu', 'shuliang', 'panduan', 'ziliao']:
            count = expected_counts[level][mod]
            ranges[mod] = (start, start + count - 1)
            start += count

        # 重新分配
        new_modules = {mod: [] for mod in ['changshi', 'yanyu', 'shuliang', 'panduan', 'ziliao']}

        for q in unique_questions:
            num = int(q['id'].split('-')[-1])

            target_mod = None
            for mod, (s, e) in ranges.items():
                if s <= num <= e:
                    target_mod = mod
                    break

            if not target_mod:
                continue

            q['category'] = target_mod
            id_parts = q['id'].split('-')
            id_parts[2] = target_mod
            q['id'] = '-'.join(id_parts)
            q['level'] = level

            new_modules[target_mod].append(q)

        # 保存
        for mod in new_modules:
            path = f'src/data/xingce/{mod}/national_{year}_{level}.json'
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(new_modules[mod], f, ensure_ascii=False, indent=2)

            actual = len(new_modules[mod])
            expected = expected_counts[level][mod]
            status = "[OK]" if actual == expected else f"[WARN] 期望{expected}"
            print(f"  {status} {mod}: {actual} 题")

# 修复 2019
fix_year('2019', {
    'fushengjia': {'changshi': 20, 'yanyu': 40, 'shuliang': 15, 'panduan': 40, 'ziliao': 20},
    'dishi': {'changshi': 20, 'yanyu': 40, 'shuliang': 10, 'panduan': 40, 'ziliao': 20},
})

print("\n修复完成！")
