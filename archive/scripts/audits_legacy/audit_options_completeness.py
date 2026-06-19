#!/usr/bin/env python3
"""
审计行测全库选项完整度。
统计每卷 options.length == 4 / < 4 / == 0 的题数，
排除合法 2 选项判断题（对/错）和图形推理图形题。
产出 options_completeness_audit.md。
"""
import json
import os
import sys
from glob import glob
from collections import defaultdict


DATA_DIR = "src/data/xingce"


def is_valid_2opt(q):
    opts = q.get("options", [])
    if len(opts) != 2:
        return False
    labels = [o.get("content", "").strip() for o in opts]
    return set(labels) <= {"正确", "错误", "对", "错"}


def is_figure_q(q):
    c = q.get("content", "")
    return any(k in c for k in ("图形选项", "[图形选项]", "见图", "[见图]"))


def audit():
    # {exam_key: {"total": n, "ex4": n, "lt4": n, "zero": n, "skip": n}}
    stats = defaultdict(lambda: {"total": 0, "ex4": 0, "lt4": 0, "zero": 0, "skip": 0})

    for f in sorted(glob(os.path.join(DATA_DIR, "**/*.json"), recursive=True)):
        ek = os.path.basename(f).replace(".json", "")
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        if not isinstance(data, list):
            continue
        for q in data:
            s = stats[ek]
            s["total"] += 1
            if is_valid_2opt(q) or is_figure_q(q):
                s["skip"] += 1
                continue
            opts = q.get("options", [])
            if len(opts) == 4:
                s["ex4"] += 1
            elif len(opts) == 0:
                s["zero"] += 1
            else:
                s["lt4"] += 1
    return stats


def main():
    stats = audit()
    out = ["# 行测题库选项完整度审计\n"]
    out.append("排除合法 2 选项判断题（对/错）和图形推理图形题。\n")
    out.append("| examKey | total | 4选项 | <4 | 0选项 | 合法跳过 | 问题率 |")
    out.append("|---|---|---|---|---|---|---|")

    grand_total = 0
    grand_ex4 = 0
    grand_bad = 0
    for ek, s in sorted(stats.items()):
        t = s["total"]
        effective = t - s["skip"]
        bad = s["lt4"] + s["zero"]
        rate = (bad / effective * 100) if effective else 0
        flag = ""
        if rate >= 20:
            flag = " ⛔️"
        elif rate >= 10:
            flag = " ⚠️"
        elif rate >= 1:
            flag = " ⚠"
        out.append(f"| {ek} | {t} | {s['ex4']} | {s['lt4']} | {s['zero']} | {s['skip']} | {rate:.0f}%{flag} |")
        grand_total += t
        grand_ex4 += s["ex4"]
        grand_bad += bad

    effective_total = grand_total - sum(s["skip"] for s in stats.values())
    out.append(f"\n**合计：total={grand_total}  4选项={grand_ex4} ({grand_ex4/effective_total*100:.1f}%)  问题题数={grand_bad}**\n")

    # Top 20 最差
    out.append("\n## Top 20 问题最严重的卷")
    out.append("| examKey | 问题数 | 问题率 |")
    out.append("|---|---|---|")
    ranked = []
    for ek, s in stats.items():
        effective = s["total"] - s["skip"]
        bad = s["lt4"] + s["zero"]
        if effective == 0:
            continue
        ranked.append((ek, bad, bad / effective * 100))
    ranked.sort(key=lambda x: -x[1])
    for ek, bad, rate in ranked[:20]:
        out.append(f"| {ek} | {bad} | {rate:.0f}% |")

    with open("options_completeness_audit.md", "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"written options_completeness_audit.md ({len(out)} lines)")
    print(f"全库 4选项率: {grand_ex4}/{effective_total} ({grand_ex4/effective_total*100:.1f}%)")
    print(f"问题题数: {grand_bad}")


if __name__ == "__main__":
    main()
