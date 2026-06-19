"""D-12 #17 - opt_too_long V5 截断（92 题攻坚到 100%）.

V4 后剩 92 题大部分是选项 D 包含长篇政策文叙述（其他选项短）。
V5 策略：用相对长度差异判定混入：
- 选项 D 长 > 200 且其他选项平均 < 50 字 → D 是一拖到底的混入
- 截到 D 第一个标点后或长度 80 字内
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
audit = json.loads((ROOT / "archive/reports/d11_audit_full.json").read_text(encoding="utf-8"))

# 截断辅助：找前 N 字内最后一个完整标点
def safe_truncate(text, max_len=80):
    """按句号截断到不超过 max_len 字，返回截后内容."""
    candidate = text[:max_len]
    # 倒序找最后一个标点
    for punct in ['。', '；', '，', '、', '：']:
        idx = candidate.rfind(punct)
        if idx > 5:
            return candidate[:idx + 1]
    return candidate

otls = [i for i in audit["issues"] if i.get("severity")=="HIGH" and i.get("type")=="opt_too_long"]
print(f"V5 扫描 {len(otls)} 题")

by_file = {}
for issue in otls:
    by_file.setdefault(issue['file'].replace("\\", "/"), []).append(issue['qid'])

fixed_total = 0
skipped_total = 0
for fp, qids in by_file.items():
    full_path = ROOT / fp
    d = json.loads(full_path.read_text(encoding="utf-8"))
    qid_set = set(qids)
    file_fixed = 0
    file_skip = 0
    for q in d:
        if q.get("id") not in qid_set:
            continue
        opts = q.get("options", []) or []
        if len(opts) != 4:
            continue
        # 找最长选项 + 计算其他 3 个平均长度
        contents = [o.get("content", "") or "" for o in opts]
        max_idx = max(range(4), key=lambda i: len(contents[i]))
        max_len = len(contents[max_idx])
        other_avg = sum(len(c) for i, c in enumerate(contents) if i != max_idx) / 3.0
        if max_len > 150 and other_avg < 50:
            # 长度差异显著，截断最长选项
            old = contents[max_idx]
            new = safe_truncate(old, max_len=80)
            if new != old and len(new) > 5:
                opts[max_idx]["content"] = new
                file_fixed += 1
                continue
        file_skip += 1
    if file_fixed:
        full_path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  {fp}: 截 {file_fixed} 题")
    fixed_total += file_fixed
    skipped_total += file_skip

print(f"\n=== V5 总计 ===")
print(f"  V5 截断: {fixed_total}")
print(f"  跳过（不符合长度差异条件）: {skipped_total}")
