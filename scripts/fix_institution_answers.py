#!/usr/bin/env python3
"""D-3 #8 事业编 19 卷答案注入：5 类×真题 PDF + 答案 PDF 联合注入。

PDF 结构：
  - 真题 PDF: 9 套合订（按年份倒序），每套 100 题，题号 "N. " 格式
  - 答案 PDF: 同结构，"N.【答案】X【解析】..." 格式

策略：
1. 加载 5 类真题 PDF + 答案 PDF
2. 真题 PDF 切年份段（"YYYY 年X月全国事业单位联考"）+ 题号块
3. 答案 PDF 同步切年份段 + 题号块
4. 同一 (类, 年月, 题号) 联合：题干 fingerprint → 答案
5. 对 examKey 缺 ans 的题，按题干前 25 字（去空格）做指纹匹配 PDF 库
6. 注入答案 + 解析（不覆写已有）
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
import numpy as np  # type: ignore[import-not-found]
from PIL import Image  # type: ignore[import-not-found]

fitz.TOOLS.mupdf_display_errors(False)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data" / "xingce"
OCR_CACHE_DIR = ROOT / "archive" / "reports"
SCALE = 2.0  # 渲染倍率（300 DPI 等效）

CLASSES = ["a", "b", "c", "d", "e"]
# D 类无对应 JSON，且真题 PDF 几乎全 CID 乱码，OCR 也救不出指纹匹配，跳过节约时间
OCR_SKIP_CLASSES = {"d"}


def find_pdf(class_letter: str, kind: str) -> Path | None:
    """kind: 'question' 或 'answer'"""
    suffix = "笔试真题答案解析.pdf" if kind == "answer" else "笔试真题.pdf"
    base = f"material/【事业编】事业单位联考历年真题/{class_letter.upper()}类/职测"
    for p in glob.glob(f"{base}/*{suffix}"):
        return Path(p)
    return None


YEAR_PAT = re.compile(
    r"(?:^|\n)\s*(20(?:18|19|20|21|22|23|24))\s*年\s*(\d{1,2})\s*月.*?事业单位联考"
)
QN_Q_PAT = re.compile(r"(?:^|\n)\s*(\d{1,3})[\.．]\s+")  # 真题: "1. ..."
QN_A_PAT = re.compile(r"(?:^|\n)\s*(\d{1,3})[\.．]\s*【\s*答案\s*】\s*([A-D]+)")


def cut_year_blocks(text: str) -> list[tuple[int, int, int]]:
    """返回 [(year, month, start_pos)] 排序。"""
    marks = [
        (int(m.group(1)), int(m.group(2)), m.start())
        for m in YEAR_PAT.finditer(text)
    ]
    marks.sort(key=lambda x: x[2])
    return marks


def cut_year_blocks_with_toc(doc: fitz.Document, text: str) -> list[tuple[int, int, int]]:
    """用 PDF TOC 标题做年份切分（更可靠，PDF 开头年份标题可能不在文字层）。

    fallback 到 YEAR_PAT 如果 TOC 不可用。
    """
    toc = doc.get_toc()
    if not toc:
        return cut_year_blocks(text)
    # TOC 项: [level, title, page]
    page_starts = []
    for off in range(doc.page_count):
        # 累计每页起始字符位置
        cum = sum(len(doc[i].get_text()) + 1 for i in range(off))  # +1 for \n
        page_starts.append(cum)

    marks: list[tuple[int, int, int]] = []
    pat = re.compile(r"(20(?:18|19|20|21|22|23|24))\s*年\s*(\d{1,2})\s*月")
    for level, title, page in toc:
        if level != 1:
            continue
        m = pat.search(title)
        if not m:
            continue
        y, mo = int(m.group(1)), int(m.group(2))
        # page 是 1-based
        idx = max(0, page - 1)
        if idx >= len(page_starts):
            continue
        marks.append((y, mo, page_starts[idx]))
    marks.sort(key=lambda x: x[2])
    return marks if len(marks) >= 3 else cut_year_blocks(text)


def _page_text_quality(text: str) -> str:
    """判定文字层质量: 'ok' / 'empty' / 'cid_garbage'。"""
    cn = sum(1 for c in text if 0x4E00 <= ord(c) <= 0x9FFF)
    if len(text) < 50:
        return "empty"
    if cn < 50:
        return "cid_garbage"
    return "ok"


def _ocr_one_page(doc: fitz.Document, page_idx: int, engine) -> str:
    page = doc[page_idx]
    mat = fitz.Matrix(SCALE, SCALE)
    pix = page.get_pixmap(matrix=mat)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    result = engine(np.array(img))
    if hasattr(result, "txts") and result.txts is not None:
        return "\n".join(result.txts)
    return ""


def get_pdf_text(
    pdf_path: Path,
    use_ocr: bool = False,
    cache_key: str | None = None,
    engine=None,
) -> str:
    """读 PDF 全文。use_ocr=True 时空白/CID 乱码页走 OCR 兜底，结果缓存。"""
    doc = fitz.open(pdf_path)
    if not use_ocr:
        text = "\n".join(doc[i].get_text() for i in range(doc.page_count))
        doc.close()
        return text

    cache_path = OCR_CACHE_DIR / f"ocr_institution_{cache_key}.txt" if cache_key else None
    if cache_path and cache_path.exists() and cache_path.stat().st_size > 1000:
        text = cache_path.read_text(encoding="utf-8")
        doc.close()
        return text

    pieces: list[str] = []
    ocr_pages = 0
    t0 = time.time()
    for i in range(doc.page_count):
        layer = doc[i].get_text()
        q = _page_text_quality(layer)
        if q == "ok":
            pieces.append(layer)
            continue
        if engine is None:
            pieces.append(layer)
            continue
        ocr_text = _ocr_one_page(doc, i, engine)
        pieces.append(ocr_text)
        ocr_pages += 1
        if ocr_pages % 10 == 0:
            print(f"    [{cache_key}] OCR {ocr_pages} 页 / {time.time() - t0:.0f}s", flush=True)
    doc.close()
    text = "\n".join(pieces)
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(text, encoding="utf-8")
        print(
            f"    [{cache_key}] OCR 共 {ocr_pages} 页 / {time.time() - t0:.0f}s "
            f"→ 缓存 {cache_path.name} ({len(text)} 字)",
            flush=True,
        )
    return text


def build_library(class_letter: str, use_ocr: bool = False, engine=None) -> dict[tuple[int, int, int], dict]:
    """返回 {(class_letter_idx, year, month, qn): {fingerprint, answer, explanation}}。

    仅返回同时在真题 + 答案 PDF 中存在的题。
    """
    q_pdf = find_pdf(class_letter, "question")
    a_pdf = find_pdf(class_letter, "answer")
    if not q_pdf or not a_pdf:
        return {}
    do_ocr = use_ocr and class_letter not in OCR_SKIP_CLASSES
    text_q = get_pdf_text(q_pdf, use_ocr=do_ocr, cache_key=f"{class_letter}_q", engine=engine)
    text_a = get_pdf_text(a_pdf, use_ocr=do_ocr, cache_key=f"{class_letter}_a", engine=engine)
    doc_q = fitz.open(q_pdf)
    year_q = cut_year_blocks_with_toc(doc_q, text_q)
    doc_q.close()
    doc_a = fitz.open(a_pdf)
    year_a = cut_year_blocks_with_toc(doc_a, text_a)
    doc_a.close()

    # 真题切块: (year, month, qn) → fingerprint
    real_q: dict[tuple[int, int, int], str] = {}
    qn_marks = [(int(m.group(1)), m.start(), m.end()) for m in QN_Q_PAT.finditer(text_q)]
    qn_marks.sort(key=lambda x: x[1])
    for i, (qn, s, e) in enumerate(qn_marks):
        if not (1 <= qn <= 200):
            continue
        # 哪个年份段
        y = mo = 0
        for yy, mm, ys in year_q:
            if ys <= s:
                y, mo = yy, mm
            else:
                break
        if y == 0:
            continue
        block_end = qn_marks[i + 1][1] if i + 1 < len(qn_marks) else len(text_q)
        block = text_q[e:block_end]
        # 选项前为题干（找 "A.", "A、", "A " 等）
        m_opt = re.search(r"\n\s*A\s*[\.．、,，]\s+", block)
        stem = block[:m_opt.start()] if m_opt else block[:300]
        # D-4 #6: 全角/半角冒号统一为 ∶（类比推理 'A：B' / 'A:B' / 'A∶B' 同义）
        fp_raw = re.sub(r"\s", "", stem)[:80]
        fingerprint = fp_raw.replace("：", "∶").replace(":", "∶")
        if len(fingerprint) >= 4 and (y, mo, qn) not in real_q:
            real_q[(y, mo, qn)] = fingerprint

    # 答案切块: (year, month, qn) → (answer, explanation)
    real_a: dict[tuple[int, int, int], tuple[str, str]] = {}
    qn_a_marks = [
        (int(m.group(1)), m.group(2), m.start(), m.end())
        for m in QN_A_PAT.finditer(text_a)
    ]
    qn_a_marks.sort(key=lambda x: x[2])
    for i, (qn, ans, s, e) in enumerate(qn_a_marks):
        if not (1 <= qn <= 200):
            continue
        y = mo = 0
        for yy, mm, ys in year_a:
            if ys <= s:
                y, mo = yy, mm
            else:
                break
        if y == 0:
            continue
        block_end = qn_a_marks[i + 1][2] if i + 1 < len(qn_a_marks) else len(text_a)
        explanation = text_a[e:block_end].strip()
        if (y, mo, qn) not in real_a:
            real_a[(y, mo, qn)] = (ans, explanation)

    # 合并
    library: dict[tuple[int, int, int], dict] = {}
    for key in real_q:
        if key in real_a:
            ans, exp = real_a[key]
            library[key] = {
                "class": class_letter,
                "year": key[0],
                "month": key[1],
                "qn": key[2],
                "fingerprint": real_q[key],
                "answer": ans,
                "explanation": exp,
            }
    return library


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exam", help="只处理指定 examKey")
    ap.add_argument("--dry", action="store_true", help="不写入")
    ap.add_argument("--use-ocr", action="store_true", help="对空白/CID 乱码页走 GPU OCR 兜底")
    args = ap.parse_args()

    engine = None
    if args.use_ocr:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from ocr_engine import make_engine  # type: ignore[import-not-found]
        engine = make_engine()

    print("构建 5 类 PDF 库...", flush=True)
    library: list[dict] = []
    by_class_count = {}
    for cls in CLASSES:
        lib = build_library(cls, use_ocr=args.use_ocr, engine=engine)
        by_class_count[cls] = len(lib)
        library.extend(lib.values())
        print(f"  [{cls}] 真题+答案 共 {len(lib)} 题", flush=True)
    print(f"总库: {len(library)} 题")

    pattern = "*" if not args.exam else args.exam
    grand_ans = grand_exp = 0
    by_exam: dict[str, tuple[int, int]] = {}
    matched_total = 0
    unmatched_total = 0

    # D-4 #5: 水印清洗 + 类比推理短题专属匹配。content 里"公考事业编学习资料加微信AS73982"
    # / "事业单位联考真题" / "老师微信：AS73982" / "· 18 ·" 等水印干扰 fingerprint。
    WATERMARK_PAT = re.compile(
        r"(?:·\s*\d+\s*·|公考事业编学习资料加微信\S*|事业单位联考真题|老师微信[：:]\S*|AS\d{3,})"
    )

    def normalize_content(text: str) -> str:
        text = WATERMARK_PAT.sub("", text)
        # D-4 #6: 全角/半角冒号统一为 '∶'（类比推理题 'A：B' / 'A:B' / 'A∶B' 同义）
        text = text.replace("：", "∶").replace(":", "∶")
        return re.sub(r"\s", "", text)

    for path in sorted(glob.glob(str(DATA / "*" / f"institution_{pattern}.json"))):
        questions = json.loads(Path(path).read_text(encoding="utf-8"))
        modified = False
        ek = Path(path).stem
        ans_filled = exp_filled = 0
        for q in questions:
            if q.get("answer") and (q.get("explanation") or q.get("analysis")):
                continue
            content = q.get("content", "")
            # D-4 #5: 用清洗后的 content 做指纹，并把门槛降到 4（救类比推理 4-7 字短题）
            fp_full = normalize_content(content)
            fp = fp_full[:25]
            if len(fp) < 4:
                continue
            # 在库里找匹配
            entry = None
            for e in library:
                if fp in e["fingerprint"]:
                    entry = e
                    break
            if not entry:
                # 短指纹兜底
                fp_short = fp[:15]
                for e in library:
                    if fp_short in e["fingerprint"]:
                        entry = e
                        break
            if not entry:
                unmatched_total += 1
                continue
            matched_total += 1
            if not q.get("answer") and entry["answer"]:
                q["answer"] = entry["answer"]
                ans_filled += 1
                modified = True
            if not (q.get("explanation") or q.get("analysis")) and entry["explanation"]:
                q["explanation"] = entry["explanation"]
                exp_filled += 1
                modified = True
        if modified and not args.dry:
            Path(path).write_text(
                json.dumps(questions, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        if ans_filled or exp_filled:
            cur = by_exam.get(ek, (0, 0))
            by_exam[ek] = (cur[0] + ans_filled, cur[1] + exp_filled)
            grand_ans += ans_filled
            grand_exp += exp_filled

    mode = "DRY" if args.dry else "WRITE"
    print(f"\n[{mode}] 合计: +{grand_ans} ans, +{grand_exp} exp")
    print(f"匹配: {matched_total}, 未匹配: {unmatched_total}")
    for ek, (a, e) in sorted(by_exam.items()):
        print(f"  {ek:30} +{a} ans, +{e} exp")


if __name__ == "__main__":
    main()
