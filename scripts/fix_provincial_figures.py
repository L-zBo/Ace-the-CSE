#!/usr/bin/env python3
"""D-3: 省考缺图通用补抽器。

从省考真题 PDF (非答案 PDF) 抽题号区间渲染 PNG。
复用 fix_question_figures.py 抽图逻辑 + fix_provincial_answers.py PDF 查找。
"""
from __future__ import annotations
import argparse
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import fitz  # type: ignore[import-not-found]
from fix_provincial_answers import PROVINCE_MAP  # type: ignore[import-not-found]
from fix_question_figures import find_qn_position, extract_one  # type: ignore[import-not-found]


def find_provincial_question_pdf(province_pinyin: str, year: str) -> Path | None:
    """找省考真题 PDF (非答案/解析)。"""
    cn = PROVINCE_MAP.get(province_pinyin)
    if not cn:
        return None
    cn_bytes = cn.encode("utf-8")
    year_bytes = year.encode("utf-8")
    for p in glob.glob("material/**/*.pdf", recursive=True):
        if "【省考】" not in p:
            continue
        if "行测" not in p:
            continue
        # 真题 PDF: 不含"答案"和"解析"
        if "答案" in p or "解析" in p:
            continue
        pb = p.encode("utf-8")
        if year_bytes not in pb or cn_bytes not in pb:
            continue
        return Path(p)
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exam", help="只跑指定 examKey")
    args = ap.parse_args()

    # 读 audit_figures.py 的产物（早先落在仓库根，现已统一进 reports/）
    audit = json.loads((ROOT / "reports" / "audit_figures.json").read_text(encoding="utf-8"))
    targets: dict[str, list[int]] = {}
    for m in audit["missing"]:
        ex = m["exam"]
        if not ex.startswith("provincial_"):
            continue
        if args.exam and ex != args.exam:
            continue
        targets.setdefault(ex, []).append(m["qn"])

    ok = fail = 0
    for exam, qns in sorted(targets.items()):
        parts = exam.split("_")
        if len(parts) < 3:
            continue
        province = parts[1]
        year = parts[2]
        pdf = find_provincial_question_pdf(province, year)
        if not pdf:
            print(f"[{exam}] ❌ 未找到真题 PDF")
            fail += len(qns)
            continue
        for qn in sorted(qns):
            out = ROOT / "public" / "img" / "questions" / exam / f"q{qn:03d}.png"
            success, msg = extract_one(pdf, qn, out)
            tag = "OK " if success else "FAIL"
            print(f"  [{tag}] {exam} q{qn:03d}: {msg}")
            if success:
                ok += 1
            else:
                fail += 1

    print(f"\n合计: ok={ok}, fail={fail}")


if __name__ == "__main__":
    main()
