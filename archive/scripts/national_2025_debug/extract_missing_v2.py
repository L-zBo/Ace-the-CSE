#!/usr/bin/env python3
"""从 PDF 中提取缺失题目 - 改进版"""
import fitz
import re
import json
import os

def find_pdf_file(year, level_cn):
    """查找 PDF 文件（支持多种命名格式）"""
    base_dir = "material/【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-真题"

    # 可能的文件名模式
    patterns = [
        f"{year}年国家公务员录用考试《行测》真题（{level_cn}）.pdf",
        f"{year}年国家公务员录用考试《行测》题（{level_cn}）.pdf",
        f"{year}年国家公务员考试《行测》真题（{level_cn}）.pdf",
        f"{year}年国家公务员考试行测真题（{level_cn}）.pdf",
        f"{year}年国家公务员考试《行测》真题卷（{level_cn}）.pdf",
        f"{year}年国家录用公务员考试《行测》真题卷（{level_cn}）.pdf",
    ]

    # 特殊处理：2019 年用"省级"而不是"副省级"
    if year == 2019 and level_cn == "副省级":
        patterns.insert(0, f"{year}年国家公务员考试行测真题（省级）.pdf")

    for pattern in patterns:
        path = os.path.join(base_dir, pattern)
        if os.path.exists(path):
            return path

    return None

def extract_question_from_pdf(pdf_path, question_num):
    """从 PDF 中提取指定题号的题目"""
    doc = fitz.open(pdf_path)

    # 1. 找到题号所在页
    target_page = None
    target_text = None

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        # 多种题号格式
        patterns = [
            rf'(?:^|\n)\s*{question_num}[\.\．、]\s*',  # 55. 或 55、
            rf'(?:^|\n)\s*{question_num}\s+',           # 55 (后面有空格)
            rf'(?:^|\n){question_num}[\.\．、]',        # 紧贴的 55.
        ]

        for pattern in patterns:
            if re.search(pattern, text):
                target_page = page_num
                target_text = text
                break

        if target_page is not None:
            break

    if target_page is None:
        doc.close()
        return None

    # 2. 提取题目内容
    # 找到题号位置
    match = None
    for pattern in [
        rf'(?:^|\n)\s*{question_num}[\.\．、]\s*',
        rf'(?:^|\n)\s*{question_num}\s+',
        rf'(?:^|\n){question_num}[\.\．、]',
    ]:
        match = re.search(pattern, target_text)
        if match:
            break

    if not match:
        doc.close()
        return None

    start_pos = match.end()

    # 找到下一题的位置
    next_num = question_num + 1
    next_match = None
    for pattern in [
        rf'(?:^|\n)\s*{next_num}[\.\．、]\s*',
        rf'(?:^|\n)\s*{next_num}\s+',
        rf'(?:^|\n){next_num}[\.\．、]',
    ]:
        next_match = re.search(pattern, target_text[start_pos:])
        if next_match:
            break

    if next_match:
        end_pos = start_pos + next_match.start()
    else:
        end_pos = len(target_text)

    content = target_text[start_pos:end_pos].strip()

    # 3. 提取选项
    options = []
    # 多种选项格式
    option_patterns = [
        r'([A-D])[\.\．、]\s*([^\n]+)',
        r'([A-D])\s+([^\n]+)',
    ]

    for opt_pattern in option_patterns:
        for m in re.finditer(opt_pattern, content):
            label = m.group(1)
            opt_content = m.group(2).strip()
            if opt_content and len(opt_content) > 2:  # 过滤太短的
                options.append({"label": label, "content": opt_content})

        if options:
            break

    # 去重
    seen = set()
    unique_options = []
    for opt in options:
        if opt['label'] not in seen:
            seen.add(opt['label'])
            unique_options.append(opt)

    options = unique_options[:4]  # 最多 4 个选项

    # 4. 清理题目内容
    if options:
        first_option_pos = content.find(options[0]['label'])
        if first_option_pos > 0:
            content = content[:first_option_pos].strip()

    doc.close()

    return {
        "content": content,
        "options": options,
        "page": target_page + 1
    }

# 需要提取的题目
missing_questions = [
    {"year": 2023, "level": "fushengjia", "level_cn": "副省级", "num": 55, "module": "yanyu"},
    {"year": 2023, "level": "dishi", "level_cn": "地市级", "num": 33, "module": "yanyu"},
    {"year": 2019, "level": "fushengjia", "level_cn": "副省级", "num": 47, "module": "yanyu"},
]

print("=" * 70)
print("从 PDF 提取缺失题目")
print("=" * 70)

extracted = []

for q in missing_questions:
    pdf_path = find_pdf_file(q['year'], q['level_cn'])

    if not pdf_path:
        print(f"\n[错误] 未找到 {q['year']} {q['level_cn']} 的 PDF 文件")
        continue

    print(f"\n提取 {q['year']} {q['level']} 第 {q['num']} 题...")
    print(f"  PDF: {os.path.basename(pdf_path)}")

    result = extract_question_from_pdf(pdf_path, q['num'])

    if result:
        print(f"  [成功] 在第 {result['page']} 页")
        print(f"  内容: {result['content'][:80]}...")
        print(f"  选项数: {len(result['options'])}")

        extracted.append({
            "info": q,
            "data": result
        })
    else:
        print(f"  [失败] 未找到题目")

# 保存
if extracted:
    with open('extracted_missing_questions.json', 'w', encoding='utf-8') as f:
        json.dump(extracted, f, ensure_ascii=False, indent=2)
    print(f"\n成功提取 {len(extracted)} 题")
else:
    print("\n未提取到任何题目")
