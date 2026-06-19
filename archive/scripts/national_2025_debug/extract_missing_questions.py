#!/usr/bin/env python3
"""从 PDF 中提取指定题号的题目"""
import fitz
import re
import json

def extract_question_from_pdf(pdf_path, question_num):
    """从 PDF 中提取指定题号的题目"""
    doc = fitz.open(pdf_path)

    # 1. 找到题号所在页
    target_page = None
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        # 搜索题号
        pattern = rf'(?:^|\n)\s*{question_num}[\.\．、]\s*'
        if re.search(pattern, text):
            target_page = page_num
            break

    if target_page is None:
        doc.close()
        return None

    # 2. 提取题目内容
    page = doc[target_page]
    text = page.get_text()

    # 找到题号位置
    pattern = rf'(?:^|\n)\s*{question_num}[\.\．、]\s*'
    match = re.search(pattern, text)
    if not match:
        doc.close()
        return None

    start_pos = match.end()

    # 找到下一题的位置（作为结束位置）
    next_num = question_num + 1
    next_pattern = rf'(?:^|\n)\s*{next_num}[\.\．、]\s*'
    next_match = re.search(next_pattern, text[start_pos:])

    if next_match:
        end_pos = start_pos + next_match.start()
    else:
        # 如果没找到下一题，可能跨页了，读取到页尾
        end_pos = len(text)

    content = text[start_pos:end_pos].strip()

    # 3. 提取选项
    options = []
    option_pattern = r'([A-D])[\.\．、]\s*([^\n]+)'
    for m in re.finditer(option_pattern, content):
        label = m.group(1)
        opt_content = m.group(2).strip()
        options.append({"label": label, "content": opt_content})

    # 4. 清理题目内容（去掉选项部分）
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
    {
        "year": 2023,
        "level": "fushengjia",
        "level_cn": "副省级",
        "num": 55,
        "module": "yanyu",
        "module_cn": "言语理解与表达"
    },
    {
        "year": 2023,
        "level": "dishi",
        "level_cn": "地市级",
        "num": 33,
        "module": "yanyu",
        "module_cn": "言语理解与表达"
    },
    {
        "year": 2019,
        "level": "fushengjia",
        "level_cn": "副省级",
        "num": 47,
        "module": "yanyu",
        "module_cn": "言语理解与表达"
    },
]

print("=" * 70)
print("从 PDF 提取缺失题目")
print("=" * 70)

extracted = []

for q in missing_questions:
    pdf_path = f"material/【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-真题/{q['year']}年国家公务员录用考试《行测》真题（{q['level_cn']}）.pdf"

    print(f"\n提取 {q['year']} {q['level']} 第 {q['num']} 题...")

    result = extract_question_from_pdf(pdf_path, q['num'])

    if result:
        print(f"  [成功] 在第 {result['page']} 页")
        print(f"  内容: {result['content'][:100]}...")
        print(f"  选项数: {len(result['options'])}")

        # 构造完整的题目对象
        question_obj = {
            "id": f"national-xingce-{q['module']}-{q['year']}-{q['level']}-{q['num']:03d}",
            "subject": "xingce",
            "category": q['module'],
            "type": "single_choice",
            "source": "national",
            "year": q['year'],
            "level": q['level'],
            "content": result['content'],
            "options": result['options'],
            "answer": "",  # 需要从答案 PDF 提取
            "explanation": "",
            "difficulty": 3,
            "tags": [q['module_cn']]
        }

        extracted.append({
            "info": q,
            "question": question_obj
        })
    else:
        print(f"  [失败] 未找到题目")

# 保存提取结果
if extracted:
    with open('extracted_missing_questions.json', 'w', encoding='utf-8') as f:
        json.dump(extracted, f, ensure_ascii=False, indent=2)

    print(f"\n成功提取 {len(extracted)} 题，已保存到 extracted_missing_questions.json")
else:
    print("\n未提取到任何题目")
