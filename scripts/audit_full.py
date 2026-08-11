"""全库审计（一次性诊断脚本，产出摘要而非全量清单）。

覆盖：字段完整性 / answer 合法性 / 选项结构 / id 与路径一致性 / 占位脏词 /
重复题 / 解析与答案矛盾 / 串题污染 / 图片引用。

用法：python scripts/audit_full.py
输出：控制台摘要 + reports/audit_full.json 明细
"""
import json
import glob
import io
import os
import re
import sys
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

PLACEHOLDER = ['OCR 抽取失败', 'OCR抽取失败', 'OCR 提取失败', 'OCR提取失败',
               '题目缺失', '题目暂缺', '暂缺', '正在全力以赴征集', '全力搜集中', '缺失']

findings = defaultdict(list)
stats = Counter()


def norm(t):
    t = re.sub(r'\s+', '', str(t or ''))
    return re.sub(r'[，。、；：？！,.;:?!（）()"\'【】\[\]]', '', t)


def load(path):
    d = json.load(io.open(path, encoding='utf-8'))
    return d if isinstance(d, list) else d.get('questions', d)


def is_placeholder(q):
    blob = str(q.get('content') or '')
    return any(p in blob for p in PLACEHOLDER)


# ---------- 行测 ----------
seen_content = defaultdict(list)
for path in sorted(glob.glob('src/data/xingce/**/*.json', recursive=True)):
    mod = path.replace('\\', '/').split('/')[3]
    paper = os.path.basename(path)[:-5]
    for q in load(path):
        stats['xingce_total'] += 1
        qid = q.get('id', '')
        num = qid.rsplit('-', 1)[-1]
        ph = is_placeholder(q)
        if ph:
            stats['placeholder'] += 1

        # 必填字段
        for f in ('id', 'content', 'options', 'answer', 'category', 'subject'):
            if not q.get(f):
                findings['missing_field'].append(f'{path}#{num} 缺 {f}')

        # id 与路径一致
        if q.get('category') != mod:
            findings['category_mismatch'].append(f'{path}#{num} category={q.get("category")} 但目录={mod}')
        y = re.search(r'_(\d{4})', paper)
        if y and str(q.get('year')) != y.group(1):
            findings['year_mismatch'].append(f'{path}#{num} year={q.get("year")} 但文件={y.group(1)}')

        # 选项结构
        opts = q.get('options') or []
        labels = [o.get('label') for o in opts if isinstance(o, dict)]
        # 判断题本来就只有「正确 / 错误」两个选项，不是缺选项。
        # 不排除的话广东 2024 那批每次审计都亮 5 个假红灯。
        contents = [str((o or {}).get('content') or '').strip() for o in opts]
        is_truefalse = (
            len(opts) == 2
            and (contents == ['正确', '错误'] or '（判断题）' in str(q.get('content') or ''))
        )
        if not ph:
            if len(opts) != 4 and not is_truefalse:
                findings['opt_count'].append(f'{path}#{num} 选项数={len(opts)}')
            if labels and labels != ['A', 'B', 'C', 'D'][:len(labels)]:
                findings['opt_label'].append(f'{path}#{num} label序列={labels}')
            for o in opts:
                if isinstance(o, dict) and not str(o.get('content') or '').strip():
                    findings['opt_empty'].append(f'{path}#{num} 选项{o.get("label")}为空')

        # answer 合法性（多选题存成 ['A','B']，先拍平再校验）
        _a = q.get('answer')
        ans = ''.join(str(x) for x in _a) if isinstance(_a, list) else str(_a or '')
        if not ph:
            if not ans:
                findings['answer_missing'].append(f'{path}#{num}')
            elif labels and not all(c in labels for c in ans):
                findings['answer_illegal'].append(f'{path}#{num} answer={ans} labels={labels}')

        # 解析 vs 答案矛盾
        exp = str(q.get('explanation') or '')
        m = re.findall(r'故正确答案为\s*([A-D]+)', exp)
        if m and not ph and ans:
            if m[-1] != ans:
                findings['answer_vs_explanation'].append(
                    f'{path}#{num} answer={ans} 但解析结论={m[-1]}')
        # 串题污染：解析里出现别的题号标记
        for t in re.findall(r'【\s*(\d{1,3})\s*[—\-－]\s*正确答案', exp):
            if t.lstrip('0') != num.lstrip('0'):
                findings['exp_crosstalk'].append(f'{path}#{num} 解析含第{t}题标记')
                break
        # 多个「故正确答案为」= 解析里塞了多题
        if len(m) > 1:
            findings['exp_multi_conclusion'].append(f'{path}#{num} 解析含{len(m)}个答案结论')

        # 重复题。签名必须带上 questionImage：图形推理的题干全是模板
        # （「从所给四个选项中，选择最合适的一个填入问号处」），只比文字会把
        # 一整套图形题都算成重复（实测 20 组假阳性），它们其实靠图区分。
        if not ph:
            key = (norm(q.get('content'))[:80], str(q.get('questionImage') or ''))
            if len(key[0]) > 20:
                seen_content[key].append(f'{path}#{num}')

for key, locs in seen_content.items():
    if len(locs) > 1:
        papers = {l.split('#')[0] for l in locs}
        bucket = 'dup_same_paper' if len(papers) == 1 else 'dup_cross_paper'
        findings[bucket].append(f'{len(locs)}处: ' + ' | '.join(locs[:4]))

# ---------- 申论 ----------
for path in sorted(glob.glob('src/data/shenlun/**/*.json', recursive=True)):
    mod = path.replace('\\', '/').split('/')[3]
    for q in load(path):
        stats['shenlun_total'] += 1
        num = q.get('id', '').rsplit('-', 1)[-1]
        for f in ('id', 'content', 'material'):
            if not q.get(f):
                findings['shenlun_missing_field'].append(f'{path}#{num} 缺 {f}')
        if q.get('category') != mod:
            findings['category_mismatch'].append(f'{path}#{num} category={q.get("category")} 但目录={mod}')

# ---------- 图片 ----------
img_root = 'public/img/questions'
have = defaultdict(set)
for p in glob.glob(f'{img_root}/*/*.png'):
    p = p.replace('\\', '/')
    exam = p.split('/')[-2]
    m = re.search(r'q(\d+)\.png$', p)
    if m:
        have[exam].add(int(m.group(1)))
stats['png_total'] = sum(len(v) for v in have.values())
stats['png_exam_dirs'] = len(have)

json.dump({'stats': dict(stats),
           'findings': {k: v for k, v in findings.items()}},
          io.open('reports/audit_full.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

print('=' * 72)
print('规模：行测 {xingce_total}  申论 {shenlun_total}  占位题 {placeholder}'.format(**stats))
print('题图：{png_total} 张，分布在 {png_exam_dirs} 个试卷目录'.format(**stats))
print('=' * 72)
order = ['missing_field', 'answer_missing', 'answer_illegal', 'answer_vs_explanation',
         'exp_crosstalk', 'exp_multi_conclusion', 'opt_count', 'opt_label', 'opt_empty',
         'category_mismatch', 'year_mismatch', 'dup_same_paper', 'dup_cross_paper',
         'shenlun_missing_field']
for k in order:
    v = findings.get(k, [])
    flag = '✅' if not v else ('🔴' if k in ('answer_illegal', 'answer_vs_explanation',
                                            'missing_field', 'answer_missing',
                                            'dup_same_paper') else '⚠️')
    print(f'{flag} {k:24} {len(v)}')
    for s in v[:3]:
        print('      ', s[:150])
print('\n明细 -> reports/audit_full.json')
