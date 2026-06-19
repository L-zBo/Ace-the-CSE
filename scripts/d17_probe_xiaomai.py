"""D-17a 批量探测小麦公考对 D-16 末 99 不可作答题所在 paperKey 的覆盖

输入：data/d17_unanswerable.json
输出：data/d17_xiaomai_coverage.json + 终端表格

小麦 area 编号（取自 paperList.html 渲染）：
"""
import json, urllib.request, urllib.parse, re, ssl, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

AREA_MAP = {
    '国家': 1, '西藏': 2, '河南': 3, '吉林': 4, '黑龙江': 5, '浙江': 6, '山西': 7, '山东': 8,
    '云南': 9, '辽宁': 10, '湖南': 11, '陕西': 12, '河北': 13, '湖北': 14, '江西': 15, '海南': 16,
    '安徽': 17, '甘肃': 18, '贵州': 19, '新疆': 20, '广西': 21, '宁夏': 22, '青海': 23, '内蒙古': 24,
    '四川': 25, '天津': 26, '广东': 27, '江苏': 28, '上海': 29, '北京': 30, '福建': 31, '重庆': 32,
    '深圳': 33, '广州': 35, '联考': 38,
}

# paperKey 里的拼音 → 小麦中文区名
PROV_PY2CN = {
    'xinjiang': '新疆', 'jilin': '吉林', 'beijing': '北京', 'gansu': '甘肃', 'ningxia': '宁夏',
    'hunan': '湖南', 'qinghai': '青海', 'shandong': '山东', 'hebei': '河北', 'shanghai': '上海',
    'guangdong': '广东', 'henan': '河南', 'neimenggu': '内蒙古', 'shanxi': '山西', 'yunnan': '云南',
    'chongqing': '重庆', 'jiangxi': '江西', 'shenzhen': '深圳', 'tianjin': '天津', 'hainan': '海南',
    'jiangsu': '江苏', 'zhejiang': '浙江', 'heilongjiang': '黑龙江', 'fujian': '福建',
    'guizhou': '贵州', 'sichuan': '四川', 'anhui': '安徽', 'liaoning': '辽宁', 'hubei': '湖北',
    'shaanxi': '陕西', 'guangxi': '广西', 'guangzhou': '广州', 'xizang': '西藏',
}


def probe(area_id: int, year: int, retries=2):
    url = f'http://www.xiaomaigongkao.com/QuestionNew/paperList/area/{area_id}/year/{year}.html'
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    last_err = None
    for _ in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
                html = r.read().decode('utf-8', errors='replace')
            pdfs = re.findall(r'http://pdf\.xiaomaijiaoyu\.com/[^"\'\s<>]+\.pdf[^"\'\s<>]*', html)
            paper_ids = re.findall(r'paperBegin/paper_id/(\d+)\.html', html)
            titles = re.findall(r'(\d{4}年[^<>"]{2,40}行测真题[^<>"]{0,30})', html)
            return {
                'url': url,
                'len': len(html),
                'empty': '该分类下暂无' in html,
                'pdf_count': len(pdfs),
                'pdfs': pdfs,
                'paper_ids': paper_ids,
                'titles': list(set(titles))[:8],
            }
        except Exception as e:
            last_err = str(e)
            time.sleep(1)
    return {'url': url, 'err': last_err}


def main():
    with open('data/d17_unanswerable.json', encoding='utf-8') as f:
        data = json.load(f)
    byprov = data['byprovyear']
    # 只保留 provincial（institution 小麦不收）
    targets = []
    for k, qcount in byprov.items():
        m = re.match(r'provincial_([a-z_]+)_(\d{4})$', k)
        if not m:
            continue
        prov_py, yr = m.groups()
        cn = PROV_PY2CN.get(prov_py)
        if not cn:
            print(f'  [SKIP unknown prov] {prov_py}', file=sys.stderr)
            continue
        area_id = AREA_MAP.get(cn)
        if not area_id:
            print(f'  [SKIP no area] {cn}', file=sys.stderr)
            continue
        targets.append((k, prov_py, cn, area_id, int(yr), qcount))

    print(f'探测 {len(targets)} 个 paperKey（并发 8 路）')
    print()

    results = [None] * len(targets)

    def _run(idx_target):
        idx, (key, prov_py, cn, aid, yr, qcount) = idx_target
        r = probe(aid, yr)
        hit = (not r.get('err')) and not r.get('empty', True) and r.get('pdf_count', 0) > 0
        return idx, {'key': key, 'cn': cn, 'aid': aid, 'year': yr, 'qcount': qcount, **r, 'hit': hit}

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(_run, (i, t)) for i, t in enumerate(targets)]
        for fut in as_completed(futures):
            idx, row = fut.result()
            results[idx] = row

    # 按原顺序输出
    for r in results:
        flag = '✓' if r['hit'] else ('×' if r.get('empty') else '!')
        n_pdf = r.get('pdf_count', 0)
        title_hint = (r.get('titles') or [''])[0][:50]
        err = r.get('err', '')
        print(f'  {flag} {r["key"]:42s} -> area={r["aid"]}/{r["year"]}  pdfs={n_pdf:2d}  q={r["qcount"]:2d}  {title_hint}{err}')

    hits = [r for r in results if r['hit']]
    print()
    print(f'命中 {len(hits)} / {len(results)} paperKey，可救题数上限 = {sum(h["qcount"] for h in hits)} 题')
    print()
    print('=== 命中清单 ===')
    for h in hits:
        # 挑标题里包含目标年份的 PDF
        yr_str = str(h['year'])
        target_pdfs = [p for p in h['pdfs'] if yr_str in urllib.parse.unquote(p)]
        for p in target_pdfs[:5]:
            print(f'  [{h["qcount"]:2d}q] {h["key"]:42s}  {urllib.parse.unquote(p)[:90]}')
        if not target_pdfs:
            print(f'  [{h["qcount"]:2d}q] {h["key"]:42s}  (页面有 PDF 但无 {yr_str} 直链，可能联考拆卷在别处)')
            for p in h['pdfs'][:3]:
                print(f'         非目标年份: {urllib.parse.unquote(p)[:80]}')

    os.makedirs('data', exist_ok=True)
    with open('data/d17_xiaomai_coverage.json', 'w', encoding='utf-8') as f:
        json.dump({'targets': len(targets), 'hits': len(hits), 'results': results},
                  f, ensure_ascii=False, indent=2)
    print()
    print('saved -> data/d17_xiaomai_coverage.json')


if __name__ == '__main__':
    main()
