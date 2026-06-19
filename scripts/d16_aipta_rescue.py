"""D-16 L-3d aipta 救援工具：按 (lib paper, aipta article, offset) 救占位题

逻辑：
  1. 用 lib 中非占位题 sim 比对 aipta，自动算 offset
  2. 对每个 lib 占位题：
     - aipta_qn = lib_qn - offset
     - 找 aipta 卷里这道题
     - 用 lib 占位题残留信息（残留 options / orig_stem 注释）做 sim 二次校验
     - 通过 → 替换 lib content + 缺失 options（加 [由aipta救援-D16L3] marker）
  3. dry-run 模式默认，--apply 实写

用法：
  python scripts/d16_aipta_rescue.py --lib src/data/xingce/ziliao/institution_2020_e.json --aipta 2243
  python scripts/d16_aipta_rescue.py --lib ... --aipta ... --apply
"""
import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

MARKERS = [
    '[题干 OCR 抽取失败-D11]',
    '[选项 OCR 抽取失败-D11]',
    '[题干/选项 OCR 抽取失败-D11]',
    '[暂缺]',
]
DERIVED_MARKER_D16L2 = '[由解析推导-D16L2]'
AIPTA_MARKER = '[由aipta救援-D16L3]'
ORIG_CONTENT_RE = re.compile(r"原 content\s*[:：]\s*['\"](.+?)['\"]")


def is_bad_opt(s: str) -> bool:
    if s is None: return True
    s2 = s.strip()
    if not s2 or s2 in ('缺失', '暂缺'): return True
    if DERIVED_MARKER_D16L2 in s: return False  # 已被 L-2 处理（更可信本地，不要冲掉）
    return any(m in s2 for m in MARKERS)


def is_bad_stem(s: str) -> bool:
    if not s: return True
    return any(m in s for m in MARKERS)


def norm(s: str, n: int = 80) -> str:
    if not s: return ''
    s = re.sub(r'\s+', '', s)
    # 归一化分隔符 / 括号差异（中英全角混用是 OCR 常见噪声）
    table = {'∶': ':', '：': ':', '；': ';', '，': ',', '（': '(', '）': ')',
             '【': '[', '】': ']', '《': '<', '》': '>'}
    s = s.translate(str.maketrans(table))
    return s[:n]


def sim(a: str, b: str, n: int = 80) -> float:
    return SequenceMatcher(None, norm(a, n), norm(b, n)).ratio()


def get_qn(qid: str) -> int:
    try: return int(qid.rsplit('-', 1)[-1])
    except: return -1


def extract_orig_content(content: str) -> str:
    """lib 题干 OCR 失败时，可能有 '原 content: xxx' 注释"""
    m = ORIG_CONTENT_RE.search(content or '')
    return m.group(1) if m else ''


def detect_offset(lib_qs, aipta_qs, window: int = 100) -> tuple:
    """从 lib 非占位题与 aipta 全卷 sim 比对，识别 offset 众数"""
    diffs = Counter()
    pairs = []
    for q in lib_qs:
        stem = q.get('content', '') or ''
        if is_bad_stem(stem): continue
        qn = get_qn(q.get('id', ''))
        if qn < 0: continue
        best_aqn = None
        best_s = 0
        for aq in aipta_qs:
            if abs(aq['qn'] - qn) > window: continue
            s = sim(stem, aq.get('stem', ''))
            if s > best_s:
                best_s = s
                best_aqn = aq['qn']
        if best_s >= 0.85 and best_aqn is not None:
            diffs[qn - best_aqn] += 1
            pairs.append((qn, best_aqn, best_s))
    if not diffs:
        return None, 0, 0, pairs
    offset, cnt = diffs.most_common(1)[0]
    return offset, cnt, sum(diffs.values()), pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lib', required=True)
    ap.add_argument('--aipta', type=int, required=True)
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--min-offset-share', type=float, default=0.6,
                    help='offset 众数最小占比（默认 0.6）')
    ap.add_argument('--min-stem-sim', type=float, default=0.7,
                    help='占位题残留 stem 与 aipta 候选题 stem sim 阈值')
    ap.add_argument('--min-opt-match', type=int, default=1,
                    help='lib 已有残留 option 跟 aipta 选项必须命中数')
    ap.add_argument('--no-stem-sim-check', action='store_true',
                    help='整题占位（无残留）时跳过 stem sim 校验')
    ap.add_argument('--trust-offset-share', type=float, default=0.95,
                    help='当 offset share ≥ 此阈值时，全空占位题信任 offset 直接救（不要求 opt 命中）')
    args = ap.parse_args()

    lib_path = Path(args.lib)
    aipta_path = Path(f'data/aipta_cache/article_{args.aipta}.json')
    if not lib_path.exists(): sys.exit(f'!! lib 不存在: {lib_path}')
    if not aipta_path.exists(): sys.exit(f'!! aipta cache 不存在: {aipta_path}')

    lib = json.loads(lib_path.read_text(encoding='utf-8'))
    aipta = json.loads(aipta_path.read_text(encoding='utf-8'))
    aipta_qs = aipta['questions']
    aipta_by_qn = {q['qn']: q for q in aipta_qs}

    # 1. 算 offset
    offset, cnt, total, pairs = detect_offset(lib, aipta_qs)
    if offset is None:
        print(f'!! 无法识别 offset（无非占位 lib 题与 aipta 高 sim 配对）')
        sys.exit(1)
    share = cnt / max(1, total)
    print(f'[offset] lib_qn - aipta_qn = {offset}  支持票 {cnt}/{total} ({share*100:.1f}%)')
    if share < args.min_offset_share:
        print(f'!! offset 不稳定（占比 {share*100:.1f}% < {args.min_offset_share*100:.0f}%），拒绝救援')
        sys.exit(1)

    # 2. 对每个 lib 占位题，找 aipta 对应题，sim 校验，准备 replacement
    rescues = []
    skipped = []
    for q in lib:
        stem = q.get('content', '') or ''
        opts = q.get('options', []) or []
        stem_bad = is_bad_stem(stem)
        opt_bad_count = sum(1 for o in opts
                            if is_bad_opt((o.get('content', '') or '') if isinstance(o, dict) else str(o)))
        if not (stem_bad or opt_bad_count > 0): continue

        qn = get_qn(q.get('id', ''))
        if qn < 0: continue
        target_aqn = qn - offset
        aq = aipta_by_qn.get(target_aqn)
        if aq is None:
            skipped.append((qn, f'aipta 无 q{target_aqn}'))
            continue

        # 校验 1：题干 sim（如果 lib 有 stem）
        ref_stem = stem if not stem_bad else extract_orig_content(stem)
        if ref_stem and not args.no_stem_sim_check:
            ss = sim(ref_stem, aq.get('stem', ''))
            if ss < args.min_stem_sim:
                skipped.append((qn, f'stem sim {ss:.2f} < {args.min_stem_sim} aipta=q{target_aqn} stem={aq["stem"][:30]}'))
                continue

        # 校验 2：lib 残留 options 与 aipta 选项 sim
        opt_hits = 0
        aipta_opts = {o['label']: o['content'] for o in aq.get('options', [])}
        for i, o in enumerate(opts):
            if i >= 4: break
            label = o.get('label', chr(65 + i)) if isinstance(o, dict) else chr(65 + i)
            cur = (o.get('content', '') or '') if isinstance(o, dict) else str(o)
            if is_bad_opt(cur): continue
            # 已有非占位选项，跟 aipta 同 label 选项做 sim
            target = aipta_opts.get(label, '')
            if not target: continue
            if sim(cur, target, 30) >= 0.7:
                opt_hits += 1

        # 全空占位题：opt_hits 必然=0，但允许通过（依赖 stem sim 或 trust-offset）
        n_real_opts = sum(1 for o in opts
                          if not is_bad_opt((o.get('content', '') or '') if isinstance(o, dict) else str(o)))
        offset_trusted = share >= args.trust_offset_share
        if n_real_opts >= 1 and opt_hits < args.min_opt_match:
            skipped.append((qn, f'opt_hits={opt_hits} < {args.min_opt_match}（残留选项不匹配）'))
            continue
        if n_real_opts == 0 and not offset_trusted:
            skipped.append((qn, f'全空占位且 offset share {share*100:.0f}% < {args.trust_offset_share*100:.0f}%（需更高信心源）'))
            continue

        # 通过 → 准备 replacement
        new_content = aq.get('stem', '') or stem
        new_options = []
        changes = {'stem': False, 'opts': []}
        for i, o in enumerate(opts):
            if i >= 4: break
            label = o.get('label', chr(65 + i)) if isinstance(o, dict) else chr(65 + i)
            cur = (o.get('content', '') or '') if isinstance(o, dict) else str(o)
            target = aipta_opts.get(label, '')
            if is_bad_opt(cur) and target:
                new_options.append({'label': label, 'content': f'{AIPTA_MARKER} {target}'})
                changes['opts'].append((label, cur[:25], target[:30]))
            else:
                new_options.append({'label': label, 'content': cur} if isinstance(o, dict) else
                                   {'label': label, 'content': str(o)})
        if stem_bad and aq.get('stem'):
            new_content = f'{AIPTA_MARKER} {aq["stem"]}'
            changes['stem'] = True

        if not (changes['stem'] or changes['opts']):
            skipped.append((qn, '已无可补字段（？）'))
            continue

        rescues.append({
            'qid': q['id'],
            'qn': qn,
            'aipta_qn': target_aqn,
            'changes': changes,
            'new_content': new_content,
            'new_options': new_options,
        })

    # 3. dry-run 报告
    print(f'\n[救援计划] {len(rescues)} 题  跳过 {len(skipped)} 题')
    for r in rescues:
        print(f'  ✓ q{r["qn"]:03d} → aipta q{r["aipta_qn"]:03d}  '
              f'stem={"Y" if r["changes"]["stem"] else "-"}  '
              f'opts={[(c[0]) for c in r["changes"]["opts"]]}')
    print('\n[skip]')
    for qn, reason in skipped[:20]:
        print(f'  - q{qn:03d}  {reason}')

    if args.apply and rescues:
        # 写回
        rescue_qids = {r['qid']: r for r in rescues}
        new_lib = []
        for q in lib:
            qid = q.get('id', '')
            if qid in rescue_qids:
                r = rescue_qids[qid]
                # 备份原 options（含 _legacy_options if any）
                if '_legacy_options' not in q:
                    q['_legacy_options'] = json.loads(json.dumps(q.get('options', [])))
                if r['changes']['stem']:
                    if '_legacy_content' not in q:
                        q['_legacy_content'] = q.get('content', '')
                    q['content'] = r['new_content']
                q['options'] = r['new_options']
            new_lib.append(q)
        lib_path.write_text(
            json.dumps(new_lib, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        print(f'\n[APPLY] 写回 {lib_path}')

    # 落报告
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    Path('data/aipta_cache').mkdir(parents=True, exist_ok=True)
    rpt = Path(f'data/aipta_cache/l3d_{"apply" if args.apply else "plan"}_{Path(args.lib).stem}_{args.aipta}_{ts}.md')
    rpt.write_text('\n'.join([
        f'# L-3d {("APPLY" if args.apply else "DRY-RUN")} {Path(args.lib).stem} × aipta_{args.aipta}',
        f'offset={offset}  支持票 {cnt}/{total} ({share*100:.1f}%)',
        f'rescues={len(rescues)} skipped={len(skipped)}',
        '',
        '## rescues',
        *[f'- q{r["qn"]:03d} → aipta q{r["aipta_qn"]:03d}  stem={"Y" if r["changes"]["stem"] else "-"} opts={[c[0] for c in r["changes"]["opts"]]}' for r in rescues],
        '',
        '## skipped',
        *[f'- q{qn:03d}  {reason}' for qn, reason in skipped],
    ]), encoding='utf-8')
    print(f'报告 -> {rpt}')


if __name__ == '__main__':
    main()
