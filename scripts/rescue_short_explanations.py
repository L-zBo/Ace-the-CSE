"""
D-18a P2d-1.2 短解析最低救援

针对扫出来的 167 题短解析，分类处理：

A 类（约 20 题）："【答案】X" 仅含答案 → 扩成"【答案】X\n\n解析：原 PDF 解析
  部分缺失，可参考相关知识点推导。正确答案为 X。" 最低救援，避免空白
B 类：OCR 错乱片段（"= 1。根据公式：时间 =" 等乱码）→ 留 D-18b vision 救援
C 类：广西 2021 整套数据坏（"、B" 等）→ 整套数据来源问题，留 D-18b PDF 重抽

所有改动加 meta.shortExplanationAuditedAt + meta.shortExplanationOrigLen，
便于 D-18b 进一步救援时定位。

用法：
    python scripts/rescue_short_explanations.py
    python scripts/rescue_short_explanations.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path


# 识别"仅有答案"模式：【答案】X / 答案：X / 答案 X
ANSWER_ONLY_RE = re.compile(
    r"^\s*[【\[]?答案[】\]]?\s*[:：]?\s*([ABCDE])\s*[。.]?\s*$"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="src/data/xingce")
    parser.add_argument("--threshold", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true", help="只打印不写盘")
    args = parser.parse_args()

    root = Path(args.root)
    today = date.today().isoformat()

    counts = {"A_answer_only": 0, "B_ocr_garbage": 0, "C_dirty_paper": 0, "files_touched": 0}
    examples: dict[str, list[str]] = {"A": [], "B": [], "C": []}

    for json_path in sorted(root.rglob("*.json")):
        if "shenlun" in json_path.parts:
            continue
        try:
            qs = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(qs, list):
            continue

        touched = False
        for q in qs:
            expl = q.get("explanation") or ""
            if len(expl) >= args.threshold:
                continue

            orig_len = len(expl)
            qid = q.get("id", "")
            paper_key = "-".join(qid.split("-")[:5]) if qid else json_path.stem
            is_guangxi_2021 = (
                "guangxi-xingce" in paper_key and paper_key.endswith("-2021")
            )

            meta = q.get("meta") or {}
            meta["shortExplanationAuditedAt"] = today
            meta["shortExplanationOrigLen"] = orig_len

            # 分类处理
            m = ANSWER_ONLY_RE.match(expl.replace("\n", " "))
            if m:
                # A 类：扩成最低救援
                ans_letter = m.group(1)
                new_expl = (
                    f"【答案】{ans_letter}\n\n"
                    "解析：原 PDF 解析部分缺失，可参考相关知识点推导，"
                    f"故正确答案为 {ans_letter}。"
                )
                q["explanation"] = new_expl
                meta["shortExplanationRescueClass"] = "A"
                meta["shortExplanationRescuedBy"] = "D18a-min-rescue"
                counts["A_answer_only"] += 1
                if len(examples["A"]) < 3:
                    examples["A"].append(qid)
            elif is_guangxi_2021:
                # C 类：广西 2021 整套数据坏，标记但不改 explanation
                meta["shortExplanationRescueClass"] = "C"
                meta["shortExplanationDeferTo"] = "D18b-pdf-reextract"
                counts["C_dirty_paper"] += 1
                if len(examples["C"]) < 3:
                    examples["C"].append(qid)
            else:
                # B 类：OCR 乱码片段，标记但不改 explanation
                meta["shortExplanationRescueClass"] = "B"
                meta["shortExplanationDeferTo"] = "D18b-vision-ocr"
                counts["B_ocr_garbage"] += 1
                if len(examples["B"]) < 3:
                    examples["B"].append(qid)

            q["meta"] = meta
            touched = True

        if touched and not args.dry_run:
            json_path.write_text(
                json.dumps(qs, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            counts["files_touched"] += 1

    print("救援分类统计：")
    print(f"  A 类 仅有答案（扩成最低救援）：{counts['A_answer_only']}  例：{examples['A']}")
    print(f"  B 类 OCR 乱码（标记，留 D-18b vision）：{counts['B_ocr_garbage']}  例：{examples['B']}")
    print(f"  C 类 整套数据坏（广西 2021，留 D-18b PDF 重抽）：{counts['C_dirty_paper']}  例：{examples['C']}")
    print(f"  改动文件数：{counts['files_touched']}")
    if args.dry_run:
        print("  [dry-run] 未写盘")


if __name__ == "__main__":
    main()
