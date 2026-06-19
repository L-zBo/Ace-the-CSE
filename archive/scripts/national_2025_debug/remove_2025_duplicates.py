#!/usr/bin/env python3
"""删除 2025 国考重复题目"""
import json

for level in ['fushengjia', 'dishi', 'xingzhengzhifa']:
    print(f"\n{'='*60}")
    print(f"检查 {level} 重复题目")
    print('='*60)

    for mod in ['changshi', 'yanyu', 'shuliang', 'panduan', 'ziliao']:
        path = f'src/data/xingce/{mod}/national_2025_{level}.json'
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 检查重复题号
        seen = {}
        duplicates = []
        for i, q in enumerate(data):
            num = int(q['id'].split('-')[-1])
            if num in seen:
                duplicates.append((i, num, q['content'][:50]))
            else:
                seen[num] = i

        if duplicates:
            print(f"\n  {mod}: 发现 {len(duplicates)} 个重复题号")
            for idx, num, content in duplicates:
                print(f"    题号 {num} (索引 {idx}): {content}...")

            # 删除重复项（保留第一个）
            unique_data = []
            seen_nums = set()
            for q in data:
                num = int(q['id'].split('-')[-1])
                if num not in seen_nums:
                    unique_data.append(q)
                    seen_nums.add(num)

            # 保存
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(unique_data, f, ensure_ascii=False, indent=2)

            print(f"    删除后: {len(unique_data)} 题")

print("\n清理完成！")
