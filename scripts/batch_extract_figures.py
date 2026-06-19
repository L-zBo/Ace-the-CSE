#!/usr/bin/env python3
"""
批量提取所有试卷的图形推理题图片。
扫描所有 panduan JSON 文件，找到对应的 PDF，提取图片。
"""

import json
import os
import re
import subprocess
import sys
import glob


def find_pdf_for_json(json_path: str) -> str:
    """根据 JSON 文件名推断对应的真题 PDF 路径"""
    basename = os.path.basename(json_path).replace(".json", "")
    # 解析: national_2025_fushengjia / provincial_anhui_2024 等
    parts = basename.split("_")

    source = parts[0]  # national / provincial
    year = None
    region = None
    level = None

    for p in parts[1:]:
        if p.isdigit() and len(p) == 4:
            year = p
        elif p in ("fushengjia", "dishi", "xingzhengzhifa"):
            level = p
        else:
            region = p

    if not year:
        return ""

    # 搜索 PDF 文件
    search_dirs = []
    if source == "national":
        search_dirs.append("material/【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-真题")
    elif source == "provincial" and region:
        # 搜索省考目录
        base = "material/【省考】2000-2025真题pdf"
        for d in os.listdir(base):
            full = os.path.join(base, d)
            if os.path.isdir(full) and not "答题卡" in d:
                # 检查是否是对应省份
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from extract_questions import REGION_CODES
                for cn_name, code in REGION_CODES.items():
                    if code == region and cn_name in d:
                        # 在这个省份目录下找行测
                        for sub in os.listdir(full):
                            sub_path = os.path.join(full, sub)
                            if os.path.isdir(sub_path) and "行测" in sub:
                                for ssub in os.listdir(sub_path):
                                    ssub_path = os.path.join(sub_path, ssub)
                                    if os.path.isdir(ssub_path) and ("题目" in ssub or "真题" in ssub):
                                        search_dirs.append(ssub_path)
                                # 如果没有子目录，直接用行测目录
                                if not search_dirs:
                                    search_dirs.append(sub_path)

    # 在搜索目录中找匹配的 PDF
    level_map = {
        "fushengjia": ["副省", "省级", "省部"],
        "dishi": ["地市", "市地"],
        "xingzhengzhifa": ["行政执法"],
    }

    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        for f in os.listdir(search_dir):
            if not f.endswith(".pdf"):
                continue
            if year not in f:
                continue

            # 检查级别匹配
            if level:
                keywords = level_map.get(level, [])
                if keywords and not any(kw in f for kw in keywords):
                    continue

            return os.path.join(search_dir, f)

    return ""


def main():
    print("=" * 60)
    print("批量提取图形推理题图片")
    print("=" * 60)

    json_files = sorted(glob.glob("src/data/xingce/panduan/*.json"))
    print(f"找到 {len(json_files)} 个判断推理 JSON 文件\n")

    total_updated = 0
    total_images = 0
    processed = 0
    skipped = 0

    for jf in json_files:
        basename = os.path.basename(jf).replace(".json", "")

        # 检查是否有需要处理的图形题
        with open(jf, "r", encoding="utf-8") as f:
            questions = json.load(f)

        figure_count = sum(1 for q in questions if (
            any(
                kw in q.get("content", "")
                for kw in [
                    "图形", "填入问号", "选择最合适的一个填入",
                    "选择最合适的一项填入", "直观图", "呈现一定的规律",
                    "多面体", "折叠", "左图", "右图",
                    "把下面的图形", "分类正确", "拼合",
                ]
            )
            or all(
                o.get("content", "").strip() == "[见图]"
                for o in q.get("options", [])
            )
            and len(q.get("options", [])) == 4
        ))

        if figure_count == 0:
            continue

        # 找到对应的 PDF
        pdf_path = find_pdf_for_json(jf)
        if not pdf_path:
            print(f"  [SKIP] {basename}: 未找到对应 PDF")
            skipped += 1
            continue

        print(f"  {basename}: {figure_count} 道图形题")
        print(f"    PDF: {os.path.basename(pdf_path)}")

        # 调用提取脚本
        cmd = [
            sys.executable, "-X", "utf8", "scripts/extract_figures.py",
            "--pdf", pdf_path,
            "--json", jf,
            "--exam-id", basename,
            "--output-dir", "public/img/questions",
        ]

        try:
            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120,
                encoding="utf-8", errors="replace", env=env,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if '更新' in line:
                        print(f"    {line.strip()}")
                        # 提取数字
                        m = re.search(r'(\d+)', line)
                        if m:
                            total_updated += int(m.group(1))
                processed += 1
            else:
                print(f"    [ERROR] 返回码 {result.returncode}")
                skipped += 1
        except subprocess.TimeoutExpired:
            print(f"    [TIMEOUT]")
            skipped += 1
        except Exception as e:
            print(f"    [ERROR] {e}")
            skipped += 1

    # 统计生成的图片数
    for root, dirs, files in os.walk("public/img/questions"):
        total_images += len([f for f in files if f.endswith(".png")])

    print(f"\n{'=' * 60}")
    print(f"完成: 处理 {processed} 套, 跳过 {skipped} 套")
    print(f"更新了 {total_updated} 道题, 生成 {total_images} 张图片")


if __name__ == "__main__":
    main()
