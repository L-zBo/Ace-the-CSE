#!/usr/bin/env python3
"""D-2: 省考扫描版 PDF OCR 抽答案 + 解析。

复用 fix_2021fsj_ocr.py 思路 + fix_provincial_answers.py 多 regex 兼容。
按命令行 --exam 单独跑某卷，或 --all 全库扫描版批量。
"""
from __future__ import annotations
import argparse
import glob
import io
import json
import re
import sys
import time
from pathlib import Path

import fitz  # type: ignore[import-not-found]
import numpy as np
from PIL import Image
from rapidocr import RapidOCR  # type: ignore[import-not-found]


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data" / "xingce"
SCALE = 2.0

# 直接复用 fix_provincial_answers.py 的 regex
sys.path.insert(0, str(ROOT / "scripts"))
from fix_provincial_answers import (  # type: ignore[import-not-found]
    HEAD_OLD, HEAD_NL, HEAD_DOT, HEAD_BRACKET, HEAD_DI_TI, HEAD_JIEXI,
    ANS_OLD, ANS_NEW, ANS_PAREN, ANS_BARE,
    PROVINCE_MAP, find_provincial_pdf,
)
from ocr_engine import make_engine  # type: ignore[import-not-found]


def ocr_pdf(pdf_path: Path, engine: RapidOCR) -> str:
    doc = fitz.open(pdf_path)
    pieces: list[str] = []
    for pi in range(doc.page_count):
        t0 = time.time()
        page = doc[pi]
        text_layer = page.get_text()
        if len(text_layer) > 200:
            pieces.append(text_layer)
            continue
        mat = fitz.Matrix(SCALE, SCALE)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        result = engine(np.array(img))
        if hasattr(result, "txts") and result.txts is not None:
            texts = list(result.txts)
        else:
            texts = []
        page_text = "\n".join(texts)
        pieces.append(page_text)
        elapsed = time.time() - t0
        print(f"    page {pi + 1}/{doc.page_count}: OCR {len(texts)} 行 / {len(page_text)} 字 / {elapsed:.1f}s", flush=True)
    return "\n".join(pieces)


def extract_blocks(text: str, total: int) -> dict[int, dict[str, str]]:
    boundaries: list[tuple[int, int]] = []
    for rgx in (HEAD_OLD, HEAD_NL, HEAD_DOT, HEAD_BRACKET, HEAD_DI_TI, HEAD_JIEXI):
        for m in rgx.finditer(text):
            qn = int(m.group(1))
            if 1 <= qn <= total:
                boundaries.append((qn, m.start(1)))

    boundaries.sort(key=lambda x: x[1])
    seen: set[int] = set()
    cleaned: list[tuple[int, int]] = []
    last_qn = 0
    for qn, pos in boundaries:
        if qn in seen or qn < last_qn:
            continue
        seen.add(qn)
        cleaned.append((qn, pos))
        last_qn = qn

    blocks: dict[int, dict[str, str]] = {}
    for i, (qn, pos) in enumerate(cleaned):
        end = cleaned[i + 1][1] - 1 if i + 1 < len(cleaned) else len(text)
        block_start = pos + len(str(qn))
        block = text[block_start:end].strip()
        ans_m = (
            ANS_OLD.search(block)
            or ANS_NEW.search(block)
            or ANS_PAREN.search(block)
            or ANS_BARE.search(block)
        )
        answer = ans_m.group(1) if ans_m else ""
        blocks[qn] = {"answer": answer, "explanation": block.strip()}
    return blocks


def inject(exam_key: str, blocks: dict[int, dict[str, str]]) -> tuple[int, int]:
    fname = f"{exam_key}.json"
    ans_filled = exp_filled = 0
    for module_dir in sorted(DATA.iterdir()):
        if not module_dir.is_dir():
            continue
        path = module_dir / fname
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
    return ans_filled, exp_filled


def total_qs(exam_key: str) -> int:
    n = 0
    for p in glob.glob(str(DATA / "*" / f"{exam_key}.json")):
        n += len(json.loads(Path(p).read_text(encoding="utf-8")))
    return n


def list_ocr_targets() -> list[tuple[str, Path]]:
    """找所有需要 OCR 的省考卷（文字层 < 5000 字符）"""
    seen: set[str] = set()
    targets: list[tuple[str, Path]] = []
    for p in glob.glob(str(DATA / "*" / "provincial_*.json")):
        name = Path(p).stem
        if name in seen:
            continue
        seen.add(name)
        # 看缺口
        no_ans = 0
        for pp in glob.glob(str(DATA / "*" / f"{name}.json")):
            for q in json.loads(Path(pp).read_text(encoding="utf-8")):
                if not q.get("answer"):
                    no_ans += 1
        if no_ans == 0:
            continue
        # 找 PDF
        parts = name.split("_")
        if len(parts) < 3:
            continue
        province, year = parts[1], parts[2]
        pdf = find_provincial_pdf(province, year)
        if not pdf:
            continue
        # 文字层
        doc = fitz.open(pdf)
        chars = sum(len(doc[i].get_text()) for i in range(doc.page_count))
        if chars < 5000:
            targets.append((name, pdf))
    return targets


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exam", help="单卷 examKey")
    ap.add_argument("--all", action="store_true", help="跑全部 OCR 卷")
    ap.add_argument("--list", action="store_true", help="只列出 OCR 卷不跑")
    ap.add_argument("--cpu", action="store_true", help="强制走 CPU（默认 GPU）")
    args = ap.parse_args()

    targets = list_ocr_targets()
    if args.list:
        for name, pdf in targets:
            print(f"  {name}: {pdf}")
        return

    if args.exam:
        targets = [t for t in targets if t[0] == args.exam]

    if not targets:
        print("无 OCR 卷")
        return

    print(f"将处理 {len(targets)} 卷")
    engine = make_engine(use_gpu=not args.cpu)
    grand_ans = grand_exp = 0
    for name, pdf in targets:
        print(f"\n=== {name} ===")
        print(f"  PDF: {pdf.name}")
        t0 = time.time()
        text = ocr_pdf(pdf, engine)
        print(f"  OCR 总耗时 {time.time() - t0:.1f}s, 全文 {len(text)} 字")
        # 落档
        out_txt = ROOT / "archive" / "reports" / f"ocr_{name}.txt"
        out_txt.parent.mkdir(parents=True, exist_ok=True)
        out_txt.write_text(text, encoding="utf-8")
        # 切块 + 注入
        total = total_qs(name)
        blocks = extract_blocks(text, total)
        ans, exp = inject(name, blocks)
        print(f"  → 切 {len(blocks)}/{total} 块, +{ans} ans, +{exp} exp")
        grand_ans += ans
        grand_exp += exp

    print(f"\n合计: +{grand_ans} answer, +{grand_exp} explanation")


if __name__ == "__main__":
    main()
