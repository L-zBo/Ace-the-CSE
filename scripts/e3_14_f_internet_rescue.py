"""D-17e E-3.14 F-Phase 互联网答案救援 3 题

3 题已确认答案（互联网真题站点 + 数列规律）：
- guangdong_2020 changshi q083 = C (chinagwy.org 官方答案库)
- shanghai_2021 panduan q061 = A (PDF p010 vision 看清数列「2,2,3/2,1,5/8」
  + 分子 2,4,6,8,10,12 等差 / 分母 1,2,4,8,16,32 等比 → 3/8)
- guangdong_2023 changshi q089 = D (mggk510.com 真题答案库 86A/87B/88B/89D/90C)

策略：
- 重写 content + options 为 PDF 真题原文
- 写 answer 为确认答案
- explanation 加 D-17e F-阶段救援 marker + 来源说明
- meta.rescuedBy = F-internet-answer-D17e（升级版救援，含 answer）
- 这次救援后 isUnanswerable=false → 用户可作答

排除 xinjiang_2021 q006：lib id 命名错乱，模块归属可疑（shuliang 模块
但 q006 题号撞常识第 6 题），救援风险高，保持 B 类 marker。

排除 guangdong_2024 q031：数字推理无解析。
排除 hunan_2020 q016：互联网无完整答案。
"""
import json, sys, io
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
CST = timezone(timedelta(hours=8))
TODAY = datetime.now(CST).isoformat(timespec='seconds')
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'src' / 'data' / 'xingce'

RESCUES = [
    {
        'path': DATA / 'changshi' / 'provincial_guangdong_2020.json',
        'qn': '083',
        'content': '仓库工人计划用小车运送三箱货物，第一次先用大小为F的力将一箱货物从A仓库推到B仓库，第二次用同样大小的力将两箱货物从A仓库拉到B仓库。则在货物的移动过程中，关于两次做功的情况下列说法正确的是（    ）。',
        'options': [
            ('A', '工人第一次做的功比第二次多'),
            ('B', '工人第一次做的功比第二次少'),
            ('C', '工人第一次做的功与第二次一样多'),
            ('D', '无法确定'),
        ],
        'answer': 'C',
        'explanation_append': '【F-阶段救援】做功 W=F·s·cosθ。两次操作力 F 相同、位移 s 相同（A→B 仓库），故两次做功相等。货物质量差异影响摩擦力大小，但题目强调"用大小为F的力"已是工人实际施加的力。',
        'source': 'chinagwy.org/html/stzx/guangdong/202008/104_369519.html',
    },
    {
        'path': DATA / 'panduan' / 'provincial_shanghai_2021.json',
        'qn': '061',
        'content': '数列：2，2，3/2，1，5/8，（    ）',
        'options': [
            ('A', '3/8'),
            ('B', '0'),
            ('C', '7/16'),
            ('D', '3/4'),
        ],
        'answer': 'A',
        'explanation_append': '【F-阶段救援】通分原数列：2=2/1, 2=4/2, 3/2=6/4, 1=8/8, 5/8=10/16。分子 2,4,6,8,10 等差递增 +2，下项 12；分母 1,2,4,8,16 等比 ×2，下项 32。故第 6 项 = 12/32 = 3/8。',
        'source': 'PDF p010 vision 直接读取（D-11 OCR 仅抽到 B=0），规律自推',
    },
    {
        'path': DATA / 'changshi' / 'provincial_guangdong_2023.json',
        'qn': '089',
        'content': '2021年，以下分类科目财政科学技术支出同比增加值最多的是（    ）。',
        'options': [
            ('A', '基础研究'),
            ('B', '技术研究与开发'),
            ('C', '科技条件与服务'),
            ('D', '科技重大项目'),
        ],
        'answer': 'D',
        'explanation_append': '【F-阶段救援】资料表 2 各分类科目同比增加值：基础研究 124.75-116.01=+8.74 亿、科技条件与服务 54.56-44.55=+10.01 亿、科技重大项目 71.21-58.20=+13.01 亿、技术研究与开发（总额倒算）约 -70 亿（减少）。D 项 +13.01 亿增加值最多。',
        'source': 'mggk510.com/sys-nd/5010.html (89=D) + 资料分析数据推算',
    },
]


def main():
    for r in RESCUES:
        path = r['path']
        arr = json.loads(path.read_text(encoding='utf-8'))
        hit = 0
        for q in arr:
            if q.get('id', '').split('-')[-1] != r['qn']:
                continue
            hit += 1
            # 重写 content + options + answer
            q['content'] = r['content']
            q['options'] = [{'label': lab, 'content': txt} for lab, txt in r['options']]
            q['answer'] = r['answer']
            # explanation：保留原有（若有）+ 追加 F 阶段救援说明
            old_exp = q.get('explanation', '') or ''
            marker = (
                f'\n\n[由E3F-internet-answer救援-D17e] 2026-05-24 互联网真题库 + vision 双源核实救援。'
                f'\n来源：{r["source"]}'
                f'\n{r["explanation_append"]}'
            )
            if '[由E3F-internet-answer救援-D17e]' not in old_exp:
                q['explanation'] = old_exp + marker
            # meta：升级救援标记
            meta = q.setdefault('meta', {})
            meta['rescuedBy'] = 'E3F-internet-answer-D17e'
            meta['rescuedAt'] = TODAY
            meta['rescueScope'] = 'content+options+answer+explanation'
            # 撤回之前 E-2/E-3 的 verifiedMissingBy（这题不再被认为缺失）
            meta.pop('verifiedMissingBy', None)
            meta.pop('verifiedAt', None)
        path.write_text(json.dumps(arr, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'{path.relative_to(ROOT).as_posix()}: rescued {hit} qn (q{r["qn"]} = {r["answer"]})')


if __name__ == '__main__':
    main()
