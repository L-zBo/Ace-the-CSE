#!/usr/bin/env python3
"""C阶段#收尾 - 修 2023 国考 6 题历史错位 bug。

bug: 早期 PDF→JSON 抽题流水线把图形推理 panduan Q78/Q80/Q106 的题干
错植到 changshi 模块 Q17/Q18/Q20/Q15/Q17/Q24 位置，
+ 答案/解析也对应错位题。

修法：从 2023 三套真题 PDF + 答案 PDF 重抽真实内容 → 覆盖 JSON。

【6 题】
- 2023_dishi changshi Q17/Q18/Q20
- 2023_fsj   changshi Q15/Q17
- 2023_fsj   yanyu    Q24
"""
from __future__ import annotations
import glob
import json
import re
from pathlib import Path

import fitz  # type: ignore[import-not-found]


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data" / "xingce"

TARGETS = [
    ("dishi", "changshi", 17),
    ("dishi", "changshi", 18),
    ("dishi", "changshi", 20),
    ("fsj", "changshi", 15),
    ("fsj", "changshi", 17),
    ("fsj", "yanyu", 24),
]

LEVEL_KEYS = {
    "dishi": ["地市级", "市地级"],
    "fsj": ["副省级", "省部级", "省级"],
}


def find_pdf(level: str, is_answer: bool) -> Path:
    for p in glob.glob("material/**/2023*行测*.pdf", recursive=True):
        if "国考" not in p:
            continue
        is_ans = "答案" in p or "解析" in p
        if is_ans != is_answer:
            continue
        for kw in LEVEL_KEYS[level]:
            if kw.encode("utf-8") in p.encode("utf-8"):
                return Path(p)
    raise FileNotFoundError(f"找不到 2023 {level} {'答案' if is_answer else '真题'}")


def extract_block(pdf_path: Path, qn: int) -> str | None:
    doc = fitz.open(pdf_path)
    text = "\n".join(doc[i].get_text() for i in range(doc.page_count))
    matches = [m.start() for m in re.finditer(rf"(?<=\n){qn}\n", text)]
    if not matches:
        return None
    pos = matches[0]
    nxt = re.search(rf"(?<=\n){qn + 1}\n", text[pos + 5 :])
    end = pos + 5 + nxt.start() if nxt else pos + 2000
    return text[pos + len(str(qn)) + 1 : end].strip()


# 选项行匹配多种格式：A、 / A. / A．/ A ， 顶部带空格
OPT_LINE_RE = re.compile(r"^\s*([A-D])\s*[、,，.．]\s*(.+)$", re.MULTILINE)


def parse_question_block(block: str) -> tuple[str, list[str]] | None:
    """从真题块解析 (content, [A,B,C,D])。"""
    # 找第一个 ABCD 行
    matches = list(OPT_LINE_RE.finditer(block))
    if len(matches) < 4:
        return None
    # 题干 = 第一个 A 选项之前的内容（去除尾部页码"\n4"等）
    content_raw = block[: matches[0].start()].strip()
    # 去除中间的 "页号\n" (单数字行) 和 trailing whitespace
    content = re.sub(r"\n\s*\d{1,2}\s*\n", "\n", "\n" + content_raw).strip()
    content = re.sub(r"[\s\n]+", " ", content).strip()

    options: dict[str, str] = {}
    for i, m in enumerate(matches[:4]):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
        opt_text = block[m.start() : end].strip()
        # 取 ABCD 后的内容
        body = OPT_LINE_RE.match(opt_text).group(2).strip()
        # 去除选项内容里的页号（"\n4\n"）
        body = re.sub(r"\s*\n\s*\d{1,2}\s*\n\s*", " ", body)
        body = re.sub(r"\s+", " ", body).strip()
        options[m.group(1)] = body

    return content, [options.get(L, "") for L in "ABCD"]


def parse_answer_block(block: str) -> tuple[str, str] | None:
    """从答案块解析 (answer, explanation)。"""
    m = re.search(r"故正确答案为\s*([A-D]+)", block)
    if not m:
        return None
    return m.group(1), block.strip()


def main() -> None:
    fixed_count = 0
    for level, module, qn in TARGETS:
        # 真题
        true_pdf = find_pdf(level, is_answer=False)
        true_block = extract_block(true_pdf, qn)
        if not true_block:
            print(f"[{level} Q{qn:03d}] ❌ 真题块未找到")
            continue
        parsed = parse_question_block(true_block)
        if not parsed:
            print(f"[{level} Q{qn:03d}] ❌ 解析 ABCD 选项失败")
            print(f"  block first 300: {true_block[:300]}")
            continue
        content, options_text = parsed

        # 答案
        ans_pdf = find_pdf(level, is_answer=True)
        ans_block = extract_block(ans_pdf, qn)
        if not ans_block:
            print(f"[{level} Q{qn:03d}] ❌ 答案块未找到")
            continue
        ans_parsed = parse_answer_block(ans_block)
        if not ans_parsed:
            print(f"[{level} Q{qn:03d}] ❌ 答案解析失败")
            continue
        answer, explanation = ans_parsed

        # 写 JSON
        full_level = "fushengjia" if level == "fsj" else level
        json_path = DATA / module / f"national_2023_{full_level}.json"
        questions = json.loads(json_path.read_text(encoding="utf-8"))
        target = None
        for q in questions:
            try:
                if int(q["id"].split("-")[-1]) == qn:
                    target = q
                    break
            except (KeyError, ValueError):
                continue
        if not target:
            print(f"[{level} Q{qn:03d}] ❌ JSON 中未找到")
            continue

        old_content = target.get("content", "")[:60]
        target["content"] = content
        target["options"] = [
            {"label": L, "content": txt} for L, txt in zip("ABCD", options_text)
        ]
        target["answer"] = answer
        target["explanation"] = explanation
        # 移除可能错位的 questionImage 字段
        target.pop("questionImage", None)

        json_path.write_text(
            json.dumps(questions, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        fixed_count += 1
        print(f"[FIX] 2023_{level} {module} Q{qn:03d}: ans={answer}")
        print(f"  旧 content: {old_content}")
        print(f"  新 content: {content[:60]}")
        print(f"  新 options: " + " | ".join(f"{L}={t[:20]}" for L, t in zip("ABCD", options_text)))

    print(f"\n合计修复 {fixed_count}/{len(TARGETS)} 题")


if __name__ == "__main__":
    main()
