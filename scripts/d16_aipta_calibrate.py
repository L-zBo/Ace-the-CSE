"""D-16 L-3c lib 整卷 vs aipta 整卷 sim 比对（版本识别 calibration）

对一组 lib paper × aipta article 做整卷比对，每道题用同 qn 比 sim，
输出平均 sim、命中题数、是否同源判定。

用法：
  python scripts/d16_aipta_calibrate.py \\
    --lib src/data/xingce/panduan/institution_2020_c.json \\
    --aipta 2241
"""
import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

MARKERS = [
    '[题干 OCR 抽取失败-D11]',
    '[选项 OCR 抽取失败-D11]',
    '[题干/选项 OCR 抽取失败-D11]',
    '[暂缺]',
]


def is_placeholder(s: str) -> bool:
    if not s: return True
    return any(m in s for m in MARKERS) or s.strip() in ('缺失', '暂缺')


def norm(s: str, n: int = 80) -> str:
    return re.sub(r'\s+', '', s or '')[:n]


def sim(a: str, b: str, n: int = 80) -> float:
    return SequenceMatcher(None, norm(a, n), norm(b, n)).ratio()


def get_qn(qid: str) -> int:
    try: return int(qid.rsplit('-', 1)[-1])
    except: return -1


def best_match_in_window(lib_q, aipta_qs, qn_target, window: int = 5):
    """对 lib_q 在 aipta qn_target±window 中找 sim 最高的题"""
    best = None
    best_score = 0
    best_qn = None
    lib_stem = lib_q.get('content', '') or ''
    if is_placeholder(lib_stem): return None, 0, None
    for aq in aipta_qs:
        if abs(aq['qn'] - qn_target) > window: continue
        s = sim(lib_stem, aq.get('stem', ''))
        if s > best_score:
            best_score = s
            best = aq
            best_qn = aq['qn']
    return best, best_score, best_qn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lib', required=True)
    ap.add_argument('--aipta', type=int, required=True)
    ap.add_argument('--window', type=int, default=5, help='qn 容差')
    args = ap.parse_args()

    lib_path = Path(args.lib)
    aipta_path = Path(f'data/aipta_cache/article_{args.aipta}.json')
    if not lib_path.exists():
        sys.exit(f'!! lib 不存在: {lib_path}')
    if not aipta_path.exists():
        sys.exit(f'!! aipta cache 不存在: {aipta_path}')

    lib = json.loads(lib_path.read_text(encoding='utf-8'))
    aipta = json.loads(aipta_path.read_text(encoding='utf-8'))
    aipta_qs = aipta['questions']

    # 仅看题干非占位的 lib 题，做 sim
    rows = []
    high_match = 0
    same_qn_hit = 0
    total = 0
    for q in lib:
        if is_placeholder(q.get('content', '') or ''): continue
        qn = get_qn(q.get('id', ''))
        if qn < 0: continue
        total += 1
        best, score, best_qn = best_match_in_window(q, aipta_qs, qn, args.window)
        if best is None:
            rows.append((qn, None, 0.0, ''))
            continue
        rows.append((qn, best_qn, score, (best.get('stem', '') or '')[:50]))
        if score >= 0.7:
            high_match += 1
        if score >= 0.7 and best_qn == qn:
            same_qn_hit += 1

    # 计算 lib_qn - aipta_qn 的众数（identify offset）
    from collections import Counter
    diff_counter = Counter()
    for qn, aqn, score, stem in rows:
        if aqn is not None and score >= 0.85:
            diff_counter[qn - aqn] += 1
    best_offset = None
    if diff_counter:
        best_offset, best_offset_n = diff_counter.most_common(1)[0]
        offset_share = best_offset_n / max(1, sum(diff_counter.values()))
    else:
        best_offset_n, offset_share = 0, 0

    avg_sim = sum(r[2] for r in rows) / max(1, len(rows))
    print(f'=== aipta calibration ===')
    print(f'lib: {args.lib}  非占位题数: {total}')
    print(f'aipta: article_{args.aipta}  题数: {len(aipta_qs)}')
    print(f'平均 sim: {avg_sim:.3f}')
    print(f'高匹配 (sim≥0.7): {high_match}/{total} ({high_match/max(1,total)*100:.1f}%)')
    print(f'同 qn 命中 (sim≥0.7 且 qn 完全相等): {same_qn_hit}/{total}')
    if best_offset is not None:
        print(f'qn 偏移众数: lib_qn - aipta_qn = **{best_offset}**  '
              f'(支持票 {best_offset_n}, 占 {offset_share*100:.1f}%)')
    print()
    if best_offset is not None and offset_share >= 0.6:
        judgment = f'SAME-WITH-OFFSET (同源，offset={best_offset})'
    elif high_match / max(1, total) >= 0.6:
        judgment = 'SAME (高度同源，可直接 sim 救援)'
    elif high_match / max(1, total) >= 0.3:
        judgment = 'OFFSET (题号偏移但不稳定，需手动检查)'
    else:
        judgment = 'DIFFERENT (基本不同卷，建议换 aipta article)'
    print(f'判定: {judgment}')
    print()
    # 详细前 30 行
    print('qn  | aipta_qn | sim   | aipta_stem')
    for qn, aqn, score, stem in sorted(rows, key=lambda r: r[0])[:30]:
        aqn_s = str(aqn) if aqn is not None else '-'
        print(f'{qn:3d} | {aqn_s:>8} | {score:.3f} | {stem}')


if __name__ == '__main__':
    main()
