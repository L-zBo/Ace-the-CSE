#!/usr/bin/env python3
"""C阶段#2：从 2023 国考三套答案 PDF 抽 answer + explanation 注入 JSON。

策略：
1. PDF 文本切块：以"故正确答案为X。N"或"\\nN\\n"为界，N 单调递增
2. 每块提取 answer (故正确答案为X) + explanation (块剩余文字)
3. 注入 JSON：仅缺 answer 的题写入 answer；
   仅缺 explanation 的题写入 explanation；
   两者皆缺则全写。已有的不覆盖。

【按用户硬要求】图形/文字选项区分，本任务只补 answer/explanation，不动 options。
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

import fitz  # type: ignore[import-not-found]


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data" / "xingce"

EXAMS = {
    "dishi": {
        "pdf_keyword": "地市级",
        "json_suffix": "dishi",
        "total": 130,
    },
    "fushengjia": {
        "pdf_keyword": "副省级",
        "json_suffix": "fushengjia",
        "total": 135,
    },
    "xingzhengzhifa": {
        "pdf_keyword": "行政执法",
        "json_suffix": "xingzhengzhifa",
        "total": 130,
    },
}


def find_pdf(keyword: str) -> Path:
    import glob
    candidates = []
    for p in glob.glob("material/**/2023*行测*.pdf", recursive=True):
        if "国考" not in p and "【国考】" not in p:
            continue
        if "答案" not in p and "解析" not in p:
            continue
        candidates.append(p)
    # 通过字节匹配避免 console 编码差异
    kw_bytes = keyword.encode("utf-8")
    for p in candidates:
        if kw_bytes in p.encode("utf-8"):
            return Path(p)
    raise FileNotFoundError(
        f"keyword bytes={kw_bytes.hex()} 未匹配任何候选 PDF (共 {len(candidates)} 个候选)"
    )


def extract_blocks(pdf_path: Path, total: int) -> dict[int, dict[str, str]]:
    """返回 {qn: {'answer': 'X', 'explanation': '...'}}。"""
    doc = fitz.open(pdf_path)
    text = "\n".join(doc[i].get_text() for i in range(doc.page_count))

    # 找所有题号位置
    # 模式 1: "故正确答案为[A-D]+。N" 这种粘连的
    # 模式 2: "\nN\n" 独立行号
    boundaries: list[tuple[int, int]] = []  # (qn, char_pos_after_marker)

    for m in re.finditer(r"故正确答案为\s*[A-D]+[。.]?(\d{1,3})", text):
        qn = int(m.group(1))
        if 1 <= qn <= total:
            boundaries.append((qn, m.start(1)))

    for m in re.finditer(r"(?:^|\n)(\d{1,3})\n", text):
        qn = int(m.group(1))
        if 1 <= qn <= total:
            boundaries.append((qn, m.start(1)))

    # 去重 + 按位置排序 + 保留单调递增
    boundaries.sort(key=lambda x: x[1])
    seen_qns: set[int] = set()
    cleaned: list[tuple[int, int]] = []
    last_qn = 0
    for qn, pos in boundaries:
        if qn in seen_qns:
            continue
        # 题号必须单调递增（允许跳号场景如 "20" 后直接 "21"）
        if qn < last_qn:
            continue
        seen_qns.add(qn)
        cleaned.append((qn, pos))
        last_qn = qn

    if len(cleaned) < total * 0.95:
        print(
            f"  [WARN] 仅找到 {len(cleaned)}/{total} 个题号边界，可能解析不全",
            file=sys.stderr,
        )

    # 切块 + 抽答案 + 解析
    result: dict[int, dict[str, str]] = {}
    for i, (qn, pos) in enumerate(cleaned):
        # 块从题号字符起，到下一题号开始字符止
        block_end = cleaned[i + 1][1] - 1 if i + 1 < len(cleaned) else len(text)
        # 切掉题号自身那几位（题号是连续数字字符）
        block_start = pos + len(str(qn))
        block = text[block_start:block_end].strip()

        # 答案
        ans_m = re.search(r"故正确答案为\s*([A-D]+)", block)
        answer = ans_m.group(1) if ans_m else ""

        # 解析：保留全文（包括"故正确答案为X"），去除尾部多余空白
        explanation = block.strip()

        result[qn] = {"answer": answer, "explanation": explanation}

    return result


def inject(level: str, blocks: dict[int, dict[str, str]]) -> tuple[int, int, int]:
    """对该卷的 5 模块 JSON 注入。返回 (touched_files, ans_filled, exp_filled)。"""
    suffix = EXAMS[level]["json_suffix"]
    fname_stem = f"national_2023_{suffix}.json"
    touched_files = 0
    ans_filled = 0
    exp_filled = 0

    for module_dir in sorted(DATA.iterdir()):
        if not module_dir.is_dir():
            continue
        path = module_dir / fname_stem
        if not path.exists():
            continue
        questions = json.loads(path.read_text(encoding="utf-8"))
        modified = False
        for q in questions:
            try:
                qn = int(str(q.get("id", "")).split("-")[-1])
            except ValueError:
                continue
            if qn not in blocks:
                continue
            blk = blocks[qn]
            if not q.get("answer") and blk["answer"]:
                q["answer"] = blk["answer"]
                ans_filled += 1
                modified = True
            if not (q.get("explanation") or q.get("analysis")) and blk["explanation"]:
                q["explanation"] = blk["explanation"]
                exp_filled += 1
                modified = True
        if modified:
            path.write_text(
                json.dumps(questions, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            touched_files += 1

    return touched_files, ans_filled, exp_filled


def main() -> None:
    grand_ans = grand_exp = 0
    for level, cfg in EXAMS.items():
        pdf = find_pdf(cfg["pdf_keyword"])
        print(f"=== {level}  PDF: {pdf.name} ===")
        blocks = extract_blocks(pdf, cfg["total"])
        with_ans = sum(1 for b in blocks.values() if b["answer"])
        with_exp = sum(1 for b in blocks.values() if b["explanation"])
        print(f"  抽出 {len(blocks)} 块，含答案 {with_ans}，含解析 {with_exp}")
        files, ans, exp = inject(level, blocks)
        print(f"  写入 {files} 文件，新增 answer {ans} 题，新增 explanation {exp} 题")
        grand_ans += ans
        grand_exp += exp
    print(f"\n合计：answer +{grand_ans} 题，explanation +{grand_exp} 题")


if __name__ == "__main__":
    main()
