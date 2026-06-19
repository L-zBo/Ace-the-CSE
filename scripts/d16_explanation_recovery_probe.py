"""D-16 L-2a 探测 A 类占位题 explanation 里是否埋了 ABCD 选项分析（用于反向恢复）"""
import glob
import json
import re
from collections import Counter
from pathlib import Path

MARKERS = [
    '[题干 OCR 抽取失败-D11]',
    '[选项 OCR 抽取失败-D11]',
    '[题干/选项 OCR 抽取失败-D11]',
    '[暂缺]',
]
PDF_MISSING_HINT = 'PDF 题目缺失'


def is_bad_opt(s: str) -> bool:
    if not s: return True
    s2 = (s or '').strip()
    if s2 in ('缺失', '暂缺'): return True
    return any(m in s2 for m in MARKERS)


def has_stem(q):
    c = (q.get('content', '') or '')
    return not any(m in c for m in MARKERS)


def is_A_class(q):
    """A 类占位题：题干在 / 部分选项在 / 非 PDF 缺失"""
    explanation = q.get('explanation', '') or ''
    if PDF_MISSING_HINT in explanation: return False
    options = q.get('options', []) or []
    if not options: return False
    opts_bad = sum(1 for o in options if is_bad_opt(
        (o.get('content', '') or '') if isinstance(o, dict) else str(o)))
    stem_bad = not has_stem(q)
    if stem_bad and opts_bad == len(options): return False  # 全空
    # 有任意 OCR marker 在题干或选项里 = A 类候选
    if stem_bad or opts_bad > 0:
        return True
    return False


# 匹配 explanation 里的 "A 项" / "A 选项" / "A、" / "A." 段
OPT_HEAD_PAT = re.compile(
    r'(?:^|[\s\n])([A-D])\s*[、.．，,：:项选]'
)


def extract_opt_segments(explanation: str) -> dict:
    """返回 {A: text, B: text, C: text, D: text} 截取自 explanation"""
    if not explanation: return {}
    # 找所有 A/B/C/D head 的位置
    matches = []
    for m in OPT_HEAD_PAT.finditer(explanation):
        ch = m.group(1)
        if ch in 'ABCD':
            matches.append((m.start(), ch))
    if not matches: return {}
    # 按出现顺序，先看是否 A B C D 顺序出现
    chars = [c for _, c in matches]
    # 取首次 A, 首次 B, 首次 C, 首次 D
    firsts = {}
    for pos, ch in matches:
        if ch not in firsts:
            firsts[ch] = pos
    # 必须至少 A 和 B 都出现
    if 'A' not in firsts or 'B' not in firsts: return {}
    # 切片：每段从该位置到下一个不同 letter 的位置（不超 800 字）
    ordered = sorted(firsts.items(), key=lambda x: x[1])
    result = {}
    for i, (ch, pos) in enumerate(ordered):
        end = ordered[i + 1][1] if i + 1 < len(ordered) else min(pos + 800, len(explanation))
        seg = explanation[pos:end].strip()
        result[ch] = seg
    return result


def main():
    total_A = 0
    with_quad = 0  # 4 个选项都能抽出
    with_at_least_two = 0
    missing_opts_filled = 0  # 缺失选项能被 explanation 补
    examples = []
    by_paper_quad = Counter()

    for mod in ['panduan', 'changshi', 'shuliang', 'ziliao', 'yanyu']:
        for fp in sorted(glob.glob(f'src/data/xingce/{mod}/*.json')):
            stem = Path(fp).stem
            lib = json.loads(Path(fp).read_text(encoding='utf-8'))
            for q in lib:
                if not is_A_class(q): continue
                total_A += 1
                exp = q.get('explanation', '') or ''
                segs = extract_opt_segments(exp)
                if len(segs) >= 4:
                    with_quad += 1
                    by_paper_quad[f'{mod}/{stem}'] += 1
                if len(segs) >= 2:
                    with_at_least_two += 1

                # 看是否能补上缺的选项
                opts = q.get('options', []) or []
                supplied = 0
                for i, o in enumerate(opts):
                    if i >= 4: break
                    letter = chr(65 + i)
                    cur = (o.get('content', '') or '') if isinstance(o, dict) else str(o)
                    if is_bad_opt(cur) and letter in segs:
                        supplied += 1
                if supplied > 0:
                    missing_opts_filled += 1
                    if len(examples) < 10:
                        examples.append({
                            'id': q.get('id'),
                            'paper': f'{mod}/{stem}',
                            'stem': (q.get('content', '') or '')[:50],
                            'opts_current': [
                                ((o.get('content', '') or '') if isinstance(o, dict) else str(o))[:30]
                                for o in opts
                            ],
                            'segs_from_exp': {k: v[:60] for k, v in segs.items()},
                            'supplied_count': supplied,
                        })

    out = []
    out.append('# D-16 L-2a explanation 反推选项可行性')
    out.append('')
    out.append(f'- A 类占位题总数: **{total_A}**')
    out.append(f'- explanation 至少含 A 和 B 段: {with_at_least_two}')
    out.append(f'- explanation 含完整 ABCD 段: **{with_quad}**')
    out.append(f'- 能实际补上缺失选项的题: **{missing_opts_filled}** ({missing_opts_filled / max(total_A,1) * 100:.1f}%)')
    out.append('')
    out.append('## 由 explanation 含 ABCD 完整段的 paper top 20')
    for pk, n in by_paper_quad.most_common(20):
        out.append(f'- {n}  {pk}')
    out.append('')
    out.append('## 实际补救样例（前 10）')
    for ex in examples:
        out.append(f'### {ex["id"]}  ({ex["paper"]})')
        out.append(f'- 题干: `{ex["stem"]}`')
        out.append(f'- 当前 opts: {ex["opts_current"]}')
        out.append(f'- 从 exp 抽出: {ex["segs_from_exp"]}')
        out.append(f'- 可补回 {ex["supplied_count"]} 个选项')
        out.append('')

    Path('data/ango_cache/exp_recovery_feasibility.md').write_text(
        '\n'.join(out), encoding='utf-8'
    )
    print(f'[exp_recovery] wrote data/ango_cache/exp_recovery_feasibility.md')
    print(f'  A 总: {total_A}, 含 4 段: {with_quad}, 能实际补救: {missing_opts_filled}')


if __name__ == '__main__':
    main()
