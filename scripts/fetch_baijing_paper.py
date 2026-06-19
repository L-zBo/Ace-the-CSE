"""D-13 baijing1.top 整卷拉取工具

API：
  GET /api/papers              -> {papers: [{id, title, category, region, year?, ...}]}
  GET /api/papers/{id}         -> {id, title, region, questions: [...]}

使用：
  python scripts/fetch_baijing_paper.py --list
      拉所有 paper 元信息，落 data/baijing_cache/_index.json
  python scripts/fetch_baijing_paper.py --fetch 709
      拉单卷完整内容，落 data/baijing_cache/paper_{id}.json
  python scripts/fetch_baijing_paper.py --search 青海 2024
      在 _index.json 里按关键词找匹配卷
"""
import argparse, json, sys, time, urllib.request, urllib.error, urllib.parse
from pathlib import Path

BASE = "https://baijing1.top"
CACHE_DIR = Path("data/baijing_cache")
INDEX_FILE = CACHE_DIR / "_index.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def http_get(url: str, retries: int = 3, sleep: float = 1.0) -> bytes:
    last_err = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_err = e
            time.sleep(sleep * (i + 1))
    raise RuntimeError(f"GET {url} failed after {retries} retries: {last_err}")


def fetch_index() -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    raw = http_get(f"{BASE}/api/papers")
    data = json.loads(raw)
    papers = data.get("papers", []) if isinstance(data, dict) else data
    INDEX_FILE.write_text(json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[index] 落 {len(papers)} 卷 -> {INDEX_FILE}")
    return papers


def load_index() -> list:
    if not INDEX_FILE.exists():
        return fetch_index()
    return json.loads(INDEX_FILE.read_text(encoding="utf-8"))


def fetch_paper(pid: int, force: bool = False) -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fp = CACHE_DIR / f"paper_{pid}.json"
    if fp.exists() and not force:
        return json.loads(fp.read_text(encoding="utf-8"))
    raw = http_get(f"{BASE}/api/papers/{pid}")
    data = json.loads(raw)
    fp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[paper] {pid} {data.get('title','')[:40]} -> {len(data.get('questions',[]))} 题")
    return data


def search(keywords: list[str]) -> list:
    papers = load_index()
    matched = []
    for p in papers:
        title = p.get("title", "")
        region = p.get("region", "") or ""
        hay = title + " " + region
        if all(k in hay for k in keywords):
            matched.append(p)
    return matched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="刷新整卷索引")
    ap.add_argument("--fetch", type=int, metavar="ID", help="按 paperId 拉单卷")
    ap.add_argument("--search", nargs="+", metavar="KW", help="按关键词搜")
    ap.add_argument("--force", action="store_true", help="强刷 cache")
    args = ap.parse_args()

    if args.list:
        fetch_index()
        return
    if args.fetch:
        fetch_paper(args.fetch, force=args.force)
        return
    if args.search:
        for p in search(args.search):
            print(f"  {p['id']:>4}  {p.get('region','?'):<6} {p.get('title','')[:60]}")
        return
    ap.print_help()


if __name__ == "__main__":
    main()
