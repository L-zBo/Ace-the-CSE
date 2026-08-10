#!/usr/bin/env python3
"""补齐缺失的题图。

前置：先跑 scripts/locate_missing_figures.py 生成 reports/missing_figures_sources.json。

安全约束：
  - 先提到 data/tmp_figs/ 临时目录，**只把缺的那些文件名**拷回 public/img/questions/
  - 已存在的图一律不覆盖（现有图可能是人工修过的，见 fix_specific_figures.py 的教训）
  - 体积过小的裁剪结果视为失败，不采用

用法：
  python scripts/fill_missing_figures.py            # 预览（只提取不回填）
  python scripts/fill_missing_figures.py --apply    # 回填
"""
import io
import json
import os
import shutil
import subprocess
import sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

APPLY = '--apply' in sys.argv
TMP = 'data/tmp_figs'
DEST = 'public/img/questions'
MIN_BYTES = 8000
# 裁不出边界时会整页导出，实测 1.2 MB 一张、里面塞了 7 道题。
# 正常单题裁剪 50~350 KB，超过这个上限一律不要。
MAX_BYTES = 600000


def main():
    rows = json.load(io.open('reports/missing_figures_sources.json', encoding='utf-8'))
    groups = defaultdict(set)
    for r in rows:
        if r.get('pdf'):
            groups[(r['examKey'], r['json'], r['pdf'])].add(r['png'])

    print(f'待处理分组 {len(groups)}，目标图片 {sum(len(v) for v in groups.values())} 张')
    extracted = 0
    for (exam, jsonp, pdf), pngs in sorted(groups.items()):
        out = os.path.join(TMP, exam)
        # 同一套卷可能分散在多个模块 JSON 里（各自对应不同 PDF），每组都要跑，
        # 不能因为目录已存在就跳过 —— 那会漏掉后面几组。
        cmd = [sys.executable, 'scripts/extract_figures.py',
               '--pdf', pdf, '--json', jsonp, '--exam-id', exam,
               '--output-dir', TMP,
               # 直接按题号提取。靠关键词判定会漏：例如「使之呈现一定规律性」
               # 少个「的」字就匹配不上关键词表里的「呈现一定的规律」。
               '--only', ','.join(str(int(p[1:4])) for p in sorted(pngs))]
        try:
            subprocess.run(cmd, capture_output=True, timeout=900)
        except Exception as e:
            print(f'  [跳过] {exam}: {e}')
            continue
        got = sum(1 for p in pngs if os.path.exists(os.path.join(out, p)))
        extracted += got
        print(f'  {exam:32} 目标 {len(pngs):2}  提到 {got}')

    print(f'\n提取成功 {extracted} 张')

    copied = skipped_exist = skipped_small = skipped_huge = 0
    for (exam, _j, _p), pngs in sorted(groups.items()):
        for png in sorted(pngs):
            src = os.path.join(TMP, exam, png)
            dst = os.path.join(DEST, exam, png)
            if not os.path.exists(src):
                continue
            if os.path.exists(dst):
                skipped_exist += 1
                continue
            size = os.path.getsize(src)
            if size < MIN_BYTES:
                skipped_small += 1
                continue
            if size > MAX_BYTES:
                skipped_huge += 1
                continue
            if APPLY:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
            copied += 1

    print(f'可回填 {copied} 张；已存在跳过 {skipped_exist}；'
          f'体积过小丢弃 {skipped_small}；整页导出丢弃 {skipped_huge}')
    print('已回填。' if APPLY else '预览模式，未回填。加 --apply 落盘。')


if __name__ == '__main__':
    main()
