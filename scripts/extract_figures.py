#!/usr/bin/env python3
"""
图形推理题图片提取器
从 PDF 中提取图形推理题的题目图片和选项图片，保存为 PNG。
使用 PyMuPDF 渲染 PDF 页面并裁剪题目区域。
"""

import argparse
import json
import os
import re
import sys
import warnings
import unicodedata

warnings.filterwarnings("ignore")

import io

import fitz  # PyMuPDF
from PIL import Image


# 裁剪兜底参数（pt 单位，1pt ≈ 1/72 英寸）
MAX_CLIP_HEIGHT = 480          # 单题图形区域最大高度（避免吞掉下一题）
MIN_CLIP_HEIGHT = 180          # 小于此高度视为"题干在页底、图在下页"，触发跨页合并
MIN_NEXT_PAGE_HEIGHT = 60      # 下一页可用高度低于此值说明图其实全在本页，别跨页
MIN_VALID_BYTES = 10000        # 小于此字节视为裁剪失败
NUMBER_LEFT_MAX_X = 120        # 题号应在左侧；x 超过此值的视为正文误匹配
OPT_BOTTOM_PAD = 18            # 选项锚点以下额外保留空间（避免切掉选项内容/字母）
TOP_PREV_OPT_SCAN = 35         # 题号上方扫描该范围内的残留选项文字


def normalize_cjk(text: str) -> str:
    """选择性正规化 CJK 兼容字符"""
    result = []
    for ch in text:
        cp = ord(ch)
        if 0x2F00 <= cp <= 0x2FDF or 0xF900 <= cp <= 0xFAD9:
            result.append(unicodedata.normalize("NFKC", ch))
        else:
            result.append(ch)
    return "".join(result)


def find_question_pages(
    doc: fitz.Document,
    q_numbers: list[int],
    content_hints: dict[int, str] | None = None,
) -> dict[int, list]:
    """
    在 PDF 中定位每道题的页码和位置。返回 {题号: [(page_idx, rect), ...]}。
    若提供 content_hints，则用题干前 8~12 字在候选 rect 下方文本中校验，
    解决"96." 多次出现的消歧问题。
    """
    content_hints = content_hints or {}
    result = {}

    for page_idx in range(len(doc)):
        page = doc[page_idx]

        for q_num in q_numbers:
            patterns = [f"{q_num}.", f"{q_num}．", f"{q_num}、"]
            for pat in patterns:
                areas = page.search_for(pat)
                if not areas:
                    continue
                left_areas = [r for r in areas if r.x0 < NUMBER_LEFT_MAX_X]
                if not left_areas:
                    continue
                result.setdefault(q_num, []).extend(
                    (page_idx, r) for r in left_areas
                )
                break

    # content_hints 消歧：对每个题号，挑最匹配的候选
    if content_hints:
        for q_num, cands in list(result.items()):
            hint = content_hints.get(q_num, "").strip()
            if not hint or len(cands) <= 1:
                continue
            # 取 hint 前 10 字（去掉空白/标点噪声）
            probe = "".join(ch for ch in hint if ch.strip())[:10]
            if not probe:
                continue
            scored = []
            for pidx, rect in cands:
                pg = doc[pidx]
                # 在题号下方 200pt 内取文本
                clip = fitz.Rect(
                    max(0, rect.x0 - 5),
                    rect.y0,
                    pg.rect.width,
                    min(pg.rect.height, rect.y1 + 200),
                )
                near_text = normalize_cjk(pg.get_textbox(clip))
                # 计算 probe 中有多少字符出现在 near_text 里
                score = sum(1 for ch in probe if ch in near_text)
                scored.append((score, pidx, rect))
            scored.sort(key=lambda x: -x[0])
            best_score = scored[0][0]
            # 只保留得分最高的；若都 0 分则全保留
            if best_score > 0:
                result[q_num] = [(p, r) for s, p, r in scored if s == best_score]

    return result


def _find_prev_opts_bottom(page: fitz.Page, y_max: float) -> float | None:
    """查找 y_max 上方 TOP_PREV_OPT_SCAN pt 内的上一题选项最后一行 y1，避免漏入本题。"""
    scan_top = max(0, y_max - TOP_PREV_OPT_SCAN)
    bottom = None
    for pat in ("D．", "D.", "D、"):
        for r in page.search_for(pat):
            if scan_top < r.y0 < y_max and r.x0 < 900:  # 选项D通常不在最右
                bottom = max(bottom or 0, r.y1)
    return bottom


def _find_options_anchor_y(page: fitz.Page, y_min: float) -> float | None:
    """
    查找选项 A 在 y_min 之下的最上方位置，作为题目图形区域 y1 的兜底。
    返回找到的 y0，或 None。
    """
    candidates = []
    for pat in ("A．", "A.", "A、"):
        for r in page.search_for(pat):
            # 必须在 y_min 之下，且 x 不能太靠右（排除选项内容里的 A.）
            if r.y0 > y_min + 5 and r.x0 < NUMBER_LEFT_MAX_X + 60:
                candidates.append(r.y0)
    return min(candidates) if candidates else None


def _render_clip(page: fitz.Page, clip: fitz.Rect, dpi: int) -> bytes:
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False)
    return pix.tobytes("png")


def _stitch_vertical(img_bytes_list: list[bytes]) -> bytes:
    """垂直拼接多张 PNG，按最大宽度对齐，白底居中。"""
    imgs = [Image.open(io.BytesIO(b)).convert("RGB") for b in img_bytes_list]
    max_w = max(im.width for im in imgs)
    total_h = sum(im.height for im in imgs) + 10 * (len(imgs) - 1)
    canvas = Image.new("RGB", (max_w, total_h), (255, 255, 255))
    y = 0
    for im in imgs:
        x = (max_w - im.width) // 2
        canvas.paste(im, (x, y))
        y += im.height + 10
    out = io.BytesIO()
    canvas.save(out, format="PNG", optimize=True)
    return out.getvalue()


def extract_question_image(
    doc: fitz.Document,
    page_idx: int,
    q_start_rect: fitz.Rect,
    next_q_rect: fitz.Rect | None,
    next_q_page_idx: int | None,
    page_height: float,
    page_width: float,
    dpi: int = 300,
) -> bytes:
    """
    裁剪题目图形区域，带三重兜底：
      1) 下一题 rect 作为 y1（本页）
      2) 选项 A 锚点作为 y1
      3) 最大高度 MAX_CLIP_HEIGHT 作为 y1
    若当前页裁出区域过小，自动跨页合并下一页上半部分。
    """
    page = doc[page_idx]

    # y0: 起点含题号本身（便于用户看到题号），再检查上方是否有上一题选项残留
    y0 = q_start_rect.y0 - 2
    prev_opt_bottom = _find_prev_opts_bottom(page, y0)
    if prev_opt_bottom and prev_opt_bottom < q_start_rect.y0:
        # 上方有上一题选项 → y0 推到选项之后但仍含本题号
        y0 = max(prev_opt_bottom + 4, q_start_rect.y0 - 2)
    x0 = 20
    x1 = page_width - 20

    # 计算 y1：选项 A 锚点 + 余量，再和下一题 rect 取 min
    anchor_y = _find_options_anchor_y(page, q_start_rect.y1 + 2)
    same_page_next = (
        next_q_rect is not None
        and next_q_page_idx == page_idx
        and next_q_rect.y0 > q_start_rect.y0
    )
    candidates = []
    if anchor_y is not None:
        # 向下保留 OPT_BOTTOM_PAD 以包含选项内容（文字/字母）
        candidates.append(anchor_y + OPT_BOTTOM_PAD)
    if same_page_next:
        candidates.append(next_q_rect.y0 - 3)
    if candidates:
        y1 = min(candidates)
    else:
        y1 = page_height - 30

    # 最大高度兜底
    if y1 - y0 > MAX_CLIP_HEIGHT:
        y1 = y0 + MAX_CLIP_HEIGHT

    y1 = min(y1, page_height - 20)
    y0 = max(y0, 20)

    clip = fitz.Rect(x0, y0, x1, y1)
    img_bytes = _render_clip(page, clip, dpi)

    # 跨页合并触发条件：
    # 1) 本页裁出区域过小 / 字节过少
    # 2) 本页未找到选项锚点 且 题号靠近页底（题干在本页、图在下页的典型场景）
    no_anchor_near_bottom = (
        anchor_y is None
        and not same_page_next
        and q_start_rect.y0 > page_height * 0.5
    )
    need_stitch = (
        (not same_page_next)
        and (page_idx + 1 < len(doc))
        and (
            y1 - y0 < MIN_CLIP_HEIGHT
            or len(img_bytes) < MIN_VALID_BYTES
            or no_anchor_near_bottom
        )
    )
    if need_stitch:
        next_page = doc[page_idx + 1]
        np_rect = next_page.rect
        np_y0 = 20
        # 下一页 y1：下一题 rect（若在下一页）→ 选项 A → 最大高度
        if next_q_rect is not None and next_q_page_idx == page_idx + 1:
            np_y1 = next_q_rect.y0 - 3
        else:
            anchor_y = _find_options_anchor_y(next_page, np_y0)
            np_y1 = anchor_y + OPT_BOTTOM_PAD if anchor_y else np_y0 + MAX_CLIP_HEIGHT
        np_y1 = min(np_y1, np_rect.height - 20)
        if np_y1 - np_y0 > MAX_CLIP_HEIGHT:
            np_y1 = np_y0 + MAX_CLIP_HEIGHT

        # 下一题的题号就顶在下一页页首 —— 下一页压根没给本题留空间，说明图其实
        # 全在本页。此时若还去拼，会拿一条几 pt 高的空白把本页好好的裁剪替换掉，
        # 产出 300 来字节的空图（上海 2021 第 47 题即此情形）。
        if np_y1 - np_y0 < MIN_NEXT_PAGE_HEIGHT:
            return img_bytes

        np_clip = fitz.Rect(20, np_y0, np_rect.width - 20, np_y1)
        np_bytes = _render_clip(next_page, np_clip, dpi)

        # 若当前页几乎空白，只用下一页；否则拼接
        if y1 - y0 < MIN_CLIP_HEIGHT:
            img_bytes = np_bytes
        else:
            # 将当前页 clip 裁到内容实际底部（去掉多余空白）
            # 简单处理：直接拼接，宽度按最大对齐
            img_bytes = _stitch_vertical([img_bytes, np_bytes])

    return img_bytes


def extract_figure_questions(
    pdf_path: str,
    question_numbers: list[int],
    output_dir: str,
    prefix: str = "",
    dpi: int = 200,
    content_hints: dict[int, str] | None = None,
    verify_hint: bool = False,
) -> dict[int, str]:
    """
    从 PDF 提取指定题号的图形推理题图片。
    返回 {题号: 图片路径}

    verify_hint=True 时，裁剪区域内的文字必须与该题题干对得上才产出。
    补缺场景下候选 PDF 是按年份/省份猜的，猜错卷时题号照样能匹配上，
    结果抽出隔壁卷的整页 —— 这道校验专门拦这个。
    """
    doc = fitz.open(pdf_path)
    result = {}

    os.makedirs(output_dir, exist_ok=True)

    all_nums = set()
    for n in question_numbers:
        all_nums.update(range(max(1, n - 1), n + 2))

    q_positions = find_question_pages(doc, sorted(all_nums), content_hints)

    for q_num in question_numbers:
        if q_num not in q_positions:
            print(f"  [WARN] Q{q_num} 未在PDF中定位到")
            continue

        page_idx, q_rect = q_positions[q_num][0]
        page = doc[page_idx]
        page_rect = page.rect

        if verify_hint:
            probe = "".join(ch for ch in (content_hints or {}).get(q_num, "")
                            if not ch.isspace())[:12]
            clip = fitz.Rect(max(0, q_rect.x0 - 5), q_rect.y0,
                             page_rect.width,
                             min(page_rect.height, q_rect.y1 + 120))
            near = normalize_cjk(page.get_textbox(clip)).replace(" ", "")
            hit = sum(1 for ch in probe if ch in near)
            if len(probe) < 8:
                # 题干本身就残缺（山东 2020 有两道题干只剩 "4%。"），没法校验。
                # 校验不了就不产出，别拿一整页别的题冒充题图。
                print(f"  [WARN] Q{q_num} 题干过短（{probe!r}）无法校验，跳过")
                continue
            if hit < len(probe) * 0.6:
                print(f"  [WARN] Q{q_num} 题干对不上（{hit}/{len(probe)}），疑似抽错卷，跳过")
                continue

        # 找下一题的位置（可能在本页或下一页）
        next_rect = None
        next_page_idx = None
        next_num = q_num + 1
        if next_num in q_positions:
            for pidx, r in q_positions[next_num]:
                if pidx == page_idx and r.y0 > q_rect.y0:
                    next_rect = r
                    next_page_idx = pidx
                    break
                elif pidx > page_idx:
                    next_rect = r
                    next_page_idx = pidx
                    break

        try:
            img_bytes = extract_question_image(
                doc, page_idx, q_rect, next_rect, next_page_idx,
                page_rect.height, page_rect.width, dpi
            )

            filename = f"{prefix}q{q_num:03d}.png"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "wb") as f:
                f.write(img_bytes)

            result[q_num] = filepath

        except Exception as e:
            print(f"  [ERROR] Q{q_num}: {e}")

    doc.close()
    return result


def update_json_with_images(
    json_path: str,
    image_map: dict[int, str],
    public_prefix: str,
):
    """
    更新 JSON 题库文件，为图形推理题添加图片路径。
    """
    with open(json_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    updated = 0
    for q in questions:
        # 从 ID 中提取题号
        parts = q["id"].split("-")
        try:
            q_num = int(parts[-1])
        except ValueError:
            continue

        if q_num in image_map:
            img_path = image_map[q_num]
            # 转为 public 相对路径
            rel_path = img_path.replace("\\", "/")
            if "public/" in rel_path:
                rel_path = "/" + rel_path.split("public/")[1]
            else:
                rel_path = public_prefix + os.path.basename(img_path)

            q["questionImage"] = rel_path

            # 标记图形推理题的选项
            is_figure = any(kw in q.get("content", "") for kw in [
                "图形", "填入问号", "选择最合适的一个填入",
                "选择最合适的一项填入", "直观图", "呈现一定的规律",
            ])
            if is_figure:
                q["options"] = [
                    {"label": "A", "content": "[见图]"},
                    {"label": "B", "content": "[见图]"},
                    {"label": "C", "content": "[见图]"},
                    {"label": "D", "content": "[见图]"},
                ]

            updated += 1

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    return updated


def process_exam(
    pdf_path: str,
    json_path: str,
    output_base: str,
    exam_id: str,
    dpi: int = 300,
    only: set[int] | None = None,
):
    """处理一套试卷的图形推理题。

    only 给定题号集合时，跳过关键词判定直接按题号提取 —— 补缺场景下我们已经
    确切知道缺哪几张图，而关键词表覆盖不全（例如「使之呈现一定规律性」少个
    「的」字就匹配不上「呈现一定的规律」），会把要补的题直接漏掉。
    """
    # 读取 JSON 找出需要提取图片的题号
    with open(json_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    figure_nums = []
    hints: dict[int, str] = {}
    for q in questions:
        parts = q["id"].split("-")
        try:
            q_num = int(parts[-1])
        except ValueError:
            continue

        if only is not None:
            if q_num not in only:
                continue
        else:
            is_figure = any(kw in q.get("content", "") for kw in [
                "图形", "填入问号", "选择最合适的一个填入", "选择最合适的一项填入",
                "直观图", "呈现一定的规律",
                "多面体", "折叠",
            ])
            if not is_figure:
                continue

        figure_nums.append(q_num)
        hints[q_num] = q.get("content", "")

    if not figure_nums:
        return 0

    # 提取图片
    output_dir = os.path.join(output_base, exam_id)
    image_map = extract_figure_questions(
        pdf_path, figure_nums, output_dir, prefix="", dpi=dpi,
        content_hints=hints, verify_hint=only is not None,
    )

    # 更新 JSON。--only 是补缺场景，图提到临时目录、由调用方挑着回填，
    # 这里不该顺手改题库（会把还没验收的路径写进去）。
    if only is not None:
        return len(image_map)
    public_prefix = f"/img/questions/{exam_id}/"
    updated = update_json_with_images(json_path, image_map, public_prefix)

    return updated


def main():
    parser = argparse.ArgumentParser(description="图形推理题图片提取器")
    parser.add_argument("--pdf", required=True, help="行测真题PDF路径")
    parser.add_argument("--json", required=True, help="对应的判断推理JSON路径")
    parser.add_argument("--exam-id", required=True, help="考试标识（如 national_2025_fushengjia）")
    parser.add_argument("--output-dir", default="public/img/questions", help="图片输出目录")
    parser.add_argument("--dpi", type=int, default=300, help="渲染分辨率")
    parser.add_argument("--only", default="", help="只提取这些题号（逗号分隔），并跳过题库写回")
    args = parser.parse_args()

    only = None
    if args.only.strip():
        only = {int(x) for x in args.only.replace('，', ',').split(',') if x.strip()}

    print(f"提取图形推理题图片: {args.exam_id}")
    updated = process_exam(args.pdf, args.json, args.output_dir, args.exam_id,
                           args.dpi, only)
    print(f"  更新了 {updated} 道题")


if __name__ == "__main__":
    main()
