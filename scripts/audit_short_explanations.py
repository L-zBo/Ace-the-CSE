"""
D-18a P2d-1.1 短解析审计

扫 src/data/xingce/**/*.json，找 explanation 长度 < 阈值（默认 20 字）的题。
产出 reports/audit_short_explanations.json，给后续 vision OCR / WebSearch 救援用。

用法：
    python scripts/audit_short_explanations.py
    python scripts/audit_short_explanations.py --threshold 30
    python scripts/audit_short_explanations.py --out reports/x.json
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default="src/data/xingce",
        help="行测数据根目录（默认 src/data/xingce）",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=20,
        help="解析长度阈值（< threshold 视为短解析，默认 20 字）",
    )
    parser.add_argument(
        "--out",
        default="reports/audit_short_explanations.json",
        help="输出 JSON 路径",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        raise SystemExit(f"数据目录不存在：{root}")

    rows: list[dict[str, object]] = []
    per_paper: dict[str, int] = defaultdict(int)
    per_category: dict[str, int] = defaultdict(int)
    total_qs = 0
    empty_count = 0

    for json_path in sorted(root.rglob("*.json")):
        # 跳过申论目录
        if "shenlun" in json_path.parts:
            continue
        try:
            qs = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            print(f"⚠️  读不动 {json_path}: {e}")
            continue
        if not isinstance(qs, list):
            continue

        for q in qs:
            total_qs += 1
            qid = q.get("id", "")
            expl = q.get("explanation") or ""
            expl_len = len(expl)
            if expl_len == 0:
                empty_count += 1
            if expl_len < args.threshold:
                paper_key = "-".join(qid.split("-")[:5]) if qid else json_path.stem
                category = q.get("category", "?")
                per_paper[paper_key] += 1
                per_category[category] += 1
                rows.append({
                    "id": qid,
                    "paperKey": paper_key,
                    "category": category,
                    "explanationLen": expl_len,
                    "explanation": expl,
                    "answer": q.get("answer", ""),
                    "isUnanswerable": q.get("isUnanswerable", False),
                    "file": str(json_path.relative_to(root.parent.parent)),
                })

    # 排序：先按 paperKey，再按 qn
    rows.sort(key=lambda r: (r["paperKey"], r["id"]))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_data = {
        "threshold": args.threshold,
        "totalScanned": total_qs,
        "emptyExplanation": empty_count,
        "shortExplanation": len(rows),
        "shortRate": round(len(rows) / total_qs * 100, 2) if total_qs else 0,
        "perPaper": dict(sorted(per_paper.items(), key=lambda x: -x[1])),
        "perCategory": dict(sorted(per_category.items(), key=lambda x: -x[1])),
        "rows": rows,
    }
    out_path.write_text(
        json.dumps(out_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"扫描 {total_qs} 题，发现 {len(rows)} 题解析 < {args.threshold} 字（{out_data['shortRate']}%）")
    print(f"  其中 explanation 完全为空：{empty_count} 题")
    print(f"  报告写入：{out_path}")
    print()
    print("Top 10 paperKey 短解析最多：")
    for paper_key, cnt in list(out_data["perPaper"].items())[:10]:
        print(f"  {cnt:3d}  {paper_key}")
    print()
    print("按 category 分布：")
    for cat, cnt in out_data["perCategory"].items():
        print(f"  {cnt:3d}  {cat}")


if __name__ == "__main__":
    main()
