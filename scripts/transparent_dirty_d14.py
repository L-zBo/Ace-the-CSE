"""D-14 透明化 D-12 事故 1 历史污染：把"暂缺/题目正在全力以赴征集"统一为 D-11 标记

策略：
- options content 是「暂缺/待补/待添加」→ 改为 `[选项 OCR 抽取失败-D11]`
- question content 含「题目正在全力以赴征集 / 正确答案默认设置为 / 默认答案为A」→ 改为 `[题干 OCR 抽取失败-D11]`

用法：
  python scripts/transparent_dirty_d14.py            # dry-run 看清单
  python scripts/transparent_dirty_d14.py --apply    # 实写
"""
import argparse, json, re, sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DIRTY_OPT = ["暂缺", "待补", "待添加"]
DIRTY_CONTENT_RE = re.compile(r"题目正在(全力)?以赴征集|正确答案默认设置为|题目数据(?:完全|全部)|默认答案为A")

CONTENT_MARK = "[题干 OCR 抽取失败-D11]"
OPT_MARK = "[选项 OCR 抽取失败-D11]"


def transparent_lib(lib_path: Path):
    lib = json.loads(lib_path.read_text(encoding="utf-8"))
    changed_q = 0
    changed_opt = 0
    changed_content = 0
    for q in lib:
        c = q.get("content", "") or ""
        if DIRTY_CONTENT_RE.search(c):
            q["content"] = CONTENT_MARK
            changed_content += 1
            changed_q += 1
            q_changed = True
        else:
            q_changed = False
        opt_changed_in_q = False
        for o in q.get("options", []) or []:
            if not isinstance(o, dict):
                continue
            oc = (o.get("content", "") or "").strip()
            for d in DIRTY_OPT:
                if oc == d or oc.startswith(d):
                    o["content"] = OPT_MARK
                    changed_opt += 1
                    opt_changed_in_q = True
                    break
        if opt_changed_in_q and not q_changed:
            changed_q += 1
    return changed_q, changed_content, changed_opt, lib


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    files = sorted((ROOT / "src/data/xingce").glob("*/*.json"))
    total_files = total_q = total_opt = total_content = 0
    for fp in files:
        cq, cc, co, lib = transparent_lib(fp)
        if cq == 0:
            continue
        total_files += 1
        total_q += cq
        total_opt += co
        total_content += cc
        rel = fp.relative_to(ROOT).as_posix()
        print(f"  {rel:<60} 题={cq} content→D11={cc} opt→D11={co}")
        if args.apply:
            fp.write_text(json.dumps(lib, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n合计: {total_files} 文件 / {total_q} 题 / content {total_content} / opt {total_opt}")
    if not args.apply:
        print("[dry-run] 加 --apply 实写")
    else:
        print("[OK] 已透明化 — git diff 复核 + commit")


if __name__ == "__main__":
    main()
