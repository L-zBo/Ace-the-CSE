"""D-13 在多个候选 paperId 中，按 lib 已有题（非占位）的题干相似度自动选最匹配的卷"""
import argparse, json, re, sys
from difflib import SequenceMatcher
from pathlib import Path

MOD2KPS = {
    "yanyu": ["言语理解"], "panduan": ["判断推理"], "shuliang": ["数量关系"],
    "ziliao": ["资料分析"], "changshi": ["常识判断", "政治理论"],
}
PLACEHOLDER = ["[题干 OCR 抽取失败-D11]", "[选项 OCR 抽取失败-D11]"]

def is_placeholder(s):
    return any(m in (s or "") for m in PLACEHOLDER)

def norm(s, n=50):
    return re.sub(r"\s+", "", s or "")[:n]

def best_match(lib_path, paper_ids):
    lib_path = Path(lib_path)
    module = lib_path.parts[-2]
    expected_kps = MOD2KPS.get(module, [])
    kp_label = '/'.join(expected_kps)
    lib = json.loads(lib_path.read_text(encoding="utf-8"))
    refs_n = [norm(q.get('content','') or '')
              for q in lib if not is_placeholder(q.get('content',''))][:8]
    if not refs_n:
        return None, "lib 没有非占位题作参考"

    results = []
    for pid in paper_ids:
        fp = Path(f"data/baijing_cache/paper_{pid}.json")
        if not fp.exists():
            results.append((pid, 0.0, "cache miss"))
            continue
        bj = json.loads(fp.read_text(encoding="utf-8"))['questions']
        bj_mod_n = [norm(q['question']) for q in bj if q.get('knowledge_point') in expected_kps]
        if not bj_mod_n:
            results.append((pid, 0.0, f"无 {kp_label} 题"))
            continue
        sims = [max((SequenceMatcher(None, ref, q).ratio() for q in bj_mod_n), default=0.0)
                for ref in refs_n]
        avg = sum(sims) / len(sims)
        results.append((pid, avg, f"{len(bj_mod_n)} {kp_label} 题"))
    results.sort(key=lambda x: -x[1])
    return results, ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lib")
    ap.add_argument("paper_ids", nargs="+", type=int)
    args = ap.parse_args()
    results, err = best_match(args.lib, args.paper_ids)
    if err:
        sys.exit(err)
    print(f"lib: {args.lib}")
    top_sim = max(r[1] for r in results) if results else 0
    for pid, avg, info in results:
        mark = "★" if avg == top_sim else " "
        print(f"  {mark} paperId={pid:>4}  avg_sim={avg:.3f}  ({info})")

if __name__ == "__main__":
    main()
