#!/usr/bin/env python3
"""Compare PDF extraction engines on the same exam paper.

This script benchmarks the current in-repo extractor against external tools
such as Docling and MinerU. It uses the same downstream parser so we can
compare how well each engine's output supports question reconstruction.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from extract_questions import detect_sections, extract_pdf_text_best, parse_questions


SPECS_PATH = PROJECT_ROOT / "scripts" / "config" / "xingce_exam_specs.json"
QUESTION_ROOT = (
    PROJECT_ROOT
    / "material"
    / "【国考】2000-2025真题pdf"
    / "2000-2025国考行测PDF"
    / "行测-真题"
)
QUESTION_NUMBER_RE = re.compile(r"(?:^|\n|\x0c)\s*(\d{1,3})\s*(?:[\.．、]|\n)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare current extractor, Docling and MinerU on one PDF."
    )
    parser.add_argument("--source", default="national", choices=["national"])
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument(
        "--level",
        required=True,
        choices=["fushengjia", "dishi", "xingzhengzhifa"],
    )
    parser.add_argument("--question-pdf", help="Optional explicit PDF path.")
    parser.add_argument(
        "--engines",
        nargs="+",
        default=["current", "docling", "mineru"],
        choices=["current", "docling", "mineru"],
        help="Extraction engines to compare.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "tmp" / "pdf_engine_compare"),
        help="Directory for intermediate files and reports.",
    )
    return parser.parse_args()


def load_specs() -> dict[str, Any]:
    return json.loads(SPECS_PATH.read_text(encoding="utf-8"))


def get_expected_total(specs: dict[str, Any], source: str, year: int, level: str) -> int | None:
    return specs.get(source, {}).get(str(year), {}).get(level, {}).get("total")


def resolve_national_pdf(year: int, level: str) -> Path:
    level_keywords = {
        "fushengjia": ["副省级", "省级"],
        "dishi": ["地市级", "市地级"],
        "xingzhengzhifa": ["行政执法卷", "行政执法"],
    }
    matches = []
    for pdf_path in QUESTION_ROOT.glob(f"*{year}*.pdf"):
        name = pdf_path.name
        if any(keyword in name for keyword in level_keywords[level]):
            matches.append(pdf_path)

    if not matches:
        raise FileNotFoundError(f"未找到{year}年{level}对应PDF")

    matches.sort()
    return matches[0]


def detect_candidate_numbers(text: str) -> list[int]:
    numbers = sorted({int(match.group(1)) for match in QUESTION_NUMBER_RE.finditer(text)})
    return [number for number in numbers if 1 <= number <= 200]


def build_missing_numbers(found_numbers: list[int], expected_total: int | None) -> list[int]:
    if not expected_total:
        return []
    expected_numbers = set(range(1, expected_total + 1))
    return sorted(expected_numbers - set(found_numbers))


def summarize_extracted_text(text: str, expected_total: int | None) -> dict[str, Any]:
    candidate_numbers = detect_candidate_numbers(text)
    sections = detect_sections(text)
    parsed_questions = parse_questions(text, sections or [{"name": "全部", "category": "changshi", "start": 0, "end": len(text)}])

    option_hist = Counter()
    category_counts = Counter()
    parsed_numbers: list[int] = []
    for question in parsed_questions:
        option_count = len(question.get("options", []))
        option_hist[str(option_count)] += 1
        category_counts[str(question.get("category", "unknown"))] += 1
        if isinstance(question.get("number"), int):
            parsed_numbers.append(question["number"])

    parsed_numbers = sorted(set(parsed_numbers))

    return {
        "textLength": len(text),
        "candidateQuestionCount": len(candidate_numbers),
        "candidateMaxQuestionNumber": max(candidate_numbers) if candidate_numbers else None,
        "candidateMissingNumbers": build_missing_numbers(candidate_numbers, expected_total),
        "sectionCount": len(sections),
        "parsedQuestionCount": len(parsed_questions),
        "parsedMaxQuestionNumber": max(parsed_numbers) if parsed_numbers else None,
        "parsedMissingNumbers": build_missing_numbers(parsed_numbers, expected_total),
        "parsedFullOptionCount": sum(
            1 for question in parsed_questions if len(question.get("options", [])) == 4
        ),
        "parsedOptionHistogram": dict(sorted(option_hist.items(), key=lambda item: int(item[0]))),
        "categoryCounts": dict(sorted(category_counts.items())),
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def prepare_ascii_pdf_copy(pdf_path: Path, engine_dir: Path, alias: str) -> Path:
    target_path = engine_dir / f"{alias}.pdf"
    if not target_path.exists():
        shutil.copyfile(pdf_path, target_path)
    return target_path


def find_primary_text_file(output_dir: Path) -> Path | None:
    markdown_files = sorted(output_dir.rglob("*.md"), key=lambda path: path.stat().st_size, reverse=True)
    if markdown_files:
        return markdown_files[0]

    text_files = sorted(output_dir.rglob("*.txt"), key=lambda path: path.stat().st_size, reverse=True)
    if text_files:
        return text_files[0]

    return None


def run_command(command: list[str], workdir: Path, timeout_seconds: int = 1800) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=workdir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        check=False,
    )


def run_current_engine(pdf_path: Path, engine_dir: Path, expected_total: int | None) -> dict[str, Any]:
    text = extract_pdf_text_best(str(pdf_path))
    text_path = engine_dir / "current_extracted.txt"
    write_text(text_path, text)

    return {
        "engine": "current",
        "status": "ok",
        "command": None,
        "stdout": "",
        "stderr": "",
        "textPath": str(text_path.relative_to(PROJECT_ROOT)),
        "summary": summarize_extracted_text(text, expected_total),
    }


def run_docling_engine(pdf_path: Path, engine_dir: Path, expected_total: int | None) -> dict[str, Any]:
    local_pdf_path = prepare_ascii_pdf_copy(pdf_path, engine_dir, "docling_input")
    command = [
        "docling",
        "--from",
        "pdf",
        "--to",
        "md",
        "--output",
        str(engine_dir),
        "--pipeline",
        "standard",
        "--pdf-backend",
        "docling_parse",
        "--no-ocr",
        "--no-tables",
        str(local_pdf_path),
    ]
    result = run_command(command, PROJECT_ROOT)
    text_file = find_primary_text_file(engine_dir)
    text = text_file.read_text(encoding="utf-8", errors="replace") if text_file else ""

    return {
        "engine": "docling",
        "status": "ok" if result.returncode == 0 and text else "error",
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
        "textPath": str(text_file.relative_to(PROJECT_ROOT)) if text_file else None,
        "summary": summarize_extracted_text(text, expected_total) if text else None,
    }


def run_mineru_engine(pdf_path: Path, engine_dir: Path, expected_total: int | None) -> dict[str, Any]:
    local_pdf_path = prepare_ascii_pdf_copy(pdf_path, engine_dir, "mineru_input")
    command = [
        "mineru",
        "-p",
        str(local_pdf_path),
        "-o",
        str(engine_dir),
        "-b",
        "pipeline",
        "-m",
        "txt",
        "-l",
        "ch",
        "-f",
        "false",
        "-t",
        "false",
    ]
    result = run_command(command, PROJECT_ROOT)
    text_file = find_primary_text_file(engine_dir)
    text = text_file.read_text(encoding="utf-8", errors="replace") if text_file else ""

    return {
        "engine": "mineru",
        "status": "ok" if result.returncode == 0 and text else "error",
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
        "textPath": str(text_file.relative_to(PROJECT_ROOT)) if text_file else None,
        "summary": summarize_extracted_text(text, expected_total) if text else None,
    }


def build_markdown_report(
    pdf_path: Path,
    expected_total: int | None,
    results: list[dict[str, Any]],
) -> str:
    lines = [
        "# PDF引擎对照报告",
        "",
        f"- PDF: `{pdf_path}`",
        f"- 期望题数: `{expected_total}`",
        "",
    ]

    for result in results:
        lines.append(f"## {result['engine']}")
        lines.append("")
        lines.append(f"- 状态: `{result['status']}`")
        if result.get("returncode") is not None:
            lines.append(f"- 返回码: `{result['returncode']}`")
        if result.get("textPath"):
            lines.append(f"- 主文本文件: `{result['textPath']}`")

        summary = result.get("summary")
        if summary:
            lines.append(f"- 文本长度: `{summary['textLength']}`")
            lines.append(f"- 候选题号数: `{summary['candidateQuestionCount']}`")
            lines.append(f"- 候选最大题号: `{summary['candidateMaxQuestionNumber']}`")
            lines.append(f"- 解析题数: `{summary['parsedQuestionCount']}`")
            lines.append(f"- 解析最大题号: `{summary['parsedMaxQuestionNumber']}`")
            lines.append(f"- 4选项题数: `{summary['parsedFullOptionCount']}`")
            lines.append(f"- 选项分布: `{json.dumps(summary['parsedOptionHistogram'], ensure_ascii=False)}`")
            lines.append(f"- 分类分布: `{json.dumps(summary['categoryCounts'], ensure_ascii=False)}`")
            lines.append(f"- 候选缺号: `{summary['candidateMissingNumbers'][:20]}`")
            lines.append(f"- 解析缺号: `{summary['parsedMissingNumbers'][:20]}`")

        stderr = (result.get("stderr") or "").strip()
        if stderr:
            lines.append("- 错误摘录:")
            lines.append("```text")
            lines.append(stderr[:2000])
            lines.append("```")

        lines.append("")

    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    specs = load_specs()
    expected_total = get_expected_total(specs, args.source, args.year, args.level)

    if args.question_pdf:
        pdf_path = Path(args.question_pdf).resolve()
    else:
        pdf_path = resolve_national_pdf(args.year, args.level)

    output_dir = Path(args.output_dir).resolve() / f"{args.source}_{args.year}_{args.level}"
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for engine in args.engines:
        engine_dir = output_dir / engine
        engine_dir.mkdir(parents=True, exist_ok=True)

        if engine == "current":
            results.append(run_current_engine(pdf_path, engine_dir, expected_total))
        elif engine == "docling":
            results.append(run_docling_engine(pdf_path, engine_dir, expected_total))
        elif engine == "mineru":
            results.append(run_mineru_engine(pdf_path, engine_dir, expected_total))

    report = {
        "pdfPath": str(pdf_path),
        "expectedTotal": expected_total,
        "results": results,
    }
    report_json_path = output_dir / "report.json"
    report_md_path = output_dir / "report.md"
    report_json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md_path.write_text(build_markdown_report(pdf_path, expected_total, results), encoding="utf-8")

    print(json.dumps({"reportJson": str(report_json_path), "reportMd": str(report_md_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
