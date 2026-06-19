#!/usr/bin/env python3
"""检查 2025 行政执法卷 PDF 页数和内容"""
try:
    import PyPDF2
    use_pypdf2 = True
except:
    use_pypdf2 = False

import fitz  # PyMuPDF

pdf_path = "material/【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-真题/2025年国家公务员录用考试《行测》题（行政执法卷）.pdf"

print(f"检查 PDF: {pdf_path}\n")

# 使用 PyMuPDF
doc = fitz.open(pdf_path)
print(f"总页数: {len(doc)}")

# 检查最后几页
print("\n最后 5 页内容预览:")
for i in range(max(0, len(doc) - 5), len(doc)):
    page = doc[i]
    text = page.get_text()
    print(f"\n{'='*60}")
    print(f"第 {i+1} 页 (共 {len(text)} 字符)")
    print('='*60)
    # 搜索题号
    import re
    numbers = re.findall(r'\b(1[0-3][0-9])\b', text)
    if numbers:
        print(f"发现题号: {set(numbers)}")
    # 避免编码错误
    try:
        print(text[:800])
    except:
        print(text[:800].encode('utf-8', errors='ignore').decode('utf-8'))

doc.close()
