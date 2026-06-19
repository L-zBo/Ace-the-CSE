"""D-16 L-8b lib 重复 ID 审计（**只 audit 不删**）

发现 126 个重复 ID **不是真重复**——是两套真题被合并到同一 paperKey
（如 institution_2020_a 装了 7.25 + 10.24 两卷的 changshi 题，同 ID
不同题）。删除会丢真题，必须**先重新 paperKey 拆分**才能做 dedup。

本工具仅落 audit 报告，不修改 lib。
"""
import argparse
import glob
import json
from collections import defaultdict
from pathlib import Path

MARKERS = ['[选项 OCR 抽取失败-D11]', '[暂缺]', '[题干 OCR 抽取失败-D11]', '[题干/选项 OCR 抽取失败-D11]']
DERIVED = ['[由解析推导-D16L2]', '[由aipta救援-D16L3]', '[由WebSearch救援-D16L6]']


def is_bad_opt(s):
    if not s: return True
    s = s.strip()
    if not s or s in ('缺失', '暂缺'): return True
    if any(d in s for d in DERIVED): return False
    return any(m in s for m in MARKERS)


def is_placeholder(q):
    c = q.get('content', '') or ''
    if any(m in c for m in MARKERS): return True
    opts = q.get('options', []) or []
    bad = sum(1 for o in opts
              if is_bad_opt((o.get('content', '') or '') if isinstance(o, dict) else str(o)))
    return bad >= 2


def score_completeness(q):
    """打分：越完整越高"""
    s = 0
    if not is_placeholder(q): s += 100
    if (q.get('content') or '').strip() and not any(m in q['content'] for m in MARKERS): s += 20
    s += len((q.get('explanation') or '')[:500]) // 50
    opts = q.get('options', []) or []
    s += sum(5 for o in opts
             if not is_bad_opt((o.get('content', '') or '') if isinstance(o, dict) else str(o)))
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true',
                    help='**慎用** apply 会删 dup（已确认非真重复才用）')
    args = ap.parse_args()
    if args.apply:
        print('!!! L-8b 发现的 dup 多数是合并 bug 而非真重复，强烈不建议 apply')
        print('!!! 建议先按 paperKey 拆分两套卷后再考虑 dedup')
        import sys; sys.exit(1)

    total_removed = 0
    files_touched = 0
    report = []
    for fp in sorted(glob.glob('src/data/xingce/**/*.json', recursive=True)):
        lib = json.loads(Path(fp).read_text(encoding='utf-8'))
        # 按 id 分组
        by_id = defaultdict(list)
        for i, q in enumerate(lib):
            by_id[q.get('id', f'__noid_{i}')].append((i, q))
        # 找重复
        dups = {qid: rows for qid, rows in by_id.items() if len(rows) > 1 and not qid.startswith('__noid')}
        if not dups: continue
        files_touched += 1
        # 决定每组保留哪个
        keep_indices = set()
        for qid, rows in dups.items():
            best = max(rows, key=lambda r: score_completeness(r[1]))
            keep_indices.add(best[0])
            for r in rows:
                if r[0] != best[0]:
                    total_removed += 1
                    report.append({
                        'fp': fp, 'qid': qid,
                        'keep_score': score_completeness(best[1]),
                        'remove_score': score_completeness(r[1]),
                        'keep_placeholder': is_placeholder(best[1]),
                        'remove_placeholder': is_placeholder(r[1]),
                        'keep_stem': (best[1].get('content', '') or '')[:40],
                        'remove_stem': (r[1].get('content', '') or '')[:40],
                    })
        # 重建：dup 组中只保留 best；非 dup 全部保留
        if args.apply:
            new_lib = []
            keep_first_seen = {qid: False for qid in dups}
            for i, q in enumerate(lib):
                qid = q.get('id', '')
                if qid in dups:
                    if i in keep_indices:
                        new_lib.append(q)
                else:
                    new_lib.append(q)
            Path(fp).write_text(json.dumps(new_lib, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'[{"APPLY" if args.apply else "DRY-RUN"}] 文件 {files_touched}, 删 {total_removed} 题')
    for r in report[:15]:
        print(f'  {Path(r["fp"]).name}  {r["qid"]}')
        print(f'    keep   (score={r["keep_score"]} ph={r["keep_placeholder"]}): {r["keep_stem"]}')
        print(f'    remove (score={r["remove_score"]} ph={r["remove_placeholder"]}): {r["remove_stem"]}')
    if len(report) > 15:
        print(f'  ... 还有 {len(report) - 15} 条')

    Path('data/aipta_cache').mkdir(exist_ok=True, parents=True)
    Path('data/aipta_cache/l8b_dedup.md').write_text('\n'.join([
        f'# L-8b dedup ({"APPLY" if args.apply else "DRY-RUN"})',
        f'- files = {files_touched}',
        f'- removed = {total_removed}',
        '',
        *[
            f'- **{r["qid"]}** ({Path(r["fp"]).name})\n'
            f'  - keep   (score={r["keep_score"]} ph={r["keep_placeholder"]}): `{r["keep_stem"]}`\n'
            f'  - remove (score={r["remove_score"]} ph={r["remove_placeholder"]}): `{r["remove_stem"]}`'
            for r in report
        ],
    ]), encoding='utf-8')


if __name__ == '__main__':
    main()
