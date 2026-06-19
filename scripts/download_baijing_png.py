"""D-14 baijing 图床 PNG 落地工具

把 data/baijing_cache/paper_{pid}.json 里所有 <img src=...> URL 下到
public/img/questions/{examkey}/q{NN}.png（多图：q{NN}.png + q{NN}_2.png ...）

用法：
  # dry-run 看会下哪些
  python scripts/download_baijing_png.py 295 provincial_sichuan_2021

  # 实写
  python scripts/download_baijing_png.py 295 provincial_sichuan_2021 --apply

  # 限定模块（只下资料分析）
  python scripts/download_baijing_png.py 295 provincial_sichuan_2021 --kp 资料分析 --apply
"""
import argparse, json, re, sys, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMG_RE = re.compile(r'<img\s+src=["\']([^"\']+)["\']')


def collect_urls(paper_path: Path, kp_filter: str = ""):
    """返回 {qn: [urls...]} 字典"""
    paper = json.loads(paper_path.read_text(encoding="utf-8"))
    out = {}
    for i, q in enumerate(paper.get("questions", []), 1):
        if kp_filter and q.get("knowledge_point") != kp_filter:
            continue
        text = (q.get("question") or "")
        for o in q.get("options") or []:
            text += str(o) if not isinstance(o, dict) else (o.get("content") or "")
        urls = IMG_RE.findall(text)
        if urls:
            out[i] = urls
    return out


def download(url: str, dest: Path, timeout: int = 15):
    if dest.exists():
        return "skip-exists"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 d14-png"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return f"ok ({len(data)} bytes)"
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        return f"fail: {e}"


def png_name(qn: int, idx: int) -> str:
    return f"q{qn:03d}.png" if idx == 0 else f"q{qn:03d}_{idx + 1}.png"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paper_id", type=int)
    ap.add_argument("examkey", help="public/img/questions/{examkey} 子目录名")
    ap.add_argument("--kp", default="", help="只下载该 knowledge_point 的题（如「资料分析」）")
    ap.add_argument("--apply", action="store_true", help="真下载，否则只 dry-run")
    args = ap.parse_args()

    paper_path = ROOT / f"data/baijing_cache/paper_{args.paper_id}.json"
    if not paper_path.exists():
        sys.exit(f"!! 缺 cache: {paper_path}")

    out_dir = ROOT / "public/img/questions" / args.examkey
    qn_urls = collect_urls(paper_path, args.kp)
    total_urls = sum(len(v) for v in qn_urls.values())
    print(f"paper_{args.paper_id} -> {out_dir.relative_to(ROOT)}")
    print(f"  {len(qn_urls)} 题含图 / {total_urls} 个 URL  (kp={args.kp or 'ALL'})")

    if not args.apply:
        for qn, urls in sorted(qn_urls.items()):
            print(f"  q{qn:03d} -> {len(urls)} 张")
        print("\n[dry-run] 加 --apply 实下")
        return

    ok = fail = skip = 0
    for qn, urls in sorted(qn_urls.items()):
        for idx, url in enumerate(urls):
            dest = out_dir / png_name(qn, idx)
            r = download(url, dest)
            if r.startswith("ok"):
                ok += 1
            elif r == "skip-exists":
                skip += 1
            else:
                fail += 1
                print(f"  {dest.name}: {r}")
    print(f"\n[done] ok={ok} skip={skip} fail={fail}")


if __name__ == "__main__":
    main()
