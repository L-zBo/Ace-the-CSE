"""D-11 #1 全库审计扫描器 - 找出题库所有差距/错位/错误.

扫描维度：
1. 选项异常：个数 != 4 / 标号缺失 / 含别题文字 / OCR 截断
2. 题干污染：页码混入、章节说明覆盖、题干被截断
3. 解析中毒：explanation 主题与 content 不匹配（D-9 指纹副作用）
4. 答案-选项不匹配：answer 字段在 options 中找不到
5. ID-文件名不匹配：ID 中的 source/year/region 与文件名/内容不符

输出：archive/reports/d11_audit_full.json + .md
"""
import json
import re
import sys
from pathlib import Path
from collections import defaultdict, Counter

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path("F:/VsCodeproject/Ace-the-CSE/src/data/xingce")
OUT_DIR = Path("F:/VsCodeproject/Ace-the-CSE/archive/reports")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 选项内容白名单：允许这些内容（图形选项、特殊占位）
ALLOWED_OPT_PATTERNS = ["[图形选项]"]

# 解析池子：D-9 指纹注入常见的"非本题主题"词汇
POISON_HINTS = [
    "S 省", "S省", "省1627", "文化企业", "文化产业",
    "2023 年前三季度", "2022 年前三季度",  # 极少同时跨多年
    "学习强国", "面试宝典",
]

# 题干污染：含明显 OCR 噪音
CONTENT_NOISE = [
    re.compile(r"\b\d+/\d+\b"),  # 页码 "9/21"
    re.compile(r"^[A-D][．、]"),  # 题干开头是 ABCD 选项
    re.compile(r"题干有缺失"),
    re.compile(r"\*{3,}"),  # 多个星号
]

# 解析-题干主题一致性：抽 content 关键名词，看 explanation 是否含
def extract_keywords(text, max_n=8):
    """抽取 2-3 字的中文专有名词候选."""
    if not text:
        return set()
    # 简单抽：连续 2-4 字中文
    candidates = re.findall(r"[一-龥]{2,4}", text[:200])
    # 过滤虚词
    stop = {"下列", "正确", "错误", "选项", "答案", "解析", "本题", "因此", "所以", "故", "可以", "不能", "需要",
             "属于", "包括", "其中", "可能", "通过", "由于", "针对", "根据", "考查", "题型", "判断", "推理",
             "分析", "考点", "首先", "然后", "最后", "并且", "如果", "比如", "例如", "或者", "但是", "虽然",
             "无论", "因为", "由此", "故选", "题目", "材料", "信息", "为本", "本部"}
    return set(c for c in candidates if c not in stop)[:max_n] if False else \
           set(list(set(c for c in candidates if c not in stop))[:max_n])

issues = []  # [(severity, type, file, qid, detail)]
file_count = 0
question_count = 0

for path in sorted(ROOT.glob("*/*.json")):
    file_count += 1
    rel = path.relative_to(ROOT.parent.parent.parent)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        issues.append(("CRITICAL", "json_error", str(rel), "-", f"JSON parse fail: {e}"))
        continue
    if not isinstance(data, list):
        issues.append(("CRITICAL", "structure_error", str(rel), "-", f"not a list, got {type(data).__name__}"))
        continue
    for q in data:
        question_count += 1
        qid = q.get("id", "<no_id>")
        content = q.get("content", "") or ""
        opts = q.get("options", []) or []
        ans = q.get("answer", "")
        exp = q.get("explanation", "") or ""

        # ===== 1. 选项异常 =====
        if len(opts) != 4:
            issues.append(("HIGH", "opt_count_anomaly", str(rel), qid,
                           f"options 个数 = {len(opts)} (expected 4)"))
        labels = [o.get("label", "") for o in opts]
        if sorted(labels) != ["A", "B", "C", "D"]:
            issues.append(("MEDIUM", "opt_label_anomaly", str(rel), qid,
                           f"options labels = {labels}"))
        # 选项顺序非 ABCD
        if labels != ["A", "B", "C", "D"] and sorted(labels) == ["A", "B", "C", "D"]:
            issues.append(("LOW", "opt_order_disorder", str(rel), qid,
                           f"options 顺序非 ABCD: {labels}"))
        # 选项内容空 / 过短 / 过长
        for o in opts:
            oc = o.get("content", "") or ""
            if not oc.strip() and o.get("label") != "":
                issues.append(("HIGH", "opt_empty", str(rel), qid,
                               f"option {o.get('label')} 内容为空"))
            elif len(oc) > 200:
                # 选项过长（200 字以上很可疑，可能混入别题）
                issues.append(("HIGH", "opt_too_long", str(rel), qid,
                               f"option {o.get('label')} 长度 = {len(oc)}（疑似混入别题）"))

        # ===== 2. 答案-选项不匹配 =====
        # 注：上海等省卷有不定项选择题，answer 可能是 'ABCD'/'AC'/'CD' 等多字母
        # 仅当 answer 中存在不在 options labels 中的字母才报错
        valid_labels = set(o.get("label", "") for o in opts)
        if ans:
            ans_letters = [c for c in ans if c in "ABCDE"]
            missing = [c for c in ans_letters if c not in valid_labels]
            if missing:
                issues.append(("HIGH", "answer_label_missing", str(rel), qid,
                               f"answer = '{ans}' 含 {missing} 不在 options labels {labels} 中"))

        # ===== 3. 题干污染 =====
        for pat in CONTENT_NOISE:
            if pat.search(content):
                issues.append(("MEDIUM", "content_noise", str(rel), qid,
                               f"content 含 OCR 噪音 (pattern: {pat.pattern})"))
                break
        # 题干末尾混入下一题（包含连续题号或大段额外材料）
        if re.search(r"\b\d{2,3}\.[A-Z]?", content[-100:]) or len(content) > 800:
            if len(content) > 800:
                issues.append(("MEDIUM", "content_too_long", str(rel), qid,
                               f"content 长度 = {len(content)}（可能含别题材料）"))

        # ===== 4. 解析中毒（D-9 指纹副作用） =====
        # 软白名单 V2：
        # - content 含"文化XXX/文旅"时，文化类 hint 跳过（文化产业/企业题误报）
        # - content 含"前三季度"时，"2023/2022 年前三季度" hint 跳过（资料分析跨年对比题）
        has_culture_in_content = bool(re.search(r"文化[^，。、 ]{1,8}|文旅|文创|文博", content))
        has_quarter_in_content = "前三季度" in content or "前三季" in content
        for hint in POISON_HINTS:
            if hint in exp and hint not in content:
                if hint in ("文化产业", "文化企业") and has_culture_in_content:
                    continue
                if hint in ("2023 年前三季度", "2022 年前三季度") and has_quarter_in_content:
                    continue
                # explanation 提到但 content 没有 → 可疑
                issues.append(("HIGH", "explanation_poison", str(rel), qid,
                               f"explanation 含 '{hint}' 但 content 不含（D-9 指纹注入嫌疑）"))
                break

        # ===== 5. 解析-题干主题一致性（抽样 NLP 启发） =====
        if exp and content and len(exp) > 100:
            content_kws = extract_keywords(content)
            exp_kws = extract_keywords(exp)
            if content_kws and exp_kws:
                overlap = content_kws & exp_kws
                # 完全无重叠且 explanation 不是占位文本
                if not overlap and "[OCR/PDF 数据极限" not in exp and "[选项暂缺]" not in exp:
                    issues.append(("LOW", "topic_mismatch", str(rel), qid,
                                   f"content/explanation 关键词无重叠: c={list(content_kws)[:4]} vs e={list(exp_kws)[:4]}"))

        # ===== 6. ID-source 不匹配 =====
        if qid:
            parts = qid.split("-")
            if len(parts) >= 2:
                src = parts[0]  # national/provincial/institution
                expected_src = q.get("source", "")
                if expected_src and src != expected_src:
                    issues.append(("HIGH", "id_source_mismatch", str(rel), qid,
                                   f"ID source='{src}' vs field source='{expected_src}'"))

# ========== 汇总输出 ==========
counter = Counter([(sev, typ) for sev, typ, *_ in issues])
total = len(issues)

# JSON
out_json = OUT_DIR / "d11_audit_full.json"
out_json.write_text(json.dumps({
    "summary": {
        "total_files": file_count,
        "total_questions": question_count,
        "total_issues": total,
        "by_severity": Counter([s for s, *_ in issues]),
        "by_type": Counter([t for _, t, *_ in issues]),
    },
    "issues": [{"severity": s, "type": t, "file": f, "qid": q, "detail": d} for s, t, f, q, d in issues],
}, ensure_ascii=False, indent=2, default=dict), encoding="utf-8")

# MD 摘要
md_lines = ["# D-11 #1 全库审计扫描报告\n"]
md_lines.append(f"\n**扫描日期**: 2026-05-04  \n")
md_lines.append(f"**总文件数**: {file_count}  \n")
md_lines.append(f"**总题数**: {question_count}  \n")
md_lines.append(f"**总问题数**: {total}\n\n")

md_lines.append("## 按严重程度\n\n")
for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
    c = sum(1 for s, *_ in issues if s == sev)
    if c:
        md_lines.append(f"- **{sev}**: {c}\n")

md_lines.append("\n## 按问题类型（高频前 15）\n\n")
type_counter = Counter([t for _, t, *_ in issues])
for typ, c in type_counter.most_common(15):
    md_lines.append(f"- `{typ}`: {c}\n")

md_lines.append("\n## HIGH 严重度题目清单（前 50）\n\n")
high_items = [i for i in issues if i[0] == "HIGH"][:50]
for sev, typ, f, q, d in high_items:
    md_lines.append(f"- `{q}` ({typ}): {d}\n")

(OUT_DIR / "d11_audit_full.md").write_text("".join(md_lines), encoding="utf-8")

# 终端摘要
print("=" * 60)
print(f"D-11 全库审计扫描完成")
print("=" * 60)
print(f"扫描文件数: {file_count}")
print(f"扫描题目数: {question_count}")
print(f"发现问题数: {total}")
print()
print("按严重度:")
for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
    c = sum(1 for s, *_ in issues if s == sev)
    if c:
        print(f"  {sev}: {c}")
print()
print("按类型 (top 10):")
for typ, c in type_counter.most_common(10):
    print(f"  {typ}: {c}")
print()
print(f"详细报告: archive/reports/d11_audit_full.md / .json")
