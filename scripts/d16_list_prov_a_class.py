"""D-16 L-5a 列残余 provincial A 类占位题（题干完整 + 部分选项缺，可搜的）"""
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
DERIVED_MARKERS = ['[由解析推导-D16L2]', '[由aipta救援-D16L3]']
PDF_MISSING_HINT = 'PDF 题目缺失'


def is_bad_opt(s):
    if s is None: return True
    s2 = s.strip()
    if not s2 or s2 in ('缺失', '暂缺'): return True
    if any(d in s for d in DERIVED_MARKERS): return False
    return any(m in s2 for m in MARKERS)


def main():
    by_paper = defaultdict(list)
    for mod in ['panduan', 'changshi', 'shuliang', 'ziliao', 'yanyu']:
        for fp in sorted(glob.glob(f'src/data/xingce/{mod}/provincial_*.json')):
            stem = Path(fp).stem
            lib = json.loads(Path(fp).read_text(encoding='utf-8'))
            for q in lib:
                content = q.get('content', '') or ''
                opts = q.get('options', []) or []
                if PDF_MISSING_HINT in (q.get('explanation', '') or ''): continue
                stem_bad = any(m in content for m in MARKERS)
                if stem_bad: continue  # 仅 A_opts_partial（题干在的）
                if len(content) < 20: continue
                opt_bad_cnt = sum(1 for o in opts
                                  if is_bad_opt((o.get('content', '') or '') if isinstance(o, dict) else str(o)))
                if opt_bad_cnt == 0: continue
                qid = q['id']
                qn_str = qid.rsplit('-', 1)[-1]
                try: qn = int(qn_str)
                except: continue
                # 资料分析题（含「以下哪个」「占比」「增长率」等图表词）救援难，标记
                is_chart = any(k in content for k in ['饼图', '柱状图', '折线图', '以下哪个', '增长率最', '占比'])
                by_paper[f'{mod}/{stem}'].append({
                    'qn': qn,
                    'qid': qid,
                    'is_chart': is_chart,
                    'stem': content.replace('\n', ' ').strip()[:90],
                    'bad_count': opt_bad_cnt,
                    'answer': q.get('answer'),
                })

    grand = sum(len(v) for v in by_paper.values())
    chart_count = sum(1 for v in by_paper.values() for x in v if x['is_chart'])
    out = ['# D-16 L-5a 残余 A 类 provincial 占位题（可搜 / 不含 PDF 缺）']
    out.append('')
    out.append(f'- 总题数: {grand}')
    out.append(f'- 资料分析图表题（搜难命中）: {chart_count}')
    out.append(f'- 文字题（搜易命中）: {grand - chart_count}')
    out.append('')
    out.append('## 按 paperKey × qn')
    for pk in sorted(by_paper, key=lambda x: -len(by_paper[x])):
        items = by_paper[pk]
        chart = sum(1 for x in items if x['is_chart'])
        out.append(f'### {pk}  (共{len(items)}, 图表{chart})')
        for it in sorted(items, key=lambda x: x['qn']):
            tag = ' 📊' if it['is_chart'] else ''
            out.append(f'- q{it["qn"]:03d} ans={it["answer"]} bad={it["bad_count"]}{tag}  `{it["stem"]}`')
        out.append('')

    Path('data/aipta_cache').mkdir(parents=True, exist_ok=True)
    Path('data/aipta_cache/l5a_prov_a_class.md').write_text('\n'.join(out), encoding='utf-8')
    print(f'[L-5a] wrote data/aipta_cache/l5a_prov_a_class.md')
    print(f'  total = {grand}, chart = {chart_count}, text = {grand - chart_count}')
    print('  top paper:')
    for pk in sorted(by_paper, key=lambda x: -len(by_paper[x]))[:10]:
        print(f'    {len(by_paper[pk]):>2}  {pk}')


if __name__ == '__main__':
    main()
