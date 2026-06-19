"""D-16 L-1a 精细分类占位题：A 类（OCR 部分失败，可搜）vs B 类（PDF 整题缺，搜不到）"""
import glob
import json
from collections import Counter, defaultdict
from pathlib import Path

MARKERS = [
    '[题干 OCR 抽取失败-D11]',
    '[选项 OCR 抽取失败-D11]',
    '[题干/选项 OCR 抽取失败-D11]',
    '[暂缺]',
]
PDF_MISSING_HINT = 'PDF 题目缺失'


def classify(q) -> str:
    """A = 题干在/部分选项在 / B = 全空 (PDF 缺) / Z = 异常"""
    content = q.get('content', '') or ''
    explanation = q.get('explanation', '') or ''
    options = q.get('options', []) or []

    stem_bad = any(m in content for m in MARKERS)
    opts_bad_count = sum(
        1 for o in options
        if any(m in ((o.get('content', '') or '') if isinstance(o, dict) else str(o))
               for m in MARKERS) or (
            isinstance(o, dict) and (o.get('content') or '').strip() == '缺失'
        ) or str(o).strip() == '缺失'
    )

    # B 类：明确标记 PDF 缺
    if PDF_MISSING_HINT in explanation:
        return 'B_pdf_missing'
    # B 类：题干 + 全部选项全空
    if stem_bad and opts_bad_count == len(options) and options:
        return 'B_all_empty'
    # A 类：题干在，部分选项缺
    if not stem_bad and opts_bad_count > 0:
        return 'A_opts_partial'
    # A 类：题干缺，部分选项在（少见）
    if stem_bad and 0 < opts_bad_count < len(options):
        return 'A_stem_only'
    # A 类：题干在，全选项 OK 但占位识别命中（应该不会有）
    if not stem_bad and opts_bad_count == 0:
        return 'A_unknown'
    return 'Z_other'


def is_bad(q):
    content = q.get('content', '') or ''
    if any(m in content for m in MARKERS):
        return True
    for o in q.get('options', []) or []:
        c = (o.get('content', '') or '') if isinstance(o, dict) else str(o)
        if any(m in c for m in MARKERS):
            return True
        if isinstance(o, dict) and (o.get('content') or '').strip() == '缺失':
            return True
        if str(o).strip() == '缺失':
            return True
    return False


def main():
    classes = Counter()
    by_paper_class = defaultdict(Counter)
    samples = defaultdict(list)

    for mod in ['panduan', 'changshi', 'shuliang', 'ziliao', 'yanyu']:
        for fp in sorted(glob.glob(f'src/data/xingce/{mod}/*.json')):
            stem = Path(fp).stem
            lib = json.loads(Path(fp).read_text(encoding='utf-8'))
            for q in lib:
                if not is_bad(q):
                    continue
                cls = classify(q)
                classes[cls] += 1
                by_paper_class[f'{mod}/{stem}'][cls] += 1
                if len(samples[cls]) < 3:
                    samples[cls].append({
                        'id': q.get('id'),
                        'paper': f'{mod}/{stem}',
                        'content_head': (q.get('content', '') or '')[:80],
                        'opts': [
                            ((o.get('content', '') or '') if isinstance(o, dict) else str(o))[:30]
                            for o in (q.get('options', []) or [])
                        ],
                        'exp_head': (q.get('explanation', '') or '')[:80],
                        'answer': q.get('answer'),
                    })

    out = []
    out.append('# D-16 L-1a 占位题精细分类（A 可救 / B 救不了）')
    out.append('')
    out.append('## 分类统计')
    grand = sum(classes.values())
    for c, n in classes.most_common():
        pct = n / grand * 100
        out.append(f'- {c}: **{n}** ({pct:.1f}%)')
    out.append(f'- **合计: {grand}**')
    out.append('')

    A_total = sum(v for k, v in classes.items() if k.startswith('A_'))
    B_total = sum(v for k, v in classes.items() if k.startswith('B_'))
    out.append(f'## 救援上限')
    out.append(f'- A 类（搜索/视觉模型可救）: **{A_total}**')
    out.append(f'- B 类（PDF 整题缺，互联网回忆版也没）: **{B_total}**')
    out.append('')

    out.append('## 各类样本')
    for c in ['A_opts_partial', 'A_stem_only', 'A_unknown', 'B_pdf_missing', 'B_all_empty']:
        if c in samples:
            out.append(f'### {c}')
            for s in samples[c]:
                out.append(f'- **{s["id"]}**')
                out.append(f'  - content: `{s["content_head"]}`')
                for i, o in enumerate(s['opts']):
                    out.append(f'  - {chr(65+i)}: `{o}`')
                out.append(f'  - answer: {s["answer"]}  exp: `{s["exp_head"]}`')
            out.append('')

    out.append('## 缺题 top 20 paperKey 的类别分布')
    sorted_papers = sorted(by_paper_class.items(), key=lambda x: -sum(x[1].values()))
    for pk, dist in sorted_papers[:20]:
        total = sum(dist.values())
        parts = ' '.join(f'{k}={v}' for k, v in dist.items())
        out.append(f'- {total:>2}  {pk}  ({parts})')

    Path('data/ango_cache/placeholders_classified.md').write_text(
        '\n'.join(out), encoding='utf-8'
    )
    print(f'[classify] wrote data/ango_cache/placeholders_classified.md')
    print(f'  A (可救): {A_total}, B (救不了): {B_total}')
    for c, n in classes.most_common():
        print(f'    {c}: {n}')


if __name__ == '__main__':
    main()
