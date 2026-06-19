"""D-16 L-8 cross-paper 借题救援：联考多省共题，一卷占位另一卷非占位时跨借

逻辑：建立全库 (year, module, qn) → [(paperKey, q)] 索引，对每个
占位题查同 key 是否有非占位题，sim 校验后借用。

用法：
  python scripts/d16_cross_paper_rescue.py            # dry-run
  python scripts/d16_cross_paper_rescue.py --apply
"""
import argparse
import glob
import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

MARKERS = [
    '[选项 OCR 抽取失败-D11]',
    '[暂缺]',
    '[题干 OCR 抽取失败-D11]',
    '[题干/选项 OCR 抽取失败-D11]',
]
DERIVED = ['[由解析推导-D16L2]', '[由aipta救援-D16L3]', '[由WebSearch救援-D16L6]']
PDF_MISSING = 'PDF 题目缺失'
CROSS_MARKER = '[由联考借题-D16L8]'


def is_bad_opt(s):
    if not s: return True
    s = s.strip()
    if not s or s in ('缺失', '暂缺'): return True
    if any(d in s for d in DERIVED): return False
    return any(m in s for m in MARKERS)


def is_bad_stem(s):
    if not s: return True
    return any(m in s for m in MARKERS)


def is_placeholder(q):
    c = q.get('content', '') or ''
    if any(m in c for m in MARKERS): return True
    opts = q.get('options', []) or []
    bad = sum(1 for o in opts
              if is_bad_opt((o.get('content', '') or '') if isinstance(o, dict) else str(o)))
    return bad >= 2


def get_qn(qid):
    try: return int(qid.rsplit('-', 1)[-1])
    except: return -1


def norm(s, n=80):
    if not s: return ''
    s = re.sub(r'\s+', '', s)
    t = {'∶': ':', '：': ':', '（': '(', '）': ')', '【': '[', '】': ']'}
    s = s.translate(str.maketrans(t))
    return s[:n]


def sim(a, b, n=80):
    return SequenceMatcher(None, norm(a, n), norm(b, n)).ratio()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--min-stem-sim', type=float, default=0.7,
                    help='占位题残留 stem 与借源题 stem sim 阈值')
    args = ap.parse_args()

    # 索引：(year, module, qn) → list of (fp, qid, q_dict)
    idx = defaultdict(list)
    all_qs = []
    for mod in ['panduan', 'changshi', 'shuliang', 'ziliao', 'yanyu']:
        for fp in sorted(glob.glob(f'src/data/xingce/{mod}/*.json')):
            lib = json.loads(Path(fp).read_text(encoding='utf-8'))
            for i, q in enumerate(lib):
                qid = q.get('id', '')
                qn = get_qn(qid)
                year = q.get('year')
                if qn < 0 or not year: continue
                key = (year, mod, qn)
                idx[key].append((fp, qid, q, i))
                all_qs.append((fp, qid, q))

    rescues = []
    skipped = []
    for fp, qid, q in all_qs:
        if not is_placeholder(q): continue
        if PDF_MISSING in (q.get('explanation', '') or ''): continue
        qn = get_qn(qid)
        year = q.get('year')
        mod = (q.get('category') or '')
        candidates = idx.get((year, mod, qn), [])
        # 找同 key 的非占位题
        donors = [(cfp, cqid, cq) for cfp, cqid, cq, _ in candidates
                  if cfp != fp and not is_placeholder(cq)]
        if not donors:
            skipped.append((qid, 'no donor'))
            continue
        # 选 sim 最高的 donor
        ref_stem = q.get('content', '') or ''
        ref_stem_clean = ref_stem if not is_bad_stem(ref_stem) else ''
        best = None
        best_s = 0
        for cfp, cqid, cq in donors:
            d_stem = cq.get('content', '') or ''
            if ref_stem_clean:
                s = sim(ref_stem_clean, d_stem)
            else:
                # 题干都缺，靠选项 sim
                ref_opts = [(o.get('content', '') or '') if isinstance(o, dict) else str(o)
                            for o in (q.get('options', []) or [])]
                d_opts = [(o.get('content', '') or '') if isinstance(o, dict) else str(o)
                          for o in (cq.get('options', []) or [])]
                hits = 0
                for ro in ref_opts:
                    if is_bad_opt(ro) or len(ro.strip()) < 5: continue
                    if any(sim(ro, dop, 30) >= 0.7 for dop in d_opts):
                        hits += 1
                s = hits / max(1, sum(1 for ro in ref_opts if not is_bad_opt(ro)))
            if s > best_s:
                best_s = s
                best = (cfp, cqid, cq)
        if best is None or best_s < args.min_stem_sim:
            skipped.append((qid, f'sim {best_s:.2f} < {args.min_stem_sim}'))
            continue
        cfp, cqid, cq = best
        # 检查答案是否一致（若双方都有非默认 answer）
        lib_ans = (q.get('answer') or '').strip()
        donor_ans = (cq.get('answer') or '').strip()
        if lib_ans and donor_ans and lib_ans != donor_ans:
            skipped.append((qid, f'answer 矛盾 lib={lib_ans} donor={donor_ans}'))
            continue
        rescues.append({
            'qid': qid, 'fp': fp,
            'donor_qid': cqid, 'donor_fp': cfp,
            'sim': best_s,
            'donor_q': cq,
        })

    print(f'[{"APPLY" if args.apply else "DRY-RUN"}] rescue 候选 {len(rescues)} 题 / skip {len(skipped)} 题')
    for r in rescues[:20]:
        print(f'  ✓ {r["qid"]}  <-  {r["donor_qid"]}  sim={r["sim"]:.2f}')
    if len(rescues) > 20:
        print(f'  ... 还有 {len(rescues) - 20} 题')

    if args.apply and rescues:
        # group by fp，写回
        by_fp = defaultdict(list)
        for r in rescues:
            by_fp[r['fp']].append(r)
        for fp, lst in by_fp.items():
            lib = json.loads(Path(fp).read_text(encoding='utf-8'))
            qid_map = {r['qid']: r for r in lst}
            for q in lib:
                if q.get('id') not in qid_map: continue
                r = qid_map[q['id']]
                dq = r['donor_q']
                # 备份原
                if '_legacy_content' not in q:
                    q['_legacy_content'] = q.get('content', '')
                if '_legacy_options' not in q:
                    q['_legacy_options'] = json.loads(json.dumps(q.get('options', [])))
                # 用 donor 替换 content + options
                new_content = dq.get('content', '') or q.get('content', '')
                if is_bad_stem(q.get('content', '') or ''):
                    q['content'] = f'{CROSS_MARKER} {new_content}'
                else:
                    q['content'] = new_content  # 题干已可读，不动
                # 选项：占位的替换
                lib_opts = q.get('options', []) or []
                d_opts = {o.get('label', ''): (o.get('content', '') or '') for o in (dq.get('options', []) or [])}
                new_opts = []
                for o in lib_opts:
                    label = o.get('label', '') if isinstance(o, dict) else ''
                    cur = (o.get('content', '') or '') if isinstance(o, dict) else str(o)
                    if is_bad_opt(cur) and label in d_opts and d_opts[label]:
                        new_opts.append({'label': label, 'content': f'{CROSS_MARKER} {d_opts[label]}'})
                    else:
                        new_opts.append(o if isinstance(o, dict) else {'label': label, 'content': cur})
                q['options'] = new_opts
            Path(fp).write_text(json.dumps(lib, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'\n[APPLY] 写回 {len(by_fp)} 文件，{len(rescues)} 题')


if __name__ == '__main__':
    main()
