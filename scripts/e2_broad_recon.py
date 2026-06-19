"""D-17e E-2.2 — 7 题宽 kw 重搜（lib 的 content+explanation 全部短语切片做 kw）"""
import json, re
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'src' / 'data' / 'xingce'
PDF_IDX = json.loads((ROOT/'data'/'e1_vision'/'pdf_index.json').read_text(encoding='utf-8'))

# 7 题
TARGETS = [
    ('provincial_guangdong_2020','083','changshi'),
    ('institution_2020_c','163','panduan'),
    ('institution_2020_c','164','panduan'),
    ('provincial_shanghai_2021','061','panduan'),
    ('provincial_xinjiang_2021','006','shuliang'),
    ('provincial_hunan_2020','016','yanyu'),
    ('provincial_jiangsu_2020','006','ziliao'),
]

# 模板词排除
STOP = ['答案','正确答案','本题考查','故选','解析','故正确','根据题干','【','】','考查','项错误','可知']


def extract_kws(text, n=8, kw_len=8):
    """从一段中文长文本切出 n 个特异 4-12 字短语"""
    if not text:
        return []
    # 去英文/数字（保留中文）
    chars = re.findall(r'[一-鿿]{4,}', text)
    kws = []
    seen = set()
    for chunk in chars:
        # 跳过含模板词的
        if any(s in chunk for s in STOP):
            continue
        # 截 kw_len 长度的切片
        for i in range(0, max(1, len(chunk)-kw_len+1), max(1, kw_len-2)):
            sub = chunk[i:i+kw_len]
            if len(sub) >= 4 and sub not in seen:
                seen.add(sub)
                kws.append(sub)
                if len(kws) >= n:
                    return kws
    return kws


def load_lib_q(pk, qn, mod):
    region = ''
    src = ''
    if pk.startswith('provincial_'):
        rest = pk[len('provincial_'):]
        # 形如 shanghai_2020 → region=shanghai
        parts = rest.rsplit('_', 1)
        region = parts[0]
        src = 'provincial'
    elif pk.startswith('institution_'):
        src = 'institution'
    path = DATA / mod / f'{pk}.json'
    arr = json.loads(path.read_text(encoding='utf-8'))
    qid_pattern = re.compile(rf'-{mod}-\d+(?:-[a-z]+)?(?:-[a-z]+)?-{qn}$')
    for q in arr:
        qid = q.get('id','')
        if qid.endswith(f'-{qn}') and f'-{mod}-' in qid:
            return q
    return None


def main():
    out = []
    for pk, qn, mod in TARGETS:
        q = load_lib_q(pk, qn, mod)
        if not q:
            out.append({'pk':pk,'qn':qn,'mod':mod,'err':'lib not found'})
            continue
        text_pool = (q.get('content','') + ' ' + q.get('explanation','')
                     + ' '.join(o.get('content','') for o in q.get('options',[])))
        kws = extract_kws(text_pool, n=10, kw_len=8)
        pdfp = ROOT / PDF_IDX[pk]
        doc = fitz.open(str(pdfp))
        hits = []
        for i, p in enumerate(doc):
            t = p.get_text()
            cnt = sum(1 for k in kws if k in t)
            if cnt >= 2:
                hits.append((i, cnt))
        doc.close()
        hits.sort(key=lambda x:-x[1])
        out.append({
            'pk':pk,'qn':qn,'mod':mod,
            'kws':kws,
            'hits':hits[:5],
            'best_page': hits[0][0] if hits else None,
        })
    Path('data/e1_vision/e2_broad_recon.json').write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    for r in out:
        print(f"{r['pk']} q{r['qn']} ({r['mod']}): best p{r.get('best_page')}, hits={r.get('hits')[:3] if r.get('hits') else '[]'}")
        if r.get('kws'):
            print(f"  kws: {r['kws'][:6]}")

if __name__ == '__main__':
    main()
