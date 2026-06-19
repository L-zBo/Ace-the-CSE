#!/usr/bin/env python3
"""D 阶段省考答案/解析批量注入器。

【方案】对每个 provincial_*.json examKey:
- 解析 examKey 拿省名 + 年份
- 在 material/【省考】.../{省名}公务员.../行测.../答案及解析/ 下找
  含年份的 PDF
- 切块抽 answer（"故正确答案为X"）+ explanation
- 仅注入空字段，不覆写

【省名映射】examKey 用拼音，PDF 文件名用中文，必须维护映射表。
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

import fitz  # type: ignore[import-not-found]


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data" / "xingce"

# 省名映射: pinyin → 中文 (用于查 PDF)
PROVINCE_MAP = {
    "anhui": "安徽",
    "beijing": "北京",
    "fujian": "福建",
    "gansu": "甘肃",
    "guangdong": "广东",
    "guangxi": "广西",
    "guangzhou": "广州",
    "guizhou": "贵州",
    "hainan": "海南",
    "hebei": "河北",
    "heilongjiang": "黑龙江",
    "henan": "河南",
    "hubei": "湖北",
    "hunan": "湖南",
    "jiangsu": "江苏",
    "jiangxi": "江西",
    "jilin": "吉林",
    "liaoning": "辽宁",
    "neimenggu": "内蒙古",
    "ningxia": "宁夏",
    "qinghai": "青海",
    "shaanxi": "陕西",
    "shandong": "山东",
    "shanghai": "上海",
    "shanxi": "山西",
    "shenzhen": "深圳",
    "sichuan": "四川",
    "tianjin": "天津",
    "xinjiang": "新疆",
    "xizang": "西藏",
    "yunnan": "云南",
    "zhejiang": "浙江",
    "chongqing": "重庆",
}


def find_provincial_pdf(province_pinyin: str, year: str) -> Path | None:
    cn = PROVINCE_MAP.get(province_pinyin)
    if not cn:
        return None
    cn_bytes = cn.encode("utf-8")
    year_bytes = year.encode("utf-8")
    for p in glob.glob("material/**/*.pdf", recursive=True):
        if "【省考】" not in p:
            continue
        if "行测" not in p:
            continue
        if "答案" not in p and "解析" not in p:
            continue
        pb = p.encode("utf-8")
        if year_bytes not in pb:
            continue
        if cn_bytes not in pb:
            continue
        return Path(p)
    return None


HEAD_OLD = re.compile(r"故正确答案为\s*[A-D]+[。.]?(\d{1,3})")
# D-3 #3：HEAD_NL 加严——题号独立行后必须紧跟中文字符（防 PDF 侧栏 "17\n18\n19\n..." 误识）
HEAD_NL = re.compile(r"(?:^|\n)(\d{1,3})\n\s*[一-鿿]")
# D-3：HEAD_DOT 加严——题号 + 顿号/点 + 至少 2 个中文字符（防"答案速查表"误抓）
HEAD_DOT = re.compile(r"(?:^|\n)\s*(\d{1,3})\s*[、,，.．]\s*[一-鿿]{2,}")
HEAD_BRACKET = re.compile(
    r"第\s*[〔【〖\(（]?\s*(\d{1,3})\s*[〕】〗\)）]?\s*题"
)
HEAD_DI_TI = re.compile(r"第\s*(\d{1,3})\s*题")
# 江西/部分省考格式: 【解析1—正确答案A】 或 【解析1--正确答案A】
HEAD_JIEXI = re.compile(
    r"【\s*解析\s*(\d{1,3})\s*[—\-－–\s]*正确答案\s*[A-D]+\s*】"
)
# 重庆/部分省考格式: 【解析N】 单独，答案在跨行的 "正确答案X】"
HEAD_JIEXI_PLAIN = re.compile(r"【\s*解析\s*(\d{1,3})\s*】")
# D-3 新增：辽宁/黑龙江/吉林 2024：【1—正确答案C】（缺"解析"二字）
HEAD_BRACKET_NX = re.compile(
    r"【\s*(\d{1,3})\s*[—\-－–]\s*正确答案\s*[A-D]+\s*】"
)
# D-4 #4：兼容 √/× 判断题 + "C/A" 双答案 头边界（chongqing/shandong/shanxi/tianjin/guangdong 2024）
HEAD_BRACKET_NX_EXT = re.compile(
    r"【\s*(?:解析\s*)?(\d{1,3})\s*[—\-－–]\s*正确答案\s*[A-D√×]+(?:[/\\、][A-D√×]+)*\s*】"
)
# D-3 新增：四川 2024：【题目1】+ 后续"故正确答案为X"
HEAD_TIMU = re.compile(r"【\s*题目\s*(\d{1,3})\s*】")
ANS_OLD = re.compile(r"故正确答案?[为选是]?[:：]?\s*([A-D]+)(?=[\s，,。.、\)）])")
ANS_NEW = re.compile(r"因此[，,]?\s*选择\s*([A-D]+)\s*选项")
# D-3 新增：因此选 X 后无"选项"二字（上海/广东/云南/山西/河南/山东 2020-2021）
ANS_NEW2 = re.compile(r"因此[，,]?\s*选择\s*([A-D]+)(?:\s*选项)?(?=[\s。.，,])")
ANS_PAREN = re.compile(r"(?:正确答案|参考答案|答案)[：:]\s*([A-D])(?=[\s，。、\)）])")
# D-3 新增：lookahead 加全角左括号（"答案：B（全站正确率…）"）
ANS_PAREN2 = re.compile(
    r"(?:正确答案|参考答案|答案)[：:]\s*([A-D])(?=[\s，。、\)）（(])"
)
ANS_BARE = re.compile(r"正确答案?\s*([A-D])(?=[\s。.\n】\)）])")
ANS_BRACE = re.compile(r"正确答案?\s*[:：]?\s*【\s*([A-D])\s*】")
# D-3 #6：兼容裸"答案【C】"格式（shanghai_2023 等）
ANS_BRACE2 = re.compile(r"答案\s*[:：]?\s*【\s*([A-D])\s*】")
# D-3 #3：兼容"正确答案是：C" / "答案为：C" 等灵活分隔（anhui_2022 等）
ANS_SHIYE = re.compile(
    r"(?:正确答案|参考答案|答案)\s*[是为][：:]?\s*([A-D])(?=[\s，。、\)）（(\n】])"
)
# D-3 新增：直接从 HEAD_BRACKET_NX/HEAD_JIEXI 头里抽答案（同位置，不依赖块尾）
ANS_HEAD_NX = re.compile(
    r"【\s*(?:解析\s*)?\d{1,3}\s*[—\-－–]\s*正确答案\s*([A-D]+)\s*】"
)
# D-4 #4 新增：兼容判断题 √/× 和双答案 "C/A"（chongqing/shandong/shanxi/tianjin/guangdong 2024）
# 取首个 token 后做映射：√→A, ×→B（2 选项判断题约定 A=正确 B=错误）
ANS_HEAD_NX_EXT = re.compile(
    r"【\s*(?:解析\s*)?\d{1,3}\s*[—\-－–]\s*正确答案\s*([A-D√×]+(?:[/\\、][A-D√×]+)*)\s*】"
)
# D-4 #4：兼容 PDF 笔误"因此，选项X 选项"（beijing_2022 q84）
ANS_NEW_TYPO = re.compile(r"因此[，,]?\s*选项\s*([A-D]+)\s*选项")


def _normalize_ans_token(raw: str) -> str:
    """把头部 ANS_HEAD_NX_EXT 抓到的 raw（如 'C/A' / '√' / 'AB'）规范成 A-D 字母。

    - 切 /\\、 取首个 token
    - √ → A，× → B（2 选项判断题约定）
    - 多字母（"AB"）保留多选
    """
    if not raw:
        return ""
    head = re.split(r"[/\\、]", raw)[0]
    head = head.replace("√", "A").replace("×", "B")
    # 仅保留 A-D
    head = re.sub(r"[^A-D]", "", head)
    return head


def extract_speed_table(text: str, max_qn_limit: int = 200) -> dict[int, str]:
    """提取 PDF/OCR 头部的"答案速查表"（如 guangxi_2021）。

    模式："N、X" 或 "N、\\nX\\n" 的连续序列（≥30 个连续题号）。
    返回 {qn: answer}，仅在长序列连续递增时认为是速查表。
    """
    # 兼容两种 OCR 拆行: "1、A" 或 "1、\\nA\\n" 或 "1、\\n\\nA"
    pat = re.compile(r"(\d{1,3})\s*[、,，.．]\s*\n?\s*([A-D])(?=[\s\n、,，.．])")
    results: list[tuple[int, str]] = []
    for m in pat.finditer(text):
        qn = int(m.group(1))
        if 1 <= qn <= max_qn_limit:
            results.append((qn, m.group(2)))
    if len(results) < 30:
        return {}
    # 取最长连续递增序列
    best_seq: list[tuple[int, str]] = []
    cur_seq: list[tuple[int, str]] = []
    for qn, ans in results:
        if not cur_seq or qn == cur_seq[-1][0] + 1:
            cur_seq.append((qn, ans))
        else:
            if len(cur_seq) > len(best_seq):
                best_seq = cur_seq
            cur_seq = [(qn, ans)] if qn == 1 else []
    if len(cur_seq) > len(best_seq):
        best_seq = cur_seq
    if len(best_seq) < 30:
        return {}
    return {qn: ans for qn, ans in best_seq}


def extract_blocks_from_text(text: str, total: int) -> dict[int, dict[str, str]]:
    """从纯文本切块，独立于 PDF 来源（PDF 文字层 / OCR txt 复用）。"""
    boundaries: list[tuple[int, int]] = []
    for rgx in (
        HEAD_OLD, HEAD_NL, HEAD_DOT, HEAD_BRACKET, HEAD_DI_TI,
        HEAD_JIEXI, HEAD_JIEXI_PLAIN, HEAD_BRACKET_NX, HEAD_TIMU,
        HEAD_BRACKET_NX_EXT,
    ):
        for m in rgx.finditer(text):
            qn = int(m.group(1))
            if 1 <= qn <= total:
                boundaries.append((qn, m.start(1)))

    boundaries.sort(key=lambda x: x[1])
    # D-3：去掉强制单调约束，仅去重 + 用 pos 排序保证顺序
    # （之前单调会被 OCR 误识的孤立大数字 "\n110\n" 把 last_qn 推上去，后续题号被ban）
    seen: set[int] = set()
    cleaned: list[tuple[int, int]] = []
    for qn, pos in boundaries:
        if qn in seen:
            continue
        seen.add(qn)
        cleaned.append((qn, pos))

    blocks: dict[int, dict[str, str]] = {}
    for i, (qn, pos) in enumerate(cleaned):
        end = cleaned[i + 1][1] - 1 if i + 1 < len(cleaned) else len(text)
        block_start = pos + len(str(qn))
        block = text[block_start:end].strip()
        # ANS 优先级：从头部 BRACKET_NX 抽（最可靠）→ 故正确答案为 → 因此选 → 答案: → 裸 → 大括号
        # 注意 HEAD_BRACKET_NX 的答案在边界标志符里，需要从原文 pos 附近抽
        head_ans = None
        head_window = text[max(0, pos - 5):min(len(text), pos + 60)]
        m = ANS_HEAD_NX.search(head_window)
        if m:
            head_ans = m.group(1)
        else:
            # D-4 #4：兼容 √/× 判断题 + "C/A" 双答案
            m_ext = ANS_HEAD_NX_EXT.search(head_window)
            if m_ext:
                head_ans = _normalize_ans_token(m_ext.group(1))
        ans_m = (
            ANS_OLD.search(block)
            or ANS_NEW2.search(block)
            or ANS_NEW.search(block)
            or ANS_NEW_TYPO.search(block)
            or ANS_PAREN2.search(block)
            or ANS_PAREN.search(block)
            or ANS_SHIYE.search(block)
            or ANS_BARE.search(block)
            or ANS_BRACE.search(block)
            or ANS_BRACE2.search(block)
        )
        answer = head_ans or (ans_m.group(1) if ans_m else "")
        blocks[qn] = {"answer": answer, "explanation": block.strip()}

    return blocks


def extract_blocks(pdf_path: Path, total: int) -> dict[int, dict[str, str]]:
    doc = fitz.open(pdf_path)
    text = "\n".join(doc[i].get_text() for i in range(doc.page_count))
    return extract_blocks_from_text(text, total)


def load_ocr_text(exam_key: str) -> str | None:
    """优先从 archive/reports/ocr_{exam_key}.txt 读 OCR 落档文本。"""
    p = ROOT / "archive" / "reports" / f"ocr_{exam_key}.txt"
    if p.exists():
        return p.read_text(encoding="utf-8")
    return None


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


def max_qn(exam_key: str) -> int:
    """返回 examKey 的 JSON 中最大题号（用作切块 regex 的题号上限）。

    xinjiang_2021 等卷题数=39 但题号范围 1~111，
    若直接把题数当上限会丢掉超过 39 的题号边界。
    """
    biggest = 0
    for p in glob.glob(str(DATA / "*" / f"{exam_key}.json")):
        for q in json.loads(Path(p).read_text(encoding="utf-8")):
            try:
                qn = int(str(q.get("id", "")).split("-")[-1])
                if qn > biggest:
                    biggest = qn
            except ValueError:
                continue
    return biggest


def gather_exam_keys() -> list[str]:
    seen: set[str] = set()
    for p in glob.glob(str(DATA / "*" / "provincial_*.json")):
        name = os.path.splitext(os.path.basename(p))[0]
        seen.add(name)
    return sorted(seen)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exam", help="只跑指定 examKey")
    ap.add_argument("--list", action="store_true", help="列出所有省考卷及当前缺口")
    args = ap.parse_args()

    if args.list:
        for ek in gather_exam_keys():
            total = total_qs(ek)
            no_ans = 0
            for p in glob.glob(str(DATA / "*" / f"{ek}.json")):
                for q in json.loads(Path(p).read_text(encoding="utf-8")):
                    if not q.get("answer"):
                        no_ans += 1
            if no_ans > 0:
                print(f"{ek}: {total} 题, 缺 ans={no_ans}")
        return

    targets = [args.exam] if args.exam else gather_exam_keys()
    grand_ans = grand_exp = pdf_missing = block_failed = 0
    for ek in targets:
        # 解析 省名_年份
        parts = ek.split("_")
        if len(parts) < 3:
            print(f"[{ek}] SKIP: 命名格式异常")
            continue
        province = parts[1]
        year = parts[2]
        # 看本卷有无缺
        no_ans = 0
        for p in glob.glob(str(DATA / "*" / f"{ek}.json")):
            for q in json.loads(Path(p).read_text(encoding="utf-8")):
                if not q.get("answer"):
                    no_ans += 1
        if no_ans == 0:
            continue

        # D-3 #4：切块 limit 用 max(题数, 最大题号 + 50)，防 xinjiang_2021 等
        # 题数 39 但题号 1-111 的稀疏卷把 OCR 块全 ban。
        block_limit = max(total_qs(ek), max_qn(ek) + 50, 250)
        # D-3：先尝试 OCR 落档文本（更全），无则回落 PDF 文字层
        ocr_text = load_ocr_text(ek)
        if ocr_text and len(ocr_text) > 1000:
            total = total_qs(ek)
            blocks = extract_blocks_from_text(ocr_text, block_limit)
            source = f"OCR txt ({len(ocr_text)} 字)"
        else:
            pdf = find_provincial_pdf(province, year)
            if not pdf:
                print(f"[{ek}] PDF MISSING (省={province} 年={year})")
                pdf_missing += 1
                continue
            doc = fitz.open(pdf)
            total_chars = sum(len(doc[i].get_text()) for i in range(doc.page_count))
            if total_chars < 5000:
                print(f"[{ek}] OCR NEEDED (PDF 文字层 {total_chars} 字符, 无 OCR txt)")
                continue
            total = total_qs(ek)
            text = "\n".join(doc[i].get_text() for i in range(doc.page_count))
            blocks = extract_blocks_from_text(text, block_limit)
            source = f"PDF.text ({total_chars} 字)"

        if not blocks:
            print(f"[{ek}] BLOCK FAILED (切块 0, source={source})")
            block_failed += 1
            continue

        # D-3 #5：尝试从头部"答案速查表"补未抽到答案的块（如 guangxi_2021）
        active_text = ocr_text if (ocr_text and len(ocr_text) > 1000) else None
        if active_text is None:
            try:
                doc2 = fitz.open(find_provincial_pdf(province, year))
                active_text = "\n".join(doc2[i].get_text() for i in range(doc2.page_count))
            except Exception:
                active_text = ""
        speed = extract_speed_table(active_text, max_qn(ek) + 50)
        speed_filled = 0
        if speed:
            for qn, ans in speed.items():
                if qn not in blocks:
                    blocks[qn] = {"answer": ans, "explanation": f"答案：{ans}（速查表）"}
                    speed_filled += 1
                elif not blocks[qn]["answer"]:
                    blocks[qn]["answer"] = ans
                    speed_filled += 1
            if speed_filled:
                source += f" + 速查表 (+{speed_filled})"

        ans, exp = inject(ek, blocks)
        with_ans = sum(1 for b in blocks.values() if b["answer"])
        print(
            f"[{ek}] {total} 题, 切 {len(blocks)} 块 (含答案 {with_ans}) "
            f"src={source} → +{ans} ans, +{exp} exp"
        )
        grand_ans += ans
        grand_exp += exp

    print(f"\n合计: +{grand_ans} answer, +{grand_exp} explanation")
    print(f"  PDF 缺失: {pdf_missing} 卷")
    print(f"  切块失败: {block_failed} 卷")


if __name__ == "__main__":
    main()
