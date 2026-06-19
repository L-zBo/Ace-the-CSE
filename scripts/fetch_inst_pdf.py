"""D-16 从事业编联考 PDF 抽题，转 baijing 兼容 cache 格式

用法：
  python scripts/fetch_inst_pdf.py 2020 a   # 输出 data/inst_pdf_cache/inst_2020_a.json

PDF 路径：material/【事业编】事业单位联考历年真题/{X}类/职测/2018年-2024年事业单位联考职测（{X}类）笔试真题.pdf
答案 PDF：…笔试真题答案解析.pdf
"""
import argparse, json, re, sys, fitz
from pathlib import Path

# (年份, 类别) -> (题目PDF起始页, 题目PDF结束页exclusive)
# 起始页是该卷封面/前言，第一题 (q1 常识判断) 通常在 +1 页
YEAR_ANCHORS = {
    "A": [
        (2024, 3, 2, 22), (2023, 8, 22, 43), (2023, 5, 43, 65),
        (2022, 9, 65, 107), (2021, 10, 107, 128), (2021, 5, 128, 149),
        (2020, 10, 149, 192), (2019, 10, 192, 212), (2019, 5, 212, 232),
        (2018, 10, 232, 271),
    ],
    "B": [
        (2024, 3, 2, 24), (2023, 8, 24, 45), (2023, 5, 45, 67),
        (2022, 5, 67, 85), (2021, 10, 85, 105), (2021, 5, 105, 148),
        (2019, 10, 148, 168), (2019, 5, 168, 190), (2018, 10, 190, 232),
    ],
    "C": [
        (2024, 3, 2, 23), (2023, 8, 23, 43), (2023, 5, 43, 62),
        (2022, 9, 62, 83), (2022, 5, 83, 103), (2021, 10, 103, 123),
        (2021, 5, 123, 144), (2020, 7, 144, 187), (2019, 5, 187, 208),
        (2018, 10, 208, 230), (2018, 5, 230, 250),
    ],
    "D": [],  # D 类 PDF 无文本锚点，可能是扫描 PDF
    "E": [
        (2024, 3, 2, 23), (2023, 8, 23, 43), (2023, 5, 43, 64),
        (2022, 9, 64, 82), (2022, 5, 82, 103), (2021, 10, 103, 123),
        (2021, 5, 123, 144), (2020, 7, 144, 165), (2019, 10, 165, 184),
        (2019, 5, 184, 205), (2018, 10, 205, 225), (2018, 5, 225, 246),
    ],
}

# 部分标题与 module 映射（事业编职测一卷通常含 5 部分）
SECTION_TO_KP = {
    "常识判断": "常识判断",
    "言语理解与表达": "言语理解",
    "言语理解": "言语理解",
    "数量关系": "数量关系",
    "判断推理": "判断推理",
    "资料分析": "资料分析",
    "综合分析": "判断推理",  # 综合分析常含图形/逻辑
}


def clean_text(s: str) -> str:
    s = re.sub(r"·\s*\d+\s*·", "", s)
    s = re.sub(r"事业单位联考真题\s*", "", s)
    s = re.sub(r"老师微信[:：]\s*\S*\s*", "", s)
    s = re.sub(r"公考事业编学习资料加微信\S*\s*", "", s)
    s = re.sub(r"版权所有\s*复制必究", "", s)
    s = re.sub(r"准考证号\s*", "", s)
    s = re.sub(r"姓\s*名\s*", "", s)
    return s


def extract_paper(pdf_path: Path, start_page: int, end_page: int):
    """抽取一卷的所有题，按 sort_order=qn 落到 list"""
    doc = fitz.open(str(pdf_path))
    full = []
    for i in range(start_page, min(end_page, doc.page_count)):
        full.append(doc[i].get_text())
    text = clean_text("\n".join(full))
    doc.close()

    # 按部分标题切 KP
    section_pat = re.compile(r"第\S+部分\s*[:：]?\s*(常识判断|言语理解(?:与表达)?|数量关系|判断推理|资料分析|综合分析)")
    section_spans = []
    for m in section_pat.finditer(text):
        section_spans.append((m.start(), m.group(1)))
    # 末尾哨兵
    section_spans.append((len(text), ""))

    def kp_of(pos: int) -> str:
        for i in range(len(section_spans) - 1):
            if section_spans[i][0] <= pos < section_spans[i + 1][0]:
                return SECTION_TO_KP.get(section_spans[i][1], "")
        return ""

    # 切题：N. 内容 直到下一个题号或部分标题
    q_pat = re.compile(r"(?<![\d\.\-])\b(\d{1,3})\.\s")
    questions = []
    matches = list(q_pat.finditer(text))
    for i, m in enumerate(matches):
        qn = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        # 别跨部分
        for sp, _ in section_spans:
            if start < sp < end:
                end = sp
                break
        body = text[start:end].strip()
        # 切选项 A. B. C. D.
        opt_pat = re.compile(r"([ABCD])[．.\s]\s*")
        opt_matches = list(opt_pat.finditer(body))
        stem = body
        options = []
        if len(opt_matches) >= 4:
            stem = body[:opt_matches[0].start()].strip()
            for j, om in enumerate(opt_matches[:4]):
                e = opt_matches[j + 1].start() if j + 1 < len(opt_matches) else len(body)
                options.append(body[om.end():e].strip())
        # 题号去重（pdf 噪音）：仅保留递增题号
        if questions and qn <= questions[-1]["sort_order"]:
            continue
        questions.append({
            "sort_order": qn,
            "qn": qn,
            "question": re.sub(r"\s+", " ", stem),
            "options": options,
            "knowledge_point": kp_of(m.start()),
            "answer": "",
            "explanation": "",
        })
    return questions


def extract_answers(pdf_path: Path, year: int, month: int, cls: str):
    """在合集答案 PDF 中找到指定卷的答案段，返回 {qn: (answer, explanation)}

    锚点策略：扫全 PDF 找所有 "YYYY 年 M 月.*?全国事业单位联考" 的页，建年月→页表。
    """
    doc = fitz.open(str(pdf_path))
    year_pat = re.compile(r"(20\d{2})\s*年\s*(\d+)\s*月.*?(?:事业|联考)")
    anchors = []  # (year, month, page)
    for i in range(doc.page_count):
        text = doc[i].get_text()
        if not text:
            continue
        m = year_pat.search(text[:300])
        if m:
            anchors.append((int(m.group(1)), int(m.group(2)), i))
    start = -1
    for j, (y, mo, pg) in enumerate(anchors):
        if y == year and mo == month:
            start = pg
            end = anchors[j + 1][2] if j + 1 < len(anchors) else doc.page_count
            break
    if start == -1:
        doc.close()
        return {}
    raw = "\n".join(doc[i].get_text() for i in range(start, end))
    doc.close()

    # 切 N.【答案】X / 【解析】xxx 到下一题号
    pat = re.compile(r"(\d{1,3})\.\s*【答案】\s*([A-D]+).*?(?=\d{1,3}\.\s*【答案】|\Z)", re.DOTALL)
    ans = {}
    for m in pat.finditer(raw):
        qn = int(m.group(1))
        a = m.group(2).strip()
        body = m.group(0)
        # 抽 【解析】xxx
        em = re.search(r"【解析】(.+)", body, re.DOTALL)
        explanation = em.group(1).strip() if em else ""
        ans[qn] = (a, explanation)
    return ans


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("year", type=int)
    ap.add_argument("cls", choices=["a", "b", "c", "d", "e"])
    ap.add_argument("--month", type=int, default=0, help="同年多月时指定（如 2021 年 5/10 月）")
    args = ap.parse_args()

    cls_u = args.cls.upper()
    anchors = YEAR_ANCHORS[cls_u]
    candidates = [a for a in anchors if a[0] == args.year and (args.month == 0 or a[1] == args.month)]
    if not candidates:
        sys.exit(f"!! {cls_u} 类 {args.year} 年(month={args.month}) 未在锚点中")
    if len(candidates) > 1 and args.month == 0:
        sys.exit(f"!! 同年多卷需 --month 指定: {[a[1] for a in candidates]}")
    yr, mo, sp, ep = candidates[0]

    pdf_q = Path(f"material/【事业编】事业单位联考历年真题/{cls_u}类/职测/2018年-2024年事业单位联考职测（{cls_u}类）笔试真题.pdf")
    pdf_a = Path(f"material/【事业编】事业单位联考历年真题/{cls_u}类/职测/2018年-2024年事业单位联考职测（{cls_u}类）笔试真题答案解析.pdf")
    if not pdf_q.exists():
        sys.exit(f"!! 题目 PDF 不存在: {pdf_q}")

    print(f"[fetch] {cls_u} 类 {yr} 年 {mo} 月 - PDF p.{sp}-{ep}")
    questions = extract_paper(pdf_q, sp, ep)
    print(f"  抽到 {len(questions)} 题")

    if pdf_a.exists():
        print(f"[answers] {pdf_a.name}")
        ans_map = extract_answers(pdf_a, yr, mo, cls_u)
        print(f"  抽到答案 {len(ans_map)} 题")
        for q in questions:
            qn = q["sort_order"]
            if qn in ans_map:
                q["answer"], q["explanation"] = ans_map[qn]

    out_dir = Path("data/inst_pdf_cache")
    out_dir.mkdir(parents=True, exist_ok=True)
    paper_id = f"inst_{yr}_{args.cls}_{mo:02d}"
    out_path = out_dir / f"paper_{paper_id}.json"
    out_path.write_text(
        json.dumps({"paperId": paper_id, "title": f"{yr}年{mo}月全国事业单位联考（{cls_u}类）",
                    "questions": questions}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"[OK] -> {out_path}")


if __name__ == "__main__":
    main()
