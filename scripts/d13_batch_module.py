"""D-13 批量推进单个模块（自动定位 paperId + fetch + dry-run + apply + commit）

用法：
  python scripts/d13_batch_module.py changshi
  python scripts/d13_batch_module.py shuliang --start-seq 50

每文件一个 commit。失败的文件记入 data/reports/d13_residual_{module}.md。
"""
import argparse, json, re, subprocess, sys
from pathlib import Path
from collections import defaultdict

import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent))
from d13_locate_paper import locate, REGION_ZH
from fetch_baijing_paper import fetch_paper

MARKERS = ['[题干 OCR 抽取失败-D11]', '[选项 OCR 抽取失败-D11]', '[题干/选项 OCR 抽取失败-D11]']

def is_bad(q):
    if any(m in (q.get('content','') or '') for m in MARKERS): return True
    for o in q.get('options',[]) or []:
        c = (o.get('content','') or '') if isinstance(o, dict) else str(o)
        if any(m in c for m in MARKERS): return True
    return False


def parse_filename(fn: str):
    """从 lib 文件名解析 source/region/year/level
    e.g. provincial_qinghai_2024.json -> ('provincial', 'qinghai', 2024, '')
         institution_2022_e.json -> ('institution', '', 2022, 'e')
         national_2025_dishi.json -> ('national', '', 2025, 'dishi')
         provincial_jiangsu_2022_b.json -> ('provincial', 'jiangsu', 2022, 'b')
    """
    stem = fn.replace('.json', '')
    parts = stem.split('_')
    src = parts[0]
    if src == 'institution':
        return src, '', int(parts[1]), parts[2] if len(parts) > 2 else ''
    if src == 'national':
        return src, '', int(parts[1]), parts[2] if len(parts) > 2 else ''
    # provincial_*
    region = parts[1]
    year = int(parts[2])
    level = parts[3] if len(parts) > 3 else ''
    return src, region, year, level


def find_paper_ids(src: str, region: str, year: int, level: str) -> list:
    """在 baijing index 里找候选 paperIds"""
    if src == 'national':
        return [p['id'] for p in locate('national', year, national=True)]
    if src == 'institution':
        return []  # baijing 没事业编
    # provincial
    matches = locate(region, year, level=level.upper() if level else '')
    if not matches:
        # 试不带 level 的
        matches = locate(region, year)
    return [p['id'] for p in matches]


def run_one(seq: int, module: str, lib_stem: str, paper_id: int, desc: str,
            allow_skip: bool = True, fallback: bool = True, cross_module: bool = False):
    cmd = ["python", "scripts/d13_run_one.py", str(seq), module, lib_stem, str(paper_id), desc]
    if allow_skip:
        cmd.append("--allow-skip")
    if fallback:
        cmd.append("--fallback")
    if cross_module:
        cmd.append("--cross-module")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout + r.stderr, r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("module")
    ap.add_argument("--start-seq", type=int, default=25)
    ap.add_argument("--max-files", type=int, default=999)
    ap.add_argument("--cross-module", action="store_true")
    ap.add_argument("--pick-threshold", type=float, default=0.3)
    args = ap.parse_args()

    # 收集缺题文件
    files_bad = {}
    for fp in sorted(Path(f"src/data/xingce/{args.module}").glob("*.json")):
        lib = json.loads(fp.read_text(encoding="utf-8"))
        bad = [q['id'].rsplit('-',1)[-1] for q in lib if is_bad(q)]
        if bad:
            files_bad[fp.name] = bad

    print(f"[batch] {args.module} 缺题 {len(files_bad)} 文件 / {sum(len(v) for v in files_bad.values())} 题")

    seq = args.start_seq
    success_files = []
    failed_files = []  # (fn, qns, reason)

    # 按缺题数从多到少
    for fn, qns in sorted(files_bad.items(), key=lambda x: -len(x[1])):
        if seq - args.start_seq >= args.max_files:
            break
        src, region, year, level = parse_filename(fn)
        if src == 'institution':
            failed_files.append((fn, qns, "事业编联考 baijing 不覆盖（硬限）"))
            continue
        candidates = find_paper_ids(src, region, year, level)
        if not candidates:
            failed_files.append((fn, qns, f"baijing 无对应卷（region={region} year={year} level={level}）"))
            continue

        # 多候选 → 用 d13_pick_paper 选最匹配
        if len(candidates) > 1:
            from d13_pick_paper import best_match
            results, _ = best_match(f"src/data/xingce/{args.module}/{fn}", candidates)
            if not results or results[0][1] < args.pick_threshold:
                failed_files.append((fn, qns, f"多候选无足够相似 paper {candidates}"))
                continue
            chosen = results[0][0]
        else:
            chosen = candidates[0]

        # fetch
        try:
            fetch_paper(chosen)
        except Exception as e:
            failed_files.append((fn, qns, f"fetch 失败: {e}"))
            continue

        # 一条龙
        desc = f"{REGION_ZH.get(region, region) or src} {year}{('_' + level) if level else ''}"
        lib_stem = fn.replace('.json','')
        print(f"\n>>> [#{seq}] {fn} (paperId={chosen}) qns={qns}")
        out, rc = run_one(seq, args.module, lib_stem, chosen, desc, cross_module=args.cross_module)
        # 解析输出
        if "✓ committed" in out:
            success_files.append((fn, qns, chosen))
            seq += 1
            # 抓 fixed/skip 数（粗略）
            m = re.search(r"fixed=(\d+)\s+skipped=(\d+)", out)
            if m:
                print(f"     fixed={m.group(1)} skipped={m.group(2)}")
        else:
            failed_files.append((fn, qns, f"run_one 失败: {out[-200:].strip()}"))
            # seq 不增
            print(f"     ✗ 跳过")

    # 汇总报告
    print(f"\n=== batch {args.module} 收尾 ===")
    print(f"成功: {len(success_files)} 卷")
    print(f"失败: {len(failed_files)} 卷")

    Path("data/reports").mkdir(parents=True, exist_ok=True)
    rep = Path(f"data/reports/d13_residual_{args.module}.md")
    with rep.open("w", encoding="utf-8") as f:
        f.write(f"# D-13 {args.module} 残余文件清单\n\n")
        f.write(f"自动 batch 后还需人工或硬限保留的文件：\n\n")
        for fn, qns, reason in failed_files:
            f.write(f"- `{fn}` qns={qns}  → **{reason}**\n")
        f.write(f"\n成功 {len(success_files)} 卷见 git log。\n")
    print(f"残余清单: {rep}")


if __name__ == "__main__":
    main()
