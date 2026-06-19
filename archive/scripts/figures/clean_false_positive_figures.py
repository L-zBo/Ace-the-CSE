#!/usr/bin/env python3
"""清理误判为图形题的 questionImage 字段，并删除对应图片文件。"""
import json
import os

# (json_path, qid) — 确认不是图形题的误判
FALSE_POSITIVES = [
    ("src/data/xingce/panduan/provincial_shanghai_2020.json", "063"),
    ("src/data/xingce/panduan/provincial_shanghai_2021.json", "061"),
    ("src/data/xingce/panduan/national_2022_fushengjia.json", "093"),
    ("src/data/xingce/panduan/national_2022_xingzhengzhifa.json", "086"),
    ("src/data/xingce/panduan/provincial_sichuan_2024.json", "085"),
    ("src/data/xingce/panduan/provincial_jiangsu_2023.json", "076"),
    # 浙江 2021 Q96-98、Q100 在 PDF 里实际是类比题（JSON content 错误），非图形题
    ("src/data/xingce/panduan/provincial_zhejiang_2021.json", "096"),
    ("src/data/xingce/panduan/provincial_zhejiang_2021.json", "097"),
    ("src/data/xingce/panduan/provincial_zhejiang_2021.json", "098"),
    ("src/data/xingce/panduan/provincial_zhejiang_2021.json", "100"),
    ("src/data/xingce/panduan/provincial_fujian_2020.json", "092"),
    # 类比推理误判（文字选项被渲染成图）
    ("src/data/xingce/panduan/national_2015_fushengjia.json", "100"),
    ("src/data/xingce/panduan/national_2018_dishi.json", "091"),
    ("src/data/xingce/panduan/national_2018_fushengjia.json", "096"),
    ("src/data/xingce/panduan/provincial_jiangsu_2024.json", "072"),
]


def main():
    for jp, qid in FALSE_POSITIVES:
        if not os.path.exists(jp):
            print(f"[SKIP] {jp} 不存在")
            continue
        qs = json.load(open(jp, encoding="utf-8"))
        changed = False
        for q in qs:
            if q["id"].split("-")[-1] == qid and "questionImage" in q:
                img = q.pop("questionImage")
                # 删除图片文件
                img_path = "public" + img
                if os.path.exists(img_path):
                    os.remove(img_path)
                    print(f"  删除图片: {img_path}")
                print(f"  清理 {jp} Q{qid} 的 questionImage")
                changed = True
        if changed:
            json.dump(qs, open(jp, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
