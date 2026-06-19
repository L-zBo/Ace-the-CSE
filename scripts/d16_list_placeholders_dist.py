"""D-16 L-0b 全库扫占位题分布（按模块 / paperKey 类别），评估各源潜在救援空间"""
import glob
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

MARKERS = [
    '[题干 OCR 抽取失败-D11]',
    '[选项 OCR 抽取失败-D11]',
    '[题干/选项 OCR 抽取失败-D11]',
    '[暂缺]',
]


def is_bad(q):
    content = q.get('content', '') or ''
    if any(m in content for m in MARKERS):
        return True
    for o in q.get('options', []) or []:
        c = (o.get('content', '') or '') if isinstance(o, dict) else str(o)
        if any(m in c for m in MARKERS):
            return True
    return False


def classify_paper_key(stem: str) -> str:
    """根据文件名推断类别"""
    if stem.startswith('institution_'):
        return 'institution'
    if stem.startswith('national_'):
        return 'national'
    if stem.startswith('provincial_'):
        return 'provincial'
    if stem.startswith('xuandiao_'):
        return 'xuandiao'
    return 'other'


def main():
    modules = ['panduan', 'changshi', 'shuliang', 'ziliao', 'yanyu']
    summary = Counter()
    by_class = defaultdict(lambda: Counter())  # paper_class -> module -> count
    by_paper = Counter()  # paperKey -> count
    files_bad = defaultdict(list)

    for mod in modules:
        for fp in sorted(glob.glob(f'src/data/xingce/{mod}/*.json')):
            stem = Path(fp).stem
            cls = classify_paper_key(stem)
            try:
                lib = json.loads(Path(fp).read_text(encoding='utf-8'))
            except Exception as e:
                print(f'[ERR] {fp}: {e}', file=sys.stderr)
                continue
            bad = [q['id'] for q in lib if is_bad(q)]
            if bad:
                summary[mod] += len(bad)
                by_class[cls][mod] += len(bad)
                by_paper[f'{mod}/{stem}'] = len(bad)
                files_bad[f'{mod}/{stem}'] = bad

    out = []
    out.append('# D-16 L-0b 全库占位题分布扫描')
    out.append('')
    out.append('## 模块汇总')
    grand = sum(summary.values())
    for m in modules:
        c = summary.get(m, 0)
        out.append(f'- {m}: {c}')
    out.append(f'- **合计: {grand}**')
    out.append('')
    out.append('## 按 paperKey 类别 × 模块（潜在源匹配）')
    out.append('| 类别 | panduan | changshi | shuliang | ziliao | yanyu | 小计 |')
    out.append('|---|---:|---:|---:|---:|---:|---:|')
    for cls in ['national', 'provincial', 'institution', 'xuandiao', 'other']:
        row = [cls]
        ss = 0
        for m in modules:
            c = by_class[cls].get(m, 0)
            row.append(str(c))
            ss += c
        row.append(str(ss))
        out.append('| ' + ' | '.join(row) + ' |')
    out.append('')
    out.append('## 缺题数 top 30 paperKey')
    for k, c in by_paper.most_common(30):
        out.append(f'  - {c:>3}  {k}')

    Path('data/ango_cache').mkdir(exist_ok=True)
    Path('data/ango_cache/placeholders_dist.md').write_text(
        '\n'.join(out), encoding='utf-8'
    )
    print(f'[placeholders] wrote data/ango_cache/placeholders_dist.md')
    print(f'  total = {grand}')
    print(f'  by class: {dict(sum(by_class.values(), Counter()))}')
    for cls in ['national', 'provincial', 'institution', 'xuandiao', 'other']:
        ss = sum(by_class[cls].values())
        print(f'  {cls}: {ss}')


if __name__ == '__main__':
    main()
