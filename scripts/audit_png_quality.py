"""D-5 #2 续：PNG 实质质量审查（清晰度 / 尺寸 / 文件大小）。

审查 public/img/questions/**/*.png 的：
1. 分辨率（width × height）分布
2. 文件大小（KB）
3. 异常 PNG 列表（过小 < 5KB / 过大 > 500KB / 极扁过宽）
"""
from __future__ import annotations
import io
import sys
from pathlib import Path
from collections import Counter

from PIL import Image  # type: ignore[import-not-found]

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "public" / "img" / "questions"
OUT = ROOT / "archive" / "reports" / "d5_png_quality.md"


def main() -> None:
    pngs = list(IMG_DIR.rglob("*.png"))
    print(f"扫 {len(pngs)} 张 PNG...")

    sizes = []
    widths = []
    heights = []
    file_sizes = []
    too_small = []
    too_large = []
    too_thin = []  # h<200 但 w>800
    too_tall = []  # h>1500
    bad_ratio = []  # 宽高比 > 5 或 < 0.1
    cant_open = []

    for p in pngs:
        try:
            with Image.open(p) as img:
                w, h = img.size
        except Exception:
            cant_open.append(p)
            continue
        sz = p.stat().st_size
        widths.append(w)
        heights.append(h)
        file_sizes.append(sz)

        if sz < 5_000:
            too_small.append((p, w, h, sz))
        if sz > 500_000:
            too_large.append((p, w, h, sz))
        if h < 200 and w > 800:
            too_thin.append((p, w, h, sz))
        if h > 1500:
            too_tall.append((p, w, h, sz))
        ratio = w / max(h, 1)
        if ratio > 5 or ratio < 0.1:
            bad_ratio.append((p, w, h, sz, ratio))

    lines = [f"# D-5 #2 PNG 实质质量审查\n\n"]
    lines.append(f"## 总览\n\n- 总数: {len(pngs)} 张\n")
    if file_sizes:
        avg_size = sum(file_sizes) / len(file_sizes)
        lines.append(f"- 平均文件大小: {avg_size/1024:.1f} KB\n")
        lines.append(f"- 最小 / 中位 / 最大: {min(file_sizes)/1024:.1f} / {sorted(file_sizes)[len(file_sizes)//2]/1024:.1f} / {max(file_sizes)/1024:.1f} KB\n")
    if widths:
        lines.append(f"- 宽度: 最小 {min(widths)} / 中位 {sorted(widths)[len(widths)//2]} / 最大 {max(widths)}\n")
        lines.append(f"- 高度: 最小 {min(heights)} / 中位 {sorted(heights)[len(heights)//2]} / 最大 {max(heights)}\n")

    sections = [
        ("打不开/损坏", cant_open, lambda x: f"  - {x}"),
        ("过小 (< 5 KB, 疑似空白/损坏)", too_small,
         lambda x: f"  - {x[0]} ({x[1]}×{x[2]}, {x[3]/1024:.1f}KB)"),
        ("过大 (> 500 KB, 未优化)", too_large,
         lambda x: f"  - {x[0]} ({x[1]}×{x[2]}, {x[3]/1024:.1f}KB)"),
        ("过扁 (h<200 & w>800, 疑似只切到一行)", too_thin,
         lambda x: f"  - {x[0]} ({x[1]}×{x[2]}, {x[3]/1024:.1f}KB)"),
        ("过高 (h>1500, 疑似跨页拼合)", too_tall,
         lambda x: f"  - {x[0]} ({x[1]}×{x[2]}, {x[3]/1024:.1f}KB)"),
        ("宽高比异常 (>5 或 <0.1)", bad_ratio,
         lambda x: f"  - {x[0]} ({x[1]}×{x[2]}, ratio={x[4]:.2f})"),
    ]
    for title, items, fmt in sections:
        lines.append(f"\n## {title}: {len(items)} 张\n\n")
        for it in items[:50]:
            lines.append(fmt(it) + "\n")
        if len(items) > 50:
            lines.append(f"\n... 共 {len(items)}，仅列前 50。\n")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(lines), encoding="utf-8")
    print(f"\n报告: {OUT}")
    print(f"\n汇总:")
    print(f"  打不开: {len(cant_open)}")
    print(f"  过小: {len(too_small)}")
    print(f"  过大: {len(too_large)}")
    print(f"  过扁: {len(too_thin)}")
    print(f"  过高: {len(too_tall)}")
    print(f"  比例异常: {len(bad_ratio)}")


if __name__ == "__main__":
    main()
