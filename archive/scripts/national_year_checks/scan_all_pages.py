#!/usr/bin/env python3
"""扫描整个 PDF 找 131-135 题号"""
import fitz
import re

pdf_path = "material/【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-真题/2025年国家公务员录用考试《行测》题（行政执法卷）.pdf"

doc = fitz.open(pdf_path)
print(f"扫描 PDF: {pdf_path}")
print(f"总页数: {len(doc)}\n")

# 扫描所有页
for i in range(len(doc)):
    page = doc[i]
    text = page.get_text()

    # 搜索 116-135 的题号
    numbers = []
    for num in range(116, 136):
        if re.search(rf'\b{num}[\.\s]', text):
            numbers.append(num)

    if numbers:
        print(f"第 {i+1} 页: 发现题号 {numbers}")

doc.close()
