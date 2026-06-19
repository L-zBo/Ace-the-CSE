"""D-17e E-2.1 vision 救援批 1 — 7 题 patch
Run: python scripts/e2_patch_batch1.py
"""
import json
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
NOW = datetime.now(CST).strftime('%Y-%m-%dT%H:%M:%S+08:00')
TAG = 'E2-vision-OCR-D17e'

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'src' / 'data' / 'xingce'

PATCHES = [
    {
        'file': DATA / 'panduan' / 'provincial_shanghai_2020.json',
        'id': 'provincial-shanghai-xingce-panduan-2020-089',
        'content': '将上海市的 ①中外合作企业、②中外合资企业和③外商独资企业按 2018 年全年进出口贸易总额同比增量从高到低排列，正确的是____。',
        'options': [
            {'label': 'A', 'content': '③>①>②'},
            {'label': 'B', 'content': '②>①>③'},
            {'label': 'C', 'content': '①>②>③'},
            {'label': 'D', 'content': '③>②>①'},
        ],
        'answer': 'A',
        'explanation': '题考查同比增量比较。从材料表 2「2018 年全国及京津沪各类型外资企业进出口贸易额及同比变化表」上海行可读：①中外合作企业出口同比增量 = 出口额×增速 ≈ 较小正值；②中外合资企业出口同比增量为负；③外商独资企业出口 + 进口同比增量均为较大正值。综合进出口同比增量，③外商独资 > ①中外合作 > ②中外合资，即 ③>①>②。故选 A。',
    },
    {
        'file': DATA / 'changshi' / 'provincial_henan_2023.json',
        'id': 'provincial-henan-xingce-changshi-2023-115',
        'content': '不能从上述资料中推出的是：',
        # 选项 + answer 已正确，仅去题干占位
        'options_skip': True,
        'answer_skip': True,
    },
    {
        'file': DATA / 'changshi' / 'provincial_shandong_2025.json',
        'id': 'provincial-shandong-xingce-changshi-2025-020',
        'b_class': True,  # PDF 原文即「题干缺失」
        'content': '[PDF 题源缺失-D17e] PDF 原文「20.题干缺失」即官方 PDF 已标缺失，无法救援。',
        'options': [
            {'label': 'A', 'content': '[PDF 题源缺失-D17e]'},
            {'label': 'B', 'content': '[PDF 题源缺失-D17e]'},
            {'label': 'C', 'content': '[PDF 题源缺失-D17e]'},
            {'label': 'D', 'content': '[PDF 题源缺失-D17e]'},
        ],
        'answer': '',
    },
    {
        'file': DATA / 'shuliang' / 'provincial_chongqing_2020.json',
        'id': 'provincial-chongqing-xingce-shuliang-2020-064',
        'options': [
            {'label': 'A', 'content': '3/5'},
            {'label': 'B', 'content': '2/5'},
            {'label': 'C', 'content': '29/42'},
            {'label': 'D', 'content': '31/42'},
        ],
        'answer': 'D',
        'explanation': '排列组合古典概型。10 人选 5 人总数 C(10,5)=252。抽到 3 名及以上特种兵 = P(=3)+P(=4)+P(=5) = C(6,3)C(4,2)+C(6,4)C(4,1)+C(6,5)C(4,0) = 120+60+6 = 186。概率 = 186/252 = 31/42。故选 D。',
    },
    {
        'file': DATA / 'shuliang' / 'provincial_jiangxi_2020.json',
        'id': 'provincial-jiangxi-xingce-shuliang-2020-063',
        'options': [
            {'label': 'A', 'content': '3/5'},
            {'label': 'B', 'content': '2/5'},
            {'label': 'C', 'content': '29/42'},
            {'label': 'D', 'content': '31/42'},
        ],
        'answer': 'D',
        'explanation': '同 chongqing 2020 q064 同题。10 人选 5 人总数 C(10,5)=252，抽到 3 名及以上特种兵 = 120+60+6 = 186，概率 186/252 = 31/42。故选 D。',
    },
    {
        'file': DATA / 'panduan' / 'provincial_shanghai_2021.json',
        'id': 'provincial-shanghai-xingce-panduan-2021-089',
        'options': [
            {'label': 'A', 'content': '[图形选项 A]'},
            {'label': 'B', 'content': '[图形选项 B]'},
            {'label': 'C', 'content': '[图形选项 C]'},
            {'label': 'D', 'content': '[图形选项 D]'},
        ],
        'answer': 'A',
        'meta_note': 'shanghai 2021 q089 选项为 4 个柱状图（粤港澳大湾区年末常住人口同比增量），需 D-9 抽 PNG 才能完整呈现，前端按图形选项渲染',
    },
    {
        'file': DATA / 'ziliao' / 'provincial_zhejiang_2021.json',
        'id': 'provincial-zhejiang-xingce-ziliao-2021-058',
        'options': [
            {'label': 'A', 'content': '1/30'},
            {'label': 'B', 'content': '1/50'},
            {'label': 'C', 'content': '2/59'},
            {'label': 'D', 'content': '2/57'},
        ],
        'answer': 'A',
        'explanation': '排列组合 + 概率。后 3 位全奇数（1,3,5,7,9 共 5 个数字），其中恰好 2 个相同：选哪个数字重复 C(5,1)=5 种 × 另一个不同的数字 C(4,1)=4 种 × 这 3 位的位置排列 C(3,1)=3 种 = 60 种可能密码。每次猜中概率 1/60，尝试不超过 2 次 ≈ 2/60 = 1/30。故选 A。',
    },
]


def apply_patch(p):
    path = p['file']
    arr = json.loads(path.read_text(encoding='utf-8'))
    found = False
    for q in arr:
        if q.get('id') != p['id']:
            continue
        found = True
        if 'content' in p:
            q['content'] = p['content']
        if not p.get('options_skip') and 'options' in p:
            q['options'] = p['options']
        if not p.get('answer_skip') and 'answer' in p:
            q['answer'] = p['answer']
        if 'explanation' in p:
            q['explanation'] = p['explanation']
        if p.get('b_class'):
            q.setdefault('meta', {})['placeholderReason'] = 'PDF-source-missing'
        meta = q.setdefault('meta', {})
        meta['rescuedBy'] = TAG
        meta['rescuedAt'] = NOW
        if p.get('meta_note'):
            meta['rescueNote'] = p['meta_note']
        break
    if not found:
        raise SystemExit(f'NOT FOUND: {p["id"]} in {path.name}')
    path.write_text(json.dumps(arr, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'  patched: {p["id"]}')


def main():
    print(f'D-17e E-2.1 batch1 patch — {len(PATCHES)} 题')
    for p in PATCHES:
        apply_patch(p)
    print('done')


if __name__ == '__main__':
    main()
