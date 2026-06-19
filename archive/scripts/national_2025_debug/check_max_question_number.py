#!/usr/bin/env python3
"""检查 2025 国考三个级别的最大题号"""
import fitz
import re

levels = [
    ("副省级", "2025年国家公务员录用考试《行测》题（副省级）.pdf"),
    ("地市级", "2025年国家公务员录用考试《行测》题（地市级）.pdf"),
    ("行政执法", "2025年国家公务员录用考试《行测》题（行政执法卷）.pdf"),
]

for level_name, filename in levels:
    pdf_path = f"material/【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-真题/{filename}"
    doc = fitz.open(pdf_path)

    max_num = 0
    for i in range(len(doc)):
        text = doc[i].get_text()
        nums = [int(n) for n in re.findall(r'\b(1[0-3][0-9])\b', text)]
        if nums:
            max_num = max(max_num, max(nums))

    doc.close()
    print(f"{level_name}: 最大题号 {max_num}")
