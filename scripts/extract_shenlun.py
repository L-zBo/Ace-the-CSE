#!/usr/bin/env python3
"""申论真题 MVP 抽取器 — 每份 PDF 一条记录，保证 100% answer/explanation 覆盖。

策略：
  - 用 "参考答案" / "参考范文" / "【参考答案】" / "答案要点" 作为 split point
  - split 前 = 材料 + 作答要求（整体 content）
  - split 后 = 参考答案 + 解析（整体 answer；explanation=同）
  - category 按文件末尾作答要求关键词识别（xiezuo 优先）
  - year/level/source/region 从 PDF 路径与文件名推断

用法：
  python scripts/extract_shenlun.py [--apply]
  默认 dry-run 只扫描打印，--apply 才写 JSON 并生效。
"""
import argparse
import glob
import json
import os
import re
import sys
import io
import warnings

warnings.filterwarnings("ignore")

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pdfminer.high_level import extract_text

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_ROOT = os.path.join(ROOT, "src", "data", "shenlun")

# 按优先级匹配 category：写作最显著、归纳最基础
CATEGORY_RULES = [
    ("xiezuo", ["文章", "写作", "作文", "不少于 8", "不少于8", "议论文", "范文", "题目自拟", "自拟标题"]),
    ("guanche", ["贯彻", "执行", "落实", "推动", "提纲", "倡议书", "宣传稿", "讲话稿", "汇报", "通知"]),
    ("duice", ["对策", "建议", "措施", "办法", "解决", "如何", "应当", "应该采取"]),
    ("fenxi", ["分析", "原因", "问题", "评析", "评价", "阐述"]),
    ("guina", ["概括", "归纳", "总结", "要点", "梳理"]),
]

SPLIT_KEYWORDS = [
    "参考答案与解析",
    "参考答案及解析",
    "【参考答案】",
    "参考答案：",
    "参考答案",
    "答案要点",
    "参考范文",
    "【答案解析】",
    "答案解析",
]

# PDF 源目录（国考+省考+事业编申论）
PDF_SOURCES = [
    {
        "root": "material/【国考】2000-2025真题pdf/2000-2025国考申论PDF",
        "source": "national",
    },
    {
        "root": "material/【省考】2000-2025真题pdf",
        "source": "provincial",
    },
    {
        "root": "material/【事业编】事业单位联考历年真题",
        "source": "institution",
    },
]


def guess_meta(filename: str, source: str, relpath: str):
    """从文件名 / 相对路径推断 year / level / region"""
    year_m = re.search(r"(20\d{2})", filename)
    year = int(year_m.group(1)) if year_m else None

    # level
    level = ""
    if "副省" in filename or "副省级" in filename or "省部级" in filename:
        level = "fushengjia"
    elif "地市" in filename or "市地" in filename:
        level = "dishi"
    elif "行政执法" in filename:
        level = "xingzhengzhifa"

    # region (省考用，从路径第 2 段取省份目录名)
    region = ""
    if source == "provincial":
        # e.g. "【01】安徽公务员考试真题pdf版"
        m = re.search(r"【\d+】([\u4e00-\u9fa5]+)公务员", relpath)
        if m:
            # 汉字省名 → 拼音代码（简版，只列主流）
            region_map = {
                "安徽": "anhui", "北京": "beijing", "福建": "fujian", "甘肃": "gansu",
                "广东": "guangdong", "广西": "guangxi", "贵州": "guizhou", "海南": "hainan",
                "河北": "hebei", "河南": "henan", "黑龙江": "heilongjiang", "湖北": "hubei",
                "湖南": "hunan", "吉林": "jilin", "江苏": "jiangsu", "江西": "jiangxi",
                "辽宁": "liaoning", "内蒙古": "neimenggu", "宁夏": "ningxia", "青海": "qinghai",
                "山东": "shandong", "山西": "shanxi", "陕西": "shaanxi", "上海": "shanghai",
                "四川": "sichuan", "天津": "tianjin", "新疆": "xinjiang", "云南": "yunnan",
                "浙江": "zhejiang", "重庆": "chongqing",
            }
            region = region_map.get(m.group(1), "")

    # institution class
    inst_class = ""
    if source == "institution":
        m = re.search(r"([A-E])\s*类", relpath + filename)
        if m:
            inst_class = m.group(1).lower()

    return year, level, region, inst_class


def detect_category(content: str) -> str:
    for cat, kws in CATEGORY_RULES:
        for kw in kws:
            if kw in content:
                return cat
    return "xiezuo"  # fallback


def find_split(text: str) -> int:
    """返回 "参考答案" 类关键词的第一个位置，找不到返回 -1"""
    best = -1
    for kw in SPLIT_KEYWORDS:
        i = text.find(kw)
        if i >= 0 and (best < 0 or i < best):
            best = i
    return best


def clean_text(t: str, limit: int = 6000) -> str:
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"公众号[:：].+", "", t)
    t = re.sub(r"TB[:：].+", "", t)
    t = t.strip()
    if len(t) > limit:
        t = t[:limit] + "\n\n[...内容截断]"
    return t


def process_pdf(pdf_path: str, source: str, rel: str):
    filename = os.path.basename(pdf_path)
    year, level, region, inst_class = guess_meta(filename, source, rel)
    if not year or year < 2000 or year > 2025:
        return None

    try:
        text = extract_text(pdf_path)
    except Exception as e:
        print(f"  [ERR] {filename}: {e}")
        return None

    if len(text) < 500:
        return None

    split_i = find_split(text)
    if split_i < 0:
        # 无答案段 → 跳过（保证 100% answer 覆盖）
        print(f"  [SKIP no-answer] {filename}")
        return None

    content_raw = text[:split_i]
    answer_raw = text[split_i:]

    content = clean_text(content_raw, limit=8000)
    answer = clean_text(answer_raw, limit=8000)

    if len(content) < 100 or len(answer) < 100:
        return None

    category = detect_category(content)

    # id 组装：shenlun-{source}-{category}-{year}[-{region}][-{level}][-{class}]-001
    id_parts = ["shenlun", source, category, str(year)]
    if region:
        id_parts.insert(2, region)  # 省考 region 放前
    if level:
        id_parts.append(level)
    if inst_class:
        id_parts.append(inst_class)
    qid = "-".join(id_parts) + "-001"

    # 文件名：source[_region]_year[_level][_class].json
    fn_parts = [source]
    if region:
        fn_parts.append(region)
    fn_parts.append(str(year))
    if level:
        fn_parts.append(level)
    if inst_class:
        fn_parts.append(inst_class)
    out_filename = "_".join(fn_parts) + ".json"

    label_parts = [f"{year}年"]
    if source == "national":
        label_parts.append("国考申论")
    elif source == "provincial":
        label_parts.append(f"{region}省考申论" if region else "省考申论")
    else:
        label_parts.append(f"事业编申论({inst_class.upper()}类)" if inst_class else "事业编申论")
    if level:
        label_parts.append({"fushengjia": "副省级", "dishi": "地市级", "xingzhengzhifa": "行政执法"}.get(level, level))
    source_label = "·".join(label_parts)

    question = {
        "id": qid,
        "subject": "shenlun",
        "category": category,
        "type": "essay",
        "source": source,
        "year": year,
        "content": content,
        "options": [],
        "answer": answer,
        "explanation": answer,  # 答案即解析（申论答案本身就是带分析的范文/要点）
        "difficulty": 5,
        "knowledgePoints": ["申论", source_label.split("·")[1] if len(source_label.split("·")) > 1 else "申论"],
        "sourceLabel": source_label,
    }
    if region:
        question["region"] = region

    return {
        "category": category,
        "out_filename": out_filename,
        "question": question,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    all_results = []
    for src_conf in PDF_SOURCES:
        root = os.path.join(ROOT, src_conf["root"])
        if not os.path.exists(root):
            print(f"[SKIP] {root} 不存在")
            continue
        pdfs = [p for p in glob.glob(os.path.join(root, "**/*申论*.pdf"), recursive=True)
                + glob.glob(os.path.join(root, "**/*Shenlun*.pdf"), recursive=True)]
        # 事业编里可能叫"综合应用能力"或"职测"，先跳过职测
        pdfs = [p for p in pdfs if "职测" not in p]
        print(f"\n=== {src_conf['source']}: {len(pdfs)} PDFs ===")
        for pdf in sorted(pdfs):
            rel = os.path.relpath(pdf, ROOT)
            r = process_pdf(pdf, src_conf["source"], rel)
            if r:
                print(f"  [OK] {os.path.basename(pdf):70} → {r['category']}/{r['out_filename']}")
                all_results.append(r)

    print(f"\n=== 合计 {len(all_results)} 条题可生成 ===")

    if not args.apply:
        print("[DRY-RUN] 未落盘。--apply 生效。")
        return

    # 按 category+文件名分组写入
    by_file = {}
    for r in all_results:
        key = (r["category"], r["out_filename"])
        by_file.setdefault(key, []).append(r["question"])

    written = 0
    for (cat, fn), qs in by_file.items():
        cat_dir = os.path.join(OUT_ROOT, cat)
        os.makedirs(cat_dir, exist_ok=True)
        fp = os.path.join(cat_dir, fn)
        # 合并：已存在则按 id 合并（保留原手工填的高质量数据）
        existing = []
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as f:
                existing = json.load(f)
        existing_ids = {q.get("id") for q in existing}
        for q in qs:
            if q["id"] not in existing_ids:
                existing.append(q)
                existing_ids.add(q["id"])
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        written += len(qs)
    print(f"\n✓ 写入 {written} 条，跨 {len(by_file)} 个 JSON")


if __name__ == "__main__":
    main()
