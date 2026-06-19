"""D-17e E-2.2 batch — 1 题救援 + 6 题 B 类 marker"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
NOW = datetime.now(CST).strftime('%Y-%m-%dT%H:%M:%S+08:00')
TAG = 'E2-vision-OCR-D17e'

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'src' / 'data' / 'xingce'

# 1 题真救援：jiangsu_2020 q006 在 PDF p001 找到真题
RESCUE = [
    {
        'file': DATA / 'ziliao' / 'provincial_jiangsu_2020.json',
        'id': 'provincial-jiangsu-xingce-ziliao-2020-006',
        'content': '我国要优化行政区划设置，提高中心城市和城市群综合承载和资源优化配置能力，实行扁平化管理，形成高效率组织体系。下列属于实行扁平化管理的改革措施的是：',
        'options': [
            {'label': 'A', 'content': '大部制改革'},
            {'label': 'B', 'content': '综合执法改革'},
            {'label': 'C', 'content': '垂直化管理改革'},
            {'label': 'D', 'content': '省直管县改革'},
        ],
        'answer': 'D',
        'explanation': '扁平化管理的核心是减少管理层级。A 大部制改革是同级合并部门，减少横向部门数；B 综合执法改革是整合执法主体；C 垂直化管理改革是上下贯通的纵向管理；D 省直管县改革是省直接管理县级，去掉地市这一中间层级，是扁平化管理的典型措施。故选 D。',
        'meta_note': 'lib 原模块挂错（D-11 时期 ziliao 实际真位置在 jiangsu changshi），但保留 id+文件位置不变，仅 content/options/answer 实质化',
    },
]

# 6 题 B 类 marker — PDF 真位置定位失败 / 图形选项 / PDF 标暂缺
B_CLASS = [
    ('changshi', 'provincial_guangdong_2020', '083',
     'PDF 文字层无关键词命中（OCR 已失败），lib content 全占位无法反向定位'),
    ('panduan', 'institution_2020_c', '163',
     '判断推理图形题（立体几何黑白色面），PDF p144-p187 段位内但图形选项无文字层，需 D-9 抽图工程'),
    ('panduan', 'institution_2020_c', '164',
     '判断推理图形题（面特征关系），同 q163，需 D-9 抽图工程'),
    ('panduan', 'provincial_shanghai_2021', '061',
     'lib 模块归类错（实际数字推理 shuliang 被错挂 panduan），PDF 真位置需 D-9 重抽 + 模块迁移'),
    ('shuliang', 'provincial_xinjiang_2021', '006',
     'lib 模块归类错（实际法律常识 changshi 被错挂 shuliang），PDF 真位置需 D-9 重抽 + 模块迁移'),
    ('yanyu', 'provincial_hunan_2020', '016',
     'PDF 原文标「16. 暂缺」，与 shandong 2025 q020 同性质，官方 PDF 已删除该题'),
]


def apply_rescue(p):
    arr = json.loads(p['file'].read_text(encoding='utf-8'))
    for q in arr:
        if q.get('id') == p['id']:
            q['content'] = p['content']
            q['options'] = p['options']
            q['answer'] = p['answer']
            q['explanation'] = p['explanation']
            meta = q.setdefault('meta', {})
            meta['rescuedBy'] = TAG
            meta['rescuedAt'] = NOW
            meta['rescueNote'] = p['meta_note']
            break
    else:
        raise SystemExit(f'rescue not found {p["id"]}')
    p['file'].write_text(json.dumps(arr, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'  rescued: {p["id"]}')


def apply_b(mod, pk, qn, reason):
    path = DATA / mod / f'{pk}.json'
    qid_suffix = f'-{qn}'
    arr = json.loads(path.read_text(encoding='utf-8'))
    for q in arr:
        if not q.get('id','').endswith(qid_suffix):
            continue
        if f'-{mod}-' not in q.get('id',''):
            continue
        meta = q.setdefault('meta', {})
        meta['placeholderReason'] = 'PDF-source-missing'
        meta['rescuedBy'] = TAG
        meta['rescuedAt'] = NOW
        meta['rescueNote'] = reason
        # content 加 marker
        cur = q.get('content', '')
        if '[PDF 题源缺失-D17e]' not in cur:
            q['content'] = f'[PDF 题源缺失-D17e] {reason}'
        # 选项也清
        q['options'] = [{'label': L, 'content': '[PDF 题源缺失-D17e]'} for L in 'ABCD']
        q['answer'] = ''
        print(f'  B marker: {q["id"]}')
        break
    else:
        raise SystemExit(f'b not found {mod}/{pk} q{qn}')
    path.write_text(json.dumps(arr, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def main():
    print('E-2.2 — rescue:')
    for r in RESCUE:
        apply_rescue(r)
    print('E-2.2 — B class:')
    for b in B_CLASS:
        apply_b(*b)
    print('done')


if __name__ == '__main__':
    main()
