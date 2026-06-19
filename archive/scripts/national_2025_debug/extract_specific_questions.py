#!/usr/bin/env python3
"""从 PDF 中提取特定题号的完整内容"""
import fitz
import re

pdf_path = "material/【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-真题/2025年国家公务员录用考试《行测》题（副省级）.pdf"

# 需要补全选项的题号
question_nums = [4, 74, 79, 122, 130]

doc = fitz.open(pdf_path)

for q_num in question_nums:
    print(f"\n{'='*70}")
    print(f"题号 {q_num}")
    print('='*70)

    # 找到题号所在页
    found = False
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        # 搜索题号
        pattern = rf'(?:^|\n)\s*{q_num}\s*[\.\．、]\s*'
        match = re.search(pattern, text)

        if match:
            found = True
            print(f"在第 {page_num + 1} 页找到")

            # 提取题号到下一题之间的内容
            start = match.end()
            next_num = q_num + 1
            next_pattern = rf'(?:^|\n)\s*{next_num}\s*[\.\．、]\s*'
            next_match = re.search(next_pattern, text[start:])

            if next_match:
                end = start + next_match.start()
            else:
                end = len(text)

            content = text[start:end].strip()

            # 显示内容
            print(f"\n原始内容:")
            print(content[:800])

            # 尝试提取选项
            print(f"\n尝试提取选项:")
            for label in ['A', 'B', 'C', 'D']:
                opt_pattern = rf'{label}\s*[\.\．、:：]\s*([^\n]+)'
                opt_match = re.search(opt_pattern, content)
                if opt_match:
                    print(f"  {label}: {opt_match.group(1)[:100]}")
                else:
                    print(f"  {label}: [未找到]")

            break

    if not found:
        print(f"未找到题号 {q_num}")

doc.close()
