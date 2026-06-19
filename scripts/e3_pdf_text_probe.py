"""D-17e E-3.12 PDF 文字层批量侦查 — 13 个散点 paperKey × 1 题

用 fitz get_text 在 PDF 全文搜「N.题目正在全力以赴征集」（或「N.题目正在
众人之力上传」），命中即确认 PDF 缺失，可批量打 B 类 marker。

输出每题命中证据：paperKey / qn / page / 原文片段。
"""
import fitz, json, re, sys, io
from pathlib import Path

# Windows 控制台 GBK 默认，强制 utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
idx = json.loads((ROOT/'data'/'e1_vision'/'pdf_index.json').read_text(encoding='utf-8'))

# 13 个散点（module, paperKey, qn）
TARGETS = [
    ('changshi', 'provincial_guangdong_2020', '083'),
    ('changshi', 'provincial_guangdong_2023', '089'),
    ('changshi', 'provincial_neimenggu_2023', '018'),
    ('changshi', 'provincial_shandong_2025', '020'),
    ('changshi', 'provincial_yunnan_2023', '055'),
    ('panduan',  'provincial_shanghai_2021', '061'),
    ('shuliang', 'provincial_guangdong_2024', '031'),
    ('shuliang', 'provincial_xinjiang_2021', '006'),
    ('yanyu',    'provincial_hunan_2020', '016'),
    ('yanyu',    'provincial_hunan_2024', '040'),
    ('ziliao',   'provincial_hainan_2024', '110'),
]

# 关键词模式
KW_PATTERNS = [
    '题目正在全力以赴征集',
    '题目正在众人之力上传',
    '题目正全力以征集',
    '题目正在全力征集',
    '题目正在征集',
]


def probe(pk, qn):
    """两级匹配：
    1. 严格：找到「{qn}.关键词」前缀模式
    2. 宽松：同一页里既有题号又有关键词
    返回 (page, kw, snippet, strict_bool)"""
    pdf_path = idx.get(pk)
    if not pdf_path:
        return None, None, 'NO_PDF_PATH', False
    try:
        doc = fitz.open(str(ROOT/pdf_path))
    except Exception as e:
        return None, None, f'PDF open fail: {e}', False

    qn_int = int(qn)
    strict_hit = None
    loose_hit = None
    for pno in range(len(doc)):
        try:
            text = doc[pno].get_text('text')
        except Exception:
            continue
        kw_found = None
        for kw in KW_PATTERNS:
            if kw in text:
                kw_found = kw
                break
        if not kw_found:
            continue
        # 严格匹配：找 "{qn_int}.关键词" 前缀
        for kw in KW_PATTERNS:
            idx_kw = 0
            while True:
                pos = text.find(kw, idx_kw)
                if pos < 0:
                    break
                idx_kw = pos + 1
                preface = text[max(0, pos-30):pos]
                m = re.search(rf'(\d+)\s*[.．、]\s*$', preface)
                if m and int(m.group(1)) == qn_int:
                    snippet = text[max(0, pos-40):pos+60].replace('\n', ' ')
                    strict_hit = (pno+1, kw, snippet)
                    break
            if strict_hit:
                break
        if strict_hit:
            break
        # 宽松匹配：同一页同时含题号 + 关键词
        if not loose_hit:
            # 找页内有"{qn}." 或 "{qn}．"
            if re.search(rf'\b{qn_int}\s*[.．、]', text):
                pos_kw = text.find(kw_found)
                snippet = text[max(0, pos_kw-40):pos_kw+60].replace('\n', ' ')
                loose_hit = (pno+1, kw_found, snippet)
    doc.close()
    if strict_hit:
        return strict_hit[0], strict_hit[1], strict_hit[2], True
    if loose_hit:
        return loose_hit[0], loose_hit[1], loose_hit[2], False
    return None, None, 'no_hit_in_PDF_text_layer', False


def main():
    print(f'侦查 {len(TARGETS)} 个散点 (严格=题号+kw / 宽松=同页有题号+kw)')
    print(f'{"module":10} {"paperKey":35} {"qn":>4} {"strict":>6}  page  snippet')
    print('-'*160)
    results = []
    for mod, pk, qn in TARGETS:
        page, kw, snippet, strict = probe(pk, qn)
        marker = 'STRICT' if strict else ('LOOSE' if page else 'MISS')
        page_s = f'p{page:03d}' if page else '----'
        print(f'{mod:10} {pk:35} {qn:>4} {marker:>6}  {page_s}  {snippet[:100]}')
        results.append({'module': mod, 'paperKey': pk, 'qn': qn,
                        'page': page, 'keyword': kw, 'snippet': snippet,
                        'match': marker})
    out = ROOT/'data'/'e1_vision'/'e3_probe_scatters.json'
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print()
    print(f'saved -> {out}')
    strict_n = sum(1 for r in results if r['match'] == 'STRICT')
    loose_n = sum(1 for r in results if r['match'] == 'LOOSE')
    miss_n = sum(1 for r in results if r['match'] == 'MISS')
    print(f'STRICT={strict_n} LOOSE={loose_n} MISS={miss_n}')


if __name__ == '__main__':
    main()
