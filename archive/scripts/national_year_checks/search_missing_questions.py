#!/usr/bin/env python3
"""在 PDF 中搜索缺失的题号"""
import fitz
import re

# 缺失题目列表
missing_questions = [
    ("2023", "fushengjia", 55, "言语"),
    ("2023", "dishi", 33, "言语"),
    ("2019", "fushengjia", None, "言语"),  # 需要先确定具体题号
]

for year, level, num, module in missing_questions:
    if num is None:
        continue

    level_map = {
        'fushengjia': '副省级',
        'dishi': '地市级',
    }

    pdf_path = f"material/【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-真题/{year}年国家公务员录用考试《行测》真题（{level_map[level]}）.pdf"

    print(f"\n{'='*60}")
    print(f"搜索 {year} {level} 第 {num} 题")
    print('='*60)

    try:
        doc = fitz.open(pdf_path)
        found = False

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            # 搜索题号
            patterns = [
                rf'(?:^|\n)\s*{num}[\.\．、]\s*',
                rf'(?:^|\n)\s*{num}\s*\n',
            ]

            for pat in patterns:
                if re.search(pat, text):
                    found = True
                    print(f"  [找到] 在第 {page_num + 1} 页")

                    # 提取题目内容
                    match = re.search(pat, text)
                    if match:
                        start = match.end()
                        end = min(start + 300, len(text))
                        content = text[start:end].replace('\n', ' ')
                        print(f"  内容预览: {content[:200]}...")
                    break

            if found:
                break

        if not found:
            print(f"  [未找到] 题号 {num}")

        doc.close()

    except Exception as e:
        print(f"  [错误] {e}")

print("\n" + "="*60)
print("搜索完成")
print("="*60)
