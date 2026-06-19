#!/usr/bin/env python3
"""C阶段#5 补图：从 PDF 真题（不是答案 PDF）抽缺失的题图。

策略：
- 找题号 N 位置（rect.x0 < 100 视为左侧题号）
- 找题号 N+1 位置（下边界）
- 渲染题号 N → N+1 之间整段 bbox 为 PNG
- 跨页时只渲染当前页（题号到页底）

不动 JSON，只补 PNG 文件。前端按 examKey/q{NN}.png 加载。
"""
from __future__ import annotations
import argparse
import glob
import sys
from pathlib import Path

import fitz  # type: ignore[import-not-found]


ROOT = Path(__file__).resolve().parent.parent

LEVEL_KEYWORDS = {
    "dishi": ["地市级", "市地级"],
    "fushengjia": ["副省级", "省部级", "省级"],
    "xingzhengzhifa": ["行政执法"],
}

# 28 张缺图清单：(examKey, [题号列表])
TARGETS: dict[str, list[int]] = {
    "national_2015_dishi": [20, 61, 70, 87],
    "national_2015_fushengjia": [20, 62, 64, 71, 75, 92],
    "national_2016_dishi": [15],
    "national_2016_fushengjia": [15],
    "national_2017_dishi": [16],
    "national_2017_fushengjia": [12],
    "national_2018_fushengjia": [13],
    "national_2019_fushengjia": [9, 43, 129],
    "national_2020_dishi": [18, 85],
    "national_2020_fushengjia": [53, 93],
    "national_2022_dishi": [70, 129],
    "national_2022_fushengjia": [80, 134],
    "national_2025_fushengjia": [26],
    "national_2025_xingzhengzhifa": [29],
}

NUMBER_LEFT_MAX_X = 120
SCALE = 2.0


def find_pdf(year: str, level: str) -> Path | None:
    keywords = LEVEL_KEYWORDS.get(level, [level])
    for p in glob.glob(f"material/**/{year}*行测*.pdf", recursive=True):
        if "国考" not in p and "【国考】" not in p:
            continue
        # 真题 PDF：不含"答案"和"解析"
        if "答案" in p or "解析" in p:
            continue
        pb = p.encode("utf-8")
        for kw in keywords:
            if kw.encode("utf-8") in pb:
                return Path(p)
    return None


def find_qn_position(doc: fitz.Document, qn: int) -> tuple[int, fitz.Rect] | None:
    patterns = [f"{qn}.", f"{qn}．", f"{qn}、"]
    for pi in range(doc.page_count):
        page = doc[pi]
        for pat in patterns:
            areas = page.search_for(pat)
            left = [r for r in areas if r.x0 < NUMBER_LEFT_MAX_X]
            if left:
                # 取 y 最小的（页面最上方那个）
                left.sort(key=lambda r: r.y0)
                return pi, left[0]
    return None


def extract_one(pdf: Path, qn: int, out_path: Path) -> tuple[bool, str]:
    doc = fitz.open(pdf)
    pos = find_qn_position(doc, qn)
    if not pos:
        return False, f"题号 {qn} 未在 PDF 中定位"
    pi, rect = pos
    pos_next = find_qn_position(doc, qn + 1)

    page = doc[pi]
    pw = page.rect.width
    ph = page.rect.height
    margin_x = 25
    top = max(rect.y0 - 8, 30)

    if pos_next and pos_next[0] == pi:
        # 同页：截到下一题号上方
        bottom = max(top + 100, pos_next[1].y0 - 5)
        clip = fitz.Rect(margin_x, top, pw - margin_x, bottom)
        mat = fitz.Matrix(SCALE, SCALE)
        pix = page.get_pixmap(matrix=mat, clip=clip)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(out_path))
        return True, f"page {pi + 1}, h={int(bottom - top)}pt, size={out_path.stat().st_size}B"

    # 跨页：拼接当前页 (top→页底) + 下一页 (顶→下题号)
    bottom1 = ph - 35
    if bottom1 <= top:
        return False, f"bbox 异常 top={top} bottom={bottom1}"

    clip1 = fitz.Rect(margin_x, top, pw - margin_x, bottom1)
    mat = fitz.Matrix(SCALE, SCALE)
    pix1 = page.get_pixmap(matrix=mat, clip=clip1)

    if pos_next is None:
        # 末题：只用当前页
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pix1.save(str(out_path))
        return True, f"page {pi + 1} only (last q), h={int(bottom1 - top)}pt"

    pi_next, rect_next = pos_next
    page_next = doc[pi_next]
    top_next = 35
    bottom_next = max(top_next + 50, rect_next.y0 - 5)
    clip2 = fitz.Rect(margin_x, top_next, page_next.rect.width - margin_x, bottom_next)
    pix2 = page_next.get_pixmap(matrix=mat, clip=clip2)

    # 用 PIL 拼接
    import io
    from PIL import Image as PILImage

    img1 = PILImage.open(io.BytesIO(pix1.tobytes("png")))
    img2 = PILImage.open(io.BytesIO(pix2.tobytes("png")))
    new_w = max(img1.width, img2.width)
    new_h = img1.height + img2.height + 6  # 中间留 6px 间隔
    canvas = PILImage.new("RGB", (new_w, new_h), "white")
    canvas.paste(img1, (0, 0))
    canvas.paste(img2, (0, img1.height + 6))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    return (
        True,
        f"stitched page {pi + 1} ({int(bottom1 - top)}pt) + page {pi_next + 1} "
        f"({int(bottom_next - top_next)}pt), size={out_path.stat().st_size}B",
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exam", help="只处理指定 examKey")
    ap.add_argument("--qn", type=int, help="只处理指定题号（需配合 --exam）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    targets = dict(TARGETS)
    if args.exam:
        if args.exam not in targets:
            print(f"不在清单: {args.exam}", file=sys.stderr)
            sys.exit(1)
        if args.qn is not None:
            targets = {args.exam: [args.qn]}
        else:
            targets = {args.exam: targets[args.exam]}

    ok = fail = 0
    for exam, qns in targets.items():
        # examKey: national_{year}_{level}
        parts = exam.split("_")
        year, level = parts[1], "_".join(parts[2:])
        pdf = find_pdf(year, level)
        if not pdf:
            print(f"[{exam}] ❌ 未找到真题 PDF", file=sys.stderr)
            fail += len(qns)
            continue
        for qn in qns:
            out = ROOT / "public" / "img" / "questions" / exam / f"q{qn:03d}.png"
            if args.dry_run:
                print(f"  [DRY] {exam} q{qn:03d}: would write {out}")
                continue
            success, msg = extract_one(pdf, qn, out)
            tag = "OK " if success else "FAIL"
            print(f"  [{tag}] {exam} q{qn:03d}: {msg}")
            if success:
                ok += 1
            else:
                fail += 1

    print(f"\n合计: ok={ok}, fail={fail}")


if __name__ == "__main__":
    main()
