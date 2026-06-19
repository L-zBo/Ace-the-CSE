#!/usr/bin/env python3
"""对题干在页底、图在下页的图形推理题强制跨页拼接。

自动扫描 public/img/questions/ 下高度过矮（<220px）的图片，
针对 panduan 分类中有图形关键词的真题，强制跨页合并重抽。
"""
import os, sys, json, glob, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fitz
from PIL import Image
from batch_extract_figures import find_pdf_for_json
from extract_figures import (
    find_question_pages, _find_options_anchor_y, NUMBER_LEFT_MAX_X,
)

MAX_CLIP = 430
DPI = 200

# 从 panduan JSON 中识别需要强制拼接的题
FIG_KW = ['图形','问号处','下列四','立方体','四面体','六面体','展开图','多面体',
          '折叠','拼合','平移','旋转','翻转','下图','上图','直观图','立体图',
          '下列图','下面图','如图','图中','图示','六个图形','一定规律性',
          '呈现规律','规律性','几何体','截面','圆锥','三棱']


def collect_targets():
    targets = []
    for png in glob.glob('public/img/questions/*/q*.png'):
        try:
            w, h = Image.open(png).size
        except Exception:
            continue
        if h >= 220:
            continue
        parts = png.replace(os.sep, '/').split('/')
        exam = parts[-2]
        qn = int(parts[-1].replace('q', '').replace('.png', ''))
        jp = f'src/data/xingce/panduan/{exam}.json'
        if not os.path.exists(jp):
            continue
        qs = json.load(open(jp, encoding='utf-8'))
        tgt = next((q for q in qs if int(q['id'].split('-')[-1]) == qn), None)
        if not tgt:
            continue
        c = tgt.get('content', '')
        if any(k in c for k in FIG_KW):
            targets.append((exam, qn))
    return targets


def extract_cross_page(pdf_path, q_num, exam, hint_text=""):
    doc = fitz.open(pdf_path)
    hints = {q_num: hint_text} if hint_text else None
    q_positions = find_question_pages(doc, [q_num - 1, q_num, q_num + 1, q_num + 2], hints)
    if q_num not in q_positions:
        return None
    page_idx, q_rect = q_positions[q_num][0]
    page = doc[page_idx]
    pw, ph = page.rect.width, page.rect.height

    # 本页 clip: 题号下方 → 页底
    y0 = q_rect.y1 + 2
    y1 = min(ph - 20, y0 + MAX_CLIP)
    # 本页可能有下一题（图形题之间挨得近，但题干可能也是空）
    nq = q_positions.get(q_num + 1, [])
    same_next = next(((p, r) for p, r in nq if p == page_idx and r.y0 > q_rect.y0), None)
    if same_next:
        y1 = min(y1, same_next[1].y0 - 3)
    anchor = _find_options_anchor_y(page, y0)
    if anchor and anchor < y1:
        y1 = anchor - 3

    mat = fitz.Matrix(DPI / 72, DPI / 72)
    clip1 = fitz.Rect(20, y0, pw - 20, y1)
    pix1 = page.get_pixmap(matrix=mat, clip=clip1, alpha=False)
    img1 = Image.open(io.BytesIO(pix1.tobytes("png"))).convert("RGB")

    # 下一页顶部到下一题或 MAX_CLIP
    if page_idx + 1 >= len(doc) or same_next:
        # 无需拼接（但既然来这，很可能仍需拼接；若同页有下一题，图就在上面）
        return img1
    np_page = doc[page_idx + 1]
    np_rect = np_page.rect
    np_y0 = 20
    # 下一题若在下一页
    np_y1 = np_y0 + MAX_CLIP
    next_on_np = next(((p, r) for p, r in nq if p == page_idx + 1), None)
    if next_on_np:
        np_y1 = min(np_y1, next_on_np[1].y0 - 3)
    anc2 = _find_options_anchor_y(np_page, np_y0)
    if anc2 and anc2 < np_y1 and anc2 > np_y0 + 30:
        # 仅在 anchor 足够靠下时才使用（否则会截短）
        # 向下多留 120pt 以包含选项
        np_y1 = min(np_y1, anc2 + 120)
    np_y1 = min(np_y1, np_rect.height - 20)

    clip2 = fitz.Rect(20, np_y0, np_rect.width - 20, np_y1)
    pix2 = np_page.get_pixmap(matrix=mat, clip=clip2, alpha=False)
    img2 = Image.open(io.BytesIO(pix2.tobytes("png"))).convert("RGB")

    w = max(img1.width, img2.width)
    canvas = Image.new("RGB", (w, img1.height + img2.height + 10), (255, 255, 255))
    canvas.paste(img1, ((w - img1.width) // 2, 0))
    canvas.paste(img2, ((w - img2.width) // 2, img1.height + 10))
    return canvas


def main():
    targets = collect_targets()
    print(f'共 {len(targets)} 道题需要重抽:')
    by_exam = {}
    for exam, qn in targets:
        by_exam.setdefault(exam, []).append(qn)

    fixed = failed = 0
    for exam, qnums in by_exam.items():
        jp = f'src/data/xingce/panduan/{exam}.json'
        pdf = find_pdf_for_json(jp)
        if not pdf:
            print(f'[SKIP] {exam}: 无PDF')
            continue
        qs = json.load(open(jp, encoding='utf-8'))
        hint_map = {int(q['id'].split('-')[-1]): q.get('content', '')
                    for q in qs}
        for qn in qnums:
            img = extract_cross_page(pdf, qn, exam, hint_map.get(qn, ''))
            if img is None:
                print(f'  [FAIL] {exam} Q{qn}')
                failed += 1
                continue
            img = img.convert("P", palette=Image.ADAPTIVE, colors=64)
            out = f'public/img/questions/{exam}/q{qn:03d}.png'
            img.save(out, "PNG", optimize=True)
            print(f'  {exam} Q{qn}: {os.path.getsize(out)}B')
            fixed += 1

    print(f'\n总计: 修复 {fixed}, 失败 {failed}')


if __name__ == '__main__':
    main()
