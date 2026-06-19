"""D-6 #1 续：裁剪 PNG 中间过长的空白行段（让 too_tall 图紧凑）。

针对 4 张 audit_figures 标 too_tall 的合法图形选项题：
- national_2025_dishi q115 / q126
- national_2025_xingzhengzhifa q125
- provincial_henan_2024 q110

算法：
1. 加载 PNG 转 grayscale
2. 找连续 >= 150 px 全白行段（white = pixel mean > 248）
3. 删除多余空白（保留首尾 30px 留白），生成新 PNG
4. 备份原图到 archive/reports/png_backup/{ek}_{qn}.png
"""
from __future__ import annotations
import shutil
import sys
import io
from pathlib import Path

import numpy as np
from PIL import Image  # type: ignore[import-not-found]

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "public" / "img" / "questions"
BACKUP_DIR = ROOT / "archive" / "reports" / "png_backup"

WHITE_THR = 248  # 像素均值 > 此值视为白行
MIN_BLANK_PX = 150  # 连续 >= 150 px 空白才裁
KEEP_PADDING = 30  # 保留首尾 30 px 空白


def trim_middle_blanks(img: Image.Image) -> Image.Image:
    """检测中间连续空白行段并裁掉，保留首尾 KEEP_PADDING px。"""
    gray = np.array(img.convert("L"))
    h, w = gray.shape
    row_mean = gray.mean(axis=1)
    is_white = row_mean > WHITE_THR

    # 找所有连续白段 (start, end)
    segments = []
    i = 0
    while i < h:
        if is_white[i]:
            j = i
            while j < h and is_white[j]:
                j += 1
            segments.append((i, j))
            i = j
        else:
            i += 1

    # 中间段（非首段非尾段）且长度 >= MIN_BLANK_PX 的，裁到 KEEP_PADDING * 2
    cuts = []  # 每段保留 [start, kept_end)
    for idx, (s, e) in enumerate(segments):
        seg_len = e - s
        is_head = (s == 0)
        is_tail = (e == h)
        if is_head or is_tail:
            cuts.append((s, e))  # 首尾段保留
        elif seg_len >= MIN_BLANK_PX:
            cuts.append((s, s + KEEP_PADDING * 2))  # 中间段保留 60 px
        else:
            cuts.append((s, e))

    # 拼接：白段按 cuts 保留，黑段保留全部
    new_rows = []
    last_end = 0
    for (s, e), (cs, ce) in zip(segments, cuts):
        # 黑段（last_end -> s）
        if s > last_end:
            new_rows.append(gray[last_end:s])
        # 白段裁后
        new_rows.append(gray[s:ce])
        last_end = e
    if last_end < h:
        new_rows.append(gray[last_end:])

    new_arr = np.concatenate(new_rows, axis=0)
    # 转回 RGB（保持原 mode）
    new_img = Image.fromarray(new_arr).convert(img.mode)
    return new_img


def process_one(rel_path: str) -> tuple[bool, int, int]:
    p = IMG_DIR / rel_path
    if not p.exists():
        return False, 0, 0
    img = Image.open(p)
    h_old = img.size[1]
    new_img = trim_middle_blanks(img)
    h_new = new_img.size[1]
    if h_new >= h_old - 30:  # 没省到 30 px 不替换
        return False, h_old, h_new
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_DIR / rel_path.replace("/", "_")
    shutil.copy2(p, backup)
    new_img.save(p, "PNG")
    return True, h_old, h_new


def main() -> None:
    targets = [
        "national_2025_dishi/q115.png",
        "national_2025_dishi/q126.png",
        "national_2025_xingzhengzhifa/q125.png",
        "provincial_henan_2024/q110.png",
    ]
    for rel in targets:
        changed, h_old, h_new = process_one(rel)
        marker = "✓" if changed else "·"
        print(f"  {marker} {rel}: {h_old} → {h_new} ({h_old - h_new:+d} px)")


if __name__ == "__main__":
    main()
