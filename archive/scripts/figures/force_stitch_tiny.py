#!/usr/bin/env python3
"""对仍然过小的 18 张图片强制跨页拼接。"""
import os, sys, glob, json, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fitz
from PIL import Image
from batch_extract_figures import find_pdf_for_json
from extract_figures import find_question_pages, _find_options_anchor_y

DPI = 200
MAX_SINGLE_PAGE = 550


def force_stitch(pdf_path, q_num, hint):
    doc = fitz.open(pdf_path)
    hints = {q_num: hint}
    positions = find_question_pages(
        doc, list(range(q_num - 1, q_num + 3)), hints
    )
    if q_num not in positions:
        return None
    page_idx, q_rect = positions[q_num][0]
    page = doc[page_idx]
    pw, ph = page.rect.width, page.rect.height

    # 第 1 段：本页 从题号上方一点 → 页底
    y0_a = max(20, q_rect.y0 - 3)
    y1_a = ph - 25
    # 若同页有下一题，截到下一题上方
    nq = positions.get(q_num + 1, [])
    for pidx, r in nq:
        if pidx == page_idx and r.y0 > q_rect.y0:
            y1_a = min(y1_a, r.y0 - 3)
            break
    mat = fitz.Matrix(DPI / 72, DPI / 72)
    pix_a = page.get_pixmap(
        matrix=mat, clip=fitz.Rect(20, y0_a, pw - 20, y1_a), alpha=False
    )
    img_a = Image.open(io.BytesIO(pix_a.tobytes("png"))).convert("RGB")

    # 若本页第一段就覆盖了下一题（整题在本页），不需要拼接
    same_page = any(
        pidx == page_idx and r.y0 > q_rect.y0 for pidx, r in nq
    )
    if same_page:
        return img_a

    # 第 2 段：下一页 顶部 → 下一题位置 或 MAX_SINGLE_PAGE
    if page_idx + 1 >= len(doc):
        return img_a
    npage = doc[page_idx + 1]
    npw, nph = npage.rect.width, npage.rect.height
    y0_b = 20
    y1_b = min(nph - 20, y0_b + MAX_SINGLE_PAGE)
    for pidx, r in nq:
        if pidx == page_idx + 1:
            y1_b = min(y1_b, r.y0 - 3)
            break
    # 用选项 A 锚点限制
    anch = _find_options_anchor_y(npage, y0_b)
    if anch and anch > y0_b + 50:
        y1_b = min(y1_b, anch + 30)
    pix_b = npage.get_pixmap(
        matrix=mat, clip=fitz.Rect(20, y0_b, npw - 20, y1_b), alpha=False
    )
    img_b = Image.open(io.BytesIO(pix_b.tobytes("png"))).convert("RGB")

    # 垂直拼接
    w = max(img_a.width, img_b.width)
    canvas = Image.new("RGB", (w, img_a.height + img_b.height + 10),
                       (255, 255, 255))
    canvas.paste(img_a, ((w - img_a.width) // 2, 0))
    canvas.paste(img_b, ((w - img_b.width) // 2, img_a.height + 10))
    return canvas


SMALL_THRESHOLD = 10000


def main():
    targets = []
    for fp in glob.glob('public/img/questions/*/q*.png'):
        if os.path.getsize(fp) < SMALL_THRESHOLD:
            parts = fp.replace(os.sep, '/').split('/')
            exam = parts[-2]
            qn = int(parts[-1].replace('q', '').replace('.png', ''))
            targets.append((exam, qn, fp))
    print(f'强制重抽 {len(targets)} 张')

    for exam, qn, out in targets:
        jp = f'src/data/xingce/panduan/{exam}.json'
        pdf = find_pdf_for_json(jp)
        if not pdf:
            print(f'  [NO PDF] {exam} Q{qn}')
            continue
        qs = json.load(open(jp, encoding='utf-8'))
        t = next((q for q in qs if int(q['id'].split('-')[-1]) == qn), None)
        hint = t.get('content', '') if t else ''
        img = force_stitch(pdf, qn, hint)
        if img is None:
            print(f'  [FAIL] {exam} Q{qn}')
            continue
        img_p = img.convert("P", palette=Image.ADAPTIVE, colors=64)
        img_p.save(out, "PNG", optimize=True)
        print(f'  {exam} Q{qn}: {os.path.getsize(out)}B')


if __name__ == '__main__':
    main()
