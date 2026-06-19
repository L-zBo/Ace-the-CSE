"""D-16 L-4a 判断题 schema 修复：识别只有 A=正确/B=错误的题，删 C/D 占位"""
import glob
import json
import re
from pathlib import Path

MARKERS = [
    '[题干 OCR 抽取失败-D11]',
    '[选项 OCR 抽取失败-D11]',
    '[题干/选项 OCR 抽取失败-D11]',
    '[暂缺]',
]


def is_bad(s):
    if not s: return True
    s2 = (s or '').strip()
    if s2 in ('缺失', '暂缺'): return True
    return any(m in s2 for m in MARKERS)


def is_true_false_question(q):
    """检测判断题：title 含「判断题」标记 或 A=正确 B=错误"""
    content = (q.get('content', '') or '')
    if '判断题' in content[:20]:
        return True
    opts = q.get('options', []) or []
    if len(opts) < 2: return False
    # A 选项 = 正确，B 选项 = 错误
    a_content = (opts[0].get('content') if isinstance(opts[0], dict) else str(opts[0])) or ''
    b_content = (opts[1].get('content') if isinstance(opts[1], dict) else str(opts[1])) or ''
    return a_content.strip() == '正确' and b_content.strip() == '错误'


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    candidates = []
    for mod in ['panduan', 'changshi', 'shuliang', 'ziliao', 'yanyu']:
        for fp in sorted(glob.glob(f'src/data/xingce/{mod}/*.json')):
            lib = json.loads(Path(fp).read_text(encoding='utf-8'))
            for q in lib:
                if not is_true_false_question(q): continue
                opts = q.get('options', []) or []
                if len(opts) <= 2: continue
                # 有 >2 选项 → 看 C/D 是不是占位
                cd_bad = sum(1 for o in opts[2:]
                             if is_bad((o.get('content', '') or '') if isinstance(o, dict) else str(o)))
                if cd_bad == 0: continue
                candidates.append({
                    'fp': fp,
                    'qid': q['id'],
                    'stem': (q.get('content', '') or '')[:60],
                    'opts': [
                        ((o.get('content', '') or '') if isinstance(o, dict) else str(o))[:30]
                        for o in opts
                    ],
                    'answer': q.get('answer'),
                })

    print(f'判断题 schema bug 候选: {len(candidates)} 题')
    by_fp = {}
    for c in candidates:
        by_fp.setdefault(c['fp'], []).append(c)
    for fp, lst in sorted(by_fp.items(), key=lambda x: -len(x[1])):
        print(f'  {len(lst):>3}  {Path(fp).name}')

    if args.apply:
        for fp, lst in by_fp.items():
            lib = json.loads(Path(fp).read_text(encoding='utf-8'))
            qids = {c['qid'] for c in lst}
            for q in lib:
                if q.get('id') not in qids: continue
                if '_legacy_options' not in q:
                    q['_legacy_options'] = json.loads(json.dumps(q.get('options', [])))
                # 仅保留 A B 两选项
                q['options'] = q['options'][:2]
            Path(fp).write_text(
                json.dumps(lib, ensure_ascii=False, indent=2),
                encoding='utf-8',
            )
        print(f'\n[APPLY] 修复 {sum(len(v) for v in by_fp.values())} 题')

    # 写报告
    out = ['# D-16 L-4a 判断题 schema 修复']
    out.append(f'- 候选题: {len(candidates)}')
    out.append('')
    for c in candidates:
        out.append(f'- **{c["qid"]}**  ans={c["answer"]}')
        out.append(f'  - stem: `{c["stem"]}`')
        for i, o in enumerate(c['opts']):
            out.append(f'  - {chr(65+i)}: `{o}`')
        out.append('')
    Path('data/aipta_cache/l4a_truefalse.md').write_text('\n'.join(out), encoding='utf-8')
    print(f'报告: data/aipta_cache/l4a_truefalse.md')


if __name__ == '__main__':
    main()
