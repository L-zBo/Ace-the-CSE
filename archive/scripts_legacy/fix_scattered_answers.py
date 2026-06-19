#!/usr/bin/env python3
"""C阶段散点答案修复：扫 2015-2022 国考 11 卷剩余 23 ans + 10 exp 字段。

兼容两种 PDF 答案格式：
  - 主流："故正确答案为X。" + "\\nN\\n" 题号边界（2015-2021 + 2023）
  - 异类："{N}.解析" 题号边界 + "因此，选择X选项" 答案标志（2022_fushengjia 格式）

仅注入缺失字段，不覆写已有内容。
"""
from __future__ import annotations
import glob
import json
import re
import sys
from pathlib import Path

import fitz  # type: ignore[import-not-found]


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data" / "xingce"

# 11 卷散点：(year, level, level_keyword_in_filename, total_qs)
TARGETS = [
    ("2015", "dishi", "地市级", 130),
    ("2015", "fushengjia", "副省级", 135),
    ("2016", "dishi", "地市级", 130),
    ("2016", "fushengjia", "副省级", 135),
    ("2017", "fushengjia", "副省级", 135),
    ("2018", "fushengjia", "副省级", 135),
    ("2019", "dishi", "地市级", 130),
    ("2019", "fushengjia", "副省级", 135),
    ("2020", "dishi", "地市级", 130),
    ("2021", "dishi", "地市级", 130),
    ("2022", "fushengjia", "副省级", 135),
]

# 早年 PDF 文件名命名差异：
#   fushengjia: "副省级"（2015-2018, 2020-2024）/ "省部级"（2019）
#   dishi:      "地市级"（2018-2024）/ "市地级"（2015-2017, 2019）
FSJ_KEYWORDS = ["副省级", "省部级", "省级"]
DISHI_KEYWORDS = ["地市级", "市地级"]


def find_pdf(year: str, level_kw: str) -> Path | None:
    if level_kw in DISHI_KEYWORDS:
        keywords = DISHI_KEYWORDS
    elif level_kw in FSJ_KEYWORDS:
        keywords = FSJ_KEYWORDS
    else:
        keywords = [level_kw]
    for p in glob.glob(f"material/**/{year}*行测*.pdf", recursive=True):
        if "国考" not in p and "【国考】" not in p:
            continue
        if "答案" not in p and "解析" not in p:
            continue
        for kw in keywords:
            if kw.encode("utf-8") in p.encode("utf-8"):
                return Path(p)
    return None


HEAD_OLD = re.compile(r"故正确答案为\s*[A-D]+[。.]?(\d{1,3})")
HEAD_NL = re.compile(r"(?:^|\n)(\d{1,3})\n")
HEAD_DOT = re.compile(r"(?:^|\n)\s*(\d{1,3})\s*[、,，.．]")
HEAD_NEW = re.compile(r"(?:^|\n)\s*(\d{1,3})[.．、,，]\s*解析")
ANS_OLD = re.compile(r"故正确答案?[为选是]?[:：]?\s*([A-D]+)(?=[\s，,。.、\)）])")
ANS_NEW = re.compile(r"因此[，,]?\s*选择\s*([A-D]+)\s*选项")
ANS_PAREN = re.compile(r"(?:正确答案|参考答案|答案)[：:]\s*([A-D])(?=[\s，。、])")


def extract_blocks(pdf_path: Path, total: int) -> dict[int, dict[str, str]]:
    doc = fitz.open(pdf_path)
    text = "\n".join(doc[i].get_text() for i in range(doc.page_count))

    boundaries: list[tuple[int, int]] = []
    for m in HEAD_OLD.finditer(text):
        qn = int(m.group(1))
        if 1 <= qn <= total:
            boundaries.append((qn, m.start(1)))
    for m in HEAD_NL.finditer(text):
        qn = int(m.group(1))
        if 1 <= qn <= total:
            boundaries.append((qn, m.start(1)))
    for m in HEAD_DOT.finditer(text):
        qn = int(m.group(1))
        if 1 <= qn <= total:
            boundaries.append((qn, m.start(1)))
    for m in HEAD_NEW.finditer(text):
        qn = int(m.group(1))
        if 1 <= qn <= total:
            boundaries.append((qn, m.start(1)))

    boundaries.sort(key=lambda x: x[1])
    seen: set[int] = set()
    cleaned: list[tuple[int, int]] = []
    last_qn = 0
    for qn, pos in boundaries:
        if qn in seen or qn < last_qn:
            continue
        seen.add(qn)
        cleaned.append((qn, pos))
        last_qn = qn

    blocks: dict[int, dict[str, str]] = {}
    for i, (qn, pos) in enumerate(cleaned):
        end = cleaned[i + 1][1] - 1 if i + 1 < len(cleaned) else len(text)
        block_start = pos + len(str(qn))
        block = text[block_start:end].strip()

        # 答案：多模式兜底
        ans_m = ANS_OLD.search(block) or ANS_NEW.search(block) or ANS_PAREN.search(block)
        answer = ans_m.group(1) if ans_m else ""

        blocks[qn] = {"answer": answer, "explanation": block.strip()}

    return blocks


def inject(year: str, level: str, blocks: dict[int, dict[str, str]]) -> tuple[int, int, int]:
    fname = f"national_{year}_{level}.json"
    touched = ans_filled = exp_filled = 0
    for module_dir in sorted(DATA.iterdir()):
        if not module_dir.is_dir():
            continue
        path = module_dir / fname
        if not path.exists():
            continue
        questions = json.loads(path.read_text(encoding="utf-8"))
        modified = False
        for q in questions:
            try:
                qn = int(str(q.get("id", "")).split("-")[-1])
            except ValueError:
                continue
            if qn not in blocks:
                continue
            blk = blocks[qn]
            if not q.get("answer") and blk["answer"]:
                q["answer"] = blk["answer"]
                ans_filled += 1
                modified = True
            if (
                not (q.get("explanation") or q.get("analysis"))
                and blk["explanation"]
            ):
                q["explanation"] = blk["explanation"]
                exp_filled += 1
                modified = True
        if modified:
            path.write_text(
                json.dumps(questions, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            touched += 1
    return touched, ans_filled, exp_filled


def main() -> None:
    grand_ans = grand_exp = 0
    for year, level, level_kw, total in TARGETS:
        pdf = find_pdf(year, level_kw)
        if not pdf:
            print(f"[{year}_{level}] ❌ 未找到 PDF", file=sys.stderr)
            continue
        blocks = extract_blocks(pdf, total)
        with_ans = sum(1 for b in blocks.values() if b["answer"])
        touched, ans, exp = inject(year, level, blocks)
        ok = "OK" if blocks else "FAIL"
        print(
            f"[{year}_{level}] {ok} 切 {len(blocks)}/{total} 块 (含答案 {with_ans}) "
            f"→ touched {touched} 文件, +{ans} ans, +{exp} exp"
        )
        grand_ans += ans
        grand_exp += exp
    print(f"\n合计：+{grand_ans} answer, +{grand_exp} explanation")


if __name__ == "__main__":
    main()
