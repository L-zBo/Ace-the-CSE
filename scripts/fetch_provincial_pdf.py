"""D-16 G 方案：从省考单卷 PDF 抽题，转 baijing 兼容 cache

用法：
  python scripts/fetch_provincial_pdf.py xinjiang 2023
  python scripts/fetch_provincial_pdf.py beijing 2023

PDF 格式特征（不同于 inst 合集）：
- 题号在题干 *之后* 的独立行：「题干...是：\n1.\nA.xxx\nB.xxx」
- 答案 PDF 用「【解析N--正确答案X】」标记
"""
import argparse, json, re, sys, glob, fitz
from pathlib import Path

REGION_ZH = {
    "qinghai": "青海", "ningxia": "宁夏", "zhejiang": "浙江", "chongqing": "重庆",
    "gansu": "甘肃", "heilongjiang": "黑龙江", "shandong": "山东", "shenzhen": "深圳",
    "tianjin": "天津", "jiangsu": "江苏", "jilin": "吉林", "neimenggu": "内蒙古",
    "sichuan": "四川", "guangdong": "广东", "guangzhou": "广州", "shanghai": "上海",
    "beijing": "北京", "hubei": "湖北", "anhui": "安徽", "fujian": "福建",
    "guangxi": "广西", "guizhou": "贵州", "hainan": "海南", "hebei": "河北",
    "henan": "河南", "hunan": "湖南", "jiangxi": "江西", "liaoning": "辽宁",
    "shanxi": "山西", "shaanxi": "陕西", "yunnan": "云南", "xinjiang": "新疆",
    "xizang": "西藏",
}

# 省份目录索引前缀
REGION_DIR_IDX = {
    "anhui": 1, "beijing": 2, "fujian": 3, "gansu": 4, "guangdong": 5,
    "guangxi": 6, "guizhou": 7, "hainan": 8, "hebei": 9, "henan": 10,
    "heilongjiang": 11, "hubei": 12, "hunan": 13, "jilin": 14, "jiangsu": 15,
    "jiangxi": 16, "liaoning": 17, "neimenggu": 18, "ningxia": 19, "qinghai": 20,
    "shandong": 21, "shanxi": 22, "shaanxi": 23, "shanghai": 24, "sichuan": 25,
    "tianjin": 26, "xizang": 27, "xinjiang": 28, "yunnan": 29, "zhejiang": 30,
    "chongqing": 31, "guangzhou": 32, "shenzhen": 33,
}

SECTION_TO_KP = {
    "常识判断": "常识判断",
    "言语理解与表达": "言语理解",
    "言语理解": "言语理解",
    "数量关系": "数量关系",
    "判断推理": "判断推理",
    "资料分析": "资料分析",
}


def find_pdfs(region: str, year: int, level: str = ""):
    rg_zh = REGION_ZH[region]
    idx = REGION_DIR_IDX[region]
    base = f"material/【省考】2000-2025真题pdf/【{idx:02d}】{rg_zh}公务员考试真题pdf版"
    # 找行测 PDF 目录（命名各异，如 "北京行测09-23"、"新疆公务员考试真题——行测09-25PDF版"）
    candidates_q = []
    candidates_a = []
    for entry in Path(base).iterdir():
        if not entry.is_dir(): continue
        name = entry.name
        if "行测" not in name: continue
        # 找题目子目录
        for sub in entry.iterdir():
            if not sub.is_dir(): continue
            for p in sub.glob("*.pdf"):
                if str(year) in p.name and rg_zh in p.name:
                    if "答案" in sub.name or "解析" in sub.name:
                        candidates_a.append(p)
                    else:
                        candidates_q.append(p)
    # level 过滤
    if level:
        candidates_q = [p for p in candidates_q if level in p.name]
        candidates_a = [p for p in candidates_a if level in p.name]
    return candidates_q, candidates_a


def clean_noise(s: str) -> str:
    s = re.sub(r"第\s*\d+\s*页[，,]?\s*共\s*\d+\s*页", "", s)
    s = re.sub(r"\(微信扫\).+\.jpg", "", s)
    return s


def extract_paper_format_b(text: str, section_spans, kp_of):
    """格式 B：题号在题干 *前* — `\\n\\d+\\.\\s+题干\\nA.xxx`"""
    q_anchor = re.compile(r"(?:^|\n)\s*(\d{1,3})\.\s+(?=\S)")
    matches = list(q_anchor.finditer(text))
    if not matches:
        return []
    questions = []
    for i, m in enumerate(matches):
        qn = int(m.group(1))
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        for sp, _ in section_spans:
            if m.end() < sp < body_end:
                body_end = sp
                break
        body = text[m.end():body_end]
        # 切选项 A./A、
        opt_pat = re.compile(r"(?:^|\n)\s*([ABCD])[．.、\s]\s*")
        opt_matches = list(opt_pat.finditer(body))
        if len(opt_matches) < 4:
            continue
        stem = body[:opt_matches[0].start()].strip()
        options = []
        for j, om in enumerate(opt_matches[:4]):
            e = opt_matches[j + 1].start() if j + 1 < len(opt_matches) else len(body)
            options.append(body[om.end():e].strip().replace("\n", " "))
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


def extract_paper(pdf_path: Path):
    """抽取省考单卷 PDF，自动判格式（A: 题号在题干后 / B: 题号在题干前）"""
    doc = fitz.open(str(pdf_path))
    raw = "\n".join(doc[i].get_text() for i in range(doc.page_count))
    doc.close()
    text = clean_noise(raw)

    section_pat = re.compile(r"(?:一|二|三|四|五|六)[\.、\s]\s*(常识判断|言语理解(?:与表达)?|数量关系|判断推理|资料分析)")
    section_spans = []
    for m in section_pat.finditer(text):
        section_spans.append((m.start(), m.group(1)))
    section_spans.append((len(text), ""))

    def kp_of(pos: int) -> str:
        for i in range(len(section_spans) - 1):
            if section_spans[i][0] <= pos < section_spans[i + 1][0]:
                return SECTION_TO_KP.get(section_spans[i][1], "")
        return ""

    # 格式 A：题号在题干后
    q_anchor = re.compile(r"(?<=\n)(\d{1,3})\.\s*\n")
    matches = list(q_anchor.finditer(text))
    qs_a = []
    if matches:
        for i, m in enumerate(matches):
            qn = int(m.group(1))
            if i == 0:
                stem_start = 0
                for sp, _ in section_spans:
                    if sp < m.start():
                        stem_start = max(stem_start, sp)
            else:
                stem_start = matches[i - 1].end()
                chunk = text[matches[i - 1].end():m.start()]
                d_pat = re.compile(r"\n[DＤ][．.\s]")
                d_matches = list(d_pat.finditer(chunk))
                if d_matches:
                    d_end = d_matches[-1].end()
                    stem_start = matches[i - 1].end() + d_end
                    next_nl = text.find('\n', stem_start)
                    if next_nl > -1:
                        stem_start = next_nl + 1
            stem = text[stem_start:m.start()].strip()
            opt_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            for sp, _ in section_spans:
                if m.end() < sp < opt_end:
                    opt_end = sp
                    break
            opts_chunk = text[m.end():opt_end]
            opt_pat = re.compile(r"\n?([ABCD])[．.\s]\s*")
            opt_matches = list(opt_pat.finditer(opts_chunk))
            options = []
            if len(opt_matches) >= 4:
                for j, om in enumerate(opt_matches[:4]):
                    e = opt_matches[j + 1].start() if j + 1 < len(opt_matches) else len(opts_chunk)
                    options.append(opts_chunk[om.end():e].strip().replace("\n", " "))
            if qs_a and qn <= qs_a[-1]["sort_order"]:
                continue
            qs_a.append({
                "sort_order": qn, "qn": qn,
                "question": re.sub(r"\s+", " ", stem),
                "options": options, "knowledge_point": kp_of(m.start()),
                "answer": "", "explanation": "",
            })

    # 格式 B：题号在题干前
    qs_b = extract_paper_format_b(text, section_spans, kp_of)

    # 选题数多 + 选项 4 个完整的版本
    def quality(qs):
        return sum(1 for q in qs if len(q["options"]) == 4 and q["question"])

    if quality(qs_b) > quality(qs_a):
        print(f"  [format=B 题号在题干前] A={quality(qs_a)} B={quality(qs_b)}")
        return qs_b
    print(f"  [format=A 题号在题干后] A={quality(qs_a)} B={quality(qs_b)}")
    return qs_a


def extract_answers(pdf_path: Path):
    """从答案 PDF 抽 {qn: (ans, explanation)}，兼容多种格式"""
    doc = fitz.open(str(pdf_path))
    raw = "\n".join(doc[i].get_text() for i in range(doc.page_count))
    doc.close()
    ans = {}
    # 格式 1: 【解析N--正确答案X】 / 【解析N—正确答案X】
    pat1 = re.compile(r"【解析\s*(\d{1,3})\s*[-—−–]+\s*正确答案\s*([A-D]+)】(.*?)(?=【解析\s*\d{1,3}\s*[-—−–]+\s*正确答案|\Z)", re.DOTALL)
    for m in pat1.finditer(raw):
        qn = int(m.group(1)); ans[qn] = (m.group(2).strip(), m.group(3).strip())
    if ans:
        return ans
    # 格式 2: 第N题 ... 正确答案[是:：]【X】
    pat2 = re.compile(r"第\s*【?(\d{1,3})】?\s*题(.*?)正确答案[是:：]+\s*【([A-D]+)】(.*?)(?=第\s*【?\d{1,3}】?\s*题|\Z)", re.DOTALL)
    for m in pat2.finditer(raw):
        qn = int(m.group(1)); ans[qn] = (m.group(3).strip(), m.group(4).strip())
    return ans


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("region", help="拼音如 xinjiang/beijing")
    ap.add_argument("year", type=int)
    ap.add_argument("--level", default="", help="如 A/B/C 类筛选")
    args = ap.parse_args()

    if args.region not in REGION_ZH:
        sys.exit(f"!! 未知 region: {args.region}")

    qs_pdfs, ans_pdfs = find_pdfs(args.region, args.year, args.level)
    if not qs_pdfs:
        sys.exit(f"!! 没找到题目 PDF: {args.region} {args.year}")
    if len(qs_pdfs) > 1:
        print(f"!! 多个候选题目 PDF:")
        for p in qs_pdfs:
            print(f"   {p.name}")
        sys.exit("请用 --level 缩小范围")

    pdf_q = qs_pdfs[0]
    print(f"[paper] {pdf_q.name}")
    questions = extract_paper(pdf_q)
    print(f"  抽到 {len(questions)} 题")

    if ans_pdfs:
        pdf_a = ans_pdfs[0]
        print(f"[answer] {pdf_a.name}")
        ans_map = extract_answers(pdf_a)
        print(f"  抽到答案 {len(ans_map)} 题")
        for q in questions:
            if q["sort_order"] in ans_map:
                q["answer"], q["explanation"] = ans_map[q["sort_order"]]
    else:
        print("  !! 答案 PDF 未找到，跳过答案抽取")

    out_dir = Path("data/prov_pdf_cache")
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"_{args.level.lower()}" if args.level else ""
    paper_id = f"prov_{args.region}_{args.year}{suffix}"
    out_path = out_dir / f"paper_{paper_id}.json"
    out_path.write_text(
        json.dumps({"paperId": paper_id, "title": pdf_q.name,
                    "questions": questions}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"[OK] -> {out_path}")


if __name__ == "__main__":
    main()
