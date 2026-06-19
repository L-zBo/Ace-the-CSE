"""P2: 跨页题手工拼接 — q079 + q081.

把题号所在页（页底的题）从题号 y 截到页底，与下一页从页顶截到下一题号 y 之间的部分
竖向拼接成一张 png，覆盖原病图。
"""
import os
import sys
import io

import fitz
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if '__file__' in dir() else '.'
ROOT = r'F:\VsCodeproject\Ace-the-CSE'

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ZOOM = 2.5  # 渲染倍率：1 = 72 dpi, 2.5 = 180 dpi，够清晰
SAFE_BOTTOM_PAD = 8  # 截页底时往下再留 pt，避开题号切断
TOP_PAD = 2  # 截页顶时往上留 pt

JOBS = [
    {
        'pdf': r'material/【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-真题/2022 年国家公务员考试行测真题（地市级）.pdf',
        'out': 'public/img/questions/national_2022_dishi/q079.png',
        'page_top': 15, 'y_top': 646.25,
        'page_bot': 16, 'y_bot': 84.65,
    },
    {
        # q081 实际单页即可（p13 末尾完整），之前误判跨页，拼了 p14 顶部的
        # 水印造成垃圾。单页模式：page_bot=None，y_bot 指定该页截止 y（避页码）。
        'pdf': r'material/【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-真题/2025年国家公务员录用考试《行测》题（地市级）.pdf',
        'out': 'public/img/questions/national_2025_dishi/q081.png',
        'page_top': 13, 'y_top': 602.82,
        'page_bot': None, 'y_bot': 770.0,  # p13 底部页码在 y≈780，截到 770 避开
    },
]


def render_crop(page: fitz.Page, y0: float, y1: float) -> Image.Image:
    page_w = page.rect.width
    clip = fitz.Rect(0, y0, page_w, y1)
    pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=clip)
    return Image.frombytes('RGB', (pix.width, pix.height), pix.samples)


def stitch_vertical(im_top: Image.Image, im_bot: Image.Image) -> Image.Image:
    w = max(im_top.width, im_bot.width)
    h = im_top.height + im_bot.height
    canvas = Image.new('RGB', (w, h), (255, 255, 255))
    canvas.paste(im_top, (0, 0))
    canvas.paste(im_bot, (0, im_top.height))
    return canvas


def main():
    for j in JOBS:
        pdf_path = os.path.join(ROOT, j['pdf'])
        out_path = os.path.join(ROOT, j['out'])
        doc = fitz.open(pdf_path)
        page_top = doc[j['page_top']]

        y_top_start = max(0, j['y_top'] - TOP_PAD)

        if j['page_bot'] is None:
            # 单页模式：page_top 从 y_top 截到 y_bot
            im_top = render_crop(page_top, y_top_start, j['y_bot'])
            out = im_top
        else:
            # 跨页模式：page_top 从 y_top 到页底 + page_bot 从页顶到 y_bot
            page_bot = doc[j['page_bot']]
            y_top_end = page_top.rect.height - SAFE_BOTTOM_PAD
            y_bot_end = max(0, j['y_bot'] - TOP_PAD)
            im_top = render_crop(page_top, y_top_start, y_top_end)
            im_bot = render_crop(page_bot, 0, y_bot_end)
            out = stitch_vertical(im_top, im_bot)

        if os.path.exists(out_path):
            bak = out_path + '.bak'
            if not os.path.exists(bak):
                os.rename(out_path, bak)
            else:
                os.remove(out_path)
        out.save(out_path, 'PNG', optimize=True)
        size = os.path.getsize(out_path)
        print(f'  {j["out"]}  {out.width}x{out.height}  {size/1024:.1f}KB')
        doc.close()


if __name__ == '__main__':
    main()
