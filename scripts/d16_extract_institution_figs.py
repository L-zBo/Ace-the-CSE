"""D-16 L-9 事业编 PDF 抽图

事业编 PDF 是多年合并版（一个 PDF 装 7 年 10+套真题），D-9 时期
batch_extract_figures.py 没加 institution 分支，整批 PDF 没抽过。

事业编 PDF 文字层完整（非扫描版），可以用 stem-based 搜索 + 复用
extract_figures.extract_question_image() 抽图。

逻辑：
  1. 对每个 institution_*.json lib 文件，找对应 PDF（A/B/C/E 类职测）
  2. 该 lib 对应的 PDF 内 sections（按年份匹配，可能有多套：lib q001-020
     是一套，q101-120 是另一套）
  3. 对 lib 中 (需要图 且 无 questionImage) 的题，用 stem 在 sections
     内搜定位，然后调 extract_question_image() 裁图
  4. 落到 public/img/questions/institution_{year}_{level}/q{qn}.png
  5. 同时更新 lib.questionImage

只处理「明确需要图」的题（content 含图关键词 / knowledgePoints 含
图形推理/资料分析 / 选项全单字母）—— 避免误抽。
"""
import argparse
import json
import re
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).parent))
from extract_figures import extract_question_image, normalize_cjk


# 事业编 PDF section 索引（从 PDF 文字层自动扫得到）
# (start_page, end_page_exclusive, year, month)
PDF_SECTIONS = {
    'A': [
        (2, 22, 2024, 3), (22, 43, 2023, 8), (43, 65, 2023, 5),
        (65, 107, 2022, 9), (107, 128, 2021, 10), (128, 149, 2021, 5),
        (149, 192, 2020, 10), (192, 212, 2019, 10), (212, 232, 2019, 5),
        (232, 271, 2018, 10),
    ],
    'B': [
        (2, 24, 2024, 3), (24, 45, 2023, 8), (45, 67, 2023, 5),
        (67, 85, 2022, 5), (85, 105, 2021, 10), (105, 148, 2021, 5),
        (148, 168, 2019, 10), (168, 190, 2019, 5), (190, 232, 2018, 10),
    ],
    'C': [
        (2, 23, 2024, 3), (23, 43, 2023, 8), (43, 62, 2023, 5),
        (62, 83, 2022, 9), (83, 103, 2022, 5), (103, 123, 2021, 10),
        (123, 144, 2021, 5), (144, 187, 2020, 7), (187, 208, 2019, 5),
        (208, 230, 2018, 10), (230, 250, 2018, 5),
    ],
    'E': [
        (2, 23, 2024, 3), (23, 43, 2023, 8), (43, 64, 2023, 5),
        (64, 82, 2022, 9), (82, 103, 2022, 5), (103, 123, 2021, 10),
        (123, 144, 2021, 5), (144, 165, 2020, 7), (165, 184, 2019, 10),
        (184, 205, 2019, 5), (205, 225, 2018, 10), (225, 246, 2018, 5),
    ],
}

PDF_PATHS = {
    cls: f'material/【事业编】事业单位联考历年真题/{cls}类/职测/'
         f'2018年-2024年事业单位联考职测（{cls}类）笔试真题.pdf'
    for cls in 'ABCE'
}

# 启发式：哪些题需要图
NEED_PATTERNS = [
    r'下图', r'如图', r'图中', r'图形', r'所示', r'示意图',
    r'左图', r'右图', r'上图', r'根据图', r'立体图', r'平面图',
    r'柱状图', r'饼图', r'折线图', r'统计图', r'扇形图',
    r'根据下', r'填入问号处', r'图\s*[12345①②③④⑤]',
]
NEED_RE = re.compile('|'.join(NEED_PATTERNS))


def needs_image(q):
    c = q.get('content', '') or ''
    if NEED_RE.search(c):
        return True
    kps = q.get('knowledgePoints', []) or []
    if any('图形推理' in (kp or '') or '资料分析' in (kp or '') for kp in kps):
        return True
    opts = q.get('options', []) or []
    if opts and all(
        isinstance(o, dict) and (o.get('content', '') or '').strip() in ('A', 'B', 'C', 'D')
        for o in opts
    ):
        return True
    return False


def find_q_by_number(doc, qn, stem, sections):
    """按题号在 sections 内搜，用 stem 验证消歧。

    PDF 题号有几种格式：「51.」「51、」「51．」「51,」
    限定 x0 < 120（题号在左侧）。
    若 stem 有内容，验证题号下方文字含 stem 前 8-12 字（消歧多套同题号）。
    """
    hint = (stem or '').strip()[:12].strip()
    candidates = []
    patterns = [f'{qn}.', f'{qn}、', f'{qn}．', f'{qn},']
    for (p0, p1, year, month) in sections:
        for pi in range(p0, min(p1, len(doc))):
            page = doc[pi]
            for pat in patterns:
                areas = page.search_for(pat)
                if not areas:
                    continue
                left = [r for r in areas if r.x0 < 120]
                for r in left:
                    # hint 验证：题号下方 350pt 内是否有 stem
                    if hint and len(hint) >= 6:
                        clip = fitz.Rect(r.x0, r.y0, page.rect.width - 20, r.y0 + 350)
                        nearby = normalize_cjk(page.get_textbox(clip))
                        if hint in nearby:
                            candidates.append((pi, r, year, month, 100))
                        elif hint[:8] in nearby:
                            candidates.append((pi, r, year, month, 50))
                    else:
                        candidates.append((pi, r, year, month, 1))
                break  # 同页每个 pattern 找一次即可
    if not candidates:
        return None
    # 选 score 最高的
    candidates.sort(key=lambda x: -x[4])
    return candidates[0][:4]


def find_next_q(doc, qn, page_idx_min, sections):
    """找 q+1 题的位置（用于 extract_question_image 的 next_q_rect）"""
    qn_next = qn + 1
    patterns = [f'{qn_next}.', f'{qn_next}、', f'{qn_next}．', f'{qn_next},']
    # 优先在 page_idx_min 之后的 2 页内搜
    for (p0, p1, _, _) in sections:
        for pi in range(max(p0, page_idx_min), min(p1, len(doc))):
            page = doc[pi]
            for pat in patterns:
                areas = page.search_for(pat)
                left = [r for r in areas if r.x0 < 120]
                if left:
                    return (pi, min(left, key=lambda x: x.y0))
            if pi - page_idx_min > 3:
                break
    return None


def process_lib(lib_path: Path, apply: bool, verbose: bool = False):
    """处理一个 lib JSON，返回 (检查数, 命中数, 抽图数)"""
    stem = lib_path.stem
    # 解析 institution_YYYY_X
    parts = stem.split('_')
    if len(parts) < 3 or parts[0] != 'institution':
        return (0, 0, 0)
    year = int(parts[1])
    cls = parts[2].upper()
    if cls not in PDF_PATHS:
        return (0, 0, 0)

    pdf_path = PDF_PATHS[cls]
    if not Path(pdf_path).exists():
        if verbose:
            print(f'  !! {pdf_path} 不存在')
        return (0, 0, 0)

    # 该年所有 sections
    sections = [s for s in PDF_SECTIONS[cls] if s[2] == year]
    if not sections:
        if verbose:
            print(f'  {lib_path.name}: 该年 PDF 无 section')
        return (0, 0, 0)

    data = json.loads(lib_path.read_text(encoding='utf-8'))
    doc = fitz.open(pdf_path)

    examkey = f'institution_{year}_{cls.lower()}'
    out_dir = Path('public/img/questions') / examkey
    if apply:
        out_dir.mkdir(parents=True, exist_ok=True)

    n_check = 0
    n_hit = 0
    n_saved = 0
    for q in data:
        # questionImage 字段已存在：只有死链（PNG 不存在）时才重抽
        url = q.get('questionImage')
        if url:
            existing_png = Path('public') / url.lstrip('/')
            if existing_png.exists():
                continue  # 真有图，跳过
            # 死链 → 落到本脚本输出 path，继续 try 重抽
        if not needs_image(q):
            continue
        c = q.get('content', '') or ''
        if len(c.strip()) < 6:
            continue  # 占位题 content 太短，无法搜
        n_check += 1

        # 解析 lib qn，处理 +100 shift（L-10 拆 dup 后的 batch2）
        try:
            lib_qn = int(q['id'].rsplit('-', 1)[-1])
        except ValueError:
            continue
        # lib qn > 100 实际是 batch2，PDF 中是 qn-100
        pdf_qn = lib_qn - 100 if lib_qn > 100 else lib_qn

        loc = find_q_by_number(doc, pdf_qn, c, sections)
        if not loc:
            continue
        pi, r, y, m = loc
        n_hit += 1

        if not apply:
            if verbose:
                print(f'  {q["id"]} -> page {pi} ({y}/{m}) qn={pdf_qn}')
            continue

        # 找下一题位置（提高裁图精度）
        next_loc = find_next_q(doc, pdf_qn, pi, sections)
        next_rect = next_loc[1] if next_loc else None
        next_page_idx = next_loc[0] if next_loc else None

        # 提图（带 next 提高精度）
        page = doc[pi]
        try:
            img_bytes = extract_question_image(
                doc, pi, r, next_rect, next_page_idx,
                page.rect.height, page.rect.width, dpi=200,
            )
        except Exception as e:
            if verbose:
                print(f'  ERROR {q["id"]}: {e}')
            continue

        # 质量检验：高度 < 200 重抽（next=None 让选项锚点兜底）
        from io import BytesIO
        try:
            from PIL import Image as _Img
            h = _Img.open(BytesIO(img_bytes)).height
        except Exception:
            h = 0
        if h < 200 and next_rect is not None:
            try:
                img_bytes2 = extract_question_image(
                    doc, pi, r, None, None,
                    page.rect.height, page.rect.width, dpi=200,
                )
                h2 = _Img.open(BytesIO(img_bytes2)).height
                if h2 > h:
                    img_bytes = img_bytes2
                    h = h2
            except Exception:
                pass

        # 最终高度仍 < 200 / 字节 < 5000 视为失败，丢弃
        if h < 200 or len(img_bytes) < 5000:
            if verbose:
                print(f'  DROP {q["id"]}: h={h} bytes={len(img_bytes)}')
            continue

        out_path = out_dir / f'q{lib_qn:03d}.png'
        out_path.write_bytes(img_bytes)
        q['questionImage'] = f'/img/questions/{examkey}/q{lib_qn:03d}.png'
        n_saved += 1

    doc.close()
    if apply and n_saved > 0:
        lib_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )
    return (n_check, n_hit, n_saved)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--lib', help='只处理特定 lib（如 institution_2020_a）',
                    default='')
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()

    total_check = 0
    total_hit = 0
    total_saved = 0

    for f in sorted(Path('src/data/xingce').rglob('institution_*.json')):
        if args.lib and args.lib not in f.stem:
            continue
        nc, nh, ns = process_lib(f, args.apply, args.verbose)
        if nc:
            print(f'{f}: check={nc} hit={nh} saved={ns}')
        total_check += nc
        total_hit += nh
        total_saved += ns

    mode = 'APPLY' if args.apply else 'DRY-RUN'
    print(f'\n[{mode}] check {total_check} 题, hit {total_hit}, saved {total_saved}')


if __name__ == '__main__':
    main()
