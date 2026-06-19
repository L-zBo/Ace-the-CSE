#!/usr/bin/env python3
"""C阶段#3：修 2015 国考两套 10 题选项异常 → [图形选项]×4。

- Q20 dishi/fsj: 以右为尊题，选项=4 动作图 + 题干被作答说明污染需清理
- Q61 dishi / Q62/64/71 fsj: 数学题，选项=图
- Q74 dishi / Q79 fsj: 图形推理折叠纸盒，选项=图
- Q87 dishi / Q92 fsj: 盛酒器言语题，选项=图

PDF 验证：所有 10 题在 PDF 文本里 ABCD 后均空白，确证选项是嵌入图。
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data" / "xingce"

# (module, exam, qn, content_clean_func or None)
TARGETS = [
    # dishi 4 题
    ("changshi", "national_2015_dishi", 20, "q20"),
    ("panduan",  "national_2015_dishi", 74, "q74"),
    ("panduan",  "national_2015_dishi", 87, "keep"),
    ("shuliang", "national_2015_dishi", 61, "q61_dishi"),
    # fushengjia 6 题
    ("changshi", "national_2015_fushengjia", 20, "q20"),
    ("panduan",  "national_2015_fushengjia", 79, "q74"),
    ("panduan",  "national_2015_fushengjia", 92, "keep"),
    ("shuliang", "national_2015_fushengjia", 62, "q62_fsj"),
    ("shuliang", "national_2015_fushengjia", 64, "keep_strip_dash"),
    ("shuliang", "national_2015_fushengjia", 71, "keep"),
]

# Q20 真实题干（从 PDF 抽）：去掉"本部分包括…"那段污染
Q20_CLEAN = (
    "中国古代以\"右\"为尊，举办宴会，座位次序为：\"宾客之中最尊贵之人居首席，"
    "面南背北而坐，居其右而面东。\"按位次依次排列。下列座次安排符合上述礼法的是？"
)
# Q61 dishi 题干（PDF 抽）：去掉 "- 6 -" 等页码
Q61_DISHI_CLEAN = (
    "某单位有 50 人，男女性别比为图所示，其中 15 人未入党。从中随机选 1 人，"
    "求其为男性党员的概率为多少？"
)
# Q62 fsj 真实题干（PDF 文字明确）："性别比为3:2"
Q62_FSJ_CLEAN = (
    "某单位有 50 人，男女性别比为 3:2，其中 15 人未入党。从中随机选 1 人，"
    "求其为男性党员的概率为多少？"
)


def make_image_options() -> list[dict]:
    return [{"label": L, "content": "[图形选项]"} for L in "ABCD"]


def strip_pollution(text: str) -> str:
    """去除题干尾部的页码 ('- 6 -') 与作答说明残片。"""
    # 去掉 "- 数字 -" 形式页码
    text = re.sub(r"\s*-\s*\d+\s*-\s*$", "", text).strip()
    # 去掉单独 "ABCD" 字母行
    text = re.sub(r"\s+[A-D][．、.]?\s+[A-D][．、.]?\s+[A-D][．、.]?\s+[A-D][．、.]?\s*$", "", text).strip()
    return text


def fix_question(q: dict, mode: str) -> tuple[bool, list[str]]:
    """返回 (是否修改, 变更说明列表)。"""
    changes = []
    old_content = q.get("content", "")

    if mode == "q20":
        new_content = Q20_CLEAN
    elif mode == "q61_dishi":
        new_content = Q61_DISHI_CLEAN
    elif mode == "q62_fsj":
        new_content = Q62_FSJ_CLEAN
    elif mode == "q74":
        # 图形推理折叠纸盒题，题干本身较干净
        new_content = strip_pollution(old_content)
    elif mode == "keep_strip_dash":
        new_content = strip_pollution(old_content)
    else:  # keep
        new_content = strip_pollution(old_content)

    if new_content != old_content:
        q["content"] = new_content
        changes.append(f"content cleaned ({len(old_content)} -> {len(new_content)})")

    old_opts = q.get("options", [])
    new_opts = make_image_options()
    if old_opts != new_opts:
        q["options"] = new_opts
        changes.append(f"options {len(old_opts)} -> 4 [图形选项]")

    return bool(changes), changes


def main():
    summary = []
    for module, exam, qn, mode in TARGETS:
        path = DATA / module / f"{exam}.json"
        questions = json.loads(path.read_text(encoding="utf-8"))
        target = None
        for q in questions:
            try:
                if int(q["id"].split("-")[-1]) == qn:
                    target = q
                    break
            except (KeyError, ValueError):
                continue
        if not target:
            summary.append(f"[MISS] {exam} Q{qn:03d} 题号不存在")
            continue
        changed, notes = fix_question(target, mode)
        if changed:
            path.write_text(
                json.dumps(questions, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            summary.append(f"[FIX] {exam} Q{qn:03d} ({module}): " + "; ".join(notes))
        else:
            summary.append(f"[SKIP] {exam} Q{qn:03d} 无变化")

    print("\n".join(summary))


if __name__ == "__main__":
    main()
