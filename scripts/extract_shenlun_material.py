"""
D-18a P2e-2 申论 material PDF 文字层抽取（PoC）

基于 fitz get_text 抽申论 PDF 的"给定资料 N" 段。本脚本是骨架 + PoC，
全 paperKey 跑批留 D-18b 数据救援专项（按 D-17e 经验 30~50 paperKey 全跑
需要数小时～数天）。

设计原则：
- 不一次性全 PDF 抽（PDF 长 + 跨页 + 多卷，错位风险高）
- 抽出后人工抽样验证再写回 JSON
- 写回时加 meta.materialRescuedBy='D18a-pdf-textlayer'

PoC：跑 national_shenlun_2024_dishi（地市级）一卷，看抽出来的"给定资料"
段是否结构完整。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import fitz  # type: ignore[import]
except ImportError:
    print("⚠️  需要 PyMuPDF：pip install pymupdf", file=sys.stderr)
    sys.exit(1)


# "给定资料 1" / "材料一" / "资料 1" 等起手词
MATERIAL_HEADER_RE = re.compile(
    r"(?:给定资料|材料|资料)\s*[一二三四五六七八九十1234567890]+\s*[：:.、]?",
)

# 题目起手词（界定 material 结束）
QUESTION_HEADER_RE = re.compile(
    r"(?:第[一二三四五六七八九十]+题|^一[、.]|^二[、.]|^三[、.]|^四[、.]|^五[、.])"
)


def extract_material(pdf_path: Path) -> dict:
    """从 PDF 抽材料段。返回 {pages: int, raw_text_head: str, material_segments: [{header, body_head}]}"""
    doc = fitz.open(pdf_path)
    pages = len(doc)
    full_text = "\n".join(doc[i].get_text("text") for i in range(pages))
    doc.close()

    # 找所有 "给定资料 N" 起手位置
    matches = list(MATERIAL_HEADER_RE.finditer(full_text))
    segments: list[dict] = []
    for i, m in enumerate(matches):
        start = m.start()
        # 段尾：下一个材料起手 / 题目起手 / 文末
        next_material = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        question_m = QUESTION_HEADER_RE.search(full_text, m.end())
        next_question = question_m.start() if question_m else len(full_text)
        end = min(next_material, next_question)
        body = full_text[m.end() : end].strip()
        segments.append({
            "header": m.group(0),
            "bodyLen": len(body),
            "bodyHead": body[:200],
            "startOffset": start,
            "endOffset": end,
        })

    return {
        "pages": pages,
        "rawTextLen": len(full_text),
        "rawTextHead": full_text[:300],
        "materialSegments": segments,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "pdf",
        nargs="?",
        default="material/【国考】2000-2025真题pdf/2000-2025国考申论PDF/2024年国考申论真题（地市级）及参考答案.pdf",
        help="PDF 路径（默认 PoC 用 2024 国考地市级）",
    )
    args = parser.parse_args()
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"PDF 不存在：{pdf_path}")

    result = extract_material(pdf_path)
    print(f"PDF: {pdf_path.name}")
    print(f"  Pages: {result['pages']}, Total text chars: {result['rawTextLen']}")
    print(f"  Raw text head: {result['rawTextHead'][:200]!r}")
    print(f"  Material segments: {len(result['materialSegments'])}")
    for i, seg in enumerate(result["materialSegments"]):
        print(f"    {i + 1}. '{seg['header']}' bodyLen={seg['bodyLen']}")
        print(f"       head: {seg['bodyHead'][:100]!r}")


if __name__ == "__main__":
    main()
