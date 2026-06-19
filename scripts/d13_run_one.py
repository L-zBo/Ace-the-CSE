"""D-13 一条龙：dry-run + 自验 + apply + commit（每文件 1 次工具调用）

用法：
  python scripts/d13_run_one.py 5 yanyu provincial_heilongjiang_2020 632 "黑龙江 2020"

参数：
  序号  模块  lib文件名(无后缀)  paperId  commit人类描述

流程：
  1. dry-run rescue  —— 查 fixed/skipped 数
  2. 任意 skipped 中断（除非 --allow-skip）
  3. apply
  4. 读 lib 抽样首题，确认无 baijing 脏标记
  5. git add + commit  —— "fix({模块}): D-13 #N {desc} {模块} {N}题救援 (paperId={pid})"
"""
import argparse, json, os, subprocess, sys
from pathlib import Path

BAIJING_DIRTY = ["暂缺", "待补", "待添加"]


def run_rescue(lib_path: str, paper_id, apply: bool, fallback: bool = False, cross_module: bool = False, cache_dir: str = "data/baijing_cache"):
    cmd = ["python", "scripts/rescue_from_baijing_d13.py",
           "--paper-id", str(paper_id), "--lib", lib_path, "--cache-dir", cache_dir]
    if apply:
        cmd.append("--apply")
    if fallback:
        cmd.append("--allow-fallback")
    if cross_module:
        cmd.append("--allow-cross-module")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    return r.stdout, r.stderr, r.returncode


def parse_counts(stdout: str):
    fixed = skipped = -1
    for line in stdout.splitlines():
        if line.startswith("fixed:"):
            parts = line.split("|")
            fixed = int(parts[0].split(":")[1].strip())
            skipped = int(parts[1].split(":")[1].strip())
            break
    return fixed, skipped


def verify_lib(lib_path: str):
    lib = json.loads(Path(lib_path).read_text(encoding="utf-8"))
    issues = []
    for q in lib:
        for o in q.get("options", []) or []:
            c = (o.get("content", "") or "") if isinstance(o, dict) else str(o)
            for d in BAIJING_DIRTY:
                if c.strip() == d or c.strip().startswith(d + " "):
                    issues.append(f"{q['id']} 选项 {o.get('label','?')} 含「{d}」")
    return issues


def safe_print(s):
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode('gbk', errors='replace').decode('gbk'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("seq", type=int, help="D-13 #N")
    ap.add_argument("module", help="yanyu/changshi/shuliang/ziliao/panduan")
    ap.add_argument("lib_stem", help="lib 文件名（无 .json 后缀）")
    ap.add_argument("paper_id", help="baijing paperId（int）或 inst_pdf cache 名（如 inst_2020_a）")
    ap.add_argument("desc", help="commit 中卷名描述，如「黑龙江 2020」")
    ap.add_argument("--allow-skip", action="store_true", help="允许 skipped > 0 时仍 apply")
    ap.add_argument("--fallback", action="store_true", help="启用题干相似度 fallback")
    ap.add_argument("--cross-module", action="store_true", help="允许跨模块高相似度匹配")
    ap.add_argument("--cache-dir", default="data/baijing_cache", help="cache 目录（gkzenti 用 data/gkzenti_cache）")
    args = ap.parse_args()

    lib_path = f"src/data/xingce/{args.module}/{args.lib_stem}.json"
    if not Path(lib_path).exists():
        sys.exit(f"!! lib 不存在: {lib_path}")

    pre_dirty = set(verify_lib(lib_path))
    if pre_dirty:
        print(f"  pre-existing baijing dirty: {len(pre_dirty)} 选项（历史残留，本次只对新增脏数据触发回滚）")

    print(f"[D-13 #{args.seq}] {args.desc} {args.module} dry-run …")
    out, err, rc = run_rescue(lib_path, args.paper_id, apply=False, fallback=args.fallback, cross_module=args.cross_module, cache_dir=args.cache_dir)
    if rc != 0:
        safe_print(out); safe_print(err)
        sys.exit("!! rescue dry-run 失败")
    fixed, skipped = parse_counts(out)
    print(f"  fixed={fixed}  skipped={skipped}")
    if fixed == 0:
        sys.exit("!! 0 修复 — 跳过本卷")
    if skipped > 0 and not args.allow_skip:
        safe_print(out)
        sys.exit(f"!! {skipped} 题跳过 — 需 --allow-skip 才能继续")

    print(f"  apply …")
    out2, err2, rc2 = run_rescue(lib_path, args.paper_id, apply=True, fallback=args.fallback, cross_module=args.cross_module, cache_dir=args.cache_dir)
    if rc2 != 0:
        safe_print(out2); safe_print(err2)
        sys.exit("!! apply 失败")

    new_dirty = set(verify_lib(lib_path)) - pre_dirty
    if new_dirty:
        print("!! 自验发现本次新增 baijing 脏数据：")
        for i in list(new_dirty)[:5]:
            print(f"   {i}")
        subprocess.run(["git", "restore", lib_path])
        sys.exit("!! 已 git restore，请人工调查")
    print(f"  self-verify pass (新增脏数据=0, 历史残留={len(pre_dirty)})")

    paper_cache = f"{args.cache_dir}/paper_{args.paper_id}.json"
    subprocess.run(["git", "add", paper_cache, lib_path], check=True)
    msg = f"fix({args.module}): D-13 #{args.seq} {args.desc} {args.module} {fixed} 题救援 (paperId={args.paper_id})"
    if skipped > 0:
        msg += f" [skip={skipped} baijing占位]"
    subprocess.run(["git", "commit", "-m", msg], check=True)
    print(f"  [OK] committed: {msg}")


if __name__ == "__main__":
    main()
