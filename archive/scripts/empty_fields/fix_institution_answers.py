"""
事业编答案 PDF 是 2018-2024 多年合并。按"20XX 年 X 月"切片后单独解析，
然后按题号后缀写回对应 JSON 的 answer / explanation。

用法：
    python scripts/fix_institution_answers.py           # 全 A-E × 2020/22/23/24 跑
    python scripts/fix_institution_answers.py --dry-run
    python scripts/fix_institution_answers.py --levels A,C --years 2024
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_questions import parse_answer_pdf  # noqa: E402

MATERIAL_ROOT = Path("material/【事业编】事业单位联考历年真题")
DATA_ROOT = Path("src/data/xingce")
ALL_LEVELS = ["A", "B", "C", "E"]  # D 类当前未接入
DEFAULT_YEARS = [2020, 2022, 2023, 2024]


def load_answer_pdf_text(level: str) -> str:
    pdf = MATERIAL_ROOT / f"{level}类/职测/2018年-2024年事业单位联考职测（{level}类）笔试真题答案解析.pdf"
    if not pdf.exists():
        raise FileNotFoundError(pdf)
    with pdfplumber.open(pdf) as p:
        return "\n".join((pg.extract_text() or "") for pg in p.pages)


def slice_by_year(text: str) -> dict[int, str]:
    """
    按 '20XX 年 X 月[...]事业单位' 切分多年合并 PDF。
    PDF 头部（pos 0）没有此分隔符，属于最新年（这里是 2024）。
    同一年出现多场次（5 月+10 月）合并拼接。
    """
    markers: list[tuple[int, int]] = []
    for m in re.finditer(r"(20\d{2})\s*年\s*\d+\s*月[^\n]{0,40}(?:事业单位|综合|职业)", text):
        markers.append((m.start(), int(m.group(1))))
    markers.sort()

    # 头段（位置 0 到第一个 marker 之前）= 最新年份。事业编 PDF 按时间倒序排列，
    # 头段的紧邻 marker 年份 + 1 即为头段年份。
    if markers and markers[0][0] > 0:
        head_year = markers[0][1] + 1  # 最新年
        markers.insert(0, (0, head_year))

    slices: dict[int, str] = {}
    for i, (pos, year) in enumerate(markers):
        end = markers[i + 1][0] if i + 1 < len(markers) else len(text)
        slices.setdefault(year, "")
        slices[year] += text[pos:end] + "\n"
    return slices


def json_num(qid: str) -> int:
    """id 'institution-xingce-changshi-2024-a-001' → 1"""
    return int(qid.rsplit("-", 1)[-1])


def inject_answers(level: str, year: int, answers: dict[int, dict], dry_run: bool) -> tuple[int, int, bool]:
    """把 {题号: {answer, explanation}} 注入到该 (year, level) 全分类的 JSON。
    若任一 JSON 含重复 id（5月/10月场次合并碰撞），整个 (year, level) 跳过以防错注入。
    返回 (填充字段数, 总题数, 是否因碰撞跳过)"""
    from collections import Counter
    level_lower = level.lower()
    files = sorted(glob.glob(str(DATA_ROOT / "**" / f"institution_{year}_{level_lower}.json"), recursive=True))

    # 先查所有 JSON 是否存在 id 碰撞
    dup_total = 0
    for f in files:
        ids = [q["id"] for q in json.load(open(f, encoding="utf-8"))]
        dup_total += sum(c - 1 for _, c in Counter(ids).items() if c > 1)
    if dup_total > 0:
        return 0, 0, True

    filled = 0
    total = 0
    for f in files:
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)
        changed = False
        for q in data:
            total += 1
            num = json_num(q["id"])
            if num not in answers:
                continue
            a = answers[num]
            if a["answer"] and not q.get("answer"):
                q["answer"] = a["answer"]
                filled += 1
                changed = True
            if a["explanation"] and not q.get("explanation"):
                q["explanation"] = a["explanation"]
                changed = True
        if changed and not dry_run:
            with open(f, "w", encoding="utf-8") as fp:
                json.dump(data, fp, ensure_ascii=False, indent=2)
    return filled, total, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels", default=",".join(ALL_LEVELS), help="A,B,C,E 子集")
    ap.add_argument("--years", default=",".join(str(y) for y in DEFAULT_YEARS))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    levels = [x.strip().upper() for x in args.levels.split(",") if x.strip()]
    years = [int(x) for x in args.years.split(",") if x.strip()]

    summary = []
    for lv in levels:
        try:
            text = load_answer_pdf_text(lv)
        except FileNotFoundError as e:
            print(f"[SKIP] {e}")
            continue
        slices = slice_by_year(text)
        print(f"\n== {lv} 类 == 年份切片：{sorted(slices.keys())}")
        for y in years:
            if y not in slices:
                print(f"  {y}: 未找到切片")
                continue
            ans = parse_answer_pdf(slices[y])
            has = sum(1 for v in ans.values() if v["answer"])
            print(f"  {y}: parse 出 {len(ans)} 题号, {has} 有答案（切片 {len(slices[y])} 字符）")
            filled, total, skipped = inject_answers(lv, y, ans, args.dry_run)
            if skipped:
                print(f"    [跳过] JSON 含重复 id（场次碰撞），建议重抽题 PDF 分拆 5/10 月")
            else:
                print(f"    注入: 填充 {filled} 字段 / JSON 总 {total} 题")
            summary.append((lv, y, has, filled, total, skipped))

    print("\n" + "=" * 60)
    print("汇总:")
    for lv, y, has, filled, total, skipped in summary:
        tag = "[碰撞跳过]" if skipped else ""
        print(f"  {lv} 类 {y}: PDF 答案 {has} / 填入 {filled} / 总题 {total} {tag}")
    if args.dry_run:
        print("\n[DRY RUN] 未写盘")


if __name__ == "__main__":
    main()
