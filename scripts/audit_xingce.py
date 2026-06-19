#!/usr/bin/env python3
"""统一审计行测客观题数据，并按需生成Manifest。"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "src" / "data" / "xingce"
META_ROOT = PROJECT_ROOT / "src" / "data" / "meta"
SPECS_PATH = PROJECT_ROOT / "scripts" / "config" / "xingce_exam_specs.json"
EXCEPTIONS_PATH = PROJECT_ROOT / "scripts" / "config" / "xingce_option_exceptions.json"
QUESTION_NUMBER_RE = re.compile(r"-(\d{1,3})$")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计行测客观题数据")
    parser.add_argument("--source", default="national", help="考试来源，如national")
    parser.add_argument("--year", help="只审计指定年份")
    parser.add_argument(
        "--write-manifest",
        action="store_true",
        help="生成src/data/meta/xingce_exam_manifest.json",
    )
    parser.add_argument("--report-json", help="输出结构化审计报告JSON路径")
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def flatten_exception_ids(raw: Any) -> set[str]:
    allowed: set[str] = set()
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str):
                allowed.add(item)
            elif isinstance(item, dict) and "id" in item:
                allowed.add(str(item["id"]))
    elif isinstance(raw, dict):
        for value in raw.values():
            allowed.update(flatten_exception_ids(value))
    return allowed


def question_number(question: dict[str, Any]) -> int | None:
    question_id = str(question.get("id", ""))
    match = QUESTION_NUMBER_RE.search(question_id)
    if not match:
        return None
    return int(match.group(1))


def find_exam_files(source: str) -> list[Path]:
    files: list[Path] = []
    for module_dir in DATA_ROOT.iterdir():
        if not module_dir.is_dir():
            continue
        files.extend(sorted(module_dir.glob(f"{source}_*.json")))
    return files


def expected_exam(specs: dict[str, Any], source: str, year: str, level: str) -> dict[str, Any] | None:
    return specs.get(source, {}).get(year, {}).get(level)


def summarize_exam(
    source: str,
    year: str,
    level: str,
    questions: list[dict[str, Any]],
    specs: dict[str, Any],
    exceptions: dict[str, Any],
) -> dict[str, Any]:
    exam_spec = expected_exam(specs, source, year, level)
    issues: list[dict[str, Any]] = []
    module_counts = Counter(str(q.get("category", "unknown")) for q in questions)
    actual_total = len(questions)
    expected_total = exam_spec["total"] if exam_spec else None
    expected_modules = exam_spec["modules"] if exam_spec else {}
    exam_exceptions = flatten_exception_ids(
        exceptions.get(source, {}).get(year, {}).get(level, [])
    )

    if exam_spec is None:
        issues.append(
            {
                "type": "missing_spec",
                "message": f"缺少规则：{source}/{year}/{level}",
            }
        )
    else:
        if actual_total != expected_total:
            issues.append(
                {
                    "type": "unexpected_total",
                    "expected": expected_total,
                    "actual": actual_total,
                }
            )

        all_modules = sorted(set(module_counts) | set(expected_modules))
        for module in all_modules:
            actual = module_counts.get(module, 0)
            expected = expected_modules.get(module, 0)
            if actual != expected:
                issues.append(
                    {
                        "type": "unexpected_module_distribution",
                        "module": module,
                        "expected": expected,
                        "actual": actual,
                    }
                )

    seen_numbers: set[int] = set()
    duplicates: set[int] = set()
    invalid_number_ids: list[str] = []
    for question in questions:
        number = question_number(question)
        if number is None:
            invalid_number_ids.append(str(question.get("id", "")))
            continue
        if number in seen_numbers:
            duplicates.add(number)
        seen_numbers.add(number)

    if invalid_number_ids:
        issues.append(
            {
                "type": "invalid_question_number",
                "ids": invalid_number_ids,
            }
        )

    if duplicates:
        issues.append(
            {
                "type": "duplicate_questions",
                "numbers": sorted(duplicates),
            }
        )

    if expected_total:
        expected_numbers = set(range(1, expected_total + 1))
        missing_numbers = sorted(expected_numbers - seen_numbers)
        if missing_numbers:
            issues.append(
                {
                    "type": "missing_questions",
                    "numbers": missing_numbers,
                }
            )

    invalid_options: list[dict[str, Any]] = []
    for question in questions:
        question_id = str(question.get("id", ""))
        if question_id in exam_exceptions:
            continue
        option_count = len(question.get("options", []) or [])
        if option_count != 4:
            invalid_options.append(
                {
                    "id": question_id,
                    "number": question_number(question),
                    "optionCount": option_count,
                }
            )

    if invalid_options:
        issues.append(
            {
                "type": "invalid_option_count",
                "items": invalid_options,
            }
        )

    return {
        "key": f"{source}_{year}_{level}",
        "source": source,
        "year": year,
        "level": level,
        "actualTotal": actual_total,
        "expectedTotal": expected_total,
        "actualModules": dict(sorted(module_counts.items())),
        "expectedModules": expected_modules,
        "issues": issues,
        "issueCount": len(issues),
        "ready": len(issues) == 0,
    }


def audit(source: str, year_filter: str | None) -> dict[str, Any]:
    specs = load_json(SPECS_PATH)
    exceptions = load_json(EXCEPTIONS_PATH)
    exam_questions: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for file_path in find_exam_files(source):
        questions = load_json(file_path)
        for question in questions:
            year = str(question.get("year", "unknown"))
            level = str(question.get("level", "unknown"))
            if year_filter and year != year_filter:
                continue
            exam_questions[(year, level)].append(question)

    exams = [
        summarize_exam(source, year, level, questions, specs, exceptions)
        for (year, level), questions in sorted(exam_questions.items())
    ]
    issue_count = sum(exam["issueCount"] for exam in exams)

    return {
        "generatedAt": now_iso(),
        "source": source,
        "filters": {"year": year_filter},
        "summary": {
            "examCount": len(exams),
            "issueCount": issue_count,
            "readyCount": sum(1 for exam in exams if exam["ready"]),
        },
        "exams": exams,
    }


def manifest_payload(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "generatedAt": report["generatedAt"],
        "source": report["source"],
        "exams": [
            {
                "key": exam["key"],
                "source": exam["source"],
                "year": exam["year"],
                "level": exam["level"],
                "expectedTotal": exam["expectedTotal"],
                "actualTotal": exam["actualTotal"],
                "expectedModules": exam["expectedModules"],
                "actualModules": exam["actualModules"],
                "issueCount": exam["issueCount"],
                "ready": exam["ready"],
            }
            for exam in report["exams"]
        ],
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    report = audit(args.source, args.year)

    if args.report_json:
        write_json((PROJECT_ROOT / args.report_json).resolve(), report)

    if args.write_manifest:
        META_ROOT.mkdir(parents=True, exist_ok=True)
        write_json(META_ROOT / "xingce_exam_manifest.json", manifest_payload(report))

    print(json.dumps(report["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
