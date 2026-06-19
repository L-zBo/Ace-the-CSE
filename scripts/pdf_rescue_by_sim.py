"""D-16 G+ 方案：用题干/选项相似度匹配 PDF 整卷，救题号偏移的省考占位

适用：lib qn 跟 PDF qn 不对齐（网友回忆版 vs 完整版排序错位），
靠 lib 占位题里残留的「原 content」+ 非占位 options 跟 PDF 全卷题做内容匹配。

用法（与 rescue_from_baijing_d13 接口对齐）：
  python scripts/pdf_rescue_by_sim.py --paper-id prov_guizhou_2023 \\
    --lib src/data/xingce/changshi/provincial_guizhou_2023.json \\
    --cache-dir data/prov_pdf_cache [--apply]
"""
import argparse, json, re, sys
from difflib import SequenceMatcher
from pathlib import Path

OCR_MARKERS = ["[题干 OCR 抽取失败-D11]", "[选项 OCR 抽取失败-D11]", "[题干/选项 OCR 抽取失败-D11]"]
ORIG_CONTENT_RE = re.compile(r"原 content\s*[:：]\s*['\"](.+?)['\"]")
PDF_PLACEHOLDER_PAT = re.compile(r"题目正在全力以赴征集|^暂缺$|^缺失$")
# PDF 选项末尾常见水印（淘宝店铺 / 教育资源 / 公众号 / QQ 群 / 微信号）
WATERMARK_PAT = re.compile(
    r"\s*(淘宝店铺[【\[].*?[】\]]|【.*?教育资源】|【.*?文化】|公众号[:：].*$|QQ\s*群?[:：]?\s*\d+.*$|微信[号:：].*$|关注微信.*$|更多资料.*$)",
    re.IGNORECASE,
)


def clean_watermark(s: str) -> str:
    """剥离选项末尾水印（淘宝店铺/教育资源/公众号 等）"""
    if not s:
        return s
    s2 = WATERMARK_PAT.sub("", s).rstrip()
    return s2

KP2MOD = {
    "言语理解": "yanyu", "判断推理": "panduan", "数量关系": "shuliang",
    "资料分析": "ziliao", "常识判断": "changshi", "政治理论": "changshi",
}


def is_placeholder_stem(s: str) -> bool:
    return any(m in (s or "") for m in OCR_MARKERS)


def is_placeholder_opt(s: str) -> bool:
    return any(m in (s or "") for m in OCR_MARKERS)


def detect_module(lib_path: str) -> str:
    return Path(lib_path).parts[-2]


def norm(s: str, n: int = 60) -> str:
    return re.sub(r"\s+", "", s or "")[:n]


def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, norm(a, 80), norm(b, 80)).ratio()


def get_qnum(qid: str) -> int:
    try:
        return int(qid.rsplit("-", 1)[-1])
    except Exception:
        return -1


def extract_lib_hints(q: dict) -> dict:
    """从 lib 占位题里提残留可用于匹配的线索"""
    content = q.get("content", "") or ""
    # 原 content 注释
    orig = ""
    m = ORIG_CONTENT_RE.search(content)
    if m:
        orig = m.group(1)
    # 非占位 stem（content 本身不含 OCR marker）
    real_stem = "" if is_placeholder_stem(content) else content
    # 非占位 options
    real_opts = []
    for o in q.get("options", []) or []:
        c = (o.get("content", "") or "") if isinstance(o, dict) else str(o)
        if c.strip() and not is_placeholder_opt(c) and len(c.strip()) >= 5:
            real_opts.append(c.strip())
    return {
        "qn": get_qnum(q["id"]),
        "ans": (q.get("answer") or "").strip(),
        "stem": real_stem,
        "orig_stem": orig,
        "real_opts": real_opts,
        "module_lib": detect_module(f"src/data/xingce/{q.get('category','')}/x.json") if "category" in q else "",
    }


def pdf_question_clean(q: dict) -> bool:
    """PDF 题本身是否「征集中」占位"""
    stem = q.get("question", "") or ""
    opts = q.get("options", []) or []
    if PDF_PLACEHOLDER_PAT.search(stem):
        return False
    # 看选项里 N 个含「暂缺」
    n_place = sum(1 for o in opts if PDF_PLACEHOLDER_PAT.search(o or "") or (o or "").strip() in ("暂缺", "缺失"))
    return n_place < 3 and len(opts) >= 4


def match_one(hint: dict, pdf_qs: list, expected_kp: str = "") -> tuple:
    """返回 (best_q, score, reason, opt_match) — score ≥ 阈值且 (opt_match≥1 或 stem 极高) 才接受"""
    best_q = None
    best_score = 0.0
    best_reason = ""
    best_opt_match = 0
    for pq in pdf_qs:
        if not pdf_question_clean(pq):
            continue
        if expected_kp and pq.get("knowledge_point") and pq["knowledge_point"] != expected_kp:
            kp_penalty = 0.85
        else:
            kp_penalty = 1.0
        opt_match = 0
        if hint["real_opts"] and pq.get("options"):
            pdf_opts_n = [norm(clean_watermark(o), 60) for o in pq["options"]]
            for ro in hint["real_opts"]:
                ro_n = norm(ro, 60)
                if len(ro_n) < 8:
                    continue
                hit = max((similar(ro_n, po) for po in pdf_opts_n), default=0)
                if hit >= 0.7:
                    opt_match += 1
        opt_score = opt_match / max(1, len(hint["real_opts"]))
        ref_stem = hint["orig_stem"] or hint["stem"]
        stem_score = similar(ref_stem, pq.get("question", "")) if ref_stem else 0
        score = max(opt_score * 0.85 + stem_score * 0.15, stem_score) * kp_penalty
        if score > best_score:
            best_score = score
            best_q = pq
            best_opt_match = opt_match
            best_reason = f"opt={opt_score:.2f}({opt_match}) stem={stem_score:.2f} kp={pq.get('knowledge_point','')}"
    return best_q, best_score, best_reason, best_opt_match


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper-id", required=True)
    ap.add_argument("--lib", required=True)
    ap.add_argument("--cache-dir", default="data/prov_pdf_cache")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--threshold", type=float, default=0.7)
    ap.add_argument("--allow-stem-only", action="store_true",
                    help="允许 opt_match=0 时单凭 stem 通过（默认禁止，防 stem 前缀冲撞）")
    args = ap.parse_args()

    lib_path = Path(args.lib)
    lib = json.loads(lib_path.read_text(encoding="utf-8"))
    cache_path = Path(args.cache_dir) / f"paper_{args.paper_id}.json"
    if not cache_path.exists():
        sys.exit(f"!! cache 不存在: {cache_path}")
    pdf = json.loads(cache_path.read_text(encoding="utf-8"))
    pdf_qs = pdf.get("questions", [])

    module = detect_module(args.lib)
    expected_kp = {v: k for k, v in KP2MOD.items()}.get(module, "")
    if module == "changshi":
        # 常识可能是「常识判断」或「政治理论」
        expected_kp = "常识判断"

    print(f"=== pdf_rescue_by_sim ===")
    print(f"lib  : {args.lib}")
    print(f"paper: paperId={args.paper_id} questions={len(pdf_qs)}")
    print(f"module={module} expected_kp={expected_kp} threshold={args.threshold} apply={args.apply}")

    fixed = []
    skipped = []
    for q in lib:
        content = q.get("content", "") or ""
        opts = q.get("options", []) or []
        stem_bad = is_placeholder_stem(content)
        opt_bad = any(is_placeholder_opt((o.get("content", "") or "") if isinstance(o, dict) else str(o)) for o in opts)
        if not (stem_bad or opt_bad):
            continue
        hint = extract_lib_hints(q)
        if not (hint["real_opts"] or hint["orig_stem"] or hint["stem"]):
            skipped.append((hint["qn"], "lib 无可匹配线索（无残留 options / 无原 content）"))
            continue
        best_q, score, reason, opt_match = match_one(hint, pdf_qs, expected_kp)
        if score < args.threshold or best_q is None:
            skipped.append((hint["qn"], f"最高 score={score:.2f} ({reason})"))
            continue
        # 关键约束 1：opt_match==0 时禁止仅靠 stem 通过（防 stem 前缀冲撞）
        if opt_match == 0 and not args.allow_stem_only:
            skipped.append((hint["qn"], f"opt_match=0 仅 stem 通过 ({reason})，需 --allow-stem-only"))
            continue
        # 关键约束 2：lib answer 与 PDF answer 必须一致（若双方都有）
        pdf_ans = (best_q.get("answer") or "").strip()
        lib_ans = hint["ans"]
        if lib_ans and pdf_ans and lib_ans != pdf_ans:
            skipped.append((hint["qn"], f"answer 矛盾 lib={lib_ans} pdf={pdf_ans} ({reason})"))
            continue
        # 选项水印剥离
        cleaned_opts = [clean_watermark(best_q["options"][i] if i < len(best_q["options"]) else "") for i in range(4)]
        new_opts = [{"label": chr(65 + i), "content": cleaned_opts[i]} for i in range(4)]
        new_stem = best_q.get("question", "") or hint["stem"]
        pdf_expl = (best_q.get("explanation") or "").strip()
        fixed.append({
            "qn": hint["qn"],
            "score": score,
            "reason": reason,
            "pdf_qn": best_q["sort_order"],
            "new_stem": new_stem,
            "new_opts": new_opts,
            "new_ans": pdf_ans if pdf_ans else lib_ans,
            "new_expl": pdf_expl,
        })

    print(f"fixed: {len(fixed)} | skipped: {len(skipped)} | dry-run={'False' if args.apply else 'True'}\n")
    if fixed:
        print("[修复明细]")
        for f in fixed:
            print(f"  qn={f['qn']:>3} -> pdf_qn={f['pdf_qn']:>3}  score={f['score']:.2f} {f['reason']}")
            print(f"     stem: {f['new_stem'][:70]}")
            print(f"     opts: {[o['content'][:30] for o in f['new_opts']]}")
            print(f"     ans:  {f['new_ans']}")
    if skipped:
        print("\n[跳过明细]")
        for qn, reason in skipped:
            print(f"  qn={qn:>3}  {reason}")

    if args.apply and fixed:
        # 实写
        by_qn = {f["qn"]: f for f in fixed}
        for q in lib:
            qn = get_qnum(q["id"])
            if qn in by_qn:
                f = by_qn[qn]
                # 题干：原 content 已含 OCR 标记，整个替换
                q["content"] = f["new_stem"]
                # options：保留原 label
                new_opts_by_label = {chr(65 + i): f["new_opts"][i]["content"] for i in range(4)}
                for o in q.get("options", []) or []:
                    label = o.get("label") if isinstance(o, dict) else None
                    if label and label in new_opts_by_label:
                        o["content"] = new_opts_by_label[label]
                if f["new_ans"]:
                    q["answer"] = f["new_ans"]
                if f["new_expl"] and not q.get("explanation"):
                    q["explanation"] = f["new_expl"]
        lib_path.write_text(json.dumps(lib, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[OK] applied to {args.lib}")


if __name__ == "__main__":
    main()
