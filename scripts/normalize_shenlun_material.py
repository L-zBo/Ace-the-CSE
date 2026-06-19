#!/usr/bin/env python3
"""Normalize Shenlun paper records by splitting material from existing content.

This script does not invent any exam data. It only moves text that already exists
in each JSON record:

- material: the "given material" section extracted from content
- content: title/notice plus answer prompts, with material removed

Dry-run by default:
  python scripts/normalize_shenlun_material.py

Write changes:
  python scripts/normalize_shenlun_material.py --apply
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


ROOT = Path("src/data/shenlun")
REPORT = Path("reports/normalize_shenlun_material_preview.json")


MATERIAL_START_TERMS = [
    "【给定资料】",
    "【给定材料】",
    "【材料一】",
    "【材料 1】",
    "【资料一】",
    "【资料 1】",
    "二、给定资料",
    "二、给定材料",
    "二、资料",
    "二、材料",
    "二.给定资料",
    "二.给定材料",
    "二.资料",
    "二.材料",
    "二．给定资料",
    "二．给定材料",
    "二、阅读资料",
    "二.阅读资料",
    "二．阅读资料",
    "二、申论材料",
    "二.申论材料",
    "二．申论材料",
    "给定资料 1",
    "给定资料1",
    "给定材料 1",
    "给定材料1",
    "材料一",
    "材料 1",
    "材料1",
    "资料一",
    "资料 1",
    "资料1",
]

PROMPT_STRONG_TERMS = [
    "【作答要求】",
    "【作答任务】",
    "【问题一】",
    "【问题 1】",
    "【问题1】",
    "三、申论要求",
    "三、作答要求",
    "三、作答任务",
    "三、要求",
    "四、作答要求",
    "申论要求",
    "作答要求",
    "答题要求",
]

PROMPT_WEAK_TERMS = [
    "问题一",
    "问题 1",
    "问题1",
    "第一题",
    "第1题",
]

PROMPT_START_TERMS = PROMPT_STRONG_TERMS + PROMPT_WEAK_TERMS

ANSWER_MARKERS = [
    "参考答案与解析",
    "参考答案及解析",
    "【参考答案】",
    "参考答案",
    "答案解析",
    "参考例文",
    "参考范文",
]


def earliest(text: str, terms: Iterable[str], start: int = 0) -> tuple[int, str] | None:
    hits: list[tuple[int, str]] = []
    for term in terms:
        pos = text.find(term, start)
        if pos >= 0:
            hits.append((pos, term))
    if not hits:
        return None
    return min(hits, key=lambda item: item[0])


def is_section_boundary(text: str, pos: int, term: str) -> bool:
    """Avoid treating words like "材料一期" as a material section header."""
    if term.startswith(("材料", "资料")):
        prev = text[pos - 1] if pos > 0 else "\n"
        next_pos = pos + len(term)
        next_char = text[next_pos] if next_pos < len(text) else "\n"
        prev_ok = prev in "\n\r\f\t 　【([（"
        next_ok = next_char in "\n\r\f\t 　】]:：、.．)"
        return prev_ok and next_ok
    return True


def earliest_material_start(text: str) -> tuple[int, str] | None:
    hits: list[tuple[int, str]] = []
    for term in MATERIAL_START_TERMS:
        pos = text.find(term)
        while pos >= 0:
            if is_section_boundary(text, pos, term):
                hits.append((pos, term))
                break
            pos = text.find(term, pos + len(term))
    if not hits:
        return None
    return min(hits, key=lambda item: item[0])


def trim_answer_leak(prompt: str) -> tuple[str, str | None]:
    """Remove answer text that leaked into content after the prompt section."""
    hits: list[tuple[int, str]] = []
    for marker in ANSWER_MARKERS:
        pos = prompt.find(marker, 80)
        if pos >= 0:
            hits.append((pos, marker))
    if not hits:
        return prompt.strip(), None
    pos, marker = min(hits, key=lambda item: item[0])
    return prompt[:pos].strip(), marker


def split_material(content: str) -> dict | None:
    text = content.strip()
    start_hit = earliest_material_start(text)
    if not start_hit:
        return None

    material_start, start_term = start_hit
    strong_prompt_hits: list[tuple[int, str]] = []
    weak_prompt_hits: list[tuple[int, str]] = []
    # Avoid matching the notice sentence before real materials.
    min_prompt_start = material_start + 300
    for term in PROMPT_STRONG_TERMS:
        pos = text.find(term, min_prompt_start)
        while pos >= 0:
            strong_prompt_hits.append((pos, term))
            pos = text.find(term, pos + len(term))
    for term in PROMPT_WEAK_TERMS:
        pos = text.find(term, min_prompt_start)
        while pos >= 0:
            weak_prompt_hits.append((pos, term))
            pos = text.find(term, pos + len(term))

    prompt_hits = strong_prompt_hits or weak_prompt_hits
    if not prompt_hits:
        return None

    prompt_start, prompt_term = min(prompt_hits, key=lambda item: item[0])
    material = text[material_start:prompt_start].strip()
    prompt_raw = text[prompt_start:].strip()
    prompt, answer_marker = trim_answer_leak(prompt_raw)
    prefix = text[:material_start].strip()
    new_content = "\n\n".join(part for part in [prefix, prompt] if part).strip()

    if len(material) < 200 or len(prompt) < 50 or len(new_content) < 80:
        return None

    return {
        "material": material,
        "content": new_content,
        "startTerm": start_term,
        "promptTerm": prompt_term,
        "answerLeakTrimmedAt": answer_marker,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write normalized JSON files")
    args = parser.parse_args()

    if not ROOT.exists():
        raise SystemExit(f"Missing data root: {ROOT}")

    summary = {
        "totalRecords": 0,
        "alreadyHadMaterial": 0,
        "normalized": 0,
        "notSplittable": 0,
        "byCategory": {},
        "normalizedFiles": [],
        "notSplittableSamples": [],
    }
    changed_files: dict[Path, list] = {}

    for path in sorted(ROOT.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue

        changed = False
        for item in data:
            summary["totalRecords"] += 1
            category = item.get("category") or "unknown"
            cat_row = summary["byCategory"].setdefault(
                category,
                {"total": 0, "alreadyHadMaterial": 0, "normalized": 0, "notSplittable": 0},
            )
            cat_row["total"] += 1

            if (item.get("material") or "").strip():
                summary["alreadyHadMaterial"] += 1
                cat_row["alreadyHadMaterial"] += 1
                continue

            result = split_material(item.get("content") or "")
            if not result:
                summary["notSplittable"] += 1
                cat_row["notSplittable"] += 1
                if len(summary["notSplittableSamples"]) < 30:
                    summary["notSplittableSamples"].append(
                        {
                            "path": str(path).replace("\\", "/"),
                            "id": item.get("id"),
                            "category": category,
                            "contentHead": (item.get("content") or "")[:180],
                        }
                    )
                continue

            item["material"] = result["material"]
            item["content"] = result["content"]
            meta = item.setdefault("meta", {})
            meta["materialRescuedBy"] = "D23-content-normalization"
            meta["materialSource"] = "existing content field"
            meta["materialSplitTerms"] = {
                "start": result["startTerm"],
                "prompt": result["promptTerm"],
            }
            if result["answerLeakTrimmedAt"]:
                meta["contentAnswerLeakTrimmedAt"] = result["answerLeakTrimmedAt"]
            summary["normalized"] += 1
            cat_row["normalized"] += 1
            changed = True

        if changed:
            changed_files[path] = data
            summary["normalizedFiles"].append(str(path).replace("\\", "/"))

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.apply:
        for path, data in changed_files.items():
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"申论记录总数: {summary['totalRecords']}")
    print(f"已有 material: {summary['alreadyHadMaterial']}")
    print(f"可规范拆分: {summary['normalized']}")
    print(f"暂不可拆分: {summary['notSplittable']}")
    print(f"报告写入: {REPORT}")
    if args.apply:
        print(f"已写入文件数: {len(changed_files)}")
    else:
        print("dry-run: 未写入数据文件，使用 --apply 生效")


if __name__ == "__main__":
    main()
