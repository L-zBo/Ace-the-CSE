"""D-16 L-9b 事业编资料分析题专项抽图（材料锚点 + 跨页拼接）

L-9 主脚本对资料分析题命中率约 53%（10/19 OK + 4 张缺图表 + 5 题未命中），
原因：资料分析图表在「材料一/二/三...」锚点下方，题号在图表后。
extract_question_image() 向下找下一题位置可能误吞或遗漏图表。

本脚本专项处理资料分析题：
  1. PDF section 内扫所有「材料一/二/三...」锚点位置
  2. 对每道资料分析题：
     - 找其前最近的材料锚点（同页或上方页）
     - clip y0 = 材料锚点 y / clip y1 = 当前题号 + 选项区
  3. 跨页时用 PIL 拼接渲染

输出与 L-9 同目录：public/img/questions/institution_*/q*.png
"""
import argparse
import io
import json
import re
import sys
from pathlib import Path

import fitz
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from d16_extract_institution_figs import PDF_SECTIONS, PDF_PATHS, needs_image

CHINESE_NUM = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
# 材料组锚点：含「材料 X」「资料 X」「（X）」「根据 ...」「阅读 ...」等多种格式
MATERIAL_PATS = (
    [f'材料{n}' for n in CHINESE_NUM]
    + [f'资料{n}' for n in CHINESE_NUM]
    + [f'（{n}）' for n in CHINESE_NUM]
    + [f'({n})' for n in CHINESE_NUM]
    + ['根据以下', '根据下列', '根据下面', '根据下表', '根据下图', '根据所给',
       '阅读以下', '阅读下面', '阅读下列']
)
# 第五部分资料分析的大标题（仅作辅助识别）
SECTION_TITLE_PATS = ['第五部分 资料分析', '第五部分资料分析', '五、资料分析']


def find_material_above(doc, q_page, q_y, section_pages):
    """向上找最近的材料锚点（同 section 内，限前 2 页内）"""
    p0, p1 = section_pages
    # 限定材料锚点必须在题前 2 页内（避免跨多页找错）
    search_start = max(p0, q_page - 2)
    best = None
    for pi in range(search_start, min(q_page + 1, p1)):
        page = doc[pi]
        for pat in MATERIAL_PATS:
            for r in page.search_for(pat):
                # 材料锚点可能左对齐或居中，宽松到 x < 400
                if r.x0 > 400:
                    continue
                # 必须在当前题之前
                if pi < q_page or (pi == q_page and r.y0 < q_y - 5):
                    candidate = (pi, r.y0, r, pat)
                    if not best or (candidate[0], candidate[1]) > (best[0], best[1]):
                        best = candidate
    return best  # (page, y, rect, pat) or None


def find_q_anchor(doc, qn, section_pages, stem_hint=''):
    """找题号位置（限定 section）"""
    p0, p1 = section_pages
    hint = (stem_hint or '').strip()[:12]
    patterns = [f'{qn}.', f'{qn}、', f'{qn}．', f'{qn},']
    candidates = []
    for pi in range(p0, min(p1, len(doc))):
        page = doc[pi]
        for pat in patterns:
            for r in page.search_for(pat):
                if r.x0 > 120:
                    continue
                score = 1
                if hint and len(hint) >= 6:
                    clip = fitz.Rect(r.x0, r.y0, page.rect.width - 20, r.y0 + 280)
                    nearby = page.get_textbox(clip)
                    if hint in nearby:
                        score = 100
                    elif hint[:8] in nearby:
                        score = 50
                candidates.append((pi, r, score))
            if candidates and pat == patterns[0]:
                break
    if not candidates:
        return None
    candidates.sort(key=lambda x: -x[2])
    return candidates[0][:2]


def find_opts_bottom(page, q_y):
    """找选项 A 锚点（用于决定 y1）"""
    for pat in ['A．', 'A.', 'A、']:
        areas = page.search_for(pat)
        for r in areas:
            if r.y0 > q_y + 5 and r.x0 < 200:
                # 找最后一个选项（D 或 D．）位置
                for last_pat in ['D．', 'D.', 'D、']:
                    d_areas = page.search_for(last_pat)
                    for dr in d_areas:
                        if dr.y0 > r.y0 and dr.x0 < 200:
                            return dr.y0 + 30
                return r.y0 + 120  # 估算 4 选项区 ~100pt
    return None


def render_multi_page(doc, p_start, y_start, p_end, y_end, dpi=180):
    """渲染从 (p_start, y_start) 到 (p_end, y_end) 的跨页区域"""
    images = []
    if p_start == p_end:
        page = doc[p_start]
        clip = fitz.Rect(20, y_start, page.rect.width - 20, y_end)
        pix = page.get_pixmap(clip=clip, dpi=dpi)
        images.append(Image.open(io.BytesIO(pix.tobytes('png'))))
    else:
        # 起始页：y_start → 页底
        page0 = doc[p_start]
        clip0 = fitz.Rect(20, y_start, page0.rect.width - 20, page0.rect.height - 30)
        pix0 = page0.get_pixmap(clip=clip0, dpi=dpi)
        images.append(Image.open(io.BytesIO(pix0.tobytes('png'))))
        # 中间整页
        for pi in range(p_start + 1, p_end):
            page = doc[pi]
            clip = fitz.Rect(20, 30, page.rect.width - 20, page.rect.height - 30)
            pix = page.get_pixmap(clip=clip, dpi=dpi)
            images.append(Image.open(io.BytesIO(pix.tobytes('png'))))
        # 结束页：页顶 → y_end
        page_e = doc[p_end]
        clip_e = fitz.Rect(20, 30, page_e.rect.width - 20, y_end)
        pix_e = page_e.get_pixmap(clip=clip_e, dpi=dpi)
        images.append(Image.open(io.BytesIO(pix_e.tobytes('png'))))

    if len(images) == 1:
        out = io.BytesIO()
        images[0].save(out, format='PNG')
        return out.getvalue()
    # 垂直拼接
    max_w = max(img.width for img in images)
    total_h = sum(img.height for img in images)
    canvas = Image.new('RGB', (max_w, total_h), 'white')
    y = 0
    for img in images:
        canvas.paste(img, (0, y))
        y += img.height
    out = io.BytesIO()
    canvas.save(out, format='PNG')
    return out.getvalue()


def is_ziliao(q):
    if q.get('category') == 'ziliao':
        return True
    kps = q.get('knowledgePoints', []) or []
    return any('资料分析' in (kp or '') for kp in kps)


def process_lib(lib_path: Path, apply: bool, overwrite_small: bool = True, verbose: bool = False):
    stem = lib_path.stem
    parts = stem.split('_')
    if len(parts) < 3 or parts[0] != 'institution':
        return (0, 0, 0)
    year = int(parts[1])
    cls = parts[2].upper()
    if cls not in PDF_PATHS:
        return (0, 0, 0)
    pdf_path = PDF_PATHS[cls]
    if not Path(pdf_path).exists():
        return (0, 0, 0)
    sections = [s for s in PDF_SECTIONS[cls] if s[2] == year]
    if not sections:
        return (0, 0, 0)

    data = json.loads(lib_path.read_text(encoding='utf-8'))
    doc = fitz.open(pdf_path)
    examkey = f'institution_{year}_{cls.lower()}'
    out_dir = Path('public/img/questions') / examkey
    if apply:
        out_dir.mkdir(parents=True, exist_ok=True)

    n_check = n_hit = n_saved = 0
    for q in data:
        if not is_ziliao(q):
            continue
        if not needs_image(q):
            continue
        # 决定是否重抽：
        url = q.get('questionImage')
        if url:
            existing = Path('public') / url.lstrip('/')
            if existing.exists():
                try:
                    h = Image.open(existing).height
                except Exception:
                    h = 0
                # 资料分析图应 > 600 才合理
                if h >= 600 or not overwrite_small:
                    continue
        c = q.get('content', '') or ''
        if len(c.strip()) < 6:
            continue
        n_check += 1

        try:
            lib_qn = int(q['id'].rsplit('-', 1)[-1])
        except ValueError:
            continue
        pdf_qn = lib_qn - 100 if lib_qn > 100 else lib_qn

        # 多 section 中找最有可能的
        for (p0, p1, sy, sm) in sections:
            qa = find_q_anchor(doc, pdf_qn, (p0, p1), c)
            if not qa:
                continue
            q_page, q_rect = qa
            mat = find_material_above(doc, q_page, q_rect.y0, (p0, p1))
            if not mat:
                continue
            mat_page, mat_y, mat_rect, mat_pat = mat
            page = doc[q_page]
            opts_bottom = find_opts_bottom(page, q_rect.y0) or (q_rect.y0 + 220)
            opts_bottom = min(opts_bottom, page.rect.height - 30)
            n_hit += 1

            if not apply:
                if verbose:
                    print(f'  {q["id"]} qn={pdf_qn}: mat=({mat_page},{mat_y:.0f}) q=({q_page},{q_rect.y0:.0f}) end={opts_bottom:.0f}')
                break

            try:
                img_bytes = render_multi_page(
                    doc, mat_page, mat_y, q_page, opts_bottom, dpi=180,
                )
            except Exception as e:
                if verbose:
                    print(f'  ERROR {q["id"]}: {e}')
                break

            # 质量检验
            try:
                ih = Image.open(io.BytesIO(img_bytes)).height
            except Exception:
                ih = 0
            if ih < 400 or len(img_bytes) < 8000:
                if verbose:
                    print(f'  DROP {q["id"]}: h={ih} bytes={len(img_bytes)}')
                break

            out_path = out_dir / f'q{lib_qn:03d}.png'
            out_path.write_bytes(img_bytes)
            q['questionImage'] = f'/img/questions/{examkey}/q{lib_qn:03d}.png'
            n_saved += 1
            break

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
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()

    total_c = total_h = total_s = 0
    for f in sorted(Path('src/data/xingce').rglob('institution_*.json')):
        nc, nh, ns = process_lib(f, args.apply, verbose=args.verbose)
        if nc:
            print(f'{f}: check={nc} hit={nh} saved={ns}')
        total_c += nc
        total_h += nh
        total_s += ns
    mode = 'APPLY' if args.apply else 'DRY-RUN'
    print(f'\n[{mode}] check {total_c} 题, hit {total_h}, saved {total_s}')


if __name__ == '__main__':
    main()
