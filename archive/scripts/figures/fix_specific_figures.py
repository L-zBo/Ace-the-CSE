#!/usr/bin/env python3
"""定点修复审计发现的 4 张问题图片。

原则：稳健——先备份，再重抽，验证通过才替换；否则回滚。
运行: python scripts/fix_specific_figures.py [--dry-run]
"""
import os, sys, json, shutil, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from extract_figures import extract_figure_questions
from batch_extract_figures import find_pdf_for_json
from audit_figures import near_white_ratio


# 审计报告认定的 4 个问题 (exam_id, qn, 原因)
TARGETS = [
    ('national_2022_dishi',      79, 'wrong_crop_prev_options'),
    ('national_2025_dishi',      81, 'nearly_blank'),
    ('provincial_jiangsu_2024',  80, 'header_in_stitch'),
    ('provincial_shandong_2022', 50, 'footer_in_stitch'),
]

IMG_ROOT = 'public/img/questions'
JSON_ROOT = 'src/data/xingce/panduan'


def load_content(json_path: str, qn: int) -> str:
    qs = json.load(open(json_path, encoding='utf-8'))
    for q in qs:
        try:
            if int(q['id'].split('-')[-1]) == qn:
                return q.get('content', '')
        except ValueError:
            continue
    return ''


def measure(png_path: str):
    if not os.path.exists(png_path):
        return None
    try:
        with Image.open(png_path) as im:
            w, h = im.size
            wr = near_white_ratio(im)
        return w, h, round(wr, 3), os.path.getsize(png_path)
    except Exception as e:
        return ('err', str(e))


def verdict(old, new) -> tuple[bool, str]:
    """判断新图是否严格优于旧图。"""
    if not new:
        return False, 'no_new'
    if len(new) < 4 or len(old) < 4:
        return False, 'bad_measure'
    ow, oh, owr, osz = old
    nw, nh, nwr, nsz = new
    # 硬规则：新图不得太矮、不得太高、不得几乎全白
    if nh < 200:
        return False, f'new_too_short(h={nh})'
    if nh > 1700:
        return False, f'new_too_tall(h={nh})'
    if nwr > 0.96 and nh < 600:
        return False, f'new_blank_strip(wr={nwr},h={nh})'
    # 改善判定：高度或内容密度有一项显著变好
    old_bad = oh < 200 or oh > 1700 or (owr > 0.96 and oh < 600)
    if old_bad:
        return True, f'old_bad→new_ok(old {ow}x{oh} wr={owr} → new {nw}x{nh} wr={nwr})'
    # 否则至少新图白比下降或尺寸更合理
    if nwr < owr - 0.02 or abs(nh - 600) < abs(oh - 600):
        return True, f'new_better(old {ow}x{oh} wr={owr} → new {nw}x{nh} wr={nwr})'
    return False, f'no_clear_improvement(old {ow}x{oh} → new {nw}x{nh})'


def run(dry_run: bool = False):
    report = []
    for exam, qn, reason in TARGETS:
        print(f'\n[{exam} q{qn:03d}]  {reason}')
        png = f'{IMG_ROOT}/{exam}/q{qn:03d}.png'
        jp = f'{JSON_ROOT}/{exam}.json'
        if not os.path.exists(jp):
            print(f'  SKIP: no json {jp}')
            continue
        pdf = find_pdf_for_json(jp)
        if not pdf or not os.path.exists(pdf):
            print(f'  SKIP: no pdf')
            continue
        print(f'  pdf: {os.path.basename(pdf)}')

        old_stats = measure(png)
        print(f'  old: {old_stats}')

        # 备份
        bak = png + '.bak'
        staging_dir = f'tmp/fix_stage/{exam}'
        os.makedirs(staging_dir, exist_ok=True)
        hint = load_content(jp, qn)

        # 抽到暂存，再验证
        image_map = extract_figure_questions(
            pdf, [qn], staging_dir, prefix='', dpi=300,
            content_hints={qn: hint} if hint else None,
        )
        new_path = image_map.get(qn)
        if not new_path or not os.path.exists(new_path):
            print('  FAIL: extraction produced no file')
            report.append((exam, qn, False, 'no_output'))
            continue
        new_stats = measure(new_path)
        print(f'  new: {new_stats}')

        ok, msg = verdict(old_stats, new_stats)
        print(f'  verdict: {"OK" if ok else "SKIP"}  {msg}')

        if ok and not dry_run:
            if not os.path.exists(bak):
                shutil.copy2(png, bak)
            shutil.copy2(new_path, png)
            print(f'  REPLACED (backup at {bak})')
        report.append((exam, qn, ok, msg))

    print('\n=== SUMMARY ===')
    for exam, qn, ok, msg in report:
        print(f'  {"✓" if ok else "✗"}  {exam}/q{qn:03d}  {msg}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    run(dry_run=args.dry_run)
