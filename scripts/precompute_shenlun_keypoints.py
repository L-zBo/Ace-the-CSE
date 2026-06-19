"""D-6 #4：申论 keyPoints 字段静态化（Python 端预计算入库）。

逻辑与 src/lib/shenlunAnswer.ts 的 extractKeywords + parseShenlunAnswer 一致：
1. 先按 "【问题N参考答案】" 拆块；无则单块
2. 每块抽要点（行首 "1. XXX。" / "一、XXX：" 短词 ≥3 字 ≤12 字）
3. 不足 2 时兜底：词频 Top 5 中文 2-5 字短语

预计算入 q.keyPoints[]: string[]
"""
from __future__ import annotations
import argparse
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data" / "shenlun"

ZH_NUM = "一二三四五六七八九十"
HEADER_RE = re.compile(rf"【(问题[{ZH_NUM}]+参考答案)】")
POINT_RE = re.compile(
    r"(?:^|\n)\s*(?:\d+|[一二三四五六七八九十]+)[.．、：]\s*([^。；，：\n]{3,12})[。；，：]"
)
PHRASE_RE = re.compile(r"[一-龥]{2,5}")

STOP_WORDS = set([
    "参考答案", "问题", "我们", "可以", "应该", "通过", "以及", "并且", "因此",
    "这些", "这种", "具有", "进行", "方面", "对策", "一是", "二是", "三是", "四是", "五是",
    "内容", "工作", "发展", "建设", "重要", "充分", "不断", "积极", "加强", "提供",
    "实现", "推动", "完善", "进一步", "相关", "有关", "同时", "目前",
    "他们", "她们", "我是", "如果", "但是", "虽然", "普通", "平凡", "需要", "存在",
    "才能", "一种", "一个", "表现", "成为", "非常", "开展", "利用",
])


def normalize_md(raw: str) -> str:
    """对应 TS 端 raw.replace(/([^\\n])\\n(?!\\n|【|\\s*\\d+[.．、])/g, '$1') 的合并逻辑。"""
    return re.sub(r"([^\n])\n(?!\n|【|\s*\d+[.．、])", r"\1", raw)


def extract_keywords(raw: str) -> list[str]:
    if not raw:
        return []
    kws = []
    seen = set()
    for m in POINT_RE.finditer(raw):
        kw = re.sub(r"\s+", "", m.group(1))
        if not (3 <= len(kw) <= 12):
            continue
        if kw in STOP_WORDS:
            continue
        if "。" in kw or "\n" in kw:
            continue
        if kw in seen:
            continue
        seen.add(kw)
        kws.append(kw)
        if len(kws) >= 5:
            return kws
    if len(kws) >= 2:
        return kws
    # 兜底：词频
    freq = {}
    for m in PHRASE_RE.finditer(raw):
        p = m.group(0)
        if p in STOP_WORDS:
            continue
        freq[p] = freq.get(p, 0) + 1
    for p, c in sorted(freq.items(), key=lambda x: -x[1]):
        if c < 2:
            break
        if p not in seen:
            seen.add(p)
            kws.append(p)
            if len(kws) >= 5:
                break
    return kws


def parse_shenlun_answer(raw: str) -> tuple[list[dict], str | None, str | None]:
    """返回 (blocks, essayModel, essayAnalysis)。每块 dict: {title, body, points}"""
    if not raw or not raw.strip():
        return [{"title": "参考答案", "body": "", "points": []}], None, None
    norm = normalize_md(raw)
    hits = []
    for m in HEADER_RE.finditer(norm):
        hits.append((m.group(1).replace("参考答案", ""), m.start(), m.end()))
    if not hits:
        blocks = [{
            "title": "参考答案",
            "body": norm.strip(),
            "points": extract_keywords(norm),
        }]
    else:
        blocks = []
        for i, (title, s, e) in enumerate(hits):
            body_start = e
            body_end = hits[i + 1][1] if i + 1 < len(hits) else len(norm)
            body = norm[body_start:body_end].strip()
            blocks.append({
                "title": title,
                "body": body,
                "points": extract_keywords(body),
            })
    # essay model + analysis 拆
    essay_model = None
    essay_analysis = None
    last = blocks[-1]
    am_re = re.compile(r"【(标题的优点|开头的优点|论述段\d+的优点|论述段之间的关系|结尾的优点)")
    m = am_re.search(last["body"])
    if m and m.start() > 50:
        essay_model = re.sub(r"\n?文章分析\s*$", "", last["body"][:m.start()]).strip()
        essay_analysis = last["body"][m.start():].strip()
        last["body"] = "（正文与分析见下方）"
        last["points"] = []
    return blocks, essay_model, essay_analysis


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    total = 0
    written = 0
    points_dist = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for p in sorted(DATA.glob("*/*.json")):
        questions = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(questions, list):
            questions = [questions]
        modified = False
        for q in questions:
            total += 1
            ans = q.get("answer") or ""
            if isinstance(ans, list):
                ans = "\n".join(ans)
            blocks, essay_model, essay_analysis = parse_shenlun_answer(ans)
            # 聚合所有 block 的 points 去重
            all_kws = []
            seen = set()
            for b in blocks:
                for k in b["points"]:
                    if k not in seen:
                        seen.add(k)
                        all_kws.append(k)
            n = len(all_kws)
            points_dist[min(n, 5)] += 1
            if q.get("keyPoints") != all_kws:
                q["keyPoints"] = all_kws
                modified = True
                written += 1
        if modified and args.apply:
            p.write_text(
                json.dumps(questions, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    mode = "WRITE" if args.apply else "DRY"
    print(f"[{mode}] 处理 {total} 题，写入 {written} 题 keyPoints")
    print(f"keyPoints 数量分布: {points_dist}")


if __name__ == "__main__":
    main()
