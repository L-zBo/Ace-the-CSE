"""
D-18a P2e-1.1 申论 material 现状审计

扫 src/data/xingce/shenlun/**/*.json，列出有 material 的题 + 按题型统计应该
有 material 的题数（duice/fenxi/guanche/guina 都应有，xiezuo 作文整篇靠原材料）。

产出 reports/audit_shenlun_material.json，给后续 PDF 抽材料救援用。
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    root = Path("src/data/shenlun")
    if not root.exists():
        raise SystemExit(f"申论数据目录不存在：{root}")

    total = 0
    has_material = 0
    has_material_qids: list[str] = []
    per_category_total: dict[str, int] = defaultdict(int)
    per_category_has_material: dict[str, int] = defaultdict(int)
    per_paper: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "has": 0})
    samples_with_material: list[dict] = []
    samples_without: list[dict] = []

    for json_path in sorted(root.rglob("*.json")):
        try:
            qs = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(qs, list):
            continue

        for q in qs:
            total += 1
            qid = q.get("id", "")
            category = q.get("category", "?")
            per_category_total[category] += 1
            # 推断 paperKey（去掉末尾 qNNN）
            parts = qid.split("-")
            paper_key = "-".join(parts[:-1]) if parts and parts[-1].startswith("q") else qid
            per_paper[paper_key]["total"] += 1

            material = q.get("material") or ""
            if material and len(material) > 10:  # 排除占位/极短
                has_material += 1
                per_category_has_material[category] += 1
                per_paper[paper_key]["has"] += 1
                has_material_qids.append(qid)
                if len(samples_with_material) < 3:
                    samples_with_material.append({
                        "id": qid,
                        "category": category,
                        "materialLen": len(material),
                        "materialHead": material[:120],
                    })
            else:
                if len(samples_without) < 5:
                    samples_without.append({
                        "id": qid,
                        "category": category,
                        "contentHead": (q.get("content") or "")[:80],
                    })

    out = {
        "totalShenlunQs": total,
        "hasMaterial": has_material,
        "missingMaterial": total - has_material,
        "missingRate": round((total - has_material) / total * 100, 2) if total else 0,
        "perCategory": [
            {
                "category": cat,
                "total": per_category_total[cat],
                "hasMaterial": per_category_has_material.get(cat, 0),
                "missingMaterial": per_category_total[cat] - per_category_has_material.get(cat, 0),
            }
            for cat in sorted(per_category_total)
        ],
        "perPaper": [
            {"paperKey": k, "total": v["total"], "hasMaterial": v["has"]}
            for k, v in sorted(per_paper.items())
        ],
        "samplesWithMaterial": samples_with_material,
        "samplesWithout": samples_without,
        "hasMaterialQids": has_material_qids,
    }

    out_path = Path("reports/audit_shenlun_material.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"扫描申论 {total} 题")
    print(f"  有 material：{has_material} 题")
    print(f"  缺 material：{out['missingMaterial']} 题 ({out['missingRate']}%)")
    print()
    print("按 category 分布（应该都有 material 但 xiezuo 作文可能整篇靠原材料）：")
    for row in out["perCategory"]:
        print(
            f"  {row['category']:10s} total={row['total']:3d}  has={row['hasMaterial']:3d}  miss={row['missingMaterial']:3d}"
        )
    print()
    print(f"涉及 paperKey 数：{len(out['perPaper'])}")
    print(f"报告写入：{out_path}")


if __name__ == "__main__":
    main()
