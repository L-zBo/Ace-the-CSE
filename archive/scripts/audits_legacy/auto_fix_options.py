#!/usr/bin/env python3
"""自动修复 2025 国考选项不全的题目（从 PDF 重新提取）"""
import json
import pdfplumber
import re

def extract_question_options_improved(pdf_path, question_num):
    """改进的选项提取（处理跨行）"""
    with pdfplumber.open(pdf_path) as pdf:
        all_text = ''
        for page in pdf.pages:
            all_text += page.extract_text() + '\n'

        # 查找题目位置（扩大范围，包含更多上下文）
        pattern = rf'(?:^|\n)\s*{question_num}\s*[\.\．、]\s*(.+?)(?=\n\s*{question_num+1}\s*[\.\．、]|\Z)'
        match = re.search(pattern, all_text, re.DOTALL)

        if not match:
            return None

        question_text = match.group(1)

        # 提取选项（使用 DOTALL 模式处理跨行）
        options = []
        opt_pattern = r'([A-D])\s*[\.\．、]\s*(.+?)(?=\n\s*[A-D]\s*[\.\．、]|\Z)'

        for m in re.finditer(opt_pattern, question_text, re.DOTALL):
            label = m.group(1)
            content = m.group(2).strip()
            # 清理内容
            content = re.sub(r'\s+', ' ', content)
            content = re.sub(r'第\d+页.*$', '', content).strip()

            if content and len(content) > 2 and len(content) < 1000:
                # 去重
                if not any(o['label'] == label for o in options):
                    options.append({'label': label, 'content': content})

        return options if len(options) == 4 else None

# 需要修复的题目（只修复能提取到 4 个选项的）
fix_targets = {
    'fushengjia': {
        4: 'changshi',
        122: 'ziliao',
    },
    'dishi': {
        4: 'changshi',
        21: 'yanyu',
        35: 'yanyu',
        117: 'ziliao',
        122: 'ziliao',
    },
    'xingzhengzhifa': {
        4: 'changshi',
    },
}

level_names = {
    'fushengjia': '副省级',
    'dishi': '地市级',
    'xingzhengzhifa': '行政执法卷',
}

print("="*70)
print("自动修复 2025 国考选项不全问题")
print("="*70)

for level, questions in fix_targets.items():
    print(f"\n{level}:")
    pdf_path = f'material/【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-真题/2025年国家公务员录用考试《行测》题（{level_names[level]}）.pdf'

    for qnum, module in questions.items():
        # 从 PDF 提取选项
        new_options = extract_question_options_improved(pdf_path, qnum)

        if not new_options:
            print(f"  题号 {qnum}: 提取失败，跳过")
            continue

        # 读取现有数据
        json_path = f'src/data/xingce/{module}/national_2025_{level}.json'
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 找到对应题目并更新选项
        updated = False
        for q in data:
            if int(q['id'].split('-')[-1]) == qnum:
                old_opts = len(q.get('options', []))
                q['options'] = new_options
                updated = True
                print(f"  题号 {qnum}: {old_opts} → 4 个选项 ✓")
                break

        if updated:
            # 保存
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

print("\n修复完成！")
