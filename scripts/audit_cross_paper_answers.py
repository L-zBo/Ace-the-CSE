#!/usr/bin/env python3
"""用跨卷同题关联反查答案矛盾。

同一道真题在多套卷里出现，答案本该一样。对不上就说明至少有一份是错的 ——
这是白捡的一层校验：不需要回官方 PDF 就能定位出可疑题。

注意这里只**定位**，不修。多数派只是线索不是证据：
  - 3 处里 2 处一致 -> 少数派那份可疑，但仍要回官方 PDF 核实才能改
  - 2 处各执一词 -> 平票，多数派规则失效，只能回源

依赖 src/data/index/cross-paper-links.json（先跑 generate_cross_paper_links.py）。

用法：python scripts/audit_cross_paper_answers.py
输出：reports/cross_paper_answer_conflicts.json
"""

import io
import json
import os
import sys
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

LINKS_FILE = 'src/data/index/cross-paper-links.json'
OUT_FILE = 'reports/cross_paper_answer_conflicts.json'


def norm_answer(ans):
    """多选题答案存成 ['A','B']，单选是 'A'。统一成可比字符串。"""
    if isinstance(ans, list):
        return ''.join(str(x) for x in ans)
    return str(ans or '')


def load_answers(wanted):
    """一次遍历题库，取出关心的那些题的答案与所在文件。"""
    import glob
    found = {}
    for path in sorted(glob.glob('src/data/*/*/*.json')):
        with open(path, encoding='utf-8') as f:
            arr = json.load(f)
        if not isinstance(arr, list):
            continue
        for q in arr:
            if isinstance(q, dict) and q.get('id') in wanted:
                found[q['id']] = {
                    'answer': norm_answer(q.get('answer')),
                    'file': path.replace(os.sep, '/'),
                }
    return found


def main():
    if not os.path.exists(LINKS_FILE):
        print(f'[中止] 找不到 {LINKS_FILE}，先跑 generate_cross_paper_links.py')
        sys.exit(1)

    with open(LINKS_FILE, encoding='utf-8') as f:
        links = json.load(f)
    labels = links['paperLabels']
    groups = links['groups']

    wanted = {row[0] for group in groups for row in group}
    info = load_answers(wanted)

    conflicts = []
    stats = Counter()
    by_paper = Counter()

    for group in groups:
        rows = []
        for qid, label_idx, qno in group:
            meta = info.get(qid)
            if not meta:
                continue
            rows.append({
                'id': qid,
                'paperLabel': labels[label_idx],
                'qno': qno,
                'answer': meta['answer'],
                'file': meta['file'],
            })
        if len(rows) < 2:
            continue
        stats['groups_checked'] += 1

        votes = Counter(r['answer'] for r in rows)
        if len(votes) == 1:
            stats['groups_consistent'] += 1
            continue

        stats['groups_conflict'] += 1
        stats['questions_involved'] += len(rows)

        top, top_n = votes.most_common(1)[0]
        runner_n = votes.most_common(2)[1][1] if len(votes) > 1 else 0
        if top_n > runner_n:
            verdict = 'majority'
            suspects = [r['id'] for r in rows if r['answer'] != top]
            stats['groups_majority'] += 1
            stats['suspect_questions'] += len(suspects)
        else:
            verdict = 'tie'
            suspects = [r['id'] for r in rows]
            stats['groups_tie'] += 1

        for r in rows:
            by_paper[r['paperLabel']] += 1

        conflicts.append({
            'verdict': verdict,
            'votes': dict(votes),
            'majorityAnswer': top if verdict == 'majority' else None,
            'suspects': suspects,
            'members': rows,
        })

    conflicts.sort(key=lambda c: (-len(c['members']), c['members'][0]['id']))

    os.makedirs('reports', exist_ok=True)
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            '_meta': ('跨卷同题的答案矛盾。majority 只是线索，改答案前必须回官方 PDF 核实；'
                      '生成命令 python scripts/audit_cross_paper_answers.py'),
            'stats': dict(stats),
            'byPaper': dict(by_paper.most_common()),
            'conflicts': conflicts,
        }, f, ensure_ascii=False, indent=2)

    print(f'检查 {stats["groups_checked"]} 组跨卷同题')
    print(f'  答案一致 {stats["groups_consistent"]} 组')
    print(f'  答案矛盾 {stats["groups_conflict"]} 组，涉及 {stats["questions_involved"]} 道题')
    print(f'    其中多数派明确 {stats["groups_majority"]} 组'
          f'（少数派可疑题 {stats["suspect_questions"]} 道）')
    print(f'    平票无法判定 {stats["groups_tie"]} 组')
    print('  集中的卷（前 8）：')
    for label, n in by_paper.most_common(8):
        print(f'    {label}  {n} 道')
    print(f'明细 -> {OUT_FILE}')


if __name__ == '__main__':
    main()
