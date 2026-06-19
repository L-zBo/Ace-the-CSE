"""D-5 #1.2：清洗题干/选项/解析里的 PDF 水印。

水印类型：
  - 公考事业编学习资料加微信AS73982
  - 事业单位联考真题
  - 老师微信：AS73982
  - AS73982 (孤立)
  - · 18 ·  (页码圆点)
  - TB：Seeyee 智库整理 持续更新
  - Seeyee
  - 多余空白行
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data" / "xingce"

# 各类水印 patterns（顺序敏感：先长后短）
WATERMARK_PATTERNS = [
    r"公考事业编学习资料加微信\s*AS\d{3,}",
    r"公考事业编学习资料加微信\S*",
    r"事业单位联考真题",
    r"老师微信\s*[：:]\s*AS\d{3,}",
    r"老师微信\s*[：:]\s*\S*",
    r"TB[：:]\s*Seeyee\S*智库\S*",
    r"TB[：:]\s*Seeyee\S*",
    r"·\s*\d+\s*·",
    r"持续更新",
    r"Seeyee\s*智库\S*",
    r"Seeyee",
    # 孤立 AS73982（只在已有水印上下文中清，避免误删）
    r"\bAS\d{4,}\b",
]

WM_RE = re.compile("|".join(f"(?:{p})" for p in WATERMARK_PATTERNS))


def clean(text: str) -> str:
    if not text:
        return text
    cleaned = WM_RE.sub("", text)
    # 整理多余空白：连续 3+ 空白行 → 2 空白行；行尾空白删
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    cleaned_content = cleaned_options = cleaned_exp = 0
    files_modified = set()
    for p in sorted(DATA.glob("*/*.json")):
        questions = json.loads(p.read_text(encoding="utf-8"))
        modified = False
        for q in questions:
            # content
            c = q.get("content") or ""
            if WM_RE.search(c):
                new_c = clean(c)
                if new_c != c:
                    q["content"] = new_c
                    cleaned_content += 1
                    modified = True
            # explanation
            for key in ("explanation", "analysis"):
                e = q.get(key) or ""
                if WM_RE.search(e):
                    new_e = clean(e)
                    if new_e != e:
                        q[key] = new_e
                        cleaned_exp += 1
                        modified = True
            # options
            for o in q.get("options", []):
                if not isinstance(o, dict):
                    continue
                oc = o.get("content") or ""
                if WM_RE.search(oc):
                    new_oc = clean(oc)
                    if new_oc != oc:
                        o["content"] = new_oc
                        cleaned_options += 1
                        modified = True
        if modified:
            files_modified.add(str(p))
            if args.apply:
                p.write_text(
                    json.dumps(questions, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )

    mode = "WRITE" if args.apply else "DRY"
    print(f"[{mode}] 清洗:")
    print(f"  题干 content: {cleaned_content}")
    print(f"  选项 options: {cleaned_options}")
    print(f"  解析 explanation: {cleaned_exp}")
    print(f"  涉及文件: {len(files_modified)}")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    main()
