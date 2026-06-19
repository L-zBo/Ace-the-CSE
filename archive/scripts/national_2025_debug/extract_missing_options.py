#!/usr/bin/env python3
"""从 PDF 中提取指定题号的选项"""
import pdfplumber
import re
import sys

def extract_question_options(pdf_path, question_num):
    """从 PDF 中提取指定题号的选项"""
    with pdfplumber.open(pdf_path) as pdf:
        all_text = ''
        for page in pdf.pages:
            all_text += page.extract_text() + '\n'

        # 查找题目位置
        pattern = rf'(?:^|\n)\s*{question_num}\s*[\.\．、]\s*(.+?)(?=\n\s*{question_num+1}\s*[\.\．、]|\n\s*第\d+页|$)'
        match = re.search(pattern, all_text, re.DOTALL)

        if not match:
            return None

        question_text = match.group(1)

        # 提取选项
        options = []
        # 策略1: 标准格式 A. B. C. D.
        opt_pattern = r'([A-D])\s*[\.\．、:：]\s*(.+?)(?=\s+[B-D]\s*[\.\．、:：]|\n|$)'
        for m in re.finditer(opt_pattern, question_text):
            label = m.group(1)
            content = m.group(2).strip()
            if content and not any(o['label'] == label for o in options):
                options.append({'label': label, 'content': content})

        return {
            'num': question_num,
            'text': question_text[:200],
            'options': options
        }

if __name__ == '__main__':
    # 2025 国考选项不全的题目
    missing_options = {
        'fushengjia': [4, 74, 79, 122, 130],
        'dishi': [4, 21, 35, 66, 68, 73, 74, 117, 122, 126],
        'xingzhengzhifa': [4, 16, 17, 70, 74, 90],
    }

    for level, nums in missing_options.items():
        print(f'\n{"="*70}')
        print(f'2025 国考 {level} - 选项不全题目')
        print(f'{"="*70}')

        pdf_path = f'material/【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-真题/2025年国家公务员录用考试《行测》题（{"副省级" if level == "fushengjia" else "地市级" if level == "dishi" else "行政执法卷"}）.pdf'

        for num in nums:
            result = extract_question_options(pdf_path, num)
            if result:
                print(f'\n题号 {num}:')
                print(f'  找到 {len(result["options"])} 个选项')
                for opt in result['options']:
                    print(f'    {opt["label"]}. {opt["content"][:60]}...')
            else:
                print(f'\n题号 {num}: 未找到')
