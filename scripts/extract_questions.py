#!/usr/bin/env python3
"""
行测 PDF 真题提取器
从行测真题PDF和答案解析PDF中提取结构化题目数据，输出为JSON格式。

支持三种PDF格式：
  - 2025式: "⼀. 政治理论：" / "1.\n" / "A.xxx"
  - 2020式: "一、常识判断。" / "1、" / "A、xxx"
  - 事业编式: "第一部分  常识判断" / "1.  " / "A．xxx"

Usage:
  python scripts/extract_questions.py \
    --question-pdf "material/.../行测真题.pdf" \
    --answer-pdf "material/.../答案解析.pdf" \
    --source national --year 2025 --level fushengjia \
    --output-dir src/data/xingce/
"""

import argparse
import json
import os
import re
import sys
import unicodedata
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

# ── pdfminer 导入 ──────────────────────────────────────────
from pdfminer.high_level import extract_text


# ── 常量 ────────────────────────────────────────────────────

# 章节名 → category 映射
SECTION_TO_CATEGORY = {
    "政治理论": "changshi",
    "常识判断": "changshi",
    "常识": "changshi",
    "言语理解与表达": "yanyu",
    "言语理解": "yanyu",
    "言语": "yanyu",
    "数量关系": "shuliang",
    "数量": "shuliang",
    "数学运算": "shuliang",
    "判断推理": "panduan",
    "判断": "panduan",
    "图形推理": "panduan",
    "定义判断": "panduan",
    "类比推理": "panduan",
    "逻辑判断": "panduan",
    "资料分析": "ziliao",
    "资料": "ziliao",
}

# category 中文名
CATEGORY_NAMES = {
    "changshi": "常识判断",
    "yanyu": "言语理解与表达",
    "shuliang": "数量关系",
    "panduan": "判断推理",
    "ziliao": "资料分析",
}

# 中文数字映射
CN_NUMS = {
    "⼀": 1, "⼆": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "⼋": 8, "⼏": 9, "⼗": 10,
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
    "第一": 1, "第二": 2, "第三": 3, "第四": 4, "第五": 5, "第六": 6,
}

# 省份代码映射
REGION_CODES = {
    "安徽": "anhui", "北京": "beijing", "福建": "fujian", "甘肃": "gansu",
    "广东": "guangdong", "广西": "guangxi", "贵州": "guizhou", "海南": "hainan",
    "河北": "hebei", "河南": "henan", "黑龙江": "heilongjiang", "湖北": "hubei",
    "湖南": "hunan", "吉林": "jilin", "江苏": "jiangsu", "江西": "jiangxi",
    "辽宁": "liaoning", "内蒙古": "neimenggu", "宁夏": "ningxia", "青海": "qinghai",
    "山东": "shandong", "山西": "shanxi", "陕西": "shaanxi", "上海": "shanghai",
    "四川": "sichuan", "天津": "tianjin", "西藏": "xizang", "新疆": "xinjiang",
    "云南": "yunnan", "浙江": "zhejiang", "重庆": "chongqing",
    "广州": "guangzhou", "深圳": "shenzhen",
}

LEVEL_LABELS = {
    "fushengjia": "副省级",
    "dishi": "地市级",
    "xingzhengzhifa": "行政执法",
    "": "",
}

MANUAL_OPTION_OVERRIDES = {
    "national-xingce-shuliang-2025-dishi-066": [
        {"label": "A", "content": "10/13"},
        {"label": "B", "content": "13/10"},
        {"label": "C", "content": "20/13"},
        {"label": "D", "content": "13/5"},
    ],
    "national-xingce-shuliang-2025-dishi-073": [
        {"label": "A", "content": "10"},
        {"label": "B", "content": "15"},
        {"label": "C", "content": "10√3"},
        {"label": "D", "content": "15√3"},
    ],
    "national-xingce-shuliang-2025-dishi-074": [
        {"label": "A", "content": "1/7"},
        {"label": "B", "content": "1/8"},
        {"label": "C", "content": "1/9"},
        {"label": "D", "content": "1/10"},
    ],
    "national-xingce-shuliang-2025-fushengjia-074": [
        {"label": "A", "content": "10"},
        {"label": "B", "content": "15"},
        {"label": "C", "content": "10√3"},
        {"label": "D", "content": "15√3"},
    ],
    "national-xingce-shuliang-2025-fushengjia-079": [
        {"label": "A", "content": "1/7"},
        {"label": "B", "content": "1/8"},
        {"label": "C", "content": "1/9"},
        {"label": "D", "content": "1/10"},
    ],
    "national-xingce-shuliang-2025-xingzhengzhifa-070": [
        {"label": "A", "content": "10/13"},
        {"label": "B", "content": "13/10"},
        {"label": "C", "content": "20/13"},
        {"label": "D", "content": "13/5"},
    ],
    "national-xingce-shuliang-2025-xingzhengzhifa-074": [
        {"label": "A", "content": "10"},
        {"label": "B", "content": "13"},
        {"label": "C", "content": "16"},
        {"label": "D", "content": "19"},
    ],
    "national-xingce-shuliang-2025-xingzhengzhifa-075": [
        {"label": "A", "content": "7/3"},
        {"label": "B", "content": "7/6"},
        {"label": "C", "content": "8/3"},
        {"label": "D", "content": "4/3"},
    ],
}


# ── PDF 文本提取 ────────────────────────────────────────────

def normalize_cjk(text: str) -> str:
    """
    选择性正规化：只转换 CJK 兼容字符（如 ⾔→言, ⼀→一），
    但保留 ①②③④⑤ 等圆圈数字不变。
    """
    result = []
    for ch in text:
        cp = ord(ch)
        # CJK 康熙部首 (U+2F00-U+2FDF) 和 CJK 兼容表意文字 (U+F900-U+FAD9)
        if 0x2F00 <= cp <= 0x2FDF or 0xF900 <= cp <= 0xFAD9:
            normalized = unicodedata.normalize("NFKC", ch)
            result.append(normalized)
        else:
            result.append(ch)
    return "".join(result)


def _fitz_extract_xy_sorted(pdf_path: str) -> str:
    """
    用 PyMuPDF 按 (y, x) 坐标重排 line 级文字。
    专门用于双列 PDF：pdfminer 默认按"读完左列再读右列"取文，导致 A/B/C/D
    双列同行的选项被拆成 A/C（左） + B/D（右列在下一屏），parse 时 B/D 错配。
    重排后同 y ±3pt 视为同一物理行，按 x 升序拼接，B/D 回到 A/C 旁边。
    """
    import fitz
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return ""
    out = []
    for page in doc:
        try:
            d = page.get_text("dict")
        except Exception:
            continue
        lines = []
        for b in d.get("blocks", []):
            if b.get("type", 0) != 0:
                continue
            for ln in b.get("lines", []):
                bbox = ln.get("bbox", [0, 0, 0, 0])
                x0, y0, x1, y1 = bbox
                text = "".join(s.get("text", "") for s in ln.get("spans", []))
                if text.strip():
                    lines.append(((y0 + y1) / 2, x0, text))
        lines.sort(key=lambda t: (t[0], t[1]))
        physical_rows = []
        for y, x, t in lines:
            if physical_rows and abs(y - physical_rows[-1][0]) <= 3:
                physical_rows[-1][1].append((x, t))
            else:
                physical_rows.append((y, [(x, t)]))
        for _, items in physical_rows:
            items.sort(key=lambda it: it[0])
            row_txt = "  ".join(t for _, t in items)
            out.append(row_txt)
        out.append("\x0c")
    doc.close()
    return "\n".join(out)


def extract_pdf_text(pdf_path: str) -> str:
    """
    默认走 pdfminer；调用方（main）如需双引擎对比取最优，调
    `extract_pdf_text_best(pdf_path)` 得到"pdfminer 和 fitz 选项更完整的那版"。
    """
    return normalize_cjk(extract_text(pdf_path, password=""))


def _option_completeness(text: str) -> float:
    """
    给定 parse 前的 PDF 文本，粗略估计 pdf→题→选项的完整率。
    = 「能在同一 150 字窗口内找到 A/B/C/D 四标签」的题号比例。
    双列错乱的文本会有大量"只找到 A/C"的 150 字窗口，得分低。
    """
    question_heads = list(re.finditer(r'(?:^|\n|\x0c)\s*(\d{1,3})\s*[\.\．、]', text))
    if len(question_heads) < 10:
        return 0.0
    complete = 0
    total = 0
    for i, m in enumerate(question_heads):
        qn = int(m.group(1))
        if qn < 1 or qn > 135:
            continue
        start = m.end()
        end = question_heads[i + 1].start() if i + 1 < len(question_heads) else min(len(text), start + 500)
        chunk = text[start:end]
        labels = set(re.findall(r'[\n\s]([A-D])\s*[\.\．、]', chunk))
        total += 1
        if len(labels) >= 4:
            complete += 1
    if total == 0:
        return 0.0
    return complete / total


def extract_pdf_text_best(pdf_path: str) -> str:
    """
    双引擎对比：pdfminer vs fitz 按 (y,x) 重排。
    选项完整率更高的那版文本胜出。完整率差 < 5% 时保守返回 pdfminer（已验证稳定）。
    """
    t_pdfminer = normalize_cjk(extract_text(pdf_path, password=""))
    # fitz 昂贵，先看 pdfminer 完整率是否 >= 0.85；是则直接用 pdfminer
    r_pdfminer = _option_completeness(t_pdfminer)
    if r_pdfminer >= 0.85:
        return t_pdfminer
    t_fitz = _fitz_extract_xy_sorted(pdf_path)
    if len(t_fitz) < 1000:
        return t_pdfminer
    t_fitz_n = normalize_cjk(t_fitz)
    r_fitz = _option_completeness(t_fitz_n)
    # 择优：差 < 5pp 保守选 pdfminer
    if r_fitz > r_pdfminer + 0.05:
        print(f"  [extract] pdfminer 选项完整率 {r_pdfminer:.0%}，切换 fitz ({r_fitz:.0%})")
        return t_fitz_n
    return t_pdfminer


# ── 章节检测 ────────────────────────────────────────────────

def detect_sections(text: str) -> list[dict]:
    """
    检测行测试卷中的章节边界。
    返回 [{name, category, start, end}, ...] 按位置排序。
    """
    patterns = [
        # 2025式: "⼀. 政治理论：" or "⼆. 常识判断："
        r'([⼀⼆三四五六七⼋⼏⼗一二三四五六七八九十]+)[\.\．]\s*(.+?)(?:：|:)',
        # 2020式: "一、常识判断。" or "一、常识判断，"
        r'([一二三四五六七八九十]+)[、，]\s*(.+?)(?:。|，)',
        # 事业编式: "第一部分  常识判断"
        r'(第[一二三四五六七八九十]+部分)\s+(.+?)(?:\s|\n)',
    ]

    sections = []
    for pat in patterns:
        for m in re.finditer(pat, text):
            name = m.group(2).strip()
            # 清理多余文字（只取第一个关键词）
            for key in SECTION_TO_CATEGORY:
                if key in name:
                    category = SECTION_TO_CATEGORY[key]
                    sections.append({
                        "name": key,
                        "category": category,
                        "start": m.start(),
                        "raw_match": m.group(0)[:50],
                    })
                    break

    # 去重（同一category可能匹配多次，如"政治理论"和"常识判断"都是changshi）
    seen_positions = set()
    unique_sections = []
    for s in sorted(sections, key=lambda x: x["start"]):
        # 避免两个距离太近的同category章节
        is_dup = False
        for existing in unique_sections:
            if existing["category"] == s["category"] and abs(existing["start"] - s["start"]) < 500:
                is_dup = True
                break
        if not is_dup:
            unique_sections.append(s)

    # 设置 end 边界
    for i, s in enumerate(unique_sections):
        if i + 1 < len(unique_sections):
            s["end"] = unique_sections[i + 1]["start"]
        else:
            s["end"] = len(text)

    return unique_sections


# ── 题目解析 ────────────────────────────────────────────────

def parse_questions(text: str, sections: list[dict]) -> list[dict]:
    """
    从试卷文本中解析所有题目。
    返回 [{number, content, options, category, raw_text}, ...]
    """
    # 匹配题号的四种格式
    # 格式1: "1.\n" (2025式，题号后换行)
    # 格式2: "1、" (2020式)
    # 格式3: "1.  " (事业编式)
    # 格式4: "1\n" (2023国考式：题号独占一行、无标点)
    q_pattern = re.compile(
        r'(?:^|\n|\x0c)\s*(\d{1,3})(?:\s*[\.\．、]\s*(?:\n|\s{2,})|\s*\n)'
    )

    def _filter(raw_matches):
        out, prev = [], 0
        for idx, m in enumerate(raw_matches):
            qn = int(m.group(1))
            if qn < 1 or qn > 135:
                continue
            tail_end = raw_matches[idx + 1].start() if idx + 1 < len(raw_matches) else len(text)
            if tail_end - m.end() < 20:
                continue
            if qn <= prev and qn > 25:
                continue
            out.append(m)
            prev = qn
        return out

    matches = _filter(list(q_pattern.finditer(text)))

    # fallback: 2019 国考省级这类"1、党..."(题号后紧跟中文无空格) 主正则漏抽
    # 触发条件：主正则 filtered 数量过少（< 50，远低于单科最低 10 + 其他四科合理量）
    if len(matches) < 50:
        loose_pattern = re.compile(r'(?:^|\n|\x0c)\s*(\d{1,3})\s*[\.\．、]')
        loose = _filter(list(loose_pattern.finditer(text)))
        if len(loose) > len(matches):
            if matches:
                print(f"  [WARN] 主正则仅 {len(matches)} 条，宽松匹配得 {len(loose)} 条，采用宽松")
            else:
                print(f"  [WARN] 未找到题目，宽松匹配得 {len(loose)} 条")
            matches = loose

    questions = []
    for i, m in enumerate(matches):
        q_num = int(m.group(1))

        # 确定题目文本范围
        start = m.end()
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)

        raw = text[start:end].strip()

        # 确定所属章节
        category = None
        for s in sections:
            if s["start"] <= m.start() < s["end"]:
                category = s["category"]
                break

        if category is None and sections:
            # 如果在第一个章节之前，归属第一个
            if m.start() < sections[0]["start"]:
                category = sections[0]["category"]
            else:
                # 找最近的前一个章节
                for s in reversed(sections):
                    if m.start() >= s["start"]:
                        category = s["category"]
                        break

        # 解析选项
        options = extract_options(raw)

        # 清理题干（去掉选项部分）
        content = extract_content(raw, options)

        questions.append({
            "number": q_num,
            "content": content,
            "options": options,
            "category": category or "changshi",
            "raw_text": raw,
        })

    return questions


def preprocess_two_column_options(raw_text: str) -> str:
    """
    预处理双列选项排版。
    pdfminer 对双列PDF的提取结果可能是:
    模式1: A.xxx\n .yyy\nB\n .zzz\nC\n .www\nD (A,B左,右列交错)
    模式2: A.xxx\nC.zzz\n .yyy\n .www\nD\nB (A,C左列 + B,D右列)
    需要重构为标准 A.xxx\nB.yyy\nC.zzz\nD.www
    """
    # 模式1: A.x → .y → B → .z → C → .w → D
    pat1 = re.compile(
        r'A\s*[\.\．]\s*(.+?)\s*\n'
        r'\s+[\.\．]\s*(.+?)\s*\n'
        r'\s*B\s*\n'
        r'\s+[\.\．]\s*(.+?)\s*\n'
        r'\s*C\s*\n'
        r'\s+[\.\．]\s*(.+?)\s*\n'
        r'\s*D\s*(?:\n|$)',
        re.DOTALL
    )
    m = pat1.search(raw_text)
    if m:
        replacement = f"A.{m.group(1).strip()}\nB.{m.group(2).strip()}\nC.{m.group(3).strip()}\nD.{m.group(4).strip()}\n"
        return raw_text[:m.start()] + replacement + raw_text[m.end():]

    # 模式2: A.x\nC.z\n .y(B的内容)\n .w(D的内容)
    # 或 A.x\n\nC.z\n\n .y\n .w\nB\nD 等变体
    # 检测: A和C紧邻出现(跳过了B)
    pat2 = re.compile(
        r'A\s*[\.\．]\s*(.+?)\s*\n+'
        r'\s*C\s*[\.\．]\s*(.+?)\s*\n+'
        r'\s+[\.\．]?\s*(.+?)\s*\n+'
        r'\s+[\.\．]?\s*(.+?)\s*\n',
        re.DOTALL
    )
    m = pat2.search(raw_text)
    if m:
        # A在左上, C在左下, B在右上, D在右下
        replacement = f"A.{m.group(1).strip()}\nB.{m.group(3).strip()}\nC.{m.group(2).strip()}\nD.{m.group(4).strip()}\n"
        return raw_text[:m.start()] + replacement + raw_text[m.end():]

    return raw_text


def extract_options(raw_text: str) -> list[dict]:
    """从题目文本中提取ABCD选项。支持多种PDF排版格式。"""
    def is_page_noise(line: str) -> bool:
        compact = re.sub(r"\s+", "", line)
        if not compact:
            return True
        if re.match(r"^第\d+页.*共\d+页$", compact):
            return True
        if "公众号" in compact:
            return True
        if "国考《行测》题" in compact or "国考《行测》真题" in compact:
            return True
        return False

    def clean_option_text(text: str) -> str:
        text = text.strip()
        text = re.sub(r"^[\.\．、:：]+\s*", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\s*第\d+页.*$", "", text).strip()
        text = re.sub(r"\s*\d{4}年国考.*$", "", text).strip()
        text = re.sub(r"\s*公众号.*$", "", text).strip()
        return text

    def split_labeled_segments(line: str) -> list[tuple[str, str]]:
        if not re.match(r"^\s*[A-D]", line):
            return []

        pattern = re.compile(r"([A-D])\s*[\.\．、]?\s*")
        matches = list(pattern.finditer(line))
        if not matches:
            return []

        segments = []
        for idx, match in enumerate(matches):
            label = match.group(1)
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(line)
            content = clean_option_text(line[match.end():end])
            segments.append((label, content))
        return segments

    def extract_options_from_lines(text: str) -> list[dict]:
        ordered = []
        option_map = {}
        pending_label = None
        pending_next_content = None
        option_mode = False

        def set_option(label: str, content: str, append: bool = False) -> None:
            cleaned = clean_option_text(content)
            if not cleaned:
                return
            if label in option_map:
                if append:
                    option_map[label]["content"] = clean_option_text(
                        f"{option_map[label]['content']} {cleaned}"
                    )
                else:
                    option_map[label]["content"] = cleaned
                return

            item = {"label": label, "content": cleaned}
            option_map[label] = item
            ordered.append(item)

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or is_page_noise(line):
                continue

            segments = split_labeled_segments(line)
            if segments:
                option_mode = True
                for label, content in segments:
                    if content:
                        set_option(label, content)
                        if pending_label == label:
                            pending_label = None
                    else:
                        if pending_next_content:
                            set_option(label, pending_next_content)
                            pending_next_content = None
                            pending_label = None
                        else:
                            pending_label = label
                continue

            if not option_mode:
                continue

            dotted = re.match(r"^[\.\．、:：]\s*(.+)$", line)
            if dotted:
                content = clean_option_text(dotted.group(1))
                if pending_label:
                    set_option(pending_label, content)
                    pending_label = None
                elif pending_next_content:
                    pending_next_content = clean_option_text(
                        f"{pending_next_content} {content}"
                    )
                else:
                    pending_next_content = content
                continue

            if re.match(r"^[A-D]$", line):
                if pending_next_content:
                    set_option(line, pending_next_content)
                    pending_next_content = None
                    pending_label = None
                else:
                    pending_label = line
                continue

            if pending_label:
                set_option(pending_label, line)
                pending_label = None
                continue

            if pending_next_content:
                pending_next_content = clean_option_text(
                    f"{pending_next_content} {line}"
                )
                continue

            if ordered:
                set_option(ordered[-1]["label"], line, append=True)

        return ordered

    options = []

    # 先预处理双列排版
    processed_text = preprocess_two_column_options(raw_text)

    options = extract_options_from_lines(processed_text)
    if len(options) >= 2:
        return options

    # === 策略2: 找到所有 A/B/C/D 标签的位置 ===
    label_positions = []
    for m in re.finditer(r'(?:^|\n|\s)([A-D])\s*[\.\．、:：]\s*', processed_text):
        label_positions.append((m.group(1), m.start(), m.end()))

    found_labels = set(lp[0] for lp in label_positions)
    if len(found_labels) >= 2:
        seen = set()
        unique_positions = []
        for label, start, end in label_positions:
            if label not in seen:
                seen.add(label)
                unique_positions.append((label, start, end))

        unique_positions.sort(key=lambda x: x[1])

        for i, (label, start, end) in enumerate(unique_positions):
            content = processed_text[end:unique_positions[i + 1][1]] if i + 1 < len(unique_positions) else processed_text[end:]
            content = clean_option_text(content)

            if content:
                options.append({"label": label, "content": content})

        if len(options) >= 2:
            return options

    # === 策略3: 内联选项（全部在1-2行内）===
    options.clear()
    inline_pattern = re.compile(
        r'([A-D])\s*[\.\．、:：]\s*(.+?)(?=\s+[B-D]\s*[\.\．、:：]|\s*$)',
    )
    for line in processed_text.split('\n'):
        labels_in_line = re.findall(r'[A-D]\s*[\.\．、:：]', line)
        if len(labels_in_line) >= 2:
            for m in inline_pattern.finditer(line):
                label = m.group(1)
                content = clean_option_text(m.group(2))
                if content and not any(o['label'] == label for o in options):
                    options.append({"label": label, "content": content})

    if len(options) >= 2:
        return options

    # === 策略4: 原始 DOTALL 匹配（最宽松的兜底）===
    options.clear()
    fallback_pattern = re.compile(
        r'(?:^|\n)\s*([A-D])\s*[\.\．、:：]\s*(.+?)(?=\n\s*[A-D]\s*[\.\．、:：]|\n\s*第\d+页|$)',
        re.DOTALL
    )
    for m in fallback_pattern.finditer(processed_text):
        label = m.group(1)
        content = clean_option_text(m.group(2))
        if content and len(content) < 500:
            options.append({"label": label, "content": content})

    return options


def extract_content(raw_text: str, options: list[dict]) -> str:
    """从raw_text中提取题干（去掉选项部分）"""
    if not options:
        # 无选项，整段都是题干
        content = raw_text.strip()
        content = re.sub(r'\s*第\d+页.*$', '', content, flags=re.MULTILINE)
        return re.sub(r'\s+', ' ', content).strip()

    # 找到第一个选项的位置，截取之前的内容作为题干
    first_opt = options[0]
    # 在原文中查找 "A." 或 "A、" 或 "A．"
    opt_start_pattern = re.compile(
        rf'(?:^|\n)\s*{re.escape(first_opt["label"])}\s*[\.\．、]',
        re.MULTILINE
    )
    m = opt_start_pattern.search(raw_text)
    if m:
        content = raw_text[:m.start()].strip()
    else:
        content = raw_text.strip()

    # 清理
    content = re.sub(r'\s*第\d+页[^\n]*', '', content)
    content = re.sub(r'\s*\d{4}年国考.*$', '', content)
    content = re.sub(r'\s+', ' ', content).strip()

    return content


# ── 答案解析 PDF 解析 ──────────────────────────────────────

def parse_answer_pdf(text: str) -> dict:
    """
    解析答案解析PDF，返回 {题号: {answer, explanation}}。
    """
    result = {}

    # Step 1: 解析快速答案表
    # 格式: "【1-5】BCDAA" 或 "【1-5】B C D A A"
    answer_key = {}
    key_pattern = re.compile(r'【(\d+)-(\d+)】\s*([A-D\s]+)')
    for m in key_pattern.finditer(text):
        start_num = int(m.group(1))
        end_num = int(m.group(2))
        answers_str = re.sub(r'\s+', '', m.group(3))
        for i, ans in enumerate(answers_str):
            if ans in 'ABCD':
                answer_key[start_num + i] = ans

    # Step 2: 解析逐题解析
    # 格式: "【N】解析" 或 "【N】" 后跟解析内容
    explanation_pattern = re.compile(
        r'【(\d+)】\s*(?:解析)?\s*\n?(.*?)(?=【\d+】|$)',
        re.DOTALL
    )
    explanations = {}
    for m in explanation_pattern.finditer(text):
        q_num = int(m.group(1))
        expl = m.group(2).strip()

        # 清理解析文本
        # 去掉页码
        expl = re.sub(r'\s*\d+\s*/\s*\d+\s*', ' ', expl)
        # 去掉公众号广告
        expl = re.sub(r'公众号[：:].+?\n', '', expl)
        expl = re.sub(r'认准公众号.+?\n', '', expl)
        # 压缩空白
        expl = re.sub(r'\n{3,}', '\n\n', expl)
        expl = expl.strip()

        # 如果答案表没有这个题号，尝试从解析中提取
        if q_num not in answer_key:
            ans_match = re.search(r'故正确答案为\s*([A-D])', expl)
            if ans_match:
                answer_key[q_num] = ans_match.group(1)

        explanations[q_num] = expl

    # 合并
    all_nums = set(list(answer_key.keys()) + list(explanations.keys()))

    # Step 3: fallback 格式（2023 国考）— 答案 PDF 不用【N】，而是纯数字行
    # + 正文 + "故正确答案为 X" 结尾。当【N】格式抽到 <20 条时触发。
    if len(all_nums) < 20:
        bare_pattern = re.compile(
            r'(?:^|\n|\x0c)\s*(\d{1,3})\s*\n(.*?)(?=(?:^|\n|\x0c)\s*\d{1,3}\s*\n|\Z)',
            re.DOTALL,
        )
        prev_num = 0
        for m in bare_pattern.finditer(text):
            qn = int(m.group(1))
            if qn < 1 or qn > 135:
                continue
            expl = m.group(2).strip()
            if len(expl) < 20:
                continue
            # 单调递增或章节重置（回到 1~25）过滤掉 "2023 年" 这种误匹配
            if qn <= prev_num and qn > 25:
                continue
            prev_num = qn
            ans_match = re.search(
                r'故正确答案为\s*([A-D])|正确答案[:：为]\s*([A-D])|答案[:：]\s*([A-D])|故选\s*([A-D])',
                expl,
            )
            if ans_match and qn not in answer_key:
                answer_key[qn] = next(g for g in ans_match.groups() if g)
            if qn not in explanations:
                # 清理页码/广告
                expl = re.sub(r'\s*\d+\s*/\s*\d+\s*', ' ', expl)
                expl = re.sub(r'公众号[:：].+?\n', '', expl)
                expl = re.sub(r'\n{3,}', '\n\n', expl).strip()
                explanations[qn] = expl
        all_nums = set(list(answer_key.keys()) + list(explanations.keys()))

    # Step 4: 通用启发式 fallback — 兼容事业编/国考 2021-2022/省考各地多种答案格式。
    # 思路：按"题号 N"（支持 N.\n / N． / N、 / N.【答案】 / N 独占行 / 【N】）分段，
    # 对每段内正文尝试 8 种常见"答案字母"收尾语。覆盖：
    #   - 故正确答案为 X       (国考 2023, 事业编)
    #   - 因此，选择 X 选项     (国考 2022)
    #   - 【答案】X            (事业编题号行)
    #   - 选择 X / 选 X 项      (省考/事业编解析)
    #   - 答案[为:：] X         (通用)
    if len(all_nums) < 30:
        seg_pattern = re.compile(
            r'(?:^|\n|\x0c)\s*(?:【)?(\d{1,3})(?:[\.\．、】]|\s*【答案】|\s*\n)',
            re.MULTILINE,
        )
        ans_patterns = [
            re.compile(r'故正确答案为\s*([A-D])'),
            re.compile(r'正确答案[为:：]\s*([A-D])'),
            re.compile(r'【答案】\s*([A-D])'),
            re.compile(r'因此，?\s*选择?\s*([A-D])\s*选项'),
            re.compile(r'故选\s*([A-D])'),
            re.compile(r'答案[为:：]\s*([A-D])\b'),
            re.compile(r'选\s*([A-D])\s*项'),
            re.compile(r'答案\s*[:：]\s*([A-D])'),
        ]
        ms = list(seg_pattern.finditer(text))
        prev_num = 0
        for i, m in enumerate(ms):
            qn = int(m.group(1))
            if qn < 1 or qn > 135:
                continue
            start = m.end()
            end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
            seg = text[start:end]
            if len(seg.strip()) < 15:
                continue
            if qn <= prev_num and qn > 25:
                continue
            prev_num = qn

            if qn not in answer_key:
                for ap in ans_patterns:
                    am = ap.search(seg)
                    if am:
                        answer_key[qn] = am.group(1)
                        break
            if qn not in explanations:
                e = re.sub(r'\s*\d+\s*/\s*\d+\s*', ' ', seg)
                e = re.sub(r'公众号[:：].+?\n', '', e)
                e = re.sub(r'\n{3,}', '\n\n', e).strip()
                explanations[qn] = e[:3000]
        all_nums = set(list(answer_key.keys()) + list(explanations.keys()))

    for num in all_nums:
        result[num] = {
            "answer": answer_key.get(num, ""),
            "explanation": explanations.get(num, ""),
        }

    return result


# ── 难度估算 ────────────────────────────────────────────────

def estimate_difficulty(category: str, q_num: int, total: int) -> int:
    """粗略估算难度 1-5"""
    # 常识判断：中等难度
    if category == "changshi":
        return 3
    # 言语理解：较易到中等
    if category == "yanyu":
        return 2
    # 数量关系：较难
    if category == "shuliang":
        return 4
    # 判断推理：中等
    if category == "panduan":
        return 3
    # 资料分析：中等到较难
    if category == "ziliao":
        return 3
    return 3


# ── 知识点推断 ──────────────────────────────────────────────

def infer_knowledge_points(content: str, category: str, explanation: str = "") -> list[str]:
    """根据题目内容和分类推断知识点标签"""
    combined = content + " " + explanation
    points = []

    if category == "changshi":
        if any(kw in combined for kw in ["习近平", "总书记", "党的", "中央", "政治", "全会", "新时代"]):
            points.append("时政热点")
        if any(kw in combined for kw in ["法律", "法规", "宪法", "民法", "刑法", "立法", "行政法", "诉讼"]):
            points.append("法律常识")
        if any(kw in combined for kw in ["经济", "GDP", "货币", "财政", "税收", "金融", "市场"]):
            points.append("经济常识")
        if any(kw in combined for kw in ["科技", "技术", "5G", "量子", "人工智能", "航天", "生物"]):
            points.append("科技常识")
        if any(kw in combined for kw in ["地理", "气候", "河流", "山脉", "盆地", "高原"]):
            points.append("地理常识")
        if any(kw in combined for kw in ["历史", "朝代", "战役", "诗人", "文化", "文学", "典故"]):
            points.append("人文常识")
        if any(kw in combined for kw in ["马克思", "唯物", "辩证", "矛盾", "哲学"]):
            points.append("政治理论")
        if not points:
            points.append("综合常识")

    elif category == "yanyu":
        if any(kw in combined for kw in ["填入", "划横线", "依次填入", "最恰当"]):
            points.append("逻辑填空")
        elif any(kw in combined for kw in ["主旨", "意在", "主要", "概括", "这段文字"]):
            points.append("片段阅读")
        else:
            points.append("语句表达")

    elif category == "shuliang":
        if any(kw in combined for kw in ["概率", "可能性"]):
            points.append("概率问题")
        elif any(kw in combined for kw in ["排列", "组合", "选取"]):
            points.append("排列组合")
        elif any(kw in combined for kw in ["速度", "路程", "行程"]):
            points.append("行程问题")
        elif any(kw in combined for kw in ["工程", "效率", "完成"]):
            points.append("工程问题")
        else:
            points.append("数学运算")

    elif category == "panduan":
        if any(kw in combined for kw in ["图形", "下列图", "规律"]):
            points.append("图形推理")
        elif any(kw in combined for kw in ["定义", "下列属于", "根据上述定义"]):
            points.append("定义判断")
        elif any(kw in combined for kw in ["类比", "之于", "对应关系"]):
            points.append("类比推理")
        else:
            points.append("逻辑推理")

    elif category == "ziliao":
        if any(kw in combined for kw in ["增长率", "增长量", "增速", "同比"]):
            points.append("增长问题")
        elif any(kw in combined for kw in ["比重", "占", "比例", "比值"]):
            points.append("比重问题")
        else:
            points.append("资料分析")

    return points if points else [CATEGORY_NAMES.get(category, "综合")]


def is_noise_question(question: dict) -> bool:
    content = re.sub(r"\s+", " ", (question.get("content") or "")).strip()
    if not content:
        return True

    if re.search(r"[\u4e00-\u9fffA-Za-z]", content):
        return False

    numeric_density = len(re.findall(r"[\d√/%:+\-]", content))
    return numeric_density >= 6


def question_quality_key(question: dict) -> tuple[int, int, int, int, int]:
    if not question:
        return (-1, -1, -1, -1, -1)

    option_count = len(question.get("options", []))
    content = question.get("content") or ""
    chinese_count = len(re.findall(r"[\u4e00-\u9fff]", content))
    is_noise = 1 if is_noise_question(question) else 0

    return (
        1 if option_count == 4 else 0,
        option_count,
        -is_noise,
        chinese_count,
        len(content),
    )


def dedupe_questions(questions: list[dict]) -> list[dict]:
    best_by_number: dict[int, dict] = {}
    for question in questions:
        number = question.get("number")
        if not isinstance(number, int):
            continue
        current = best_by_number.get(number)
        if current is None or question_quality_key(question) > question_quality_key(current):
            best_by_number[number] = question

    return [best_by_number[number] for number in sorted(best_by_number)]


def merge_questions_with_fitz(question_pdf: str, primary_questions: list[dict]) -> list[dict]:
    primary_questions = dedupe_questions(primary_questions)
    if not primary_questions:
        return primary_questions

    if not any(len(question.get("options", [])) < 4 for question in primary_questions):
        return primary_questions

    fitz_text = normalize_cjk(_fitz_extract_xy_sorted(question_pdf))
    fitz_sections = detect_sections(fitz_text)
    fitz_questions = dedupe_questions(
        parse_questions(
            fitz_text,
            fitz_sections or [{"name": "全部", "category": "changshi", "start": 0, "end": len(fitz_text)}],
        )
    )
    fitz_by_number = {question["number"]: question for question in fitz_questions}

    merged = []
    for primary in primary_questions:
        fallback = fitz_by_number.get(primary["number"])
        best = primary
        if fallback and question_quality_key(fallback) > question_quality_key(primary):
            best = fallback
        merged.append(best)

    return merged


# ── 主流程 ──────────────────────────────────────────────────

def build_questions_json(
    questions: list[dict],
    answers: dict,
    source: str,
    year: int,
    level: str = "",
    region: str = "",
) -> dict[str, list[dict]]:
    """
    将解析后的题目和答案合并为JSON格式。
    返回 {category: [question_objects]}
    """
    result = {}

    level_label = LEVEL_LABELS.get(level, level)
    source_label_map = {
        "national": "国考",
        "provincial": "省考",
        "institution": "事业编",
    }
    source_cn = source_label_map.get(source, source)

    for q in questions:
        cat = q["category"]
        if cat not in result:
            result[cat] = []

        q_num = q["number"]
        ans_data = answers.get(q_num, {})

        # 生成 ID
        region_part = f"-{region}" if region else ""
        level_part = f"-{level}" if level else ""
        q_id = f"{source}{region_part}-xingce-{cat}-{year}{level_part}-{q_num:03d}"

        # sourceLabel
        level_str = f"（{level_label}）" if level_label else ""
        region_str = f"{region}" if region else ""
        s_label = f"{year}年{source_cn}{region_str}行测{level_str}第{q_num}题"

        question_obj = {
            "id": q_id,
            "subject": "xingce",
            "category": cat,
            "type": "single_choice",
            "source": source,
            "year": year,
            "content": q["content"],
            "options": q["options"] if q["options"] else [],
            "answer": ans_data.get("answer", ""),
            "explanation": ans_data.get("explanation", ""),
            "difficulty": estimate_difficulty(cat, q_num, len(questions)),
            "knowledgePoints": infer_knowledge_points(
                q["content"], cat, ans_data.get("explanation", "")
            ),
            "sourceLabel": s_label,
        }
        if level:
            question_obj["level"] = level

        manual_options = MANUAL_OPTION_OVERRIDES.get(q_id)
        if manual_options:
            question_obj["options"] = manual_options

        # 图形推理检测：选项不足且题干含图形关键词 → 标记为图形题
        is_figure = any(kw in q["content"] for kw in [
            "图形", "图示", "下列图", "下图", "图中", "饼状图", "柱状图", "折线图",
            "填入问号", "选择最合适的一个填入", "选择最合适的一项填入",
            "直观图", "立体图", "多面体",
        ])
        if len(question_obj["options"]) < 4 and is_figure:
            question_obj["options"] = [
                {"label": "A", "content": "[图形选项]"},
                {"label": "B", "content": "[图形选项]"},
                {"label": "C", "content": "[图形选项]"},
                {"label": "D", "content": "[图形选项]"},
            ]
            question_obj["knowledgePoints"] = ["图形推理"]

        # 选项不足时，尝试从答案解析中补救 ABCD 描述
        if len(question_obj["options"]) < 4 and not is_figure:
            expl = ans_data.get("explanation", "")
            recovered = []
            for label in "ABCD":
                pat = re.compile(
                    rf'{label}\s*(?:项|选项)?\s*(?:正确|错误|，|。|：|:)?\s*(.{{5,100}}?)(?=[B-D]\s*(?:项|选项)|故正确|$)',
                    re.DOTALL,
                )
                m = pat.search(expl)
                if m:
                    recovered.append({"label": label, "content": m.group(1).strip()[:100]})
            if len(recovered) >= 3:
                question_obj["options"] = recovered

        if region:
            question_obj["region"] = region

        result[cat].append(question_obj)

    return result


def save_questions(
    categorized: dict[str, list[dict]],
    output_dir: str,
    source: str,
    year: int,
    region: str = "",
    level: str = "",
    replace_existing: bool = False,
):
    """将分类后的题目保存为JSON文件"""
    for cat, questions in categorized.items():
        cat_dir = os.path.join(output_dir, cat)
        os.makedirs(cat_dir, exist_ok=True)

        # 文件名: national_2025_fushengjia.json 或 provincial_anhui_2024.json
        parts = [source]
        if region:
            parts.append(region)
        parts.append(str(year))
        if level:
            parts.append(level)
        filename = "_".join(parts) + ".json"

        filepath = os.path.join(cat_dir, filename)

        # 如果文件已存在，合并（保留原数据，但允许空字段被新抽到的值填充）
        existing = []
        if os.path.exists(filepath) and not replace_existing:
            with open(filepath, "r", encoding="utf-8") as f:
                existing = json.load(f)

        # 先建 id -> existing-q 映射，便于更新；保持原 existing 的顺序稳定
        existing_by_id = {q.get("id"): q for q in existing if q.get("id")}
        new_added = 0
        fields_filled = 0
        for q in questions:
            qid = q.get("id")
            if not qid:
                continue
            if qid in existing_by_id:
                old = existing_by_id[qid]
                # 规则 1: 旧字段空时用新值填充（answer/explanation/content/options）
                for k in ("answer", "explanation", "content", "options"):
                    if q.get(k) and not old.get(k):
                        old[k] = q[k]
                        fields_filled += 1
                # 规则 2: 新 options 比旧更完整时替换（修复历史双列错抽的 [A,C] 脏数据）
                new_opts = q.get("options") or []
                old_opts = old.get("options") or []
                if len(new_opts) > len(old_opts) and len(new_opts) >= 3:
                    old["options"] = new_opts
                    fields_filled += 1
            else:
                existing.append(q)
                existing_by_id[qid] = q
                new_added += 1

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

        extra = f", 更新空字段 {fields_filled}" if fields_filled else ""
        mode = "覆盖" if replace_existing else "合并"
        print(f"  [{cat}] {mode}: {new_added} 新题{extra} → {filepath} (共 {len(existing)} 题)")


def main():
    parser = argparse.ArgumentParser(description="行测PDF真题提取器")
    parser.add_argument("--question-pdf", required=True, help="行测真题PDF路径")
    parser.add_argument("--answer-pdf", required=True, help="答案解析PDF路径")
    parser.add_argument("--source", required=True, choices=["national", "provincial", "institution"],
                        help="考试来源")
    parser.add_argument("--year", required=True, type=int, help="考试年份")
    parser.add_argument("--level", default="", help="考试级别 (fushengjia/dishi/xingzhengzhifa)")
    parser.add_argument("--region", default="", help="省份代码 (如 anhui, 省考用)")
    parser.add_argument("--output-dir", default="src/data/xingce/", help="输出目录")
    parser.add_argument("--dry-run", action="store_true", help="仅解析不保存，打印统计")
    parser.add_argument("--replace-existing", action="store_true", help="覆盖当前卷对应分类文件，而不是与历史结果合并")

    args = parser.parse_args()

    print(f"=" * 60)
    print(f"行测真题提取: {args.source} {args.year} {args.level}")
    print(f"  真题PDF: {args.question_pdf}")
    print(f"  答案PDF: {args.answer_pdf}")
    print(f"=" * 60)

    # 1. 提取PDF文本
    print("\n[1/5] 提取真题PDF文本...")
    q_text = extract_pdf_text_best(args.question_pdf)
    print(f"  文本长度: {len(q_text)} 字符")

    print("\n[2/5] 提取答案PDF文本...")
    a_text = extract_pdf_text(args.answer_pdf)
    print(f"  文本长度: {len(a_text)} 字符")

    # 2. 检测章节
    print("\n[3/5] 检测章节...")
    sections = detect_sections(q_text)
    for s in sections:
        print(f"  {s['name']} → {s['category']} (pos {s['start']}-{s['end']})")

    if not sections:
        print("  [WARN] 未检测到章节标题，所有题目将归入 changshi")
        sections = [{"name": "全部", "category": "changshi", "start": 0, "end": len(q_text)}]

    # 3. 解析题目
    print("\n[4/5] 解析题目...")
    questions = parse_questions(q_text, sections)
    questions = merge_questions_with_fitz(args.question_pdf, questions)
    print(f"  共解析 {len(questions)} 道题")

    # 统计各分类
    cat_counts = {}
    for q in questions:
        cat_counts[q["category"]] = cat_counts.get(q["category"], 0) + 1
    for cat, cnt in sorted(cat_counts.items()):
        print(f"    {CATEGORY_NAMES.get(cat, cat)}: {cnt} 题")

    # 检查无选项的题目
    no_opts = [q for q in questions if not q["options"]]
    if no_opts:
        print(f"  [WARN] {len(no_opts)} 道题未提取到选项: {[q['number'] for q in no_opts[:10]]}")

    # 4. 解析答案
    print("\n[5/5] 解析答案和解析...")
    answers = parse_answer_pdf(a_text)
    print(f"  共解析 {len(answers)} 道答案")

    has_answer = sum(1 for a in answers.values() if a["answer"])
    has_expl = sum(1 for a in answers.values() if a["explanation"])
    print(f"    有答案: {has_answer}, 有解析: {has_expl}")

    # 5. 合并并输出
    categorized = build_questions_json(
        questions, answers, args.source, args.year, args.level, args.region
    )

    total = sum(len(qs) for qs in categorized.values())
    with_answer = sum(1 for qs in categorized.values() for q in qs if q["answer"])
    with_expl = sum(1 for qs in categorized.values() for q in qs if q["explanation"])
    print(f"\n{'=' * 60}")
    print(f"总计: {total} 题, 有答案: {with_answer}, 有解析: {with_expl}")

    if args.dry_run:
        print("\n[DRY RUN] 不保存文件")
        # 打印前3题预览
        for cat, qs in categorized.items():
            print(f"\n--- {CATEGORY_NAMES.get(cat, cat)} 预览 ---")
            for q in qs[:2]:
                print(f"  [{q['id']}] {q['content'][:80]}...")
                if q["options"]:
                    for opt in q["options"][:2]:
                        print(f"    {opt['label']}. {opt['content'][:50]}")
                print(f"    答案: {q['answer']}")
                print()
    else:
        print(f"\n保存到: {args.output_dir}")
        save_questions(
            categorized,
            args.output_dir,
            args.source,
            args.year,
            args.region,
            args.level,
            replace_existing=args.replace_existing,
        )
        print("\n完成!")


if __name__ == "__main__":
    main()
