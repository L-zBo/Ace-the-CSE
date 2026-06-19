"""D-16 L-2b 从 explanation 反推 A 类占位题的缺失选项

用法：
  # 默认 dry-run：仅生成 data/ango_cache/l2b_plan.md
  python scripts/d16_explanation_to_options.py

  # 实际写回 lib（先 dry-run 确认）
  python scripts/d16_explanation_to_options.py --apply

  # 只处理某些 paper
  python scripts/d16_explanation_to_options.py --filter institution_2020

策略：
- 仅处理 A 类占位题（题干在 / 部分选项在 / 非 PDF 整缺）
- explanation 必须含完整 ABCD 段（首字符为 A 项 / B 项 等）
- 仅替换原本是 OCR 失败 marker 或 "缺失" 的选项
- 替换文本前加 `[由解析推导-D16L2]` marker，便于审查/回滚
- 备份原 options 到 _legacy_options (用于 apply 模式)
"""
import argparse
import glob
import json
import re
import sys
from datetime import datetime
from pathlib import Path

MARKERS = [
    '[题干 OCR 抽取失败-D11]',
    '[选项 OCR 抽取失败-D11]',
    '[题干/选项 OCR 抽取失败-D11]',
    '[暂缺]',
]
PDF_MISSING_HINT = 'PDF 题目缺失'
RECOVERED_MARKER = '[由解析推导-D16L2]'

# 把 head 整段吃掉（"A 项：" / "A 选项：" / "A、" / "A. " / "A：" / "A:"）
OPT_HEAD_PAT = re.compile(
    r'(?:^|[\s\n])([A-D])(?:\s*项\s*[：:]|\s*选项\s*[：:]|\s*[、\.．：:])\s*'
)


def is_bad_opt(s: str) -> bool:
    if s is None: return True
    s2 = s.strip()
    if not s2 or s2 in ('缺失', '暂缺'): return True
    return any(m in s2 for m in MARKERS)


def has_stem(q):
    c = (q.get('content', '') or '')
    return not any(m in c for m in MARKERS)


def is_A_class(q):
    explanation = q.get('explanation', '') or ''
    if PDF_MISSING_HINT in explanation: return False
    options = q.get('options', []) or []
    if not options: return False
    opts_bad = sum(1 for o in options
                   if is_bad_opt((o.get('content', '') or '') if isinstance(o, dict) else str(o)))
    stem_bad = not has_stem(q)
    if stem_bad and opts_bad == len(options): return False
    if stem_bad or opts_bad > 0:
        return True
    return False


def extract_opt_segments(explanation: str) -> dict:
    """从 explanation 抽取 {A: text, B: text, C: text, D: text}"""
    if not explanation: return {}
    matches = []
    for m in OPT_HEAD_PAT.finditer(explanation):
        ch = m.group(1)
        if ch in 'ABCD':
            matches.append((m.start(), m.end(), ch))
    if not matches: return {}
    firsts = {}
    for pos, end, ch in matches:
        if ch not in firsts:
            firsts[ch] = (pos, end)
    if 'A' not in firsts or 'B' not in firsts: return {}
    ordered = sorted(firsts.items(), key=lambda x: x[1][0])
    result = {}
    for i, (ch, (pos, end)) in enumerate(ordered):
        next_pos = ordered[i + 1][1][0] if i + 1 < len(ordered) else min(pos + 600, len(explanation))
        # 从 head 之后开始（剥 "A 项：" 前缀）
        seg = explanation[end:next_pos].strip()
        # 去掉常见末尾评价短句（保守剥离）
        seg = trim_tail(seg)
        # 截最长 250 字
        if len(seg) > 250:
            seg = seg[:250].rstrip() + '…'
        result[ch] = seg
    return result


TAIL_TRIM_PAT = re.compile(
    r'[，,。；;]?\s*(故\s*(正确答案|本题答案|答案)\s*(为|是|选).*$'
    r'|与题干.*?(一致|不一致).*?(当选|排除)?.*$'
    r'|(符合|不符合)定义[。；；,，;].*$'
    r'|(当选|排除)[。；；,，;。\.\s]*$'
    r')',
    re.DOTALL,
)


def trim_tail(s: str) -> str:
    """温和去掉解析末尾的评价短句"""
    if not s: return s
    s = s.strip().rstrip('；;。.,，')
    s = TAIL_TRIM_PAT.sub('', s).rstrip('，,。；;. ')
    return s


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='实际写回 lib（默认 dry-run）')
    parser.add_argument('--filter', default='', help='paper 文件名子串过滤')
    args = parser.parse_args()

    plan = []  # 计划修改记录
    total_qs_examined = 0
    total_qs_a_class = 0
    total_qs_recoverable = 0
    total_opts_recovered = 0
    file_changes = {}  # fp -> 改动数

    for mod in ['panduan', 'changshi', 'shuliang', 'ziliao', 'yanyu']:
        for fp in sorted(glob.glob(f'src/data/xingce/{mod}/*.json')):
            if args.filter and args.filter not in fp: continue
            stem = Path(fp).stem
            lib = json.loads(Path(fp).read_text(encoding='utf-8'))
            file_dirty = False
            for q in lib:
                total_qs_examined += 1
                if not is_A_class(q): continue
                total_qs_a_class += 1
                segs = extract_opt_segments(q.get('explanation', '') or '')
                if len(segs) < 4: continue

                opts = q.get('options', []) or []
                changes = []  # [(idx, label, old, new)]
                for i, o in enumerate(opts):
                    if i >= 4: break
                    if not isinstance(o, dict): continue
                    label = o.get('label', chr(65 + i))
                    if label not in segs: continue
                    cur = o.get('content', '') or ''
                    if not is_bad_opt(cur): continue
                    new_text = f'{RECOVERED_MARKER} {segs[label]}'
                    changes.append((i, label, cur, new_text))

                if not changes: continue
                total_qs_recoverable += 1
                total_opts_recovered += len(changes)
                plan.append({
                    'paper': f'{mod}/{stem}',
                    'qid': q.get('id'),
                    'stem': (q.get('content', '') or '')[:80],
                    'changes': changes,
                    'answer': q.get('answer'),
                })

                if args.apply:
                    # 备份原 options 一次（同 q 多次 apply 会保留首次备份）
                    if '_legacy_options' not in q:
                        q['_legacy_options'] = json.loads(json.dumps(opts))
                    for idx, label, _, new_text in changes:
                        q['options'][idx]['content'] = new_text
                    file_dirty = True

            if file_dirty and args.apply:
                Path(fp).write_text(
                    json.dumps(lib, ensure_ascii=False, indent=2),
                    encoding='utf-8',
                )
                file_changes[fp] = sum(len(p['changes']) for p in plan if p['paper'] == f'{mod}/{stem}')

    # 报告
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out = []
    out.append(f'# D-16 L-2b explanation→options 救援报告  ({"APPLY" if args.apply else "DRY-RUN"})')
    out.append(f'生成时间: {datetime.now().isoformat(timespec="seconds")}')
    out.append('')
    out.append(f'- 全库扫描题数: {total_qs_examined}')
    out.append(f'- A 类占位题: {total_qs_a_class}')
    out.append(f'- 本次可救题数: **{total_qs_recoverable}**')
    out.append(f'- 本次拟补选项总数: **{total_opts_recovered}**')
    if args.apply:
        out.append(f'- 实际写回文件: {len(file_changes)}')
        for fp, n in sorted(file_changes.items()):
            out.append(f'    - {fp}: {n} 处')
    out.append('')
    out.append('## 详细计划')
    for p in plan:
        out.append(f'### {p["qid"]}  ({p["paper"]})')
        out.append(f'- 题干: `{p["stem"]}`')
        out.append(f'- 答案: {p["answer"]}')
        for idx, label, old, new in p['changes']:
            out.append(f'- **{label}**: `{old[:30]}` → `{new[:80]}`')
        out.append('')

    report_path = Path('data/ango_cache') / f'l2b_{"apply" if args.apply else "plan"}_{ts}.md'
    report_path.write_text('\n'.join(out), encoding='utf-8')
    print(f'[L-2b] mode={"APPLY" if args.apply else "DRY-RUN"}')
    print(f'  A 类 = {total_qs_a_class}, 救题 = {total_qs_recoverable}, 补选项 = {total_opts_recovered}')
    print(f'  报告 -> {report_path}')


if __name__ == '__main__':
    main()
