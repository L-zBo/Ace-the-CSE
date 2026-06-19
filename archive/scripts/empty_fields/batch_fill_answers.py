#!/usr/bin/env python3
"""
批量修复空答案/解析：扫描所有 JSON 题库，找到 answer 或 explanation 为空的题目，
从对应的答案 PDF 中重新提取并填充。

同时使用 PyMuPDF (fitz) 作为后备文本提取器，处理 pdfminer 失败的 PDF。
"""

import json
import os
import re
import sys
import unicodedata
import warnings

warnings.filterwarnings("ignore")

import fitz  # PyMuPDF
from pdfminer.high_level import extract_text


# ── 常量 ────────────────────────────────────────────────────

NATIONAL_ANSWER_DIR = "material/【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-答案及解析"
PROVINCIAL_BASE = "material/【省考】2000-2025真题pdf"
DATA_DIR = "src/data/xingce"

LEVEL_MAP = {
    "fushengjia": ["副省级", "副省", "省级", "省部级"],
    "dishi": ["地市级", "地市", "市地级"],
    "xingzhengzhifa": ["行政执法", "行政执法卷"],
}

REGION_CN = {
    "anhui": "安徽", "beijing": "北京", "fujian": "福建", "gansu": "甘肃",
    "guangdong": "广东", "guangxi": "广西", "guizhou": "贵州", "hainan": "海南",
    "hebei": "河北", "henan": "河南", "heilongjiang": "黑龙江", "hubei": "湖北",
    "hunan": "湖南", "jilin": "吉林", "jiangsu": "江苏", "jiangxi": "江西",
    "liaoning": "辽宁", "neimenggu": "内蒙古", "ningxia": "宁夏", "qinghai": "青海",
    "shandong": "山东", "shanxi": "山西", "shaanxi": "陕西", "shanghai": "上海",
    "sichuan": "四川", "tianjin": "天津", "xizang": "西藏", "xinjiang": "新疆",
    "yunnan": "云南", "zhejiang": "浙江", "chongqing": "重庆",
}


def normalize_cjk(text: str) -> str:
    result = []
    for ch in text:
        cp = ord(ch)
        if 0x2F00 <= cp <= 0x2FDF or 0xF900 <= cp <= 0xFAD9:
            result.append(unicodedata.normalize("NFKC", ch))
        else:
            result.append(ch)
    return "".join(result)


def extract_text_pymupdf(pdf_path: str) -> str:
    """使用 PyMuPDF 提取全文"""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return normalize_cjk(text)


def extract_text_best(pdf_path: str) -> str:
    """尝试两种方法提取文本，选择结果更长的"""
    try:
        t1 = normalize_cjk(extract_text(pdf_path, password=""))
    except Exception:
        t1 = ""
    try:
        t2 = extract_text_pymupdf(pdf_path)
    except Exception:
        t2 = ""
    return t1 if len(t1) >= len(t2) else t2


def parse_answers_flexible(text: str) -> dict:
    """
    灵活解析多种答案PDF格式，返回 {题号: {answer, explanation}}
    """
    result = {}

    # ── 格式1: 【1-5】BCDAA 答案表 ──
    key_pattern = re.compile(r'【(\d+)\s*[-—–]\s*(\d+)】\s*([A-D\s]+)')
    for m in key_pattern.finditer(text):
        start_num = int(m.group(1))
        end_num = int(m.group(2))
        answers_str = re.sub(r'\s+', '', m.group(3))
        for i, ans in enumerate(answers_str):
            if ans in 'ABCD' and start_num + i <= end_num:
                if start_num + i not in result:
                    result[start_num + i] = {"answer": "", "explanation": ""}
                result[start_num + i]["answer"] = ans

    # ── 格式1b: 【解析N—正确答案X】解析内容 (新版省考/国考格式) ──
    combined_pattern = re.compile(
        r'【解析\s*(\d+)\s*[—\-–]\s*正确答案\s*([A-D])】\s*(.*?)(?=【解析\s*\d+|$)',
        re.DOTALL
    )
    for m in combined_pattern.finditer(text):
        q_num = int(m.group(1))
        ans = m.group(2)
        expl = m.group(3).strip()
        expl = re.sub(r'\s*\d+\s*/\s*\d+\s*', ' ', expl)
        expl = re.sub(r'公众号[：:].+?\n', '', expl)
        expl = re.sub(r'(?:认准|关注)\s*(?:TB|公众号)[：:].+?\n', '', expl)
        expl = re.sub(r'\n{3,}', '\n\n', expl)
        expl = expl.strip()
        if q_num not in result:
            result[q_num] = {"answer": "", "explanation": ""}
        result[q_num]["answer"] = ans
        if expl:
            result[q_num]["explanation"] = expl

    # ── 格式1c: 【答案】X 【解析】... 逐题格式 ──
    ans_expl_pattern = re.compile(
        r'(?:^|\n)\s*(\d{1,3})\s*[\.\．、]\s*【答案】\s*([A-D])\s*\n\s*【解析】\s*(.*?)(?=\n\s*\d{1,3}\s*[\.\．、]\s*【答案】|$)',
        re.DOTALL
    )
    for m in ans_expl_pattern.finditer(text):
        q_num = int(m.group(1))
        ans = m.group(2)
        expl = m.group(3).strip()
        if q_num not in result:
            result[q_num] = {"answer": "", "explanation": ""}
        if not result[q_num]["answer"]:
            result[q_num]["answer"] = ans
        if not result[q_num]["explanation"] and expl:
            result[q_num]["explanation"] = expl

    # ── 格式2: 【N】解析... 逐题解析 ──
    # Also handle N.解析 or N、解析 format without 【】
    expl_pattern = re.compile(
        r'【(\d+)】\s*(?:解析)?\s*(.*?)(?=【\d+】|$)',
        re.DOTALL
    )
    # Also try format: "N.【解析】" or "N.解析"
    alt_expl_pattern = re.compile(
        r'(?:^|\n)\s*(\d{1,3})\s*[\.\．、]\s*(?:【解析】|【答案】|解析)\s*(.*?)(?=\n\s*\d{1,3}\s*[\.\．、]\s*(?:【解析】|【答案】|解析)|$)',
        re.DOTALL
    )
    for m in expl_pattern.finditer(text):
        q_num = int(m.group(1))
        expl = m.group(2).strip()
        expl = re.sub(r'\s*\d+\s*/\s*\d+\s*', ' ', expl)
        expl = re.sub(r'公众号[：:].+?\n', '', expl)
        expl = re.sub(r'认准公众号.+?\n', '', expl)
        expl = re.sub(r'\n{3,}', '\n\n', expl)
        expl = expl.strip()

        if q_num not in result:
            result[q_num] = {"answer": "", "explanation": ""}
        result[q_num]["explanation"] = expl

        if not result[q_num]["answer"]:
            ans_m = re.search(r'故正确答案为\s*([A-D])', expl)
            if not ans_m:
                ans_m = re.search(r'答案[为是选]\s*([A-D])', expl)
            if not ans_m:
                ans_m = re.search(r'选\s*([A-D])\s*[。项]', expl)
            if ans_m:
                result[q_num]["answer"] = ans_m.group(1)

    # Try alt format if 【N】 format got few results
    if len(result) < 10:
        for m in alt_expl_pattern.finditer(text):
            q_num = int(m.group(1))
            expl = m.group(2).strip()
            expl = re.sub(r'\s*\d+\s*/\s*\d+\s*', ' ', expl)
            expl = re.sub(r'公众号[：:].+?\n', '', expl)
            expl = re.sub(r'\n{3,}', '\n\n', expl)
            expl = expl.strip()

            if q_num not in result:
                result[q_num] = {"answer": "", "explanation": ""}
            if not result[q_num]["explanation"]:
                result[q_num]["explanation"] = expl

            if not result[q_num]["answer"]:
                ans_m = re.search(r'故正确答案为\s*([A-D])', expl)
                if not ans_m:
                    ans_m = re.search(r'答案[为是选]?\s*([A-D])', expl)
                if ans_m:
                    result[q_num]["answer"] = ans_m.group(1)

    # ── 格式3: 没有【】标记的逐题格式 ──
    # "1、解析内容...故正确答案为A。" or "1. A  解析：..."
    if len(result) < 20:
        # Format 3a: "N、解析..." with answer inside
        q3_pattern = re.compile(
            r'(?:^|\n)\s*(\d{1,3})\s*[、，\.．]\s*(.*?)(?=\n\s*\d{1,3}\s*[、，\.．]\s*[A-D\u4e00-\u9fff]|$)',
            re.DOTALL
        )
        for m in q3_pattern.finditer(text):
            q_num = int(m.group(1))
            block = m.group(2).strip()
            if len(block) < 20:
                continue  # skip tiny matches
            if q_num in result and result[q_num]["answer"]:
                continue  # already have answer

            ans_m = re.search(r'故正确答案为\s*([A-D])', block)
            if not ans_m:
                ans_m = re.search(r'答案[为是选择]?\s*([A-D])', block)
            if not ans_m:
                ans_m = re.search(r'选\s*([A-D])\s*[。项]', block)

            if ans_m:
                if q_num not in result:
                    result[q_num] = {"answer": "", "explanation": ""}
                result[q_num]["answer"] = ans_m.group(1)
                if not result[q_num]["explanation"]:
                    result[q_num]["explanation"] = block

        # Format 3b: "N. A\n" simple answer list
        if len(result) < 10:
            line_pattern = re.compile(
                r'(?:^|\n)\s*(\d{1,3})\s*[\.\．、]\s*([A-D])\s*(?:\n|[\.\．、])',
            )
            for m in line_pattern.finditer(text):
                q_num = int(m.group(1))
                ans = m.group(2)
                if q_num not in result:
                    result[q_num] = {"answer": ans, "explanation": ""}

    # ── 格式4: 没有题号标记的连续答案+解析（如2021副省级格式）──
    # 检测: 第一行是单个字母A-D
    if not result:
        lines = text.strip().split('\n')
        q_num = 0
        current_answer = ""
        current_expl_lines = []

        for line in lines:
            stripped = line.strip()
            # 单独一行的答案字母
            if re.match(r'^[A-D]$', stripped):
                if current_answer and q_num > 0:
                    result[q_num] = {
                        "answer": current_answer,
                        "explanation": '\n'.join(current_expl_lines).strip()
                    }
                q_num += 1
                current_answer = stripped
                current_expl_lines = []
            elif stripped.startswith('解析'):
                current_expl_lines.append(stripped.replace('解析', '', 1).strip())
            elif stripped and q_num > 0:
                current_expl_lines.append(stripped)

        if current_answer and q_num > 0:
            result[q_num] = {
                "answer": current_answer,
                "explanation": '\n'.join(current_expl_lines).strip()
            }

    # 从解析文本中补充缺失的答案
    for q_num, data in result.items():
        if not data["answer"] and data["explanation"]:
            ans_m = re.search(r'故正确答案为\s*([A-D])', data["explanation"])
            if not ans_m:
                ans_m = re.search(r'答案[为是]\s*([A-D])', data["explanation"])
            if ans_m:
                data["answer"] = ans_m.group(1)

    return result


def find_national_answer_pdf(year: int, level: str) -> str:
    """找到国考对应年份和级别的答案PDF"""
    if not os.path.isdir(NATIONAL_ANSWER_DIR):
        return ""
    files = os.listdir(NATIONAL_ANSWER_DIR)
    candidates = [f for f in files if str(year) in f and f.endswith('.pdf')]

    if not candidates:
        return ""

    if not level:
        # 没有级别要求，返回第一个匹配
        return os.path.join(NATIONAL_ANSWER_DIR, candidates[0])

    # 按级别匹配
    level_keywords = LEVEL_MAP.get(level, [])
    for c in candidates:
        if any(kw in c for kw in level_keywords):
            return os.path.join(NATIONAL_ANSWER_DIR, c)

    # 如果找不到精确匹配，用第一个候选
    return os.path.join(NATIONAL_ANSWER_DIR, candidates[0])


def find_provincial_answer_pdf(region: str, year: int) -> str:
    """找到省考对应省份和年份的答案PDF"""
    region_cn = REGION_CN.get(region, "")
    if not region_cn:
        return ""

    # 搜索省考目录
    best = ""
    for dirname in os.listdir(PROVINCIAL_BASE):
        if region_cn in dirname:
            prov_dir = os.path.join(PROVINCIAL_BASE, dirname)
            # 递归搜索答案PDF — 必须包含"行测"且包含"答案"或"解析"
            for root, dirs, files in os.walk(prov_dir):
                for f in files:
                    if not f.endswith('.pdf'):
                        continue
                    if str(year) not in f:
                        continue
                    has_xingce = '行测' in f or '行政' in f
                    has_answer = '答案' in f or '解析' in f
                    # 排除申论
                    is_shenlun = '申论' in f
                    if has_answer and not is_shenlun:
                        path = os.path.join(root, f)
                        if has_xingce:
                            return path  # 最佳匹配：明确标注行测
                        if not best:
                            best = path  # 次佳匹配：有答案但未标注科目
    return best


def parse_json_filename(filepath: str):
    """从JSON文件路径解析出 source, region, year, level"""
    basename = os.path.basename(filepath).replace('.json', '')
    parts = basename.split('_')

    source = parts[0] if parts else ""
    region = ""
    year = 0
    level = ""

    if source == "national":
        # national_2025_fushengjia.json
        for p in parts[1:]:
            if p.isdigit() and len(p) == 4:
                year = int(p)
            elif p in LEVEL_MAP:
                level = p
    elif source == "provincial":
        # provincial_anhui_2024.json
        if len(parts) >= 3:
            region = parts[1]
            for p in parts[2:]:
                if p.isdigit() and len(p) == 4:
                    year = int(p)

    return source, region, year, level


def main():
    # 收集所有需要修复的JSON文件
    json_files = []
    for root, dirs, files in os.walk(DATA_DIR):
        for f in files:
            if f.endswith('.json'):
                path = os.path.join(root, f)
                json_files.append(path)

    print(f"扫描到 {len(json_files)} 个题库文件")

    # 缓存已解析的答案PDF
    answer_cache = {}
    total_fixed = 0
    total_files_fixed = 0

    for jf in sorted(json_files):
        with open(jf, 'r', encoding='utf-8') as f:
            questions = json.load(f)

        # 统计空答案
        empty_count = sum(1 for q in questions if not q.get('answer'))
        if empty_count == 0:
            continue

        source, region, year, level = parse_json_filename(jf)
        if not year:
            continue

        # 找答案PDF
        if source == "national":
            answer_pdf = find_national_answer_pdf(year, level)
        elif source == "provincial":
            answer_pdf = find_provincial_answer_pdf(region, year)
        else:
            continue

        if not answer_pdf or not os.path.exists(answer_pdf):
            print(f"  [SKIP] {os.path.basename(jf)} — 未找到答案PDF (year={year}, level={level}, region={region})")
            continue

        # 解析答案（带缓存）
        if answer_pdf not in answer_cache:
            text = extract_text_best(answer_pdf)
            if len(text) < 500:
                print(f"  [SKIP] {os.path.basename(jf)} — 答案PDF为扫描件: {os.path.basename(answer_pdf)}")
                continue
            answers = parse_answers_flexible(text)
            answer_cache[answer_pdf] = answers
        else:
            answers = answer_cache[answer_pdf]

        if not answers:
            print(f"  [SKIP] {os.path.basename(jf)} — 答案PDF解析失败")
            continue

        # 填充空答案
        fixed = 0
        for q in questions:
            parts = q["id"].split("-")
            try:
                q_num = int(parts[-1])
            except ValueError:
                continue

            ans_data = answers.get(q_num, {})

            if not q.get("answer") and ans_data.get("answer"):
                q["answer"] = ans_data["answer"]
                fixed += 1

            if not q.get("explanation") and ans_data.get("explanation"):
                q["explanation"] = ans_data["explanation"]

        if fixed > 0:
            with open(jf, 'w', encoding='utf-8') as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)
            total_fixed += fixed
            total_files_fixed += 1
            print(f"  [OK] {os.path.basename(jf)}: 修复 {fixed}/{empty_count} 个空答案 (PDF: {os.path.basename(answer_pdf)})")
        else:
            print(f"  [--] {os.path.basename(jf)}: 0/{empty_count} 匹配 (PDF有{len(answers)}题)")

    print(f"\n{'='*60}")
    print(f"总计修复 {total_fixed} 个空答案，涉及 {total_files_fixed} 个文件")


if __name__ == "__main__":
    main()
