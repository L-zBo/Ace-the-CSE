"""
extract_idioms.py — 从 yanyu 题库提取逻辑填空里的成语，做"成语词卡"板块的数据源。

输入: src/data/xingce/yanyu/*.json
输出: src/data/idioms_raw.json
       [{word, frequency, frequencyTier, sources, sourceTypes, pinyin, pinyinAbbr,
         originalContext, originalExplanation}]

频次分档:
- 超高频: >= 10 次
- 高频:   5-9 次
- 中频:   2-4 次
- 低频:   1 次

题源分类: national(国考) / provincial(省考) / institution(事业编)

拼音字段: 需 pypinyin。pip install pypinyin。未安装则字段空字符串，不阻塞。
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
YANYU_DIR = PROJECT_ROOT / "src" / "data" / "xingce" / "yanyu"
OUTPUT_FILE = PROJECT_ROOT / "src" / "data" / "idioms_raw.json"

LOGIC_FILL_KEYWORDS = ("___", "____", "_____", "横线", "填入划线")
IDIOM_PATTERN = re.compile(r"^[一-龥]{4,8}$")
SPLIT_PATTERN = re.compile(r"[、，,；;\s]+")

try:
    from pypinyin import lazy_pinyin, Style
    HAS_PINYIN = True
except ImportError:
    HAS_PINYIN = False
    print("[warn] pypinyin 未安装，pinyin / pinyinAbbr 字段将为空。\n"
          "       pip install pypinyin 后重跑可补全。", file=sys.stderr)


def is_logic_fill(question: dict) -> bool:
    content = question.get("content", "")
    return any(k in content for k in LOGIC_FILL_KEYWORDS)


def extract_idioms_from_options(options: list) -> list:
    idioms = []
    for opt in options:
        text = opt.get("content", "") if isinstance(opt, dict) else str(opt)
        text = re.sub(r"^[A-Da-d][．.、)）\s]*", "", text).strip()
        for tok in SPLIT_PATTERN.split(text):
            tok = tok.strip()
            if IDIOM_PATTERN.match(tok):
                idioms.append(tok)
    return idioms


def truncate(text: str, n: int) -> str:
    text = text.replace("\n", " ").strip()
    return text[:n] + ("…" if len(text) > n else "")


def freq_tier(n: int) -> str:
    if n >= 10:
        return "ultra_high"  # 超高频
    if n >= 5:
        return "high"  # 高频
    if n >= 2:
        return "mid"  # 中频
    return "low"  # 低频


def source_type(qid: str) -> str:
    if qid.startswith("national-"):
        return "national"
    if qid.startswith("provincial-"):
        return "provincial"
    if qid.startswith("institution-"):
        return "institution"
    return "other"


def get_pinyin(word: str) -> tuple[str, str]:
    if not HAS_PINYIN:
        return "", ""
    full = " ".join(lazy_pinyin(word, style=Style.NORMAL))
    abbr = "".join(lazy_pinyin(word, style=Style.FIRST_LETTER))
    return full, abbr


def main() -> int:
    if not YANYU_DIR.exists():
        print(f"FATAL: yanyu 目录不存在: {YANYU_DIR}", file=sys.stderr)
        return 1

    files = sorted(YANYU_DIR.glob("*.json"))
    print(f"扫描 yanyu 库 {len(files)} 个文件...")

    total_q = 0
    logic_fill_q = 0
    idiom_freq: dict = defaultdict(int)
    idiom_sources: dict = defaultdict(list)
    idiom_source_types: dict = defaultdict(lambda: defaultdict(int))
    idiom_first_context: dict = {}
    idiom_first_explanation: dict = {}

    for fp in files:
        try:
            with fp.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"  跳过 {fp.name}: {e}", file=sys.stderr)
            continue

        for q in data:
            total_q += 1
            if not is_logic_fill(q):
                continue
            logic_fill_q += 1

            qid = q.get("id", "")
            content = q.get("content", "")
            explanation = q.get("explanation", "")
            stype = source_type(qid)

            for word in extract_idioms_from_options(q.get("options", [])):
                idiom_freq[word] += 1
                idiom_sources[word].append(qid)
                idiom_source_types[word][stype] += 1
                if word not in idiom_first_context:
                    idiom_first_context[word] = truncate(content, 160)
                    idiom_first_explanation[word] = truncate(explanation, 220)

    records = []
    for word in sorted(idiom_freq.keys(), key=lambda w: (-idiom_freq[w], w)):
        full_py, abbr_py = get_pinyin(word)
        records.append({
            "word": word,
            "frequency": idiom_freq[word],
            "frequencyTier": freq_tier(idiom_freq[word]),
            "sources": idiom_sources[word][:50],
            "sourceTypes": dict(idiom_source_types[word]),
            "pinyin": full_py,
            "pinyinAbbr": abbr_py,
            "originalContext": idiom_first_context.get(word, ""),
            "originalExplanation": idiom_first_explanation.get(word, ""),
        })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    tier_counts = defaultdict(int)
    for r in records:
        tier_counts[r["frequencyTier"]] += 1

    type_counts = defaultdict(int)
    for r in records:
        for t in r["sourceTypes"]:
            type_counts[t] += r["sourceTypes"][t]

    print(f"\n{'='*50}")
    print(f"yanyu 题总数: {total_q}")
    print(f"识别逻辑填空: {logic_fill_q} ({logic_fill_q/max(total_q,1)*100:.1f}%)")
    print(f"去重成语候选: {len(records)}")
    print(f"\n频次分档:")
    print(f"  超高频 (>=10): {tier_counts['ultra_high']}")
    print(f"  高频   (5-9):  {tier_counts['high']}")
    print(f"  中频   (2-4):  {tier_counts['mid']}")
    print(f"  低频   (1):    {tier_counts['low']}")
    print(f"\n题源出现总数:")
    print(f"  国考(national):     {type_counts['national']}")
    print(f"  省考(provincial):   {type_counts['provincial']}")
    print(f"  事业编(institution):{type_counts['institution']}")
    if HAS_PINYIN:
        print(f"\npypinyin: 已生成 pinyin / pinyinAbbr")
    print(f"\n输出: {OUTPUT_FILE.relative_to(PROJECT_ROOT)}")

    print(f"\n--- Top 10 高频成语 (含拼音首字母) ---")
    for r in records[:10]:
        py = r["pinyinAbbr"] or "-"
        print(f"  [{r['frequency']:>3}x] {r['word']} ({py})  | {r['frequencyTier']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
