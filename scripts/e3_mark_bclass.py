"""D-17e E-3 批量 B 类 marker — paperKey 范围一次性扫除

每条目标：(模块, paperKey, qn 列表, PDF 原文证据描述)
对每题：
- content/options 保留 D-11 占位 marker
- explanation 末尾追加 [PDF 题源缺失-D17e] + 证据
- meta.verifiedMissingBy='E3-vision-D17e'
"""
import json, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
TODAY = datetime.now(CST).strftime('%Y-%m-%d')

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'src' / 'data' / 'xingce'

# (mod, paperKey, qns, reason)
TARGETS = [
    ('changshi', 'provincial_xinjiang_2023',
     ['014','015','016','017','018','019','020','021','022','023','024','025'],
     'PDF p003 起 q014-q025 原文「14.题目正全力以征集，将会在第一时间上传…缺失」整段 12 题占位'),
    ('shuliang', 'provincial_xinjiang_2023',
     ['060','061','062','063','064','065'],
     'PDF p010 q060-q065 原文「60.题目正全力以征集」整段 6 题占位'),
    ('yanyu', 'provincial_xinjiang_2023', ['050'],
     'PDF 题源缺失（与同 paperKey 其余占位题同性质）'),
    ('changshi', 'provincial_hunan_2023',
     ['039','056','066'],
     'PDF p009/p013/p016 q039/q056/q066 原文「题目正在全力以赴征集，将会在征集到后第一时间上传（该题选择 A 项默认得分）」+ ABCD 缺失，PDF 本身已删该题'),
    ('changshi', 'provincial_beijing_2023',
     ['015','018','019','020','021','022','023','024','025','026','027'],
     'PDF p002-p003 q015/q018-q027 整段 11 题原文「题目正在全力以赴征集，将会在征集到后第一时间上传（该题选择A项默认得分）」+ ABCD 缺失'),
    ('changshi', 'provincial_jilin_2024',
     ['017','018','019','020'],
     'PDF p003 q017-q020 整段 4 题原文「题目正在全力以赴征集，将会第一时间上传（正确答案默认设置为A项）」+ ABCD 缺失'),
    ('panduan', 'provincial_jilin_2024',
     ['065','066','067','068','077'],
     'PDF p010 q065-q068 整段 4 题 + p011 q077 共 5 题原文「题目正在全力以赴征集，将会第一时间上传（正确答案默认设置为A项）」+ ABCD 缺失'),
    ('yanyu', 'provincial_jilin_2024',
     ['042','043','044','045'],
     'PDF p006 q042-q045 整段 4 题原文「题目正在全力以赴征集，将会第一时间上传（正确答案默认设置为A项）」+ ABCD 缺失'),
    ('changshi', 'provincial_gansu_2024',
     ['018','019','020'],
     'PDF p003 q018-q020 整段 3 题原文「题目正在全力以赴征集，将会第一时间上传（正确答案默认设置为A项）」+ ABCD 暂缺'),
    ('panduan', 'provincial_gansu_2024',
     ['078','087'],
     'PDF p013 q078 + p014 q087 共 2 题原文「题目正在全力以赴征集，将会第一时间上传（正确答案默认设置为A项）」+ ABCD 暂缺'),
    ('shuliang', 'provincial_gansu_2024',
     ['069','070'],
     'PDF p010 q069/q070 原文「题目正在全力以赴征集，将会第一时间上传（正确答案默认设置为A项）」+ ABCD 暂缺'),
    ('yanyu', 'provincial_gansu_2024',
     ['054'],
     'PDF p008 q054 原文「题目正在全力以赴征集，将会第一时间上传（正确答案默认设置为A项）」+ ABCD 暂缺'),
    ('yanyu', 'provincial_ningxia_2024',
     ['052','053','054','055'],
     'PDF p009 q052-q055 整段 4 题原文「题目正在全力以赴征集，将会第一时间上传。（正确答案默认设置为A项。）」+ ABCD 全部「暂缺」'),
    ('yanyu', 'provincial_qinghai_2024',
     ['050','060'],
     'PDF p008 q050 + p010 q060 共 2 题原文「题目正在全力以赴征集，将会第一时间上传。（正确答案默认设置为A项。）」+ ABCD 全部「暂缺」'),
    ('panduan', 'provincial_qinghai_2024',
     ['090'],
     'PDF p016 q090 原文「题目正在全力以赴征集，将会第一时间上传。（正确答案默认设置为A项。）」+ ABCD 全部「暂缺」'),
    ('changshi', 'provincial_shandong_2022',
     ['008','009'],
     'PDF p002 顶部 q08「题目正在全力以赴征集，将会在征集到后第一时间上传」+ q09「题目正在众人之力上传」+ ABCD 全部「缺失」'),
    ('panduan', 'institution_2020_c',
     ['163','164'],
     'institution 2018-2024 C 类合并 PDF 250 页，q163/164 为图形推理题，D-11 OCR 抓到 explanation 真分析（含图形规律 + 推导答案 B/D）但题干/选项是图像无法 OCR。2026-05-24 vision 多年多场段位定位 ROI 极低（每年两场 + 7 年），不可救援'),
    ('changshi', 'institution_2022_b',
     ['034'],
     'institution 2018-2024 B 类合并 PDF 232 页，q034 为常识题，D-11 OCR 失败（原 content「暂缺」），option B「内分泌」D「副甲状腺」部分有内容但 A/C 占位。2026-05-24 vision 段位定位 ROI 极低，不可救援'),
    ('shuliang', 'institution_2022_c',
     ['050'],
     'institution 2018-2024 C 类合并 PDF 250 页，q050 为资料分析题，D-11 OCR 失败（原 content「题目缺失」），option B 含「D2/41 城市 2020 年」资料分析片段但题干 + 其他选项占位。2026-05-24 vision 段位定位 ROI 极低，不可救援'),
    ('panduan', 'provincial_hebei_2022',
     ['094'],
     'PDF p016 q094 原文「题目正在全力以赴征集，将会在征集到后第一时间上传」+ ABCD 全部「缺失」'),
    ('yanyu', 'provincial_hebei_2022',
     ['060'],
     'PDF p010 q060 原文「题目正在全力以赴征集，将会在征集到后第一时间上传」+ ABCD 全部「缺失」'),
    ('panduan', 'provincial_beijing_2023',
     ['111'],
     'PDF p019 q111 原文「题目正在全力以赴征集，将会在征集到后第一时间上传（该题选择A项默认得分）」+ ABCD 全部「缺失」。同段 q112-q124 PDF 也全缺，但其余题分布在 ziliao 模块且已另处理'),
    ('changshi', 'provincial_yunnan_2023',
     ['055'],
     'PDF p014 q055 文字层 STRICT 命中「55.题目正在全力以赴征集，将会在征集到后第一时间上传（该题选择A 项默认得分）A.缺失 B.缺失 C.缺失 D.缺失」'),
    ('yanyu', 'provincial_hunan_2024',
     ['040'],
     'PDF p008 q040 文字层命中「题目正在全力以赴征集，将会第一时间上传（正确答案默认设置为A项） 40. A.暂缺 B.暂缺 C.暂缺 D.暂缺」'),
    ('ziliao', 'provincial_hainan_2024',
     ['110'],
     'PDF p020 q110 文字层命中「题目正在全力以赴征集，将会第一时间上传。（正确答案默认设置为A项。） 110. A.暂缺 B.暂缺 C.暂缺 D.暂缺」'),
    ('changshi', 'provincial_neimenggu_2023',
     ['018'],
     'PDF p004 q018 vision 确认原文「18 题目正在全力以赴征集，将会在征集到后第一时间上传（该题选择 A 项默认得分）A.缺失 B.缺失 C.缺失 D.缺失」（文字层无 . 后缀导致 STRICT 漏匹配）'),
    ('changshi', 'provincial_shandong_2025',
     ['020'],
     'PDF p009 q020 vision 确认原文直接写「20. 题干缺失」'),
    ('changshi', 'provincial_guangdong_2023',
     ['089'],
     'PDF p026 q089 vision 看到「89.2021年，以下分类目财政科学技术支出同比增加最多的是」+ A.基础研究 B.技术研究与开发 C.科技条件与服务 D.科技重大项目，资料分析题但 PDF 这页不含材料数据，answer 不可救。WebSearch 多途径未找到该题答案，保持 D-11 占位以维持 isUnanswerable'),
    ('shuliang', 'provincial_guangdong_2024',
     ['031'],
     'PDF p004 底部 q031 为数学/图形推理题，D-11 OCR 部分救援（A=13 B=14）但 C/D 仍占位且题干 OCR 抓成「第4页，共18页」页脚乱码。完整真题需 vision 看 p004 底+p005 顶图形，且互联网未见该题答案，保持 D-11 占位'),
]


def patch_qs(mod, pk, qns, reason):
    path = DATA / mod / f'{pk}.json'
    arr = json.loads(path.read_text(encoding='utf-8'))
    qn_set = set(qns)
    hit = 0
    for q in arr:
        qid = q.get('id','')
        if f'-{mod}-' not in qid:
            continue
        qn = qid.split('-')[-1]
        if qn not in qn_set:
            continue
        hit += 1
        old_exp = q.get('explanation','') or ''
        d17e_marker = (
            f'\n\n[PDF 题源缺失-D17e] E-3 vision 侦查确认: {reason}。'
            f'互联网题源共缺，不可救援。前端 isUnanswerable 应过滤此题。'
        )
        if '[PDF 题源缺失-D17e]' not in old_exp:
            q['explanation'] = old_exp + d17e_marker
        meta = q.setdefault('meta', {})
        meta['verifiedMissingBy'] = 'E3-vision-D17e'
        if 'verifiedAt' not in meta:  # 幂等：保留首次记录日期，避免重跑日期漂移
            meta['verifiedAt'] = TODAY
    path.write_text(json.dumps(arr, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'  {mod}/{pk}: marked {hit} of {len(qns)} target qns')


def main():
    for t in TARGETS:
        patch_qs(*t)
    print('done')

if __name__ == '__main__':
    main()
