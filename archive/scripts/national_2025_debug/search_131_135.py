#!/usr/bin/env python3
"""在 2025 行政执法卷 PDF 中搜索 131-135 题号"""
from pdfminer.high_level import extract_text
import re

pdf_path = "material/【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-真题/2025年国家公务员录用考试《行测》题（行政执法卷）.pdf"
print(f"正在读取 PDF: {pdf_path}")
text = extract_text(pdf_path)
print(f"PDF 总字符数: {len(text)}")

# 搜索 131-135 题号
print("\n" + "="*60)
print("搜索题号 131-135")
print("="*60)

for num in [131, 132, 133, 134, 135]:
    # 多种题号格式
    patterns = [
        rf'(?:^|\n)\s*{num}[\.\．、]\s*',  # 131. 或 131、
        rf'(?:^|\n)\s*{num}\s*\n',         # 131 后换行
    ]

    found = False
    for pat in patterns:
        matches = list(re.finditer(pat, text))
        if matches:
            found = True
            print(f"\n[找到] 题号 {num} (匹配 {len(matches)} 次):")
            for m in matches[:2]:  # 只显示前2个
                start = max(0, m.start() - 100)
                end = min(len(text), m.end() + 300)
                context = text[start:end].replace('\n', ' ')
                print(f"  位置 {m.start()}: ...{context}...")
            break

    if not found:
        print(f"\n[未找到] 题号 {num}")

# 搜索资料分析章节
print("\n" + "="*60)
print("搜索资料分析章节")
print("="*60)
ziliao_patterns = [
    r'[五5][\.\．、]\s*资料分析',
    r'第[五5]部分\s*资料分析',
]

for pat in ziliao_patterns:
    matches = list(re.finditer(pat, text, re.IGNORECASE))
    if matches:
        print(f"\n找到章节标记 (匹配 {len(matches)} 次):")
        for m in matches:
            start = max(0, m.start() - 50)
            end = min(len(text), m.end() + 500)
            context = text[start:end].replace('\n', ' ')
            print(f"  位置 {m.start()}: ...{context}...")
