#!/usr/bin/env python3
"""修复 2025 副省级题目分类"""
import json

print("=" * 70)
print("修复 2025 副省级")
print("=" * 70)

# 读取所有数据
all_questions = []
for mod in ['changshi', 'yanyu', 'shuliang', 'panduan', 'ziliao']:
    path = f'src/data/xingce/{mod}/national_2025_fushengjia.json'
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_questions.extend(data)
    except:
        continue

print(f"总共读取 {len(all_questions)} 题")

# 去重
seen = {}
unique_questions = []
for q in all_questions:
    num = int(q['id'].split('-')[-1])
    if num not in seen:
        seen[num] = q
        unique_questions.append(q)

print(f"去重后 {len(unique_questions)} 题")

# 排序
unique_questions.sort(key=lambda x: int(x['id'].split('-')[-1]))

# 标准题号范围（副省级 135 题）
ranges = {
    'changshi': (1, 20),
    'yanyu': (21, 60),
    'shuliang': (61, 75),
    'panduan': (76, 115),
    'ziliao': (116, 135),
}

# 重新分配
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
        print(f"[WARN] 题号 {num} 超出范围")
        continue

    # 更新 category、id 和 level
    q['category'] = target_mod
    id_parts = q['id'].split('-')
    id_parts[2] = target_mod
    q['id'] = '-'.join(id_parts)
    q['level'] = 'fushengjia'

    new_modules[target_mod].append(q)

# 保存
for mod in new_modules:
    path = f'src/data/xingce/{mod}/national_2025_fushengjia.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(new_modules[mod], f, ensure_ascii=False, indent=2)

    actual = len(new_modules[mod])
    expected = ranges[mod][1] - ranges[mod][0] + 1
    status = "[OK]" if actual == expected else f"[WARN] 期望{expected}"
    print(f"  {status} {mod}: {actual} 题")

print("\n修复完成！")
