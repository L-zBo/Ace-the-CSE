"""D-15 gkzenti.cn 整卷抓取（事业编联考专用，baijing 不覆盖）

gkzenti.cn 是 fenbi 镜像，paperId 是 13 位 timestamp。
HTML 结构：
- 题号: <div class="col-xs-1 left">N</div>
- 题干+选项: <div class="col-xs-11 right">...<p>...</p>... 选项 div ...</div>
- 选项: <div class="col-xs-{3|6|12}">A、...</div>
- 模块标题: <div class="col-xs-12 subtitle">一、常识判断...</div>
- 答案页: <div class="col-xs-1-5">N、A</div>

输出仿 baijing 格式落 data/gkzenti_cache/paper_{ts_id}.json，
让 rescue_from_baijing_d13.py 用 --cache-dir 切换即可复用。

用法：
  python scripts/fetch_gkzenti.py --fetch 1702961782131
  python scripts/fetch_gkzenti.py --fetch 1702961782131 --force
"""
import argparse, json, re, sys, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "data/gkzenti_cache"
HEADERS = {"User-Agent": "Mozilla/5.0 d15-gkzenti"}

SUBTITLE_TO_KP = {
    "常识判断": "常识判断",
    "言语理解": "言语理解",
    "数量关系": "数量关系",
    "判断推理": "判断推理",
    "资料分析": "资料分析",
}

ROW_RE = re.compile(
    r'<div class="row"><div class="col-xs-1 left">(\d+)</div>'
    r'<div class="col-xs-11 right">(.*?)</div></div></div>',
    re.DOTALL,
)
SUBTITLE_RE = re.compile(r'<div class="col-xs-12 subtitle">(.*?)</div>', re.DOTALL)
OPTION_RE = re.compile(r'<div class="col-xs-(?:3|6|12)">([A-D])、(.*?)</div>', re.DOTALL)
P_RE = re.compile(r'<p[^>]*>(.*?)</p>', re.DOTALL)
ANSWER_RE = re.compile(r'<div class="col-xs-1-5">(\d+)、([A-D]+)</div>')
TAG_RE = re.compile(r'<(?!img\b)[^>]+>')


def http_get(url: str, retries: int = 3, timeout: int = 20) -> str:
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
    raise RuntimeError(f"GET {url} failed after {retries}: {last}")


def strip_tags_keep_img(html: str) -> str:
    """剥 HTML 标签但保留 <img> 标签"""
    return TAG_RE.sub("", html).strip()


def parse_question_block(qn: int, body: str, current_kp: str) -> dict:
    """从 col-xs-11 right 内容解析一题"""
    options = OPTION_RE.findall(body)
    body_no_opts = re.sub(
        r'<div class="col-xs-(?:3|6|12)">[A-D]、.*?</div>', "", body, flags=re.DOTALL
    )
    paras = P_RE.findall(body_no_opts)
    question_text = "\n".join(strip_tags_keep_img(p) for p in paras if strip_tags_keep_img(p))
    if not question_text:
        question_text = strip_tags_keep_img(body_no_opts)
    # 输出 list[str] 兼容 baijing 格式
    opts_dict = {label: strip_tags_keep_img(content) for label, content in options}
    opts = [opts_dict.get(L, "") for L in "ABCD"]
    return {
        "qn": qn,
        "sort_order": qn,
        "question": question_text,
        "options": opts,
        "knowledge_point": current_kp,
    }


def parse_paper(html: str) -> tuple[str, list]:
    i = html.find('id="printcontent"')
    if i < 0:
        raise RuntimeError("no printcontent in paper page")
    body = html[i:]
    title_m = re.search(r"<h3[^>]*>(.*?)</h3>", body, re.DOTALL)
    title = strip_tags_keep_img(title_m.group(1)) if title_m else ""

    # 按 row 边界 split：每段含一题 (题号 + col-xs-11 right) 直到下一个 <div class="row"> 或末尾
    # subtitle 也是边界
    splitters = re.split(r'(<div class="(?:row|col-xs-12 subtitle)">)', body, flags=re.DOTALL)
    questions = []
    current_kp = ""
    j = 0
    while j < len(splitters):
        marker = splitters[j]
        if 'subtitle' in marker:
            sub_text = strip_tags_keep_img(splitters[j + 1] if j + 1 < len(splitters) else "")
            for key, kp in SUBTITLE_TO_KP.items():
                if key in sub_text:
                    current_kp = kp
                    break
            j += 2
            continue
        if 'row' in marker:
            row_inner = splitters[j + 1] if j + 1 < len(splitters) else ""
            qn_m = re.match(r'<div class="col-xs-1 left">(\d+)</div>(.*)', row_inner, re.DOTALL)
            if qn_m:
                qn = int(qn_m.group(1))
                rest = qn_m.group(2)
                content_m = re.match(r'<div class="col-xs-11 right">(.*)</div></div>\s*$',
                                     rest.strip(), re.DOTALL)
                if content_m:
                    qbody = content_m.group(1)
                    questions.append(parse_question_block(qn, qbody, current_kp))
            j += 2
            continue
        j += 1
    return title, questions


def parse_answers(html: str) -> dict:
    return {int(qn): ans for qn, ans in ANSWER_RE.findall(html)}


def fetch_paper(pid: str, force: bool = False) -> dict:
    cache = CACHE_DIR / f"paper_{pid}.json"
    if cache.exists() and not force:
        return json.loads(cache.read_text(encoding="utf-8"))

    paper_html = http_get(f"https://www.gkzenti.cn/paper/{pid}")
    answer_html = http_get(f"https://www.gkzenti.cn/answer/{pid}")
    title, questions = parse_paper(paper_html)
    answers = parse_answers(answer_html)
    for q in questions:
        q["answer"] = answers.get(q["qn"], "")

    out = {"id": pid, "title": title, "questions": questions, "source": "gkzenti.cn"}
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", required=True, help="gkzenti paperId（13 位 timestamp）")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    out = fetch_paper(args.fetch, args.force)
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    print(f"[paper] {args.fetch} {out['title'][:60]} -> {len(out['questions'])} 题")
    if out["questions"]:
        q = out["questions"][0]
        print(f"  q{q['qn']:03d} kp={q['knowledge_point']} ans={q.get('answer','?')}")
        print(f"    {q['question'][:80]}")
        for L, c in zip("AB", q["options"][:2]):
            print(f"    {L}: {c[:60]}")


if __name__ == "__main__":
    main()
