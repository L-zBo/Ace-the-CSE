"""D-13 按 region+year 定位 paperId 并自动 fetch（不实写 lib）

用法：
  python scripts/d13_locate_paper.py qinghai 2024
  python scripts/d13_locate_paper.py zhejiang 2023 --level B
  python scripts/d13_locate_paper.py guizhou 2024 --national  (国考)

不带 region 参数则从 stdin 读 region year level 多行。
"""
import argparse, json, sys
from pathlib import Path

INDEX = Path("data/baijing_cache/_index_xingce.json")

REGION_ZH = {
    "qinghai": "青海", "ningxia": "宁夏", "zhejiang": "浙江",
    "chongqing": "重庆", "gansu": "甘肃", "heilongjiang": "黑龙江",
    "shandong": "山东", "shenzhen": "深圳", "tianjin": "天津",
    "jiangsu": "江苏", "jilin": "吉林", "neimenggu": "内蒙古",
    "sichuan": "四川", "guangdong": "广东", "guangzhou": "广州",
    "shanghai": "上海", "beijing": "北京", "hubei": "湖北",
    "anhui": "安徽", "fujian": "福建", "guangxi": "广西",
    "guizhou": "贵州", "hainan": "海南", "hebei": "河北",
    "henan": "河南", "hunan": "湖南", "jiangxi": "江西",
    "liaoning": "辽宁", "shanxi": "山西", "shaanxi": "陕西",
    "yunnan": "云南", "xinjiang": "新疆", "xizang": "西藏",
    "national": "国考",
}


def locate(region: str, year: int, level: str = "", national: bool = False, xuandiao: bool = False):
    papers = json.loads(INDEX.read_text(encoding="utf-8"))
    rg_zh = REGION_ZH.get(region, region)
    if national:
        rg_zh = "国考"
    matches = []
    for p in papers:
        if p.get("region") != rg_zh:
            continue
        if p.get("year") != year:
            continue
        if national and not p.get("national"):
            continue
        if level:
            t = p.get("title", "")
            if f"（{level}类" not in t and f"({level}类" not in t and f"（{level}卷" not in t:
                continue
        if xuandiao and not p.get("xuandiao"):
            continue
        if not xuandiao and p.get("xuandiao"):
            continue
        matches.append(p)
    return matches


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("region", nargs="?")
    ap.add_argument("year", nargs="?", type=int)
    ap.add_argument("--level", default="")
    ap.add_argument("--national", action="store_true")
    ap.add_argument("--xuandiao", action="store_true")
    args = ap.parse_args()
    if not args.region:
        ap.print_help()
        return
    matches = locate(args.region, args.year, args.level, args.national, args.xuandiao)
    if not matches:
        print(f"!! 没找到 {args.region} {args.year} (level={args.level} national={args.national})")
        # 模糊
        papers = json.loads(INDEX.read_text(encoding="utf-8"))
        rg_zh = REGION_ZH.get(args.region, args.region)
        nearby = [p for p in papers if p.get("region") == rg_zh]
        if nearby:
            print(f"   {rg_zh} 现有:")
            for p in nearby:
                print(f"     {p['id']:>4}  {p['year']}  level={p['level']}  national={p.get('national')}  {p['title'][:50]}")
        return
    for p in matches:
        print(f"{p['id']:>5}  {p['region']:<6} {p['year']}  level={p['level']}  national={p.get('national')}  {p['title'][:60]}")


if __name__ == "__main__":
    main()
