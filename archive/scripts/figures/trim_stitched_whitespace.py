#!/usr/bin/env python3
"""剪除跨页拼接图中间的大段空白带。

场景：`extract_figures.py::_stitch_vertical` 把两页垂直拼接时，
源图自带的"页底空白"和"页顶空白"原样带入，最终图片中段常见 100~400px 全白带。

算法：
  1) 逐行扫描 alpha≈白的比例，高亮≥99% 的连续行 → "白带"
  2) 只剪图片"中段"白带（不动顶部题号上的小白、底部的边距留白）
  3) 连续剪除段高度阈值 MIN_TRIM_BAND = 120px
  4) 每张图最多剪 1 条内部白带（保守：避免把正常的图间留白全剪穿）
  5) 剪完后必须满足：新高 < 旧高 且 新高 > 旧高 * 0.4（防剪穿）；否则回滚

稳健：
  - 只处理 `git diff --name-only --diff-filter=M` 里 png（本轮修改过的 491 张）
  - 原图备份到 `.bak`；新图验证通过才覆盖
  - 产出 `tmp/trim_report.md` 列出剪与未剪的文件
"""
import os, sys, subprocess, shutil, argparse
import numpy as np
from PIL import Image

WHITE_THRESH = 248          # 灰度 >=此值视为白
ROW_WHITE_RATIO = 0.985     # 某行白像素占比 >= 此值 → 全白行
MIN_TRIM_BAND = 120         # 剪除的连续白带最小高度（像素）
TOP_TEXT_GUARD = 25         # 保留顶部 25px 内的首段白（即题号行上方的余白）
BOTTOM_EDGE_GUARD = 40      # 底部 40px 内的白不剪（保留底部边距）
KEEP_PAD = 10               # 白带两端保留的白边


def detect_inner_white_band(arr: np.ndarray) -> tuple[int, int] | None:
    """返回 (y_start, y_end) 的最长内部白带；无则 None。"""
    h = arr.shape[0]
    gray = arr if arr.ndim == 2 else arr.mean(axis=2)
    row_white = (gray >= WHITE_THRESH).mean(axis=1)
    white_rows = row_white >= ROW_WHITE_RATIO

    best = None
    cur_start = None
    for y in range(h):
        if white_rows[y]:
            if cur_start is None:
                cur_start = y
        else:
            if cur_start is not None and y - cur_start >= MIN_TRIM_BAND:
                s, e = cur_start, y
                # 顶部豁免：如果白带紧贴图片顶端（起点<25），当成题号上方留白不剪
                # 底部豁免：白带贴底部 40px 内不剪
                if s > TOP_TEXT_GUARD and (h - e) > BOTTOM_EDGE_GUARD:
                    if best is None or (e - s) > (best[1] - best[0]):
                        best = (s, e)
            cur_start = None
    # 尾端
    if cur_start is not None and h - cur_start >= MIN_TRIM_BAND:
        pass  # 尾端视为底部边距，不剪
    return best


def trim_image(path: str, dry: bool):
    try:
        im = Image.open(path).convert('L' if Image.open(path).mode in ('L', '1') else 'RGB')
        arr = np.asarray(im)
    except Exception as e:
        return None, f'open_err: {e}'

    band = detect_inner_white_band(arr)
    if not band:
        return None, 'no_band'

    s, e = band
    old_h = arr.shape[0]
    # 保留两端 KEEP_PAD 作为过渡
    new_s = max(0, s + KEEP_PAD)
    new_e = min(old_h, e - KEEP_PAD)
    if new_e <= new_s:
        return None, 'band_too_thin_after_pad'

    # 合成：[0..new_s] + [new_e..h]
    top = arr[:new_s]
    bot = arr[new_e:]
    new_arr = np.concatenate([top, bot], axis=0)
    new_h = new_arr.shape[0]

    # 守卫
    if new_h >= old_h:
        return None, 'no_shrink'
    if new_h < old_h * 0.4:
        return None, f'shrank_too_much({old_h}→{new_h})'

    removed = old_h - new_h
    if dry:
        return ('would_trim', removed), f'band=[{s},{e}] removed={removed}px  {old_h}→{new_h}'

    # 备份 + 覆写
    bak = path + '.bak'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    Image.fromarray(new_arr).save(path, format='PNG', optimize=True)
    return ('trimmed', removed), f'band=[{s},{e}] removed={removed}px  {old_h}→{new_h}'


def get_targets() -> list[str]:
    r = subprocess.run(['git', 'diff', '--name-only', '--diff-filter=M'],
                       capture_output=True, text=True)
    return [l for l in r.stdout.splitlines()
            if l.endswith('.png') and 'public/img/questions/' in l]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--limit', type=int, default=0, help='只处理前 N 张（调试）')
    args = ap.parse_args()

    targets = get_targets()
    if args.limit:
        targets = targets[:args.limit]
    print(f'MODE: {"APPLY" if args.apply else "DRY-RUN"}  targets: {len(targets)}')

    trimmed = []
    skipped = []
    for i, p in enumerate(targets):
        st, msg = trim_image(p, dry=not args.apply)
        if st and st[0] in ('would_trim', 'trimmed'):
            trimmed.append((p, st[1], msg))
        else:
            skipped.append((p, msg))
        if (i + 1) % 100 == 0:
            print(f'  progress {i+1}/{len(targets)}')

    # report
    lines = [f'# 去白带报告', '', f'- 模式: {"APPLY" if args.apply else "DRY-RUN"}',
             f'- 目标: {len(targets)}',
             f'- 可剪/已剪: {len(trimmed)}',
             f'- 跳过: {len(skipped)}', '']
    lines.append('## 剪除明细')
    for p, removed, msg in sorted(trimmed, key=lambda x: -x[1])[:80]:
        lines.append(f'- `{p}`  **-{removed}px**  {msg}')
    if len(trimmed) > 80:
        lines.append(f'  ...余 {len(trimmed)-80} 张')
    os.makedirs('tmp', exist_ok=True)
    open('tmp/trim_report.md', 'w', encoding='utf-8').write('\n'.join(lines))

    print(f'\n=== SUMMARY ===')
    print(f'  可剪/已剪: {len(trimmed)}')
    print(f'  跳过:     {len(skipped)} (多数 no_band / no_shrink)')
    print(f'  详见 tmp/trim_report.md')


if __name__ == '__main__':
    main()
