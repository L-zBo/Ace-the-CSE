#!/usr/bin/env python3
"""为 content 严重异常的题目打 invalid 标记。

场景：PDF 提取时部分题干残缺（"暂缺"/"题干缺失"/"23"/"（"），
前端应能识别 meta.invalid 跳过这类条目，避免用户看到"空题"。

判定（必须命中任一）：
  - content 去标点后 <6 字 且 命中 dirty 关键词（暂缺/缺失/题干缺失/题目缺失）
  - content 完全由 数字 / 标点 / 编号符号 组成
  - content 以题号数字点开头且全长 <6（如 '78.'）
  - content 为 "17%.", "9%."（纯数字百分号）

注意：**不改动 options**；**不删除题目**；只加 meta.invalid=true 让前端过滤。

用法: python scripts/fix_invalid_content.py [--apply]
"""
import os, sys, json, glob, re, argparse
from collections import Counter

DIRTY_WORDS = ('暂缺', '缺失', '题干缺失', '题目缺失')
PURE_PUNCT_RE = re.compile(r'^[\d\s.,，、：:（）()①-⑩【】《》"\'“”"`～~/%\-]+$')
QNUM_RE = re.compile(r'^\d{1,3}[.。]$')
PCT_RE = re.compile(r'^\d+(\.\d+)?%[.。]?$')


def is_invalid_content(c: str) -> tuple[bool, str]:
    c = (c or '').strip()
    if not c:
        return True, 'empty'
    alpha = ''.join(ch for ch in c if ch.strip())
    if any(w in c for w in DIRTY_WORDS) and len(alpha) < 10:
        return True, 'dirty_keyword'
    if PURE_PUNCT_RE.fullmatch(c) and len(alpha) < 10:
        return True, 'pure_punct'
    if QNUM_RE.fullmatch(c):
        return True, 'qnum_only'
    if PCT_RE.fullmatch(c):
        return True, 'pct_only'
    return False, ''


def main(apply: bool):
    stats = Counter()
    by_file = {}
    for path in sorted(glob.glob('src/data/xingce/**/*.json', recursive=True)):
        qs = json.load(open(path, encoding='utf-8'))
        touched = []
        for q in qs:
            bad, why = is_invalid_content(q.get('content'))
            if not bad:
                continue
            meta = q.get('meta') or {}
            if meta.get('invalid'):
                continue  # 已标过
            meta['invalid'] = True
            meta['reason'] = f'content_{why}'
            q['meta'] = meta
            touched.append((q['id'], why, (q.get('content') or '')[:30]))
            stats[why] += 1
        if touched and apply:
            json.dump(qs, open(path, 'w', encoding='utf-8'),
                      ensure_ascii=False, indent=2)
        if touched:
            by_file[path.replace(os.sep, '/')] = touched

    print(f'MODE: {"APPLY" if apply else "DRY-RUN"}')
    print(f'Totals: {dict(stats)}')
    total = sum(stats.values())
    print(f'Total invalidated: {total}  across {len(by_file)} files')
    for p, items in list(by_file.items())[:30]:
        print(f'\n  {p}')
        for qid, why, c in items:
            print(f'    {why:15s}  {qid:50s}  {c!r}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    main(ap.parse_args().apply)
