"""D-17a 列出 D-16 末 99 题不可作答的 paperKey × qn 完整分布

不可作答 = 占位 marker + 无 questionImage + 无救援 marker
（与 src/lib/placeholder.ts isUnanswerable 等价）

marker 唯一真相源在 src/lib/markers.json（D-17 P1-8 抽出来共享）。

输出 data/d17_unanswerable.json + 终端表格
"""
import json, glob, re, os, sys
from collections import defaultdict

with open('src/lib/markers.json', encoding='utf-8') as _f:
    _MARKERS = json.load(_f)
PLACEHOLDER_MARKERS = _MARKERS['placeholderMarkers']
SOURCE_PLACEHOLDERS = _MARKERS['sourcePlaceholderShort']
RECOVERY_MARKERS = list(_MARKERS['recoveryMarkers'].values())


def is_unanswerable(q):
    """复刻 src/lib/placeholder.ts 的 isUnanswerable

    占位 = content 有 OCR marker / 「题目正在全力以赴征集」/ ≥2 个选项 OCR 失败
    不可作答 = 占位 + 无 questionImage（救援 marker 不算占位）
    """
    if q.get('questionImage'):
        return False
    content = q.get('content', '') or ''
    opts = q.get('options', []) or []
    # 救援 marker 不算占位（有补救的可以作答）
    if any(m in content for m in RECOVERY_MARKERS):
        # content 已含救援 marker → 题干已补，不算占位题干
        stem_bad = False
    else:
        stem_bad = any(m in content for m in PLACEHOLDER_MARKERS) or '题目正在全力以赴征集' in content

    bad_opts = 0
    for o in opts:
        oc = o.get('content', '') if isinstance(o, dict) else (o or '')
        if any(m in oc for m in RECOVERY_MARKERS):
            continue  # 救援过的选项不算坏
        if any(m in oc for m in PLACEHOLDER_MARKERS) or '题目正在全力以赴征集' in oc:
            bad_opts += 1

    is_placeholder = stem_bad or bad_opts >= 2
    return is_placeholder


def main():
    bypaper = defaultdict(list)
    total_q = 0
    total_unans = 0

    for jp in glob.glob('src/data/xingce/**/*.json', recursive=True):
        try:
            data = json.load(open(jp, encoding='utf-8'))
        except Exception:
            continue
        qs = data.get('questions') if isinstance(data, dict) else data
        if not isinstance(qs, list):
            continue
        base = os.path.basename(jp).replace('.json', '')
        norm = jp.replace('\\', '/')
        module = norm.split('/xingce/')[1].split('/')[0]
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
