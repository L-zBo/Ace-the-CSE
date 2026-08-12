"""D-17a 列出不可作答题的 paperKey × qn 完整分布

不可作答 = 占位题 + 无 questionImage，判定统一走 scripts/placeholder_lib.py
（与 src/lib/placeholder.ts 等价）。

⚠️ 早先这里自己写了一份判定：读了 markers.json 却没用 `sourcePlaceholderShort`，
还额外把「救援 marker 过的」排除在占位之外 —— 两处偏差叠加，报出来是 50，
而前端实际过滤 73。现在改为直接复用共享实现，不再自带口径。

输出 data/d17_unanswerable.json + 终端表格
"""
import json, glob, re, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from placeholder_lib import is_unanswerable  # noqa: E402


def main():
    bypaper = defaultdict(list)
    total_q = 0
    total_unans = 0

    for jp in glob.glob('src/data/*/*/*.json'):
        try:
            data = json.load(open(jp, encoding='utf-8'))
        except Exception:
            continue
        qs = data.get('questions') if isinstance(data, dict) else data
        if not isinstance(qs, list):
            continue
        base = os.path.basename(jp).replace('.json', '')
        norm = jp.replace('\\', '/')
        # 早先只扫 src/data/xingce/，申论那 652 题一直没进统计，
        # 与前端「全库过滤」的口径又差一截。改成扫全库。
        parts = norm.split('/')
        module = f'{parts[2]}/{parts[3]}'
        for q in qs:
            total_q += 1
            if is_unanswerable(q):
                total_unans += 1
                qid = q.get('id', '')
                qn = qid.split('-')[-1] if qid else '?'
                bypaper[(module, base)].append(qn)

    print(f'total_q={total_q}, total_unanswerable={total_unans}')
    print(f'distinct (module, paperKey)={len(bypaper)}')
    print()
    print('=== top (module, paperKey) by unanswerable count ===')
    rows = sorted(bypaper.items(), key=lambda x: -len(x[1]))
    for (mod, pk), qns in rows:
        print(f'  {mod:9s}  {pk:42s}  {len(qns):3d}: {",".join(qns[:8])}{"..." if len(qns)>8 else ""}')

    # 按 source_prov_year 合并
    prov_year = defaultdict(int)
    prov_year_papers = defaultdict(list)
    for (mod, pk), qns in bypaper.items():
        m = re.match(r'(provincial|institution|national)_([a-z_]+?)_(\d{4})$', pk)
        if m:
            src, prov, yr = m.groups()
            key = f'{src}_{prov}_{yr}'
            prov_year[key] += len(qns)
            prov_year_papers[key].append((mod, pk, len(qns)))
        else:
            prov_year[pk] += len(qns)
            prov_year_papers[pk].append((mod, pk, len(qns)))

    print()
    print('=== 按 paperKey base (source_prov_year) 合并 ===')
    for k, v in sorted(prov_year.items(), key=lambda x: -x[1]):
        print(f'  {k:42s}  {v:3d}')

    # 落 JSON
    out = {
        'total_q': total_q,
        'total_unanswerable': total_unans,
        'bypaper': {f'{m}/{p}': q for (m, p), q in bypaper.items()},
        'byprovyear': dict(prov_year),
    }
    os.makedirs('data', exist_ok=True)
    with open('data/d17_unanswerable.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print()
    print('saved -> data/d17_unanswerable.json')


if __name__ == '__main__':
    main()
