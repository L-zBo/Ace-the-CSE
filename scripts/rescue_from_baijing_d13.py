"""D-13 baijing1.top 救援工具

按 lib JSON 路径 + baijing paperId，把库里的占位题用 baijing 完整数据补回来。

策略（继承 D-12 跨源双校验）：
- lib qnum (id 末三位) → baijing sort_order 直接对齐（同一卷题号一致）
- 二次校验：lib 已有 content 前 25 字 vs baijing question 前 25 字 cosine 相似度
  - >= 0.7 视为同题；< 0.7 跳过该题（保护错位）
  - lib 原 content 是占位时跳过相似度，直接用 baijing 题干
- 模块校验：lib 文件路径模块名（yanyu/changshi/...）必须匹配 baijing knowledge_point
- 修复内容：
  - content：如原是占位 → 用 baijing question；否则保留
  - options：按 baijing list[str] 顺序映射 [{label:A,content},{B,...},{C,...},{D,...}]
  - answer：如 lib answer 不是 ABCD 之一 → 用 baijing answer；否则保留 lib（D-8 错位修正可选 --accept-baijing-ans）
  - explanation：去 HTML 标签 + 注 source 注释 [来源 baijing1.top paperId={N}]
- 输出 dry-run 报告 + 实写

用法：
  python scripts/rescue_from_baijing_d13.py \
    --paper-id 710 \
    --lib src/data/xingce/yanyu/provincial_qinghai_2024.json \
    [--accept-baijing-ans] [--dry-run]
"""
import argparse, json, re, sys
from pathlib import Path
from difflib import SequenceMatcher

KP2MOD = {
    "言语理解": "yanyu",
    "判断推理": "panduan",
    "数量关系": "shuliang",
    "资料分析": "ziliao",
    "常识判断": "changshi",
    "政治理论": "changshi",
}

PLACEHOLDER_MARKERS = [
    "[题干 OCR 抽取失败-D11]",
    "[选项 OCR 抽取失败-D11]",
    "[题干/选项 OCR 抽取失败-D11]",
    "[D-11 标记",
]

# baijing1.top 自身的占位词（如其数据库未补全）— 命中即拒绝救援
BAIJING_DIRTY_MARKERS = [
    "暂缺", "待补", "待添加", "[暂缺]", "(暂缺)", "无", "略",
]


def is_placeholder(s: str) -> bool:
    return any(m in (s or "") for m in PLACEHOLDER_MARKERS)


def baijing_options_dirty(opts: list) -> tuple[bool, str]:
    """返回 (是否脏, 原因)。命中任一 marker 或全部为同一字符即脏"""
    if not opts or len(opts) != 4:
        return True, f"baijing options 数量={len(opts)} ≠ 4"
    cleaned = [(o or "").strip() for o in opts]
    # 任意一个等于 marker 或长度过短
    for i, c in enumerate(cleaned):
        if c in BAIJING_DIRTY_MARKERS:
            return True, f"baijing 选项 {chr(65+i)} 是占位词「{c}」"
        if len(c) < 1:
            return True, f"baijing 选项 {chr(65+i)} 为空"
    # 全相同 -> 脏
    if len(set(cleaned)) == 1:
        return True, "baijing 4 个选项内容完全一致（疑似占位）"
    return False, ""


def baijing_options_has_image(opts: list) -> bool:
    """检测 baijing options 是否含 <img src= URL（图形题，需占位化）"""
    for o in opts:
        if "<img" in (o or "") or "upload.gkzhenti.cn" in (o or ""):
            return True
    return False


def normalize_options(opts: list) -> list:
    """把 baijing list[str] 转 [{label,content}]。含图则全部转 [图形选项]"""
    if baijing_options_has_image(opts):
        return [{"label": L, "content": "[图形选项]"} for L in "ABCD"]
    return [{"label": L, "content": (opts[i] or "").strip()} for i, L in enumerate("ABCD")]


def html_to_text(html: str) -> str:
    if not html:
        return ""
    s = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    s = re.sub(r"</p>", "\n", s, flags=re.I)
    s = re.sub(r"<p[^>]*>", "", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"&nbsp;", " ", s)
    s = re.sub(r"&lt;", "<", s)
    s = re.sub(r"&gt;", ">", s)
    s = re.sub(r"&amp;", "&", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def similar(a: str, b: str, n: int = 25) -> float:
    a = re.sub(r"\s+", "", html_to_text(a or ""))[:n]
    b = re.sub(r"\s+", "", html_to_text(b or ""))[:n]
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def detect_module(lib_path: Path) -> str:
    parts = lib_path.parts
    return parts[-2]


def get_qnum(qid: str) -> int:
    try:
        return int(qid.rsplit("-", 1)[-1])
    except ValueError:
        return -1


def rescue(args):
    lib_path = Path(args.lib)
    lib = json.loads(lib_path.read_text(encoding="utf-8"))
    bj_path = Path(args.cache_dir) / f"paper_{args.paper_id}.json"
    if not bj_path.exists():
        sys.exit(f"cache 不存在：{bj_path}")
    paper = json.loads(bj_path.read_text(encoding="utf-8"))
    bj_qs = paper.get("questions", [])
    bj_by_sort = {q.get("sort_order", q.get("qn")): q for q in bj_qs}

    module = detect_module(lib_path)
    expected_kp = {v: k for k, v in KP2MOD.items()}.get(module, "")

    fixed = []
    skipped = []

    for q in lib:
        qn = get_qnum(q["id"])
        if qn < 0:
            continue
        content = q.get("content", "") or ""
        opts = q.get("options", []) or []
        opts_text = " ".join(
            (o.get("content", "") or "") if isinstance(o, dict) else str(o) for o in opts
        )
        stem_bad = is_placeholder(content)
        opt_bad = any(is_placeholder((o.get("content", "") or "") if isinstance(o, dict) else str(o)) for o in opts)
        if not (stem_bad or opt_bad):
            continue

        bj_q = bj_by_sort.get(qn)
        # Fallback：sort_order 对齐失败 → 全卷按题干相似度找
        match_strategy = "sort_order"
        if bj_q:
            bj_kp = bj_q.get("knowledge_point", "")
            kp_match = bj_kp == expected_kp or (module == "changshi" and bj_kp in ("常识判断", "政治理论"))
            if not kp_match:
                if args.allow_cross_module:
                    # cross-module: sort_order 跨模块命中时
                    # - stem_bad: 无 content 可校验，直接接受（库模块归类异常）
                    # - 否则: 题干 sim 校验
                    if stem_bad:
                        match_strategy = f"sort_order_xmod_stem_bad kp={bj_kp}"
                    else:
                        sim = similar(content, bj_q.get("question", ""))
                        if sim >= 0.7:
                            match_strategy = f"sort_order_xmod_sim={sim:.2f}"
                        else:
                            bj_q = None
                            match_strategy = f"fallback_kp_mismatch xmod_sim={sim:.2f}"
                else:
                    bj_q = None
                    match_strategy = "fallback_kp_mismatch"
        else:
            match_strategy = "fallback_no_qn"

        if bj_q is None and not stem_bad and args.allow_fallback:
            # Fallback A: 在本模块所有 baijing 题中按题干相似度找
            bj_mod = [q for q in bj_qs if q.get("knowledge_point") == expected_kp
                      or (module == "changshi" and q.get("knowledge_point") in ("常识判断", "政治理论"))]
            target = re.sub(r"\s+", "", content)[:80]
            best = None
            best_sim = 0.0
            for cand in bj_mod:
                cand_n = re.sub(r"\s+", "", cand.get("question", ""))[:80]
                sim = SequenceMatcher(None, target, cand_n).ratio()
                if sim > best_sim:
                    best_sim = sim
                    best = cand
            if best and best_sim >= 0.8:
                bj_q = best
                match_strategy = f"fallback_sim_{best_sim:.2f}"
            elif args.allow_cross_module:
                # Fallback B: 跨模块全卷搜（高阈值 0.85）
                best = None
                best_sim = 0.0
                for cand in bj_qs:
                    cand_n = re.sub(r"\s+", "", cand.get("question", ""))[:80]
                    sim = SequenceMatcher(None, target, cand_n).ratio()
                    if sim > best_sim:
                        best_sim = sim
                        best = cand
                if best and best_sim >= 0.85:
                    bj_q = best
                    match_strategy = f"fallback_xmod_{best_sim:.2f}"
                else:
                    skipped.append((qn, f"{match_strategy} & xmod 最高 sim={best_sim:.2f}"))
                    continue
            else:
                skipped.append((qn, f"{match_strategy} & fallback 最高 sim={best_sim:.2f}"))
                continue

        if bj_q is None:
            reason = "baijing 无此题号" if match_strategy == "fallback_no_qn" else f"模块不匹配 lib={module}"
            skipped.append((qn, reason))
            continue

        # 相似度二次校验（仅 stem 不占位时；fallback 已校过免双重）
        bj_question = bj_q.get("question", "")
        if not stem_bad and not match_strategy.startswith("fallback_sim"):
            sim = similar(content, bj_question)
            if sim < 0.7:
                skipped.append((qn, f"题干相似度仅 {sim:.2f}"))
                continue

        # 选项 list[str] -> [{label, content}]（含图自动转 [图形选项]）
        bj_opts = bj_q.get("options", []) or []
        dirty, reason = baijing_options_dirty(bj_opts)
        if dirty:
            skipped.append((qn, reason))
            continue
        new_opts = normalize_options(bj_opts)
        had_image = baijing_options_has_image(bj_opts)

        # answer
        bj_ans = (bj_q.get("answer") or "").strip().upper()
        lib_ans = (q.get("answer") or "").strip().upper()
        new_ans = lib_ans
        ans_changed = False
        if lib_ans not in ("A", "B", "C", "D"):
            new_ans = bj_ans
            ans_changed = True
        elif args.accept_baijing_ans and lib_ans != bj_ans:
            new_ans = bj_ans
            ans_changed = True

        # explanation
        new_exp = html_to_text(bj_q.get("explanation", "")) + \
            f"\n\n[来源 baijing1.top paperId={args.paper_id} sort={qn} - D13 救援]"
        if had_image:
            new_exp += "\n[注：本题选项为图形，原 baijing 含 <img>，已转 [图形选项] 占位，前端需补 PNG]"

        before = {
            "content": content[:60],
            "options": [(o.get("content", "") or "")[:30] if isinstance(o, dict) else str(o)[:30] for o in opts],
            "answer": lib_ans,
        }
        after = {
            "content": (bj_question if stem_bad else content)[:60],
            "options": [o["content"][:30] for o in new_opts],
            "answer": new_ans,
        }

        if not args.dry_run:
            if stem_bad:
                q["content"] = bj_question
            q["options"] = new_opts
            q["answer"] = new_ans
            q["explanation"] = new_exp

        fixed.append({"qn": qn, "id": q["id"], "stem_was_bad": stem_bad,
                      "ans_changed": ans_changed, "before": before, "after": after})

    # 写回
    if not args.dry_run and fixed:
        lib_path.write_text(json.dumps(lib, ensure_ascii=False, indent=2), encoding="utf-8")

    # 报告
    print(f"=== rescue_from_baijing_d13 ===")
    print(f"lib  : {lib_path}")
    print(f"paper: paperId={args.paper_id} title={paper.get('title','')[:40]}")
    print(f"fixed: {len(fixed)} | skipped: {len(skipped)} | dry-run={args.dry_run}")
    if fixed:
        print(f"\n[修复明细]")
        for f in fixed[:10]:
            mark = "*" if f["ans_changed"] else " "
            print(f"  {mark} qn={f['qn']:>3} {f['id'][-30:]} stem_bad={f['stem_was_bad']}")
            print(f"     before opts: {f['before']['options']}")
            print(f"     after  opts: {f['after']['options']}")
            print(f"     ans: {f['before']['answer']} -> {f['after']['answer']}")
        if len(fixed) > 10:
            print(f"  ... 还有 {len(fixed)-10} 条")
    if skipped:
        print(f"\n[跳过明细]")
        for qn, reason in skipped[:20]:
            print(f"  qn={qn:>3}  {reason}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper-id", required=True, help="paperId（baijing 数字 / gkzenti 13 位 timestamp）")
    ap.add_argument("--cache-dir", default="data/baijing_cache",
                    help="cache 目录（默认 baijing_cache，gkzenti 用 data/gkzenti_cache）")
    ap.add_argument("--lib", required=True)
    ap.add_argument("--accept-baijing-ans", action="store_true",
                    help="允许用 baijing answer 覆盖 lib answer（D-8 错位修正）")
    ap.add_argument("--apply", action="store_true",
                    help="实写 lib 文件。默认 dry-run（D-13 救援事故后默认安全）")
    ap.add_argument("--allow-fallback", action="store_true",
                    help="题号对齐失败时按题干相似度全卷搜（>=0.8 才接受）")
    ap.add_argument("--allow-cross-module", action="store_true",
                    help="允许跨模块匹配（高阈值 0.85），救 lib 模块归类错的题")
    args = ap.parse_args()
    args.dry_run = not args.apply
    rescue(args)


if __name__ == "__main__":
    main()
