#!/usr/bin/env python3
"""修正 2025 国考题目分类错误"""
import json
import os

def fix_2025_classification(level):
    """
    修正分类错误:
    - 常识 21-35 → 言语
    - 言语 61-65 → 数量
    - 数量 66-80 → 数量 61-75
    - 判断 7 → 常识（如果存在）
    - 判断 81-115 → 判断 76-115
    """

    # 读取所有模块数据
    modules = {}
    for mod in ['changshi', 'yanyu', 'shuliang', 'panduan', 'ziliao']:
        path = f'src/data/xingce/{mod}/national_2025_{level}.json'
        with open(path, 'r', encoding='utf-8') as f:
            modules[mod] = json.load(f)

    # 收集需要移动的题目
    moves = []

    # 1. 常识 21-35 → 言语
    for q in modules['changshi'][:]:
        num = int(q['id'].split('-')[-1])
        if 21 <= num <= 35:
            moves.append(('changshi', 'yanyu', q, num))

    # 2. 言语 61-65 → 数量
    for q in modules['yanyu'][:]:
        num = int(q['id'].split('-')[-1])
        if 61 <= num <= 65:
            moves.append(('yanyu', 'shuliang', q, num))

    # 3. 判断 7 → 常识
    for q in modules['panduan'][:]:
        num = int(q['id'].split('-')[-1])
        if num == 7:
            moves.append(('panduan', 'changshi', q, num))

    # 4. 判断 81-115 → 重新编号为 76-110
    for q in modules['panduan'][:]:
        num = int(q['id'].split('-')[-1])
        if 81 <= num <= 115:
            # 重新编号: 81→76, 82→77, ..., 115→110
            new_num = num - 5
            q['id'] = q['id'].rsplit('-', 1)[0] + f'-{new_num:03d}'

    # 5. 数量 66-80 → 重新编号为 61-75
    for q in modules['shuliang'][:]:
        num = int(q['id'].split('-')[-1])
        if 66 <= num <= 80:
            new_num = num - 5
            q['id'] = q['id'].rsplit('-', 1)[0] + f'-{new_num:03d}'

    # 执行移动
    for from_mod, to_mod, q, num in moves:
        # 从源模块删除
        modules[from_mod] = [x for x in modules[from_mod] if int(x['id'].split('-')[-1]) != num]

        # 更新 category 和 id
        q['category'] = to_mod
        old_id_parts = q['id'].split('-')
        old_id_parts[2] = to_mod  # 更新 category 部分
        q['id'] = '-'.join(old_id_parts)

        # 添加到目标模块
        modules[to_mod].append(q)

    # 排序并保存
    for mod in modules:
        # 按题号排序
        modules[mod].sort(key=lambda x: int(x['id'].split('-')[-1]))

        path = f'src/data/xingce/{mod}/national_2025_{level}.json'
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(modules[mod], f, ensure_ascii=False, indent=2)

        print(f"[OK] {mod}: {len(modules[mod])} 题")

    return modules

# 修复三个级别
for level in ['fushengjia', 'dishi', 'xingzhengzhifa']:
    print(f"\n{'='*60}")
    print(f"修复 {level}")
    print('='*60)
    fix_2025_classification(level)

print("\n修复完成！")
