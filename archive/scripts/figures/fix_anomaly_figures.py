#!/usr/bin/env python3
"""
针对 <20KB 和 >300KB 的异常图片，重新按新裁剪逻辑提取单题。
复用 batch_extract_figures.find_pdf_for_json 定位 PDF。
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from batch_extract_figures import find_pdf_for_json
from extract_figures import (
    extract_figure_questions,
    update_json_with_images,
)


ANOMALIES = [
    # 真图形题但需裁剪/消歧修复
    ("national_2015_fushengjia", 100),
    ("national_2018_dishi", 91),
    ("national_2018_fushengjia", 96),
    ("national_2021", 76),
    ("provincial_fujian_2020", 72),
    ("provincial_fujian_2020", 92),
    ("provincial_hubei_2020", 75),
    ("provincial_jiangsu_2021", 79),
    ("provincial_jiangsu_2023", 81),
    ("provincial_jiangsu_2024", 72),
    ("provincial_shandong_2020", 49),
    ("provincial_shanghai_2020", 38),
    ("provincial_shanghai_2020", 75),
    ("provincial_shanghai_2021", 38),
    ("provincial_shanghai_2021", 43),
    ("provincial_sichuan_2020", 58),
    ("national_2022_dishi", 77),
    ("provincial_henan_2021", 106),
    ("provincial_jiangsu_2021", 85),
    ("provincial_jiangsu_2021", 89),
    ("provincial_jiangsu_2023", 82),
    ("provincial_jiangsu_2023", 84),
    ("provincial_shandong_2024", 62),
]


def main():
    # 按 exam_id 分组
    by_exam: dict[str, list[int]] = {}
    for exam_id, q_num in ANOMALIES:
        by_exam.setdefault(exam_id, []).append(q_num)

    for exam_id, q_nums in by_exam.items():
        json_path = f"src/data/xingce/panduan/{exam_id}.json"
        if not os.path.exists(json_path):
            print(f"[SKIP] {exam_id}: JSON 不存在 → {json_path}")
            continue

        pdf_path = find_pdf_for_json(json_path)
        if not pdf_path:
            print(f"[SKIP] {exam_id}: 找不到 PDF")
            continue

        # 读题干作为消歧提示
        import json as _json
        qs = _json.load(open(json_path, encoding="utf-8"))
        hints = {}
        for q in qs:
            try:
                qn = int(q["id"].split("-")[-1])
                if qn in q_nums:
                    hints[qn] = q.get("content", "")
            except ValueError:
                pass

        print(f"\n== {exam_id} (Qs: {q_nums}) ==")
        print(f"   PDF: {os.path.basename(pdf_path)}")

        output_dir = f"public/img/questions/{exam_id}"
        image_map = extract_figure_questions(
            pdf_path, q_nums, output_dir, prefix="", dpi=300,
            content_hints=hints,
        )

        for q in q_nums:
            p = image_map.get(q)
            if p and os.path.exists(p):
                size = os.path.getsize(p)
                flag = ""
                if size < 15000:
                    flag = " [仍偏小]"
                elif size > 280000:
                    flag = " [仍偏大]"
                print(f"   Q{q}: {size} bytes{flag}")
            else:
                print(f"   Q{q}: [FAILED]")

        # 更新 JSON 引用（虽然路径不变，但确保一致）
        update_json_with_images(json_path, image_map, f"/img/questions/{exam_id}/")


if __name__ == "__main__":
    main()
