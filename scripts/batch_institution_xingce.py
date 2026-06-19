#!/usr/bin/env python3
"""
事业单位联考「职测」（A/B/C/D/E 类）行测真题抽取。
每份 PDF 打包 2018-2024 多年真题，需先按年份头分段，再逐年抽取。

输出：src/data/xingce/{category}/institution_{type}_{year}.json
"""
import os, sys, re, json, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from extract_questions import (
    extract_pdf_text, detect_sections, parse_questions,
    parse_answer_pdf, build_questions_json, save_questions,
    SECTION_TO_CATEGORY,
)

BASE = 'material/【事业编】事业单位联考历年真题'
OUT = 'src/data/xingce'

# 年份头：例如 "2024 年 3 月全国事业单位联考"
YEAR_HEADER = re.compile(
    r'(\d{4})\s*年\s*\d+\s*月.{0,20}?事业单位联考.{0,30}?'
    r'(?:职业能力倾向测验|综合应用能力)?.{0,10}?'
    r'[（(]\s*(?:中学|小学)?\s*([A-E])\s*类\s*[)）]',
    re.DOTALL,
)


def split_by_year(text: str, cat_type: str):
    """返回 [(year, cat_type, sub_text), ...]"""
    matches = list(YEAR_HEADER.finditer(text))
    print(f'  检测到 {len(matches)} 个年份段')
    segs = []
    for i, m in enumerate(matches):
        year = int(m.group(1))
        t = m.group(2)
        assert t == cat_type or t.upper() == cat_type.upper(), f'类别不符: {t} vs {cat_type}'
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        segs.append((year, cat_type, text[start:end]))
    return segs


def process_class(cls: str):
    """处理一个类别的职测 PDF（A/B/C/D/E）"""
    q_pdf = f'{BASE}/{cls}类/职测/2018年-2024年事业单位联考职测（{cls}类）笔试真题.pdf'
    a_pdf = f'{BASE}/{cls}类/职测/2018年-2024年事业单位联考职测（{cls}类）笔试真题答案解析.pdf'
    if not os.path.exists(q_pdf):
        print(f'[SKIP] {cls}类: 找不到 PDF')
        return

    print(f'\n=== {cls}类 ===')
    q_text = extract_pdf_text(q_pdf)
    a_text = extract_pdf_text(a_pdf) if os.path.exists(a_pdf) else ''
    print(f'  题目文本: {len(q_text)} 字  答案文本: {len(a_text)} 字')

    q_segs = split_by_year(q_text, cls)
    a_segs = split_by_year(a_text, cls) if a_text else []
    a_map = {y: txt for y, _, txt in a_segs}

    for year, _, q_sub in q_segs:
        if year < 2020 or year > 2025:
            continue
        sections = detect_sections(q_sub)
        if not sections:
            sections = [{'name': '全部', 'category': 'changshi',
                         'start': 0, 'end': len(q_sub)}]
        qs = parse_questions(q_sub, sections)
        if not qs:
            print(f'  [WARN] {year} 无题目')
            continue
        a_sub = a_map.get(year, '')
        answers = parse_answer_pdf(a_sub) if a_sub else {}
        categorized = build_questions_json(
            qs, answers, 'institution', year, level=cls.lower(), region=''
        )
        total = sum(len(v) for v in categorized.values())
        print(f'  {year}: {total} 题')

        # save_questions 默认按 level 作后缀 → institution_{year}_{cls}.json
        save_questions(categorized, OUT, 'institution', year, region='', level=cls.lower())


def main():
    for cls in ['A', 'B', 'C', 'D', 'E']:
        process_class(cls)


if __name__ == '__main__':
    main()
