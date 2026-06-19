#!/usr/bin/env python3
"""收紧 png 底部多余白边，保证选项行完整。

算法：
  1) 灰度化，逐行统计白像素占比（>=WHITE_THRESH 视为白）
  2) 从底部往上找第一个"有实质内容行"：该行白占比 < CONTENT_WHITE_RATIO
  3) 保留 content_bottom + SAFETY_PAD 之下全部剪除
  4) 若底部多余白 < TRIGGER_PAD，跳过（不值得动）
  5) 剪后必须仍 >= 原高 * 0.5，否则回滚（防炸）

使用：
  python scripts/trim_bottom_whitespace.py --dry-run        # 默认
  python scripts/trim_bottom_whitespace.py --apply           # 实际覆写
  python scripts/trim_bottom_whitespace.py --apply --limit 10
"""
import os
import sys
import argparse
import shutil
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_ROOT = os.path.join(ROOT, 'public', 'img', 'questions')

WHITE_THRESH = 248          # 灰度 >= 此值算白
CONTENT_WHITE_RATIO = 0.97  # 行白占比 < 此值 → 有内容（留有余量防噪点）
SAFETY_PAD = 20             # 内容底边下保留的安全白边
TRIGGER_PAD = 40            # 多余白边 >= 此值才触发剪（< 40 不动）
MIN_SHRINK_RATIO = 0.5      # 剪后高度 >= 原高 * 此值，否则回滚


def analyze_bottom(arr: np.ndarray) -> tuple[int, int, int] | None:
    """返回 (content_bottom_y, trailing_white_px, new_h) 或 None（不需剪）。"""
    h = arr.shape[0]
    gray = arr if arr.ndim == 2 else arr.mean(axis=2)
    row_white = (gray >= WHITE_THRESH).mean(axis=1)

    # 从底部往上找第一个有内容行
    content_bottom = None
    for y in range(h - 1, -1, -1):
        if row_white[y] < CONTENT_WHITE_RATIO:
            content_bottom = y
            break

    if content_bottom is None:
        return None  # 整张白图，别动

    trailing_white = h - 1 - content_bottom
    if trailing_white < TRIGGER_PAD:
        return None  # 底部白边不够多，不值得剪

    new_h = min(h, content_bottom + 1 + SAFETY_PAD)
    if new_h >= h:
        return None
    return content_bottom, trailing_white, new_h


def trim_image(path: str, dry: bool) -> tuple[str, dict]:
    try:
        im = Image.open(path)
        mode = im.mode
        if mode not in ('RGB', 'L', 'RGBA'):
            im = im.convert('RGB')
            mode = 'RGB'
        arr = np.asarray(im)
    except Exception as e:
        return 'open_err', {'err': str(e)}

    result = analyze_bottom(arr)
    if result is None:
        return 'skip_no_need', {}

    content_bottom, trailing, new_h = result
    old_h = arr.shape[0]

    if new_h < old_h * MIN_SHRINK_RATIO:
        return 'skip_would_shrink_too_much', {
            'old_h': old_h, 'new_h': new_h,
        }

    removed = old_h - new_h
    info = {
        'old_h': old_h, 'new_h': new_h,
        'content_bottom': content_bottom,
        'trailing_white': trailing,
        'removed': removed,
    }

    if dry:
        return 'would_trim', info

    bak = path + '.bak'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)

    new_arr = arr[:new_h]
    Image.fromarray(new_arr).save(path, format='PNG', optimize=True)
    return 'trimmed', info


def collect_targets(limit: int = 0) -> list[str]:
    out = []
    for folder in sorted(os.listdir(IMG_ROOT)):
        fd = os.path.join(IMG_ROOT, folder)
        if not os.path.isdir(fd):
            continue
        for f in sorted(os.listdir(fd)):
            if f.endswith('.png'):
                out.append(os.path.join(fd, f))
    if limit:
        out = out[:limit]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--only', type=str, default='',
                    help='只处理路径含此子串的文件（调试用）')
    args = ap.parse_args()

    targets = collect_targets(args.limit)
    if args.only:
        targets = [t for t in targets if args.only in t.replace('\\', '/')]

    print(f'MODE: {"APPLY" if args.apply else "DRY-RUN"}  targets: {len(targets)}')

    buckets = {'would_trim': [], 'trimmed': [], 'skip_no_need': [],
               'skip_would_shrink_too_much': [], 'open_err': []}
    for i, p in enumerate(targets):
        st, info = trim_image(p, dry=not args.apply)
        buckets.setdefault(st, []).append((p, info))
        if (i + 1) % 200 == 0:
            print(f'  progress {i+1}/{len(targets)}')

    # 报告
    lines = [f'# 底部去白报告', '',
             f'- 模式: {"APPLY" if args.apply else "DRY-RUN"}',
             f'- 目标: {len(targets)}', '']
    for k in ('trimmed', 'would_trim', 'skip_would_shrink_too_much',
              'skip_no_need', 'open_err'):
        lines.append(f'- {k}: **{len(buckets.get(k, []))}**')
    lines.append('')

    # 明细：按 removed 降序列前 60
    cut = buckets.get('trimmed') or buckets.get('would_trim') or []
    lines.append('## 剪除明细（按 removed 降序）')
    for p, info in sorted(cut, key=lambda x: -x[1].get('removed', 0))[:60]:
        rel = os.path.relpath(p, ROOT).replace('\\', '/')
        lines.append(
            f'- `{rel}`  **-{info["removed"]}px**  '
            f'({info["old_h"]}→{info["new_h"]}, '
            f'content_bottom={info["content_bottom"]}, '
            f'trailing_white={info["trailing_white"]})'
        )
    if len(cut) > 60:
        lines.append(f'  ...余 {len(cut) - 60} 张')

    if buckets.get('skip_would_shrink_too_much'):
        lines.append('')
        lines.append('## 回滚保护（剪后会过矮）')
        for p, info in buckets['skip_would_shrink_too_much'][:20]:
            rel = os.path.relpath(p, ROOT).replace('\\', '/')
            lines.append(f'- `{rel}`  ({info["old_h"]} → {info["new_h"]})')

    os.makedirs(os.path.join(ROOT, 'tmp'), exist_ok=True)
    report_path = os.path.join(ROOT, 'tmp', 'trim_bottom_report.md')
    open(report_path, 'w', encoding='utf-8').write('\n'.join(lines))

    print(f'\n=== SUMMARY ===')
    for k, v in buckets.items():
        if v:
            print(f'  {k:<32} {len(v)}')
    print(f'  详见 tmp/trim_bottom_report.md')


if __name__ == '__main__':
    main()
