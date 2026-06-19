"""D-16 J 批量 sim dry-run：扫所有 PDF cache × 模块 lib 组合，列出有候选的项

用法：python scripts/d16_batch_sim.py [--apply]
"""
import argparse
import subprocess
import sys
from pathlib import Path

MODULES = ["panduan", "changshi", "ziliao", "shuliang", "yanyu"]


def lib_path(paper_id: str, module: str) -> Path:
    if paper_id.startswith("prov_"):
        loc = paper_id[len("prov_"):]
        return Path("src/data/xingce") / module / f"provincial_{loc}.json"
    if paper_id.startswith("inst_"):
        return Path("src/data/xingce") / module / f"institution_{paper_id[len('inst_'):]}.json"
    return Path()


def detect_caches() -> list:
    pairs = []
    for cache_dir in ("data/prov_pdf_cache", "data/inst_pdf_cache"):
        d = Path(cache_dir)
        if not d.exists():
            continue
        for f in sorted(d.glob("paper_*.json")):
            pid = f.stem[len("paper_"):]
            pairs.append((pid, str(d)))
    return pairs


def run_dryrun(paper_id: str, cache_dir: str, lib: Path, apply: bool, allow_stem_only: bool = False) -> tuple:
    if not lib.exists():
        return None
    cmd = [
        sys.executable, "scripts/pdf_rescue_by_sim.py",
        "--paper-id", paper_id, "--lib", str(lib),
        "--cache-dir", cache_dir,
    ]
    if apply:
        cmd.append("--apply")
    if allow_stem_only:
        cmd.append("--allow-stem-only")
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**__import__('os').environ, "PYTHONIOENCODING": "utf-8"})
    out = p.stdout or ""
    # 解析 fixed: N | skipped: M
    fixed = 0
    skipped = 0
    for line in out.splitlines():
        if line.startswith("fixed:"):
            try:
                parts = line.split("|")
                fixed = int(parts[0].split(":")[1].strip())
                skipped = int(parts[1].split(":")[1].strip())
            except Exception:
                pass
    return fixed, skipped, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", help="仅扫该 paperId（如 prov_guizhou_2023）", default=None)
    ap.add_argument("--allow-stem-only", action="store_true")
    args = ap.parse_args()

    print("=== D-16 J 批量 sim 扫描 ===")
    caches = detect_caches()
    if args.only:
        caches = [(p, c) for p, c in caches if p == args.only]
    print(f"扫 {len(caches)} 张 PDF cache × {len(MODULES)} 模块")

    hits = []
    for pid, cache_dir in caches:
        for mod in MODULES:
            lib = lib_path(pid, mod)
            if not lib.exists():
                continue
            r = run_dryrun(pid, cache_dir, lib, args.apply, args.allow_stem_only)
            if r is None:
                continue
            fixed, skipped, out = r
            if fixed > 0:
                print(f"\n>> {pid}/{mod}: fixed={fixed} skipped={skipped}")
                # 摘 [修复明细] 段
                in_detail = False
                for line in out.splitlines():
                    if line.startswith("[修复明细]"):
                        in_detail = True
                        continue
                    if line.startswith("[跳过明细]"):
                        in_detail = False
                    if in_detail and line.strip():
                        print(f"   {line}")
                hits.append((pid, mod, fixed, skipped))

    print(f"\n=== 总结 ===")
    print(f"有候选的 (paper, module) 对：{len(hits)}")
    total_fixed = sum(h[2] for h in hits)
    print(f"预计可救：{total_fixed} 题")
    for pid, mod, f, s in hits:
        print(f"  {pid}/{mod}: {f} 救 / {s} skip")


if __name__ == "__main__":
    main()
