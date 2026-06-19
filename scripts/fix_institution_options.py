"""D-4 #7：事业编空选项题从真题 PDF 抽 ABCD 文字。

逻辑：
1. 加载 A/B/C/E 类真题 PDF（已 OCR 兜底过的文本）
2. 切分年份段 + 题号块
3. 对 examKey 中空选项题 fingerprint 匹配 PDF 题号块
4. 从匹配块抽出 A./B./C./D. 选项内容
5. 写回 JSON（保留原 label 顺序）
"""
from __future__ import annotations
import json
import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fix_institution_answers import (  # type: ignore[import-not-found]
    CLASSES, OCR_SKIP_CLASSES, find_pdf, get_pdf_text,
    QN_Q_PAT, cut_year_blocks_with_toc,
)
import fitz  # type: ignore[import-not-found]
fitz.TOOLS.mupdf_display_errors(False)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data" / "xingce"

OPT_PAT = re.compile(r"\b([A-D])\s*[\.．、,，]\s*([^\n]+)")


def extract_options_from_block(block: str) -> dict[str, str]:
    """从题号块（含题干+选项）抽 A/B/C/D 选项内容。"""
    out = {}
    # 找选项段：第一个 "A." 起到选项段尾
    m = re.search(r"\n\s*A\s*[\.．、,，]", block)
    if not m:
        return out
    opt_text = block[m.start():]
    # 切到下一年份/水印/答案标志
    end_pos = len(opt_text)
    next_qn = re.search(r"\n\s*\d{1,3}\s*[\.．、]\s+", opt_text[20:])
    if next_qn:
        end_pos = min(end_pos, next_qn.start() + 20)
    ans_mark = re.search(r"答案[：:]|【\s*答案", opt_text)
    if ans_mark:
        end_pos = min(end_pos, ans_mark.start())
    opt_text = opt_text[:end_pos]
    # 抽 A-D。逐行扫描，每行取首个 "[A-D]．..." 模式
    for line in opt_text.split("\n"):
        line = line.strip()
        m2 = re.match(r"^([A-D])\s*[\.．、,，]\s*(.+)$", line)
        if m2:
            label, content = m2.group(1), m2.group(2).strip()
            # 去水印
            content = re.sub(
                r"·\s*\d+\s*·|公考事业编学习资料加微信\S*|事业单位联考真题|老师微信[：:]\S*|AS\d{3,}",
                "", content,
            ).strip()
            if label not in out and 1 < len(content) < 200:
                out[label] = content
    return out


def build_options_library(use_ocr: bool = True) -> dict[tuple[int, int, int], dict]:
    """对 A/B/C/E 类真题 PDF 切年份+题号 → fingerprint + options。"""
    library: dict[tuple[int, int, int], dict] = {}
    for cls in CLASSES:
        if cls in OCR_SKIP_CLASSES:
            continue
        q_pdf = find_pdf(cls, "question")
        if not q_pdf:
            continue
        text_q = get_pdf_text(q_pdf, use_ocr=use_ocr, cache_key=f"{cls}_q", engine=None)
        doc_q = fitz.open(q_pdf)
        year_q = cut_year_blocks_with_toc(doc_q, text_q)
        doc_q.close()
        qn_marks = [(int(m.group(1)), m.start(), m.end()) for m in QN_Q_PAT.finditer(text_q)]
        qn_marks.sort(key=lambda x: x[1])
        for i, (qn, s, e) in enumerate(qn_marks):
            if not (1 <= qn <= 200):
                continue
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
            opts = extract_options_from_block(block)
            if len(opts) < 2:
                continue
            stem_match = re.search(r"\n\s*A\s*[\.．、,，]", block)
            stem = block[:stem_match.start()] if stem_match else block[:300]
            fingerprint = re.sub(r"\s", "", stem)[:80]
            fingerprint = fingerprint.replace("：", "∶").replace(":", "∶")
            if len(fingerprint) >= 4:
                key = (y, mo, qn)
                if key not in library:
                    library[key] = {
                        "class": cls, "qn": qn, "year": y, "month": mo,
                        "fingerprint": fingerprint, "options": opts,
                    }
    return library


def normalize_content(text: str) -> str:
    WATERMARK_PAT = re.compile(
        r"(?:·\s*\d+\s*·|公考事业编学习资料加微信\S*|事业单位联考真题|老师微信[：:]\S*|AS\d{3,})"
    )
    text = WATERMARK_PAT.sub("", text)
    text = text.replace("：", "∶").replace(":", "∶")
    return re.sub(r"\s", "", text)


def main() -> None:
    print("构建事业编选项库...", flush=True)
    library = build_options_library(use_ocr=True)
    print(f"库 {len(library)} 题（A/B/C/E）", flush=True)

    grand_filled = 0
    for path in sorted(DATA.glob("*/institution_*.json")):
        questions = json.loads(path.read_text(encoding="utf-8"))
        modified = False
        ek_filled = 0
        for q in questions:
            opts = q.get("options", [])
            is_empty = (not opts) or all(
                not (o.get("content", "").strip() if isinstance(o, dict) else "")
                for o in opts
            )
            if not is_empty:
                continue
            content = q.get("content", "")
            fp = normalize_content(content)[:25]
            if len(fp) < 6:
                continue
            entry = None
            for e in library.values():
                if fp in e["fingerprint"]:
                    entry = e
                    break
            if not entry:
                continue
            new_opts = entry["options"]
            if len(new_opts) < 2:
                continue
            # 写回 options
            if not opts:
                q["options"] = [
                    {"label": l, "content": new_opts[l]}
                    for l in sorted(new_opts.keys())
                ]
            else:
                for o in opts:
                    if isinstance(o, dict):
                        lab = o.get("label")
                        if lab in new_opts:
                            o["content"] = new_opts[lab]
            ek_filled += 1
            modified = True
        if modified:
            path.write_text(
                json.dumps(questions, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            grand_filled += ek_filled
            print(f"  {path.parent.name}/{path.stem}: +{ek_filled} 题填了选项")

    print(f"\n合计: 填了 {grand_filled} 题选项")


if __name__ == "__main__":
    main()
