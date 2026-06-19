"""D-17e E-2.3 修正 batch2 的 7 题 B 类标记错误

batch1/batch2 错误地把 content/options 覆盖为 [PDF 题源缺失-D17e]，导致
placeholder.ts isUnanswerable 失败（marker 不在 OCR_MARKERS 列表）。

正确做法（参照 D-17e commit 2843555）：
- content/options 保留 D-11 OCR 占位 marker
- explanation 末尾追加 [PDF 题源缺失-D17e] 说明
- meta.verifiedMissingBy='E2-vision-D17e'
"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
NOW = datetime.now(CST).strftime('%Y-%m-%d')

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'src' / 'data' / 'xingce'

# 7 题：shandong_2025 q020 (batch1) + batch2 6 题
TARGETS = [
    ('changshi', 'provincial_shandong_2025', '020',
     'PDF 原文标「20.题干缺失」官方 PDF 已删该题，与 hunan_2020 q016 同性质'),
    ('changshi', 'provincial_guangdong_2020', '083',
     'PDF 文字层无关键词命中，lib 原 content/options 全 D-11 OCR 占位无法反向定位'),
    ('panduan', 'institution_2020_c', '163',
     '判断推理图形题（立体几何黑白色面），需 D-9 图形选项抽图工程'),
    ('panduan', 'institution_2020_c', '164',
     '判断推理图形题（面特征关系），同 q163 需 D-9 抽图'),
    ('panduan', 'provincial_shanghai_2021', '061',
     'lib 模块归类错（实际数字推理被错挂 panduan），救援需 D-9 重抽 + 模块迁移'),
    ('shuliang', 'provincial_xinjiang_2021', '006',
     'lib 模块归类错（实际法律常识被错挂 shuliang），救援需 D-9 重抽 + 模块迁移'),
    ('yanyu', 'provincial_hunan_2020', '016',
     'PDF 原文标「16. 暂缺」官方 PDF 已删该题'),
]


def fix(mod, pk, qn, reason):
    path = DATA / mod / f'{pk}.json'
    arr = json.loads(path.read_text(encoding='utf-8'))
    qid_suffix = f'-{qn}'
    for q in arr:
        if not q.get('id','').endswith(qid_suffix):
            continue
        if f'-{mod}-' not in q.get('id',''):
            continue
        # 恢复 content/options 为 D-11 占位（保证 isUnanswerable=True）
        q['content'] = '[题干 OCR 抽取失败-D11] PDF 题源缺失-D17e'
        q['options'] = [{'label': L, 'content': '[选项 OCR 抽取失败-D11]'} for L in 'ABCD']
        # explanation 末尾加说明
        old_exp = q.get('explanation','') or ''
        d17e_marker = (
            f'\n\n[PDF 题源缺失-D17e] E-2 vision 侦查确认原 PDF 此题为缺失/'
            f'图形选项/模块挂错。{reason}前端 isUnanswerable 应过滤此题。'
        )
        if '[PDF 题源缺失-D17e]' not in old_exp:
            q['explanation'] = old_exp + d17e_marker
        # meta 加 verified
        meta = q.setdefault('meta', {})
        meta['verifiedMissingBy'] = 'E2-vision-D17e'
        meta['verifiedAt'] = NOW
        # 清掉之前误写的 placeholderReason 等（保留 rescuedBy / rescuedAt 历史）
        meta.pop('placeholderReason', None)
        meta.pop('rescueNote', None)
        # answer 保留空（B 类无标准答案）
        q['answer'] = ''
        print(f'  fixed: {q["id"]}')
        break
    else:
        raise SystemExit(f'not found {mod}/{pk} q{qn}')
    path.write_text(json.dumps(arr, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def main():
    print('E-2.3 fix 7 B 类 marker 错误:')
    for t in TARGETS:
        fix(*t)
    print('done')

if __name__ == '__main__':
    main()
