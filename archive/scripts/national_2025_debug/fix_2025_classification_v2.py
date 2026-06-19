#!/usr/bin/env python3
"""修正 2025 国考题目分类和编号错误

问题分析（以副省级为例）:
- 常识: 1-35 (实际应该 1-20)
  - 1-20: 正确的常识
  - 21-35: 错误，应该是言语
- 言语: 36-65 (实际应该 21-60)
  - 36-60: 正确的言语，但编号错误（应该 21-60）
  - 61-65: 错误，应该是数量
- 数量: 66-80 (实际应该 61-75)
  - 66-80: 正确的数量，但编号错误（应该 61-75）
- 判断: 7, 81-115 (实际应该 76-115，共40题)
  - 7: 错误，应该是常识
  - 81-115: 正确的判断，但编号错误（应该 76-115）
"""
import json

def fix_level(level, expected_counts):
    """
    expected_counts: {'changshi': 20, 'yanyu': 40, 'shuliang': 15, 'panduan': 40, 'ziliao': 20}
    """
    print(f"\n{'='*60}")
    print(f"修复 {level}")
    print('='*60)

    # 1. 读取所有数据
    all_questions = []
    for mod in ['changshi', 'yanyu', 'shuliang', 'panduan', 'ziliao']:
        path = f'src/data/xingce/{mod}/national_2025_{level}.json'
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for q in data:
                q['_original_module'] = mod
                all_questions.append(q)

    # 2. 按题号排序
    all_questions.sort(key=lambda x: int(x['id'].split('-')[-1]))

    # 3. 重新分配到正确的模块
    new_modules = {
        'changshi': [],
        'yanyu': [],
        'shuliang': [],
        'panduan': [],
        'ziliao': []
    }

    # 标准题号范围
    ranges = {
        'changshi': (1, expected_counts['changshi']),
        'yanyu': (expected_counts['changshi'] + 1, expected_counts['changshi'] + expected_counts['yanyu']),
        'shuliang': (expected_counts['changshi'] + expected_counts['yanyu'] + 1,
                     expected_counts['changshi'] + expected_counts['yanyu'] + expected_counts['shuliang']),
        'panduan': (expected_counts['changshi'] + expected_counts['yanyu'] + expected_counts['shuliang'] + 1,
                    expected_counts['changshi'] + expected_counts['yanyu'] + expected_counts['shuliang'] + expected_counts['panduan']),
        'ziliao': (expected_counts['changshi'] + expected_counts['yanyu'] + expected_counts['shuliang'] + expected_counts['panduan'] + 1,
                   sum(expected_counts.values()))
    }

    # 按题号重新分配
    for q in all_questions:
        old_num = int(q['id'].split('-')[-1])

        # 找到应该属于哪个模块
        target_mod = None
        for mod, (start, end) in ranges.items():
            if start <= old_num <= end:
                target_mod = mod
                break

        if not target_mod:
            print(f"  [WARN] 题号 {old_num} 超出范围，跳过")
            continue

        # 更新 category 和 id
        q['category'] = target_mod
        id_parts = q['id'].split('-')
        id_parts[2] = target_mod  # 更新 category
        q['id'] = '-'.join(id_parts)

        new_modules[target_mod].append(q)

    # 4. 保存
    for mod in new_modules:
        path = f'src/data/xingce/{mod}/national_2025_{level}.json'
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(new_modules[mod], f, ensure_ascii=False, indent=2)

        actual = len(new_modules[mod])
        expected = expected_counts[mod]
        status = "[OK]" if actual == expected else f"[WARN] 期望{expected}"
        print(f"  {status} {mod}: {actual} 题")

# 修复三个级别
fix_level('fushengjia', {
    'changshi': 20, 'yanyu': 40, 'shuliang': 15, 'panduan': 40, 'ziliao': 20
})

fix_level('dishi', {
    'changshi': 20, 'yanyu': 40, 'shuliang': 10, 'panduan': 40, 'ziliao': 20
})

fix_level('xingzhengzhifa', {
    'changshi': 20, 'yanyu': 40, 'shuliang': 15, 'panduan': 40, 'ziliao': 20
})

print("\n修复完成！")
