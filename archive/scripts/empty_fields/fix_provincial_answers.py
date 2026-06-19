"""
省考答案 PDF 批量注入：扫描低答案率 provincial_*.json，对应找答案 PDF，
parse + 按题号注入到 JSON 的 answer/explanation 字段。

用法：
    python scripts/fix_provincial_answers.py                  # 全跑 <60% 答案率的卷
    python scripts/fix_provincial_answers.py --dry-run
    python scripts/fix_provincial_answers.py --region beijing --year 2022
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_questions import parse_answer_pdf  # noqa: E402

MATERIAL_ROOT = Path("material/【省考】2000-2025真题pdf")
DATA_ROOT = Path("src/data/xingce")

# region 拼音 → 中文（与 MATERIAL_ROOT 下目录名对应）
REGION_MAP = {
    "anhui": "安徽", "beijing": "北京", "fujian": "福建", "gansu": "甘肃",
    "guangdong": "广东", "guangxi": "广西", "guizhou": "贵州", "hainan": "海南",
    "hebei": "河北", "henan": "河南", "heilongjiang": "黑龙江", "hubei": "湖北",
    "hunan": "湖南", "jilin": "吉林", "jiangsu": "江苏", "jiangxi": "江西",
    "liaoning": "辽宁", "neimenggu": "内蒙古", "ningxia": "宁夏", "qinghai": "青海",
    "shandong": "山东", "shanxi": "山西", "shaanxi": "陕西", "shanghai": "上海",
    "sichuan": "四川", "tianjin": "天津", "xizang": "西藏", "xinjiang": "新疆",
    "yunnan": "云南", "zhejiang": "浙江", "chongqing": "重庆", "guangzhou": "广州",
    "shenzhen": "深圳",
}


def find_answer_pdfs(region_cn: str, year: int) -> list[Path]:
    """按 region_cn + 年份在 material 下找答案 PDF。合并所有版本（区级/乡镇等）。"""
    pat_candidates = list(MATERIAL_ROOT.glob(f"*{region_cn}*/**/*{year}*.pdf"))
    # 筛选"答案/解析"类
    ans = [p for p in pat_candidates if re.search(r"答案|解析", p.name)]
    # 排除申论
    ans = [p for p in ans if "申论" not in str(p)]
    return ans


def extract_pdf_text(pdfs: list[Path]) -> str:
    """合并多份 PDF 文本"""
    texts = []
    for pdf in pdfs:
        try:
            with pdfplumber.open(pdf) as p:
                t = "\n".join((pg.extract_text() or "") for pg in p.pages)
            texts.append(t)
        except Exception as e:
            print(f"  [WARN] 读取失败 {pdf.name}: {e}")
    return "\n\n".join(texts)


def json_num(qid: str) -> int:
    return int(qid.rsplit("-", 1)[-1])


def inject_answers(region: str, year: int, answers: dict[int, dict], dry_run: bool) -> tuple[int, int]:
    files = sorted(glob.glob(str(DATA_ROOT / "**" / f"provincial_{region}_{year}*.json"), recursive=True))
    filled = 0
    total = 0
    for f in files:
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)
        changed = False
        for q in data:
            total += 1
            num = json_num(q["id"])
            if num not in answers:
                continue
            a = answers[num]
            if a["answer"] and not q.get("answer"):
                q["answer"] = a["answer"]
                filled += 1
                changed = True
            if a["explanation"] and not q.get("explanation"):
                q["explanation"] = a["explanation"]
                changed = True
        if changed and not dry_run:
            with open(f, "w", encoding="utf-8") as fp:
                json.dump(data, fp, ensure_ascii=False, indent=2)
    return filled, total


def list_low_answer_papers() -> list[tuple[str, int]]:
    """返回所有答案率 <60% 且题量>20 的 (region, year) 列表"""
    stats: dict[str, dict] = {}
    for f in sorted(glob.glob(str(DATA_ROOT / "**" / "provincial_*.json"), recursive=True)):
        name = Path(f).stem.replace("provincial_", "")
        m = re.match(r"([a-z]+)_(\d{4})", name)
        if not m:
            continue
        region, year = m.group(1), int(m.group(2))
        key = f"{region}_{year}"
        s = stats.setdefault(key, {"t": 0, "a": 0, "region": region, "year": year})
        for q in json.load(open(f, encoding="utf-8")):
            s["t"] += 1
            if q.get("answer"):
                s["a"] += 1
    low = []
    for k, v in stats.items():
        if v["t"] > 20 and v["a"] / v["t"] < 0.6:
            low.append((v["region"], v["year"], v["a"], v["t"]))
    low.sort(key=lambda x: (x[2] / x[3], -x[3]))
    return low


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", help="指定省份，如 beijing")
    ap.add_argument("--year", type=int, help="指定年份")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.region and args.year:
        targets = [(args.region, args.year, 0, 0)]
    else:
        targets = list_low_answer_papers()
        print(f"扫描到 {len(targets)} 卷低答案率卷子 (<60%)")

    summary = []
    for region, year, a0, t0 in targets:
        if region not in REGION_MAP:
            print(f"\n[跳过] {region}_{year}: 未知 region 代码")
            continue
        region_cn = REGION_MAP[region]
        print(f"\n=== {region}_{year} ({region_cn}) 当前答案率 {a0}/{t0} ===")

        pdfs = find_answer_pdfs(region_cn, year)
        if not pdfs:
            print(f"  [未找到答案 PDF]")
            summary.append((region, year, 0, 0, 0, "未找到 PDF"))
            continue
        for p in pdfs:
            print(f"  -> {p.name}")

        text = extract_pdf_text(pdfs)
        if len(text) < 1000:
            print(f"  [警告] 抽出文本过短 ({len(text)} 字符)")
        ans = parse_answer_pdf(text)
        has = sum(1 for v in ans.values() if v["answer"])
        print(f"  parse: {len(ans)} 题号, {has} 有答案")

        filled, total = inject_answers(region, year, ans, args.dry_run)
        print(f"  注入: 填 {filled} 字段 / JSON 共 {total} 题")
        summary.append((region, year, has, filled, total, ""))

    print("\n" + "=" * 60)
    print("汇总:")
    for region, year, has, filled, total, note in summary:
        print(f"  {region}_{year}: PDF {has} / 填 {filled} / 总 {total} {note}")
    if args.dry_run:
        print("\n[DRY RUN] 未写盘")


if __name__ == "__main__":
    main()
