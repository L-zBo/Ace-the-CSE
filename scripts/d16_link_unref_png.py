"""D-16 L-7c 反向扫描：PNG 已存在但 lib 无 questionImage 字段

L-7a 顺向只扫占位题，错过了大批「非占位但有 PNG」的题（全库 2053 PNG
中 1157 无引用）。

但简单加字段有水分——比如 q001 PNG 可能是题号前的标题图/页眉。
加内容启发式：只给「内容明确需要图」的题加字段。

判定「需要图」：
  - content 含「图」「下图」「如图」「图中」「图形」「所示」「示意图」等关键词
  - 或选项含 [见图] / [图形选项] marker
  - 或 category 是 panduan + 题号在图形推理题号区（panduan 后半段）
"""
import argparse
import json
import re
from pathlib import Path
from collections import defaultdict, Counter

# 内容需要图的关键词
NEED_IMG_PATTERNS = [
    r'下图',
    r'如图',
    r'图中',
    r'图形',
    r'所示',
    r'示意图',
    r'图\s*[①②③④⑤]',
    r'左图',
    r'右图',
    r'上图',
    r'下方图',
    r'根据图',
    r'\(\s*见图\s*\)',
    r'参见图',
    r'根据.{0,5}图',
    r'立体图',
    r'平面图',
    r'柱状图',
    r'饼图',
    r'折线图',
    r'统计图',
    r'扇形图',
    r'\b图\d',
    r'图\s*[12345]',
    r'根据下',
]
NEED_RE = re.compile('|'.join(NEED_IMG_PATTERNS))

FIG_OPT_MARKERS = ['[见图]', '[图形选项]']


def needs_image(q):
    """题目是否明确需要图"""
    c = q.get('content', '') or ''
    if NEED_RE.search(c):
        return True
    # knowledgePoints 含「图形推理」/「资料分析」
    kps = q.get('knowledgePoints', []) or []
    if any('图形推理' in (kp or '') or '资料分析' in (kp or '') for kp in kps):
        return True
    opts = q.get('options', []) or []
    # 选项 marker
    for o in opts:
        s = o.get('content', '') if isinstance(o, dict) else str(o)
        if any(m in (s or '') for m in FIG_OPT_MARKERS):
            return True
    # 选项全是单字母（A/B/C/D 占位，原始应是图形选项）
    if opts and all(
        isinstance(o, dict) and (o.get('content', '') or '').strip() in ('A', 'B', 'C', 'D')
        for o in opts
    ):
        return True
    return False


def qid_to_examkey(qid):
    parts = qid.split('-')
    if parts[0] == 'national' and len(parts) >= 6:
        return f'national_{parts[3]}_{parts[4]}'
    if parts[0] == 'provincial' and len(parts) >= 6:
        return f'provincial_{parts[1]}_{parts[4]}'
    if parts[0] == 'institution' and len(parts) >= 6:
        return f'institution_{parts[3]}_{parts[4]}'
    return ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--show-skip', action='store_true',
                    help='打印被启发式排除的题（debug 用）')
    args = ap.parse_args()

    png_dir = Path('public/img/questions')
    png_index = defaultdict(set)
    for ek_dir in png_dir.iterdir():
        if not ek_dir.is_dir():
            continue
        for png in ek_dir.glob('*.png'):
            m = re.match(r'q(\d+)\.png$', png.name)
            if m:
                png_index[ek_dir.name].add(int(m.group(1)))

    to_fix = []  # (filepath, qid, ek, qn)
    skipped = []  # 有 PNG 但内容不需要图

    for f in Path('src/data/xingce').rglob('*.json'):
        data = json.loads(f.read_text(encoding='utf-8'))
        for q in data:
            if q.get('questionImage'):
                continue
            ek = qid_to_examkey(q['id'])
            if not ek or ek not in png_index:
                continue
            qn_str = q['id'].rsplit('-', 1)[-1]
            try:
                qn = int(qn_str)
            except ValueError:
                continue
            if qn not in png_index[ek]:
                continue
            if needs_image(q):
                to_fix.append((f, q['id'], ek, qn))
            else:
                skipped.append((f, q['id'], ek, qn, (q.get('content', '') or '')[:40]))

    print(f'PNG 总: {sum(len(s) for s in png_index.values())}')
    print(f'未引用且明确需要图 = {len(to_fix)} 题  ← 准备补')
    print(f'未引用但内容不要图 = {len(skipped)} 题  ← 跳过（疑似误抽）')

    by_ek = Counter(u[2] for u in to_fix)
    print('\n=== 补字段按 examKey 分布 (top 15) ===')
    for ek, n in by_ek.most_common(15):
        print(f'  {n:3d}  {ek}')

    if args.show_skip:
        print('\n=== 跳过样本 ===')
        for f, qid, ek, qn, c in skipped[:8]:
            print(f'  {qid}  /img/questions/{ek}/q{qn:03d}.png')
            print(f'    {c}')

    if args.apply and to_fix:
        by_file = defaultdict(dict)
        for f, qid, ek, qn in to_fix:
            url = f'/img/questions/{ek}/q{qn:03d}.png'
            by_file[str(f)][qid] = url
        n_changed = 0
        for fp, updates in by_file.items():
            data = json.loads(Path(fp).read_text(encoding='utf-8'))
            for q in data:
                if q['id'] in updates and not q.get('questionImage'):
                    q['questionImage'] = updates[q['id']]
                    n_changed += 1
            Path(fp).write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
        print(f'\n[APPLY] 已加 {n_changed} 个 questionImage 字段')


if __name__ == '__main__':
    main()
