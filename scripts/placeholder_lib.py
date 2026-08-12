#!/usr/bin/env python3
"""占位题判定 —— Python 侧唯一实现，逐条对齐 src/lib/placeholder.ts。

## 为什么有这个文件

同一个「有多少题不能做」的问题，全库一度给出三个数：

| 出处 | 数字 | 偏差原因 |
|---|---|---|
| `src/lib/placeholder.ts`（前端真正执行的） | 73 | 基准 |
| `scripts/audit_full.py` | 78 | 自带一份硬编码词表，只看题干、不看选项和兜底图 |
| `scripts/d17_list_unanswerable.py` | 50 | 读了 markers.json 却没用 `sourcePlaceholderShort` |

每个脚本各写一份判定，漂移是迟早的事。这里收口成一份，
marker 仍然从 `src/lib/markers.json` 读（TS 和 Python 共用的真相源）。

## 口径（与 placeholder.ts 一一对应）

- `is_placeholder_text`  ← isPlaceholderText：含 OCR marker、含「题目正在全力
  以赴征集」、或整串就是「暂缺」「缺失」这类短占位词
- `is_placeholder_question` ← isPlaceholderQuestion：题干坏，或 ≥2 个选项坏
- `is_unanswerable` ← isUnanswerable：占位题且没有 questionImage 兜底图
  （占位题 + 有图 = 图像作答模式，仍可作答）

⚠️ 救援 marker（`[由解析推导-D16L2]` 等）**不参与**占位判定 —— TS 侧只拿它
决定要不要加角标。d17 早先额外做了「救援过的不算占位」，那是多出来的差异。
"""

import json
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(_ROOT, 'src/lib/markers.json'), encoding='utf-8') as _f:
    _M = json.load(_f)

OCR_MARKERS = _M['placeholderMarkers']
SOURCE_PLACEHOLDERS = _M['sourcePlaceholderShort']
RECOVERY_MARKERS = list(_M['recoveryMarkers'].values())


def is_short_placeholder(s):
    """整串就是占位词才算，避免长正文里出现「暂缺」被误判。"""
    t = (s or '').strip()
    if not t:
        return False
    return any(t == p or t == p + '。' or t == p + '.' for p in SOURCE_PLACEHOLDERS)


def is_placeholder_text(s):
    if not s:
        return False
    if any(m in s for m in OCR_MARKERS):
        return True
    if '题目正在全力以赴征集' in s:
        return True
    return is_short_placeholder(s)


def is_placeholder_option(opt):
    if not isinstance(opt, dict):
        return is_placeholder_text(opt)
    return is_placeholder_text(opt.get('content'))


def is_placeholder_question(q):
    """题干坏，或 ≥2 个选项坏。无选项的题只看题干。"""
    if is_placeholder_text(q.get('content')):
        return True
    opts = q.get('options') or []
    if not opts:
        return False
    return sum(1 for o in opts if is_placeholder_option(o)) >= 2


def is_unanswerable(q):
    """前端列表 / 模考实际过滤掉的那批。"""
    return is_placeholder_question(q) and not q.get('questionImage')


def placeholder_reason(q):
    stem_bad = is_placeholder_text(q.get('content'))
    opts = q.get('options') or []
    bad = sum(1 for o in opts if is_placeholder_option(o))
    if stem_bad and bad:
        return f'题干 + {bad} 个选项源数据缺失'
    if stem_bad:
        return '题干源数据缺失'
    if bad >= 2:
        return f'{bad} 个选项源数据缺失'
    if bad == 1:
        return '1 个选项源数据缺失'
    return '源数据缺失'
