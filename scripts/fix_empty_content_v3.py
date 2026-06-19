"""D-6 #6：空 content 救援 v3 — 覆盖独立行题号 + 中嵌页码 + 事业编。

D-6 #2 (fix_empty_content_ocr) 用的 ABCD_BLOCK_RE 在以下卷失效：
- 浙江/北京/海南/天津 等用「独立行纯数字」做题号（无 N、 标点）
- D 选项 lookhead `\n\s*\d` 太宽松，让 D group 跨题贪婪吞下一题 ABCD
- 选项之间嵌入页码（如 q15 B 和 C 之间夹一行 `4`）触发 [\s,，]+ 失败
- 短选项（"1项"、"2项"）触及 .{3,150}? 长度下限被拒

本脚本：
1. ABCD_BLOCK_RE_V3 紧化 D lookhead 为「独立行 1-3 位数字」
2. 选项之间允许跨页页码（\n\d{1,3}\n）作为分隔
3. 选项最短 1 字（兼容极短选项）
4. 题号识别同时支持「独立行数字」和「N、」，按 expected_qns 优先
5. 走真题 OCR 缓存（GPU），覆盖事业编
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
fitz.TOOLS.mupdf_display_errors(False)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fix_provincial_answers import PROVINCE_MAP  # type: ignore[import-not-found]


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data" / "xingce"
OCR_CACHE_DIR = ROOT / "archive" / "reports"


# v3: STRICT 模式 — 每个选项必须在单行内（不含 \n），选项间允许跨页页码独立行
# 这样可以避免上一题 D 选项贪婪吞下一题 ABCD 的错配
# 取舍：跨行长选项（资料分析多行）救不到，但错配率为 0
ABCD_BLOCK_RE_V3 = re.compile(
    r"(?:^|\n)\s*A\s*[\.．、,，]\s*([^\n]{1,250})\n"
    r"(?:\s*\d{1,3}\s*\n|\s*\n)*"
    r"\s*B\s*[\.．、,，]\s*([^\n]{1,250})\n"
    r"(?:\s*\d{1,3}\s*\n|\s*\n)*"
    r"\s*C\s*[\.．、,，]\s*([^\n]{1,250})\n"
    r"(?:\s*\d{1,3}\s*\n|\s*\n)*"
    r"\s*D\s*[\.．、,，]\s*([^\n]{1,250})(?=\n|\Z)"
)

QN_PATS_V3 = [
    (r"(?:^|\n)\s*(\d{1,3})\s*\n", "standalone"),
    (r"(?:^|\n)\s*(\d{1,3})\s*[、.．,]", "dot"),
    (r"第\s*(\d{1,3})\s*题", "dt"),
    (r"【\s*(?:解析|题目)?\s*(\d{1,3})\s*", "bracket"),
]

WATERMARK_PAT = re.compile(
    r"·\s*\d+\s*·|公考事业编学习资料加微信\S*|事业单位联考真题|"
    r"老师微信[：:]\S*|AS\d{3,}|TB[：:]\s*Seeyee\S*"
)


def cut_blocks_v3(text: str, expected_qns: set[int] | None = None) -> dict[int, dict]:
    """切块 v3：返回 {qn: {stem, options}}。"""
    blocks_raw = []
    for m in ABCD_BLOCK_RE_V3.finditer(text):
        blocks_raw.append({
            "abcd_start": m.start(),
            "abcd_end": m.end(),
            "options": {
                "A": m.group(1).strip(),
                "B": m.group(2).strip(),
                "C": m.group(3).strip(),
                "D": m.group(4).strip(),
            },
        })
    if not blocks_raw:
        return {}

    out: dict[int, dict] = {}
    used_qns: set[int] = set()
    for i, b in enumerate(blocks_raw):
        prev_end = blocks_raw[i - 1]["abcd_end"] if i > 0 else 0
        stem_region = text[prev_end:b["abcd_start"]]

        # 题号识别：收候选 → 优先 expected_qns
        qn = None
        qn_pos = None
        candidates: list[tuple[int, int]] = []
        for pat, _ in QN_PATS_V3:
            for m in re.finditer(pat, stem_region):
                cand = int(m.group(1))
                if 1 <= cand <= 200 and cand not in used_qns:
                    candidates.append((cand, m.start()))
        if not candidates:
            continue
        # 优先 expected_qns 中的；同样优先时取 stem_region 末尾最近的（更稳）
        if expected_qns:
            exp_in = [c for c in candidates if c[0] in expected_qns]
            if exp_in:
                # 取离 abcd_start 最近的（即 pos 最大的）
                qn, qn_pos = max(exp_in, key=lambda x: x[1])
        if qn is None:
            qn, qn_pos = max(candidates, key=lambda x: x[1])

        used_qns.add(qn)

        # 题干提取
        if qn_pos is not None:
            stem_before = stem_region[:qn_pos].strip()
            line_end = stem_region.find("\n", qn_pos + len(str(qn)))
            stem_after = stem_region[line_end:].strip() if line_end >= 0 else ""
            if len(stem_after) > 8:
                stem = stem_after
            else:
                stem = stem_before
        else:
            stem = stem_region.strip()

        stem = WATERMARK_PAT.sub("", stem).strip()
        # 砍开头光秃 ABCD 残留（上一题图形选项空）
        stem = re.sub(
            r"^(?:[A-D]\s*[\.．、,，]\s*[^\n]{0,30}\n\s*){1,5}", "", stem
        ).strip()
        # 砍开头与本题号匹配的回声（不能砍任意数字开头，因为题干可能以"8.5 公里"起头）
        stem = re.sub(rf"^\s*{qn}\s*[、.．,]\s*", "", stem).strip()
        stem = re.sub(rf"^\s*{qn}\s*\n", "", stem).strip()
        # 砍页眉
        stem = re.sub(
            r"第\s*\d+\s*页\s*[，,]\s*共\s*\d+\s*页", "", stem
        ).strip()
        # 砍标题/章节头（"三. 数量关系：在这部分..."），仅匹配明显是题型说明的
        stem = re.sub(
            r"^\s*[一二三四五六七八九十]+\s*[\.．、]\s*"
            r"[^\n]*?[（(](?:共?\s*\d+\s*题|本部分)[^\n]*?[:：]\s*\n?",
            "", stem,
        ).strip()
        stem = re.sub(
            r"^\s*[一二三四五六七八九十]+\s*[\.．、]\s*"
            r"(?:数量关系|资料分析|言语理解|判断推理|常识判断)\s*[:：][^\n]*\n",
            "", stem,
        ).strip()
        if len(stem) < 6 or len(stem) > 1500:
            continue
        # stem 头部 30 字必须含汉字（拒数列残缺、纯英数污染）
        if not re.search(r"[一-鿿]", stem[:30]):
            continue
        # 校验：stem 不能包含完整 ABCD 序列（说明吞了下一题）
        if re.search(
            r"[A-D]\s*[\.．、]\s*[^\n]{1,40}\n\s*[A-D]\s*[\.．、]\s*[^\n]{1,40}",
            stem,
        ):
            continue
        # 校验：stem 不能含独立行题号 + ABCD 起头（错配上一题）
        if re.search(r"\n\s*\d{1,3}\s*\n\s*[A-D]\s*[\.．、]", stem):
            continue
        # 校验：stem 必须能在原文中以题号附近窗口找到（防错配）
        # 题号可能在 stem 之前（行测主体）或之后（资料分析）
        head = stem[:18].replace(" ", "").replace("\n", "")
        if len(head) >= 8:
            text_packed = re.sub(r"\s", "", text)
            ok = False
            for m in re.finditer(re.escape(head), text_packed):
                s = max(0, m.start() - 600)
                e = min(len(text_packed), m.end() + 600)
                win = text_packed[s:e]
                # 题号格式：N、 / N. / 独立 N
                if (
                    re.search(rf"(?<!\d){qn}[、.．,]", win)
                    or re.search(rf"(?<!\d){qn}(?!\d)", win)
                ):
                    ok = True
                    break
            if not ok:
                continue

        # 清选项尾巴（防贪婪吞下一题）
        cleaned = {}
        for k, v in b["options"].items():
            for tail in (
                r"\n\s*\d{1,3}\s*\n",
                r"\n\s*第[一二三四五六七八九十]+\s*部分",
                r"\n\s*[（\(]\s*材料",
                r"\n\s*[一二三四五六七八九十]+\s*、",
            ):
                m_t = re.search(tail, v)
                if m_t:
                    v = v[:m_t.start()].strip()
                    break
            cleaned[k] = v.strip()

        out[qn] = {"stem": stem, "options": cleaned}
    return out


def gather_empty_examkeys() -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    for p in DATA.glob("*/*.json"):
        for q in json.loads(p.read_text(encoding="utf-8")):
            if not (q.get("content") or "").strip():
                ek = p.stem
                qn = int(str(q.get("id", "")).split("-")[-1])
                if qn > 0:
                    out.setdefault(ek, []).append(qn)
    return out


def find_question_pdf_provincial(province: str, year: str, region: str = "") -> Path | None:
    cn = PROVINCE_MAP.get(province)
    if not cn:
        return None
    cn_b = cn.encode("utf-8")
    year_b = year.encode("utf-8")
    region_b = region.encode("utf-8") if region else b""
    candidates: list[str] = []
    for p in glob.glob("material/**/*.pdf", recursive=True):
        if "/题目/" not in p.replace("\\", "/"):
            continue
        if "省考" not in p:
            continue
        if "行测" not in p:
            continue
        pb = p.encode("utf-8")
        if year_b not in pb:
            continue
        if cn_b not in pb:
            continue
        if region_b and region_b not in pb:
            continue
        candidates.append(p)
    return Path(candidates[0]) if candidates else None


def find_question_pdf_institution(year: str, code: str = "") -> Path | None:
    """事业编：material/【事业】.../年/类别真题/题目/*.pdf"""
    year_b = year.encode("utf-8")
    code_upper = code.upper()
    candidates: list[str] = []
    for p in glob.glob("material/**/*.pdf", recursive=True):
        if "事业" not in p:
            continue
        p_norm = p.replace("\\", "/")
        if "/题目/" not in p_norm and "题目" not in p_norm:
            continue
        pb = p.encode("utf-8")
        if year_b not in pb:
            continue
        if code_upper and (f"{code_upper}类" not in p) and (f"（{code_upper}）" not in p):
            continue
        candidates.append(p)
    return Path(candidates[0]) if candidates else None


def get_pdf_text(pdf: Path, ek: str, engine=None) -> str:
    """文字层 ≥ 5000 字直接用，否则用 OCR 缓存（如有）或新 OCR。"""
    cache = OCR_CACHE_DIR / f"ocr_{ek}_question.txt"
    if cache.exists() and cache.stat().st_size > 1000:
        return cache.read_text(encoding="utf-8")
    doc = fitz.open(pdf)
    layer = "\n".join(doc[i].get_text() for i in range(doc.page_count))
    doc.close()
    if len(layer) >= 5000:
        return layer
    if engine is None:
        return layer
    import numpy as np  # type: ignore[import-not-found]
    from PIL import Image  # type: ignore[import-not-found]
    doc = fitz.open(pdf)
    pieces = []
    t0 = time.time()
    for i in range(doc.page_count):
        page = doc[i]
        sub = page.get_text()
        cn = sum(1 for c in sub if 0x4E00 <= ord(c) <= 0x9FFF)
        if cn > 50:
            pieces.append(sub)
            continue
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        res = engine(np.array(img))
        txts = list(res.txts) if (hasattr(res, "txts") and res.txts) else []
        pieces.append("\n".join(txts))
    doc.close()
    text = "\n".join(pieces)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(text, encoding="utf-8")
    print(f"    [{ek}] OCR {time.time()-t0:.0f}s", flush=True)
    return text


def fix(apply: bool, exam: str | None = None, verbose: bool = False) -> None:
    targets = gather_empty_examkeys()
    if exam:
        targets = {exam: targets.get(exam, [])}
    print(f"待处理 {len(targets)} 卷 / {sum(len(v) for v in targets.values())} 题空 content")

    engine = None
    grand_filled = 0
    grand_total = 0
    by_ek: list[tuple[str, int, int]] = []
    for ek, qns in sorted(targets.items()):
        parts = ek.split("_")
        pdf: Path | None
        if parts[0] == "provincial":
            province = parts[1]
            year = parts[2]
            region = parts[3] if len(parts) > 3 else ""
            pdf = find_question_pdf_provincial(province, year, region)
        elif parts[0] == "institution":
            year = parts[1]
            code = parts[2] if len(parts) > 2 else ""
            pdf = find_question_pdf_institution(year, code)
        else:
            continue
        if not pdf:
            print(f"  [{ek}] PDF 缺失 ({len(qns)} 题)")
            by_ek.append((ek, 0, len(qns)))
            grand_total += len(qns)
            continue

        # 文字层 vs OCR
        doc = fitz.open(pdf)
        layer = "\n".join(doc[i].get_text() for i in range(doc.page_count))
        doc.close()
        if len(layer) >= 5000:
            text = layer
        else:
            if engine is None:
                from ocr_engine import make_engine  # type: ignore[import-not-found]
                engine = make_engine()
            text = get_pdf_text(pdf, ek, engine)

        blocks = cut_blocks_v3(text, expected_qns=set(qns))
        if verbose:
            print(f"  [{ek}] cut_blocks 命中 {len(blocks)} 题，期望 {qns}")
            for qn in sorted(qns):
                b = blocks.get(qn)
                if b:
                    print(f"    Q{qn:03d}: stem={b['stem'][:50]!r}")
                else:
                    print(f"    Q{qn:03d}: NOT FOUND")

        ek_filled = 0
        for path in DATA.glob(f"*/{ek}.json"):
            qs = json.loads(path.read_text(encoding="utf-8"))
            modified = False
            for q in qs:
                if (q.get("content") or "").strip():
                    continue
                qn = int(str(q.get("id", "")).split("-")[-1])
                if qn == 0:
                    continue
                block = blocks.get(qn)
                if not block:
                    continue
                stem = block["stem"]
                opts = block["options"]
                if not stem or len(stem) < 6:
                    continue

                cur_opts = q.get("options", [])
                cur_labels = {
                    o.get("label"): (o.get("content") or "").strip()
                    for o in cur_opts if isinstance(o, dict)
                }
                broken = (
                    len(cur_labels) < 4
                    or any(len(v) > 200 for v in cur_labels.values())
                )
                q["content"] = stem
                modified = True
                if opts and broken and len(opts) >= 2:
                    q["options"] = [
                        {"label": L, "content": opts[L]}
                        for L in "ABCD" if L in opts
                    ]
                ek_filled += 1
            if modified and apply:
                path.write_text(
                    json.dumps(qs, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
        if ek_filled > 0:
            print(f"  [{ek}] +{ek_filled} 题救")
            grand_filled += ek_filled
        by_ek.append((ek, ek_filled, len(qns)))
        grand_total += len(qns)

    mode = "WRITE" if apply else "DRY"
    print(f"\n[{mode}] 合计救 {grand_filled} / {grand_total} 题")


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--exam")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    fix(args.apply, args.exam, args.verbose)


if __name__ == "__main__":
    main()
