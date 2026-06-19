#!/usr/bin/env python3
"""Recover missing Shenlun `material` fields from local source PDFs.

This script only writes when a verifiable chain exists:
1. Locate a candidate local PDF for the missing Shenlun record.
2. Match the existing JSON `answer` text back into the PDF text layer.
3. Split the PDF into exam paper vs. answer section.
4. Split the exam paper into `material` and prompt `content`.

Dry-run by default:
  python scripts/rescue_shenlun_remaining_material.py

Apply changes:
  python scripts/rescue_shenlun_remaining_material.py --apply
"""

from __future__ import annotations

import argparse
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from pdfminer.high_level import extract_text


ROOT = Path(__file__).resolve().parent.parent
MISSING_REPORT = ROOT / "reports" / "shenlun_missing_material_140.json"
OUT_REPORT = ROOT / "reports" / "shenlun_material_pdf_rescue_preview.json"
PACK_FILES_ROOT = ROOT / "data" / "gap_rescue_pack" / "files"

NATIONAL_PDF_ROOT = ROOT / "material" / "【国考】2000-2025真题pdf" / "2000-2025国考申论PDF"
PROVINCIAL_PDF_ROOT = ROOT / "material" / "【省考】2000-2025真题pdf"
INSTITUTION_PDF_ROOT = ROOT / "material" / "【事业编】事业单位联考历年真题"

REGION_ZH = {
    "anhui": "安徽",
    "beijing": "北京",
    "chongqing": "重庆",
    "fujian": "福建",
    "gansu": "甘肃",
    "guangdong": "广东",
    "guangxi": "广西",
    "guangzhou": "广州",
    "guizhou": "贵州",
    "hainan": "海南",
    "hebei": "河北",
    "heilongjiang": "黑龙江",
    "henan": "河南",
    "hubei": "湖北",
    "hunan": "湖南",
    "jiangsu": "江苏",
    "jiangxi": "江西",
    "liaoning": "辽宁",
    "neimenggu": "内蒙古",
    "ningxia": "宁夏",
    "qinghai": "青海",
    "shaanxi": "陕西",
    "shandong": "山东",
    "shanghai": "上海",
    "shanxi": "山西",
    "sichuan": "四川",
    "tianjin": "天津",
    "xinjiang": "新疆",
    "yunnan": "云南",
    "zhejiang": "浙江",
}

DIRECT_PROMPT_HEADS = (
    "作答要求",
    "申论要求",
    "答题要求",
    "三、作答要求",
    "三、申论要求",
    "三、答题要求",
    "二、作答要求",
    "二、答题要求",
    "二、【作答要求】",
    "三、问题",
    "问题：",
    "问题:",
    "写作要求",
)

QUESTION_VERBS = (
    "根据",
    "结合",
    "阅读",
    "假定",
    "假如",
    "假设",
    "请",
    "围绕",
    "谈谈",
    "概括",
    "概述",
    "简述",
    "归纳",
    "指出",
    "提出",
    "分析",
    "写",
    "撰写",
    "自拟",
    "就",
    "谈",
    "针对",
    "说明",
    "认真阅读",
    "用",
    "就",
    "针对",
    "围绕",
    "草拟",
)

NOISE_LINE_RE = re.compile(
    r"^(?:获取试卷更新.*|来源：\s*微信：gwy288.*|分类：申论(?:/.*)?来源：粉笔)$"
)
TITLE_RE = re.compile(r"20\d{2}.*(?:申论|公务员)")
MATERIAL_BRACKET_RE = re.compile(r"^[【\[](?:给定资料|给定材料)[一二三四五六七八九十0-9]+[】\]]")
GENERIC_MATERIAL_BRACKET_RE = re.compile(r"^[【\[]?(?:材料|资料)\s*[一二三四五六七八九十0-9]+[】\]]?(?:[:：]|$)")
MATERIAL_LINE_RE = re.compile(r"^(?:材料|资料)\s*[一二三四五六七八九十0-9]+(?:[:：]|$)")
QUESTION_LINE_RE = re.compile(
    r"^(?:[(（]?[一二三四五六七八九十\d]+[)）]|第[一二三四五六七八九十0-9]+题|[一二三四五六七八九十\d]+、)\s*(.*)$"
)
PURE_QUESTION_HEADER_RE = re.compile(r"^第[一二三四五六七八九十0-9]+题(?:\s*[（(]\s*\d+\s*分\s*[)）])?$")
PROBLEM_LABEL_RE = re.compile(
    r"^[【\[]?问题[一二三四五六七八九十0-9]+[】\]]?(?:\s*[（(]\s*\d+\s*分\s*[)）])?(?:[:：]\s*(.*))?$"
)
ENUM_MATERIAL_RE = re.compile(r"^\(\d{1,2}\)")
SCORE_SPLIT_RE = re.compile(r"[（(]\s*\d+\s*分\s*[）)]")
ROMAN_ANSWER_HEAD_RE = re.compile(r"^[一二三四五六七八九十]+[、，,:：]?(?:参考答案|答案提示|参考范文)")
ANSWER_LINE_MARKERS = (
    "试卷参考答案",
    "参考答案",
    "答案提示",
    "参考范文",
    "问题一参考答案",
    "问题二参考答案",
    "问题三参考答案",
    "问题四参考答案",
    "问题五参考答案",
)


ALT_DIRECT_PROMPT_HEAD_RE = re.compile(
    r"^(?:[一二三四五六七八九十\d\uff10-\uff19]+、)?(?:作答要求|申论要求|答题要求)$"
)
ALT_MATERIAL_SECTION_RE = re.compile(
    r"^(?:[一二三四五六七八九十\d\uff10-\uff19]+、)?(?:给定资料|给定材料|所给材料|背景材料|阅读资料)$"
)
ALT_MATERIAL_ITEM_RE = re.compile(
    r"^(?:[\u3010\[])?(?:材料|资料)\s*[一二三四五六七八九十\d\uff10-\uff19]+(?:[\u3011\]])?(?:[:：]|$)"
)
ALT_QUESTION_LABEL_RE = re.compile(
    r"^(?:(?:第\s*[一二三四五六七八九十\d\uff10-\uff19]+\s*题)|(?:问题\s*[一二三四五六七八九十\d\uff10-\uff19]+)|(?:[一二三四五六七八九十\d\uff10-\uff19]+\s*题))(?:\s*[（(]\s*[\d\uff10-\uff19]+\s*分\s*[)）])?(?:\s*[:：]\s*(.*))?$"
)
ALT_PURE_QUESTION_HEADER_RE = re.compile(
    r"^(?:(?:第\s*[一二三四五六七八九十\d\uff10-\uff19]+\s*题)|(?:问题\s*[一二三四五六七八九十\d\uff10-\uff19]+)|(?:[一二三四五六七八九十\d\uff10-\uff19]+\s*题))(?:\s*[（(]\s*[\d\uff10-\uff19]+\s*分\s*[)）])?$"
)
ALT_QUESTION_WINDOW_RE = re.compile(
    r"(?:第\s*[一二三四五六七八九十\d\uff10-\uff19]+\s*题|问题\s*[一二三四五六七八九十\d\uff10-\uff19]+|[一二三四五六七八九十\d\uff10-\uff19]+\s*题)"
)
ALT_SCORE_SPLIT_RE = re.compile(r"[（(]\s*[\d\uff10-\uff19]+\s*分\s*[)）]")


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", "", text)


def clean_extracted_text(text: str) -> str:
    text = text.replace("\r", "").replace("\x0c", "\n")
    text = re.sub(r"(?m)^\s*-\s*\d+\s*-\s*$", "", text)
    text = re.sub(r"(?m)^\s*\d+\s*$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_noise_lines(text: str) -> str:
    cleaned: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue
        if NOISE_LINE_RE.match(line):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def derive_title(content: str) -> str:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    for line in lines[:8]:
        if TITLE_RE.search(line):
            return line
    return lines[0] if lines else ""


def extract_title_tokens(title: str) -> set[str]:
    tokens: set[str] = set()
    keyword_pool = (
        "广州",
        "国考",
        "国家",
        "联考",
        "副省级",
        "省部级",
        "地市级",
        "行政执法",
        "县级",
        "县乡",
        "乡镇",
        "乡市",
        "上半年",
        "下半年",
        "A卷",
        "B卷",
        "C卷",
        "A类",
        "B类",
        "C类",
        "单考区",
        "网友回忆版",
    )
    for keyword in keyword_pool:
        if keyword in title:
            tokens.add(keyword)
    for frag in re.findall(r"[\u4e00-\u9fff]{2,6}", title):
        if frag in {
            "公务员考试",
            "公务员录用考试",
            "公务员",
            "国考",
            "真题",
            "考试",
            "申论",
            "试卷",
        }:
            continue
        tokens.add(frag)
    return tokens


def detect_region_keyword(question: dict[str, Any], title: str) -> str | None:
    region = question.get("region")
    if region and region in REGION_ZH:
        return REGION_ZH[region]
    if "广州市" in title or "广州" in title:
        return "广州"
    return None


def detect_level_keywords(question: dict[str, Any], title: str, source_label: str) -> set[str]:
    text = " ".join(
        [
            str(question.get("id") or ""),
            title,
            source_label,
            str(question.get("content", "")[:200]),
        ]
    )
    keywords: set[str] = set()
    if any(flag in text for flag in ("fushengjia", "副省级", "省部级")):
        keywords.update({"副省级", "省部级"})
    if any(flag in text for flag in ("dishi", "地市级")):
        keywords.add("地市级")
    if any(flag in text for flag in ("xingzhengzhifa", "行政执法")):
        keywords.add("行政执法")
    for token in (
        "A卷",
        "B卷",
        "C卷",
        "A 类",
        "B 类",
        "C 类",
        "A类",
        "B类",
        "C类",
        "县级",
        "县乡",
        "乡镇",
        "市县",
        "单考区",
        "上半年",
        "下半年",
        "网友回忆版",
    ):
        if token in text:
            keywords.add(token)
    return keywords


@lru_cache(maxsize=4096)
def load_pdf_text(pdf_path: str) -> str:
    return clean_extracted_text(extract_text(pdf_path))


def raw_index_from_normalized(raw: str, normalized_pos: int) -> int:
    if normalized_pos <= 0:
        return 0
    index = 0
    for raw_index, ch in enumerate(raw):
        if ch.isspace():
            continue
        if index == normalized_pos:
            return raw_index
        index += 1
    return len(raw)


def raw_end_index_from_normalized(raw: str, normalized_end_pos: int) -> int:
    if normalized_end_pos <= 0:
        return 0
    index = 0
    for raw_index, ch in enumerate(raw):
        if ch.isspace():
            continue
        index += 1
        if index >= normalized_end_pos:
            return raw_index + 1
    return len(raw)


def answer_probe_fragments(answer: str) -> list[str]:
    probes: list[str] = []
    stripped = strip_noise_lines(answer)
    normalized = normalize_ws(stripped)

    for size in (320, 260, 220, 180, 160, 120, 80):
        if len(normalized) >= size:
            probes.append(normalized[:size])

    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    line_candidates = sorted(lines, key=lambda item: len(normalize_ws(item)), reverse=True)
    for line in line_candidates:
        norm_line = normalize_ws(line)
        if len(norm_line) >= 30:
            probes.append(norm_line[: min(len(norm_line), 180)])

    paragraph_candidates = [
        part.strip()
        for part in re.split(r"\n\s*\n", stripped)
        if part.strip()
    ]
    for part in sorted(paragraph_candidates, key=lambda item: len(normalize_ws(item)), reverse=True):
        norm_part = normalize_ws(part)
        if len(norm_part) >= 50:
            probes.append(norm_part[: min(len(norm_part), 220)])

    deduped: list[str] = []
    seen: set[str] = set()
    for probe in probes:
        probe = probe.strip()
        if len(probe) < 30:
            continue
        if probe not in seen:
            seen.add(probe)
            deduped.append(probe)
    return deduped


def anchor_score(raw_prefix: str, answer: str) -> int:
    score = 0
    for probe in answer_probe_fragments(answer):
        if probe in normalize_ws(raw_prefix):
            score += len(probe)
    return score


def to_project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def find_answer_split_candidates(pdf_text: str, answer: str, limit: int = 24) -> list[int]:
    haystack = normalize_ws(pdf_text)
    if len(haystack) < 100:
        return []

    matches: list[tuple[int, int, int]] = []
    seen_positions: set[tuple[int, int]] = set()
    for probe in answer_probe_fragments(answer):
        pos = haystack.find(probe)
        while pos >= 0:
            end_pos = pos + len(probe)
            match_key = (pos, end_pos)
            if match_key not in seen_positions:
                seen_positions.add(match_key)
                raw_end = raw_end_index_from_normalized(pdf_text, end_pos)
                prefix = pdf_text[:raw_end]
                score = anchor_score(prefix[-12000:], answer)
                matches.append((score, pos, end_pos))
            pos = haystack.find(probe, pos + 1)

    if not matches:
        return []

    ranked = sorted(matches, key=lambda item: (-item[0], item[1], item[2]))
    ordered_positions: list[int] = []
    seen_raw: set[int] = set()
    for _, start_pos, _ in ranked:
        raw_start = raw_index_from_normalized(pdf_text, start_pos)
        if raw_start not in seen_raw:
            seen_raw.add(raw_start)
            ordered_positions.append(raw_start)
        if len(ordered_positions) >= limit:
            break
    return ordered_positions


def find_answer_split(pdf_text: str, answer: str) -> int | None:
    candidates = find_answer_split_candidates(pdf_text, answer, limit=1)
    return candidates[0] if candidates else None


def is_material_header(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if ALT_MATERIAL_SECTION_RE.match(stripped):
        return True
    if stripped.startswith(("二、给定资料", "二、给定材料", "二、阅读资料", "二、申论材料", "二、资料", "给定资料", "给定材料")):
        return True
    if MATERIAL_BRACKET_RE.match(stripped):
        return True
    if GENERIC_MATERIAL_BRACKET_RE.match(stripped):
        return True
    if MATERIAL_LINE_RE.match(stripped):
        return True
    if ALT_MATERIAL_ITEM_RE.match(stripped):
        return True
    return False


def looks_like_question_requirement(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    stripped = ALT_SCORE_SPLIT_RE.sub("", stripped)
    stripped = SCORE_SPLIT_RE.sub("", stripped)
    stripped = re.sub(r"^[（(]?[一二三四五六七八九十\d]+[)）、．. ]*", "", stripped)
    stripped = re.sub(r"^第[一二三四五六七八九十0-9]+题", "", stripped).strip()
    stripped = re.sub(
        r"^(?:第\s*[一二三四五六七八九十\d\uff10-\uff19]+\s*题|问题\s*[一二三四五六七八九十\d\uff10-\uff19]+|[一二三四五六七八九十\d\uff10-\uff19]+\s*题)\s*[:：]?",
        "",
        stripped,
    ).strip()
    if any(stripped.startswith(verb) for verb in QUESTION_VERBS):
        return True
    if stripped.startswith(("要求", "作答", "请就", "请根据", "请结合", "请你", "根据")):
        return True
    if any(token in stripped[:80] for token in ("字数", "要求", "作答", "不超过", "写一篇", "发言提纲", "短文", "文章", "建议书", "宣传单", "概括", "分析", "谈谈", "写一份")):
        return True
    return False


def is_prompt_header(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if ALT_DIRECT_PROMPT_HEAD_RE.match(stripped):
        return True
    if stripped.startswith(DIRECT_PROMPT_HEADS):
        return True
    alt_problem_label = ALT_QUESTION_LABEL_RE.match(stripped)
    if alt_problem_label:
        remainder = (alt_problem_label.group(1) or "").strip()
        return not remainder or looks_like_question_requirement(remainder)
    problem_label = PROBLEM_LABEL_RE.match(stripped)
    if problem_label:
        remainder = (problem_label.group(1) or "").strip()
        return not remainder or looks_like_question_requirement(remainder)
    if ALT_PURE_QUESTION_HEADER_RE.match(stripped):
        return True
    if PURE_QUESTION_HEADER_RE.match(stripped):
        return True
    matched = QUESTION_LINE_RE.match(stripped)
    if matched:
        remainder = matched.group(1).strip()
        if not remainder:
            return True
        return looks_like_question_requirement(remainder)
    return False


def is_explicit_question_header(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if ALT_DIRECT_PROMPT_HEAD_RE.match(stripped):
        return True
    if ALT_QUESTION_LABEL_RE.match(stripped):
        return True
    if PROBLEM_LABEL_RE.match(stripped):
        return True
    if ALT_PURE_QUESTION_HEADER_RE.match(stripped):
        return True
    if PURE_QUESTION_HEADER_RE.match(stripped):
        return True
    return False


def rewind_prompt_cluster(lines: list[str], start_index: int, window: int = 18) -> int:
    explicit_headers = [start_index] if is_explicit_question_header(lines[start_index]) else []
    nonempty_seen = 0

    for index in range(start_index - 1, -1, -1):
        stripped = lines[index].strip()
        if not stripped:
            continue
        nonempty_seen += 1
        if nonempty_seen > window:
            break
        if is_explicit_question_header(stripped):
            explicit_headers.append(index)

    if len(explicit_headers) >= 2:
        return min(explicit_headers)
    return start_index


def find_prompt_start_line(lines: list[str], prompt_search_start: int) -> int | None:
    for index in range(prompt_search_start, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith(DIRECT_PROMPT_HEADS) or ALT_DIRECT_PROMPT_HEAD_RE.match(stripped):
            return rewind_prompt_cluster(lines, index)

    for index in range(prompt_search_start, len(lines)):
        if is_prompt_header(lines[index]):
            stripped = lines[index].strip()
            if PURE_QUESTION_HEADER_RE.match(stripped) or ALT_PURE_QUESTION_HEADER_RE.match(stripped):
                next_window = "\n".join(
                    line.strip() for line in lines[index + 1 : index + 5] if line.strip()
                )
                if not looks_like_question_requirement(next_window):
                    continue
            return rewind_prompt_cluster(lines, index)
    return None


def find_explicit_answer_start(pdf_text: str, title: str) -> int | None:
    lines = pdf_text.splitlines()
    total_lines = max(len(lines), 1)
    title_norm = normalize_ws(title)
    title_seen = False
    cursor = 0

    for index, line in enumerate(lines):
        stripped = line.strip()
        raw_pos = cursor
        cursor += len(line) + 1
        if not stripped:
            continue
        if index < max(8, total_lines // 12):
            if title_norm and normalize_ws(stripped) == title_norm:
                title_seen = True
            continue

        if title_norm and normalize_ws(stripped) == title_norm:
            if title_seen:
                return raw_pos
            title_seen = True

        if any(marker in stripped for marker in ANSWER_LINE_MARKERS):
            return raw_pos

    return None


def is_split_plausible(material: str, content: str, prompt_header: str) -> bool:
    material_head_lines = [line.strip() for line in material.splitlines() if line.strip()][:8]
    content_head_lines = [line.strip() for line in content.splitlines() if line.strip()][:20]
    prompt_window = "\n".join(content_head_lines[-10:] + [prompt_header])

    if material_head_lines:
        joined_head = " ".join(material_head_lines)
        if joined_head.startswith("一、注意事项") or joined_head.startswith("1.本题本由"):
            return False

    if not (
        prompt_header.startswith(DIRECT_PROMPT_HEADS)
        or ALT_DIRECT_PROMPT_HEAD_RE.match(prompt_header)
        or is_explicit_question_header(prompt_header)
        or looks_like_question_requirement(prompt_header)
        or looks_like_question_requirement(prompt_window)
    ):
        return False

    if "三、作答要求" not in content and "三、申论要求" not in content and "三、答题要求" not in content:
        if not (
            re.search(r"(?:第[一二三四五六七八九十0-9]+题|[（(]?[一二三四五六七八九十0-9]+[)）、])", prompt_window)
            or ALT_QUESTION_WINDOW_RE.search(prompt_window)
        ):
            return False

    material_tail = "\n".join([line.strip() for line in material.splitlines() if line.strip()][-12:])
    if "字数" in material_tail and "要求" in material_tail:
        return False

    return True


def split_exam_sections(exam_text: str) -> dict[str, str] | None:
    lines = exam_text.split("\n")
    positions: list[int] = []
    cursor = 0
    for line in lines:
        positions.append(cursor)
        cursor += len(line) + 1

    material_indices = [i for i, line in enumerate(lines) if is_material_header(line)]
    prefix_before_material = ""
    if material_indices:
        material_start_line = material_indices[0]
        prompt_search_start = material_start_line + 1
    else:
        fallback_lines = [
            i
            for i, line in enumerate(lines)
            if ENUM_MATERIAL_RE.match(line.strip()) and len(line.strip()) > 20
        ]
        generic_material_lines = [
            i
            for i, line in enumerate(lines)
            if GENERIC_MATERIAL_BRACKET_RE.match(line.strip())
        ]
        if generic_material_lines:
            fallback_lines = generic_material_lines
        if not fallback_lines:
            return None
        material_start_line = fallback_lines[0]
        prompt_search_start = material_start_line + 1

    prompt_start_line = find_prompt_start_line(lines, prompt_search_start)
    if prompt_start_line is None and material_start_line > 0:
        prompt_start_line = find_prompt_start_line(lines, 0)
    if prompt_start_line is None:
        return None

    material_start = positions[material_start_line]
    prompt_start = positions[prompt_start_line]

    if prompt_start_line < material_start_line:
        prefix_before_material = strip_noise_lines(exam_text[:prompt_start])
        prompt = strip_noise_lines(exam_text[prompt_start:material_start])
        material = strip_noise_lines(exam_text[material_start:])
        prefix = prefix_before_material
    else:
        prefix = strip_noise_lines(exam_text[:material_start])
        material = strip_noise_lines(exam_text[material_start:prompt_start])
        prompt = strip_noise_lines(exam_text[prompt_start:])
    content = "\n\n".join(part for part in (prefix, prompt) if part).strip()

    if len(material) < 200 or len(prompt) < 30 or len(content) < 80:
        return None
    if not is_split_plausible(material, content, lines[prompt_start_line].strip()):
        return None

    return {
        "material": material,
        "content": content,
        "promptHeader": lines[prompt_start_line].strip(),
        "materialStartLine": str(material_start_line),
        "promptStartLine": str(prompt_start_line),
    }


def score_pdf_candidate(
    pdf_path: Path,
    question: dict[str, Any],
    title: str,
    source_label: str,
    region_keyword: str | None,
    level_keywords: set[str],
    title_tokens: set[str],
) -> int:
    full = pdf_path.as_posix()
    score = 0
    year = str(question["year"])
    if year in full:
        score += 100
    if "申论" in full:
        score += 40
    if question.get("source") == "national" and "国考" in full:
        score += 40
    if region_keyword and region_keyword in full:
        score += 90
    if "广州" in title and "广州" in full:
        score += 120
    if "联考" in title and "联考" in full:
        score += 60
    if "网友回忆版" in title and "网友回忆版" in full:
        score += 20
    for keyword in level_keywords:
        if keyword and keyword in full:
            score += 35
    for token in title_tokens:
        if token in full:
            score += 12
    if "答案" in full or "解析" in full:
        score += 10
    return score


@lru_cache(maxsize=8)
def get_source_pdf_pool(source: str) -> list[Path]:
    if source == "national":
        return sorted(NATIONAL_PDF_ROOT.rglob("*.pdf"))
    if source == "institution":
        return sorted(INSTITUTION_PDF_ROOT.rglob("*.pdf"))
    return sorted(PROVINCIAL_PDF_ROOT.rglob("*.pdf"))


def get_candidate_pdfs(question: dict[str, Any], top_n: int = 16) -> list[Path]:
    title = derive_title(question.get("content", ""))
    source_label = str(question.get("sourceLabel") or "")
    region_keyword = detect_region_keyword(question, title)
    level_keywords = detect_level_keywords(question, title, source_label)
    title_tokens = extract_title_tokens(title)
    pool = get_source_pdf_pool(str(question.get("source")))

    year = str(question["year"])
    year_filtered = [pdf for pdf in pool if year in pdf.as_posix()]
    candidates = year_filtered or pool

    if region_keyword:
        region_filtered = [pdf for pdf in candidates if region_keyword in pdf.as_posix()]
        if region_filtered:
            candidates = region_filtered

    if level_keywords:
        level_filtered = [
            pdf
            for pdf in candidates
            if any(keyword in pdf.as_posix() for keyword in level_keywords)
        ]
        if level_filtered:
            candidates = level_filtered

    scored = sorted(
        candidates,
        key=lambda pdf: score_pdf_candidate(
            pdf,
            question,
            title,
            source_label,
            region_keyword,
            level_keywords,
            title_tokens,
        ),
        reverse=True,
    )
    return scored[:top_n]


def rescue_one(json_path: Path) -> dict[str, Any]:
    records = json.loads(json_path.read_text(encoding="utf-8"))
    question = records[0]
    title = derive_title(question.get("content", ""))
    relative_json_path = to_project_relative(json_path)
    candidates = get_candidate_pdfs(question)
    attempted: list[dict[str, Any]] = []

    for rank, pdf_path in enumerate(candidates, start=1):
        try:
            pdf_text = load_pdf_text(str(pdf_path))
        except Exception as exc:  # noqa: BLE001
            attempted.append(
                {
                    "rank": rank,
                    "pdfPath": pdf_path.as_posix(),
                    "reason": f"pdf_read_failed:{type(exc).__name__}",
                }
            )
            continue

        explicit_answer_start = find_explicit_answer_start(pdf_text, title)
        split_candidates = find_answer_split_candidates(pdf_text, str(question.get("answer") or ""))
        if not split_candidates:
            attempted.append(
                {
                    "rank": rank,
                    "pdfPath": pdf_path.as_posix(),
                    "reason": "answer_anchor_not_found",
                }
            )
            continue

        split: dict[str, str] | None = None
        winning_split_index: int | None = None
        for anchor_try, split_index in enumerate(split_candidates, start=1):
            exam_end = split_index
            if explicit_answer_start is not None and 0 < explicit_answer_start < split_index:
                exam_end = explicit_answer_start
            exam_text = pdf_text[:exam_end].strip()
            split = split_exam_sections(exam_text)
            if split is not None:
                winning_split_index = exam_end
                break
            if anchor_try >= 8:
                break

        if split is None or winning_split_index is None:
            attempted.append(
                {
                    "rank": rank,
                    "pdfPath": pdf_path.as_posix(),
                    "reason": "exam_split_failed",
                    "anchorCandidates": len(split_candidates),
                }
            )
            continue

        return {
            "status": "rescued",
            "jsonPath": relative_json_path,
            "id": question.get("id"),
            "title": title,
            "pdfPath": pdf_path.as_posix(),
            "candidateRank": rank,
            "answerSplitIndex": winning_split_index,
            "promptHeader": split["promptHeader"],
            "materialLength": len(split["material"]),
            "contentLength": len(split["content"]),
            "material": split["material"],
            "content": split["content"],
        }

    return {
        "status": "unresolved",
        "jsonPath": relative_json_path,
        "id": question.get("id"),
        "title": title,
        "candidateCount": len(candidates),
        "topCandidates": [path.as_posix() for path in candidates[:8]],
        "attempted": attempted[:8],
    }


def apply_rescue(result: dict[str, Any]) -> None:
    json_path = ROOT / result["jsonPath"]
    records = json.loads(json_path.read_text(encoding="utf-8"))
    question = records[0]
    question["material"] = result["material"]
    question["content"] = result["content"]
    meta = question.setdefault("meta", {})
    meta["materialRescuedBy"] = "D24-pdf-backfill"
    meta["materialSource"] = "local source pdf"
    meta["materialPdfPath"] = result["pdfPath"]
    meta["materialPromptHeader"] = result["promptHeader"]
    json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    mirror_path = PACK_FILES_ROOT / result["jsonPath"]
    mirror_path.parent.mkdir(parents=True, exist_ok=True)
    mirror_path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def discover_missing_material_targets() -> list[dict[str, str]]:
    targets: list[dict[str, str]] = []
    for json_path in sorted((ROOT / "src" / "data" / "shenlun").rglob("*.json")):
        records = json.loads(json_path.read_text(encoding="utf-8"))
        if not records:
            continue
        question = records[0]
        material = str(question.get("material") or "").strip()
        if not material:
            targets.append({"path": to_project_relative(json_path)})
    return targets


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write rescued data back to JSON")
    parser.add_argument("--limit", type=int, default=0, help="only process first N targets")
    parser.add_argument(
        "--only",
        type=str,
        default="",
        help="comma-separated relative JSON paths to process",
    )
    args = parser.parse_args()

    if MISSING_REPORT.exists():
        targets = json.loads(MISSING_REPORT.read_text(encoding="utf-8"))
    else:
        targets = discover_missing_material_targets()

    if args.only.strip():
        allowed = {item.strip().replace("\\", "/") for item in args.only.split(",") if item.strip()}
        targets = [item for item in targets if item["path"].replace("\\", "/") in allowed]
    if args.limit > 0:
        targets = targets[: args.limit]

    results: list[dict[str, Any]] = []
    rescued = 0

    for item in targets:
        json_path = ROOT / item["path"]
        result = rescue_one(json_path)
        results.append(result)
        if result["status"] == "rescued":
            rescued += 1
            if args.apply:
                apply_rescue(result)

    summary = {
        "targetCount": len(targets),
        "rescuedCount": rescued,
        "unresolvedCount": len(targets) - rescued,
        "results": results,
    }
    OUT_REPORT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"目标缺口: {len(targets)}")
    print(f"可回填: {rescued}")
    print(f"仍未解决: {len(targets) - rescued}")
    print(f"报告写入: {OUT_REPORT.as_posix()}")
    if args.apply:
        print("已写回题库与 gap_rescue_pack 镜像。")
    else:
        print("dry-run: 未写回数据，使用 --apply 生效。")


if __name__ == "__main__":
    main()
