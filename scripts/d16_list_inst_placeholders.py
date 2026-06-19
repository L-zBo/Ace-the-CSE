"""D-16 L-3a 列 institution_* 全部占位题 (paperKey × qn) 清单，用于 aipta 抓取规划"""
import glob
import json
from collections import defaultdict
from pathlib import Path

MARKERS = [
    '[题干 OCR 抽取失败-D11]',
    '[选项 OCR 抽取失败-D11]',
    '[题干/选项 OCR 抽取失败-D11]',
    '[暂缺]',
]
DERIVED_MARKER = '[由解析推导-D16L2]'
PDF_MISSING_HINT = 'PDF 题目缺失'


def is_bad(q):
    content = q.get('content', '') or ''
    if any(m in content for m in MARKERS): return True
    for o in q.get('options', []) or []:
        c = (o.get('content', '') or '') if isinstance(o, dict) else str(o)
        if DERIVED_MARKER in c: continue  # 已被 L-2 反推的不算占位
        if any(m in c for m in MARKERS): return True
        if c.strip() in ('缺失', '暂缺'): return True
    return False


def is_pdf_missing(q):
    """B 类：PDF 整题缺。L-3 也救不了，aipta 同样缺。"""
    return PDF_MISSING_HINT in (q.get('explanation', '') or '')


def main():
    inst_papers = defaultdict(list)
    pdf_missing_count = 0
    inst_pdf_missing_count = 0

    for mod in ['panduan', 'changshi', 'shuliang', 'ziliao', 'yanyu']:
        for fp in sorted(glob.glob(f'src/data/xingce/{mod}/institution_*.json')):
            stem = Path(fp).stem
            lib = json.loads(Path(fp).read_text(encoding='utf-8'))
            for q in lib:
                if not is_bad(q): continue
                qid = q.get('id', '')
                qn_str = qid.rsplit('-', 1)[-1]
                try: qn = int(qn_str)
                except: continue
                pm = is_pdf_missing(q)
                if pm:
                    pdf_missing_count += 1
                    inst_pdf_missing_count += 1
                inst_papers[f'{mod}/{stem}'].append({
                    'qn': qn,
                    'qid': qid,
                    'pdf_missing': pm,
                    'stem_head': (q.get('content', '') or '')[:50],
                })

    out = []
    out.append('# D-16 L-3a institution_* 占位题清单（aipta 抓取规划）')
    out.append('')
    out.append(f'- 文件总数: {len(inst_papers)}')
    out.append(f'- 占位题总数: {sum(len(v) for v in inst_papers.values())}')
    out.append(f'- 其中 B 类 PDF 缺（aipta 救不了）: {inst_pdf_missing_count}')
    out.append(f'- A 类（aipta 有望救）: {sum(len(v) for v in inst_papers.values()) - inst_pdf_missing_count}')
    out.append('')
    out.append('## 按 paperKey 分组')
    for pk in sorted(inst_papers.keys()):
        items = inst_papers[pk]
        a_n = sum(1 for x in items if not x['pdf_missing'])
        b_n = sum(1 for x in items if x['pdf_missing'])
        out.append(f'### {pk}  (A={a_n}, B={b_n})')
        for it in sorted(items, key=lambda x: x['qn']):
            tag = ' [PDF 缺]' if it['pdf_missing'] else ''
            out.append(f'- q{it["qn"]:03d}{tag}  `{it["stem_head"]}`')
        out.append('')

    Path('data/aipta_cache').mkdir(parents=True, exist_ok=True)
    Path('data/aipta_cache/inst_placeholders.md').write_text(
        '\n'.join(out), encoding='utf-8'
    )
    print(f'[L-3a] wrote data/aipta_cache/inst_placeholders.md')
    print(f'  institution placeholders: {sum(len(v) for v in inst_papers.values())} (A={sum(len(v) for v in inst_papers.values()) - inst_pdf_missing_count}, B={inst_pdf_missing_count})')


if __name__ == '__main__':
    main()
