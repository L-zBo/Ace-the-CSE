#!/usr/bin/env python3
"""
批量提取省考行测真题。
扫描所有省份目录，自动匹配真题和答案PDF。
"""

import os
import re
import subprocess
import sys

BASE_DIR = "material/【省考】2000-2025真题pdf"
OUTPUT_DIR = "src/data/xingce"

# 省份目录 → region代码
REGION_CODES = {
    "安徽": "anhui", "北京": "beijing", "福建": "fujian", "甘肃": "gansu",
    "广东": "guangdong", "广西": "guangxi", "贵州": "guizhou", "海南": "hainan",
    "河北": "hebei", "河南": "henan", "黑龙江": "heilongjiang", "湖北": "hubei",
    "湖南": "hunan", "吉林": "jilin", "江苏": "jiangsu", "江西": "jiangxi",
    "辽宁": "liaoning", "内蒙古": "neimenggu", "宁夏": "ningxia", "青海": "qinghai",
    "山东": "shandong", "山西": "shanxi", "陕西": "shaanxi", "上海": "shanghai",
    "四川": "sichuan", "天津": "tianjin", "西藏": "xizang", "新疆": "xinjiang",
    "云南": "yunnan", "浙江": "zhejiang", "重庆": "chongqing",
    "广州": "guangzhou", "深圳": "shenzhen",
}

# 重点省份（优先处理）
PRIORITY_REGIONS = [
    "山东", "广东", "江苏", "浙江", "四川", "北京", "上海",
    "河南", "湖北", "安徽", "福建", "河北",
]


def detect_year(filename: str) -> int:
    m = re.search(r'(\d{4})', filename)
    return int(m.group(1)) if m else 0


def detect_region(dirname: str) -> str:
    for name, code in REGION_CODES.items():
        if name in dirname:
            return code
    return ""


def detect_region_cn(dirname: str) -> str:
    for name in REGION_CODES:
        if name in dirname:
            return name
    return ""


def find_xingce_dirs(province_dir: str):
    """在省份目录下找到行测题目和答案目录"""
    question_dir = None
    answer_dir = None

    for item in os.listdir(province_dir):
        full_path = os.path.join(province_dir, item)
        if not os.path.isdir(full_path):
            continue
        if "行测" in item:
            # 检查是否有子目录（题目/答案）
            sub_items = os.listdir(full_path) if os.path.isdir(full_path) else []
            for sub in sub_items:
                sub_path = os.path.join(full_path, sub)
                if os.path.isdir(sub_path):
                    if "答案" in sub or "解析" in sub:
                        answer_dir = sub_path
                    elif "题目" in sub or "真题" in sub:
                        question_dir = sub_path

            # 如果没有子目录分离，题目和答案可能混在一起
            if not question_dir and not answer_dir:
                # 检查是否有PDF直接在此目录
                pdfs = [f for f in sub_items if f.endswith('.pdf')]
                if pdfs:
                    question_dir = full_path
                    answer_dir = full_path

    return question_dir, answer_dir


def match_q_and_a(q_dir: str, a_dir: str, min_year: int = 2020):
    """匹配真题和答案PDF"""
    pairs = []

    if not q_dir or not a_dir:
        return pairs

    q_files = [f for f in os.listdir(q_dir) if f.endswith('.pdf')]
    a_files = [f for f in os.listdir(a_dir) if f.endswith('.pdf')]

    for qf in q_files:
        year = detect_year(qf)
        if year < min_year:
            continue

        # 在答案目录找匹配
        best_match = ""
        for af in a_files:
            a_year = detect_year(af)
            if a_year == year and ("答案" in af or "解析" in af):
                best_match = af
                break

        if best_match:
            pairs.append((
                os.path.join(q_dir, qf),
                os.path.join(a_dir, best_match),
                year,
            ))

    return sorted(pairs, key=lambda x: x[2])


def main():
    min_year = int(sys.argv[1]) if len(sys.argv) > 1 else 2020
    max_provinces = int(sys.argv[2]) if len(sys.argv) > 2 else 999

    # 列出所有省份目录
    province_dirs = sorted([
        d for d in os.listdir(BASE_DIR)
        if os.path.isdir(os.path.join(BASE_DIR, d)) and "答题卡" not in d
    ])

    # 按优先级排序
    def priority_key(d):
        region_cn = detect_region_cn(d)
        if region_cn in PRIORITY_REGIONS:
            return PRIORITY_REGIONS.index(region_cn)
        return 100

    province_dirs.sort(key=priority_key)

    print(f"找到 {len(province_dirs)} 个省份目录")
    print(f"提取范围: {min_year}-2025, 最多 {max_provinces} 个省份")
    print("=" * 60)

    total_success = 0
    total_failed = 0
    total_skipped = 0
    processed_provinces = 0

    for pdir in province_dirs:
        if processed_provinces >= max_provinces:
            break

        full_pdir = os.path.join(BASE_DIR, pdir)
        region = detect_region(pdir)
        region_cn = detect_region_cn(pdir)

        if not region:
            print(f"\n[SKIP] {pdir} — 未识别省份")
            continue

        q_dir, a_dir = find_xingce_dirs(full_pdir)
        if not q_dir:
            print(f"\n[SKIP] {pdir} — 未找到行测目录")
            total_skipped += 1
            continue

        pairs = match_q_and_a(q_dir, a_dir, min_year)
        if not pairs:
            print(f"\n[SKIP] {region_cn} — 无 {min_year}+ 年的匹配PDF对")
            total_skipped += 1
            continue

        processed_provinces += 1
        print(f"\n{'═' * 60}")
        print(f"省份: {region_cn} ({region}), {len(pairs)} 套试卷")

        for q_path, a_path, year in pairs:
            print(f"\n  {year}年:")
            print(f"    真题: {os.path.basename(q_path)}")
            print(f"    答案: {os.path.basename(a_path)}")

            cmd = [
                sys.executable, "-X", "utf8", "scripts/extract_questions.py",
                "--question-pdf", q_path,
                "--answer-pdf", a_path,
                "--source", "provincial",
                "--region", region,
                "--year", str(year),
                "--output-dir", OUTPUT_DIR,
            ]

            try:
                env = os.environ.copy()
                env["PYTHONUTF8"] = "1"
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=300,
                    encoding="utf-8", errors="replace", env=env,
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if '新题' in line or '总计' in line:
                            print(f"    {line.strip()}")
                    total_success += 1
                else:
                    print(f"    [ERROR] 返回码 {result.returncode}")
                    stderr_short = result.stderr[:200] if result.stderr else ""
                    if stderr_short:
                        print(f"    {stderr_short}")
                    total_failed += 1
            except subprocess.TimeoutExpired:
                print(f"    [TIMEOUT]")
                total_failed += 1
            except Exception as e:
                print(f"    [ERROR] {e}")
                total_failed += 1

    print(f"\n{'═' * 60}")
    print(f"省考批量处理完成: 成功 {total_success}, 失败 {total_failed}, 跳过 {total_skipped}")
    print(f"已处理 {processed_provinces} 个省份")


if __name__ == "__main__":
    main()
