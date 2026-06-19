#!/usr/bin/env python3
"""
批量提取国考行测真题。
自动匹配真题PDF和答案PDF，调用 extract_questions.py 进行提取。
"""

import os
import re
import subprocess
import sys

QUESTION_DIR = "material/【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-真题"
ANSWER_DIR = "material/【国考】2000-2025真题pdf/2000-2025国考行测PDF/行测-答案及解析"
OUTPUT_DIR = "src/data/xingce"

# 年份 → 级别代码映射
LEVEL_MAP = {
    "副省级": "fushengjia",
    "副省": "fushengjia",
    "省级": "fushengjia",
    "省部级": "fushengjia",
    "地市级": "dishi",
    "地市": "dishi",
    "市地级": "dishi",  # 2021 国考用此写法
    "市地": "dishi",
    "行政执法": "xingzhengzhifa",
    "行政执法卷": "xingzhengzhifa",
}


def detect_level(filename: str) -> str:
    """从文件名中检测考试级别"""
    # 统一全角半角括号
    fn = filename.replace("（", "(").replace("）", ")")
    for keyword, code in LEVEL_MAP.items():
        if keyword in fn:
            return code
    return ""


def detect_year(filename: str) -> int:
    """从文件名中检测年份"""
    m = re.search(r'(\d{4})', filename)
    return int(m.group(1)) if m else 0


def find_answer_pdf(q_file: str, answer_files: list[str]) -> str:
    """为真题PDF找到匹配的答案PDF"""
    year = detect_year(q_file)
    level = detect_level(q_file)

    if not year:
        return ""

    best_match = ""
    best_score = 0

    for af in answer_files:
        a_year = detect_year(af)
        a_level = detect_level(af)

        if a_year != year:
            continue

        score = 1  # 年份匹配
        if level and a_level == level:
            score += 10  # 级别也匹配
        elif not level and not a_level:
            score += 5  # 都没有级别标识

        if score > best_score:
            best_score = score
            best_match = af

    return best_match


def main():
    min_year = int(sys.argv[1]) if len(sys.argv) > 1 else 2015

    # 列出所有PDF文件
    q_files = sorted([f for f in os.listdir(QUESTION_DIR) if f.endswith('.pdf')])
    a_files = sorted([f for f in os.listdir(ANSWER_DIR) if f.endswith('.pdf')])

    print(f"找到 {len(q_files)} 个真题PDF, {len(a_files)} 个答案PDF")
    print(f"提取范围: {min_year}-2025")
    print("=" * 60)

    success = 0
    failed = 0
    skipped = 0

    for qf in q_files:
        year = detect_year(qf)
        if year < min_year:
            skipped += 1
            continue

        level = detect_level(qf)
        af = find_answer_pdf(qf, a_files)

        if not af:
            print(f"\n[SKIP] {qf} — 未找到匹配的答案PDF")
            skipped += 1
            continue

        q_path = os.path.join(QUESTION_DIR, qf)
        a_path = os.path.join(ANSWER_DIR, af)

        print(f"\n{'─' * 60}")
        print(f"提取: {year}年 {LEVEL_MAP.get(level, '无级别') if level else '无级别'}")
        print(f"  真题: {qf}")
        print(f"  答案: {af}")

        cmd = [
            sys.executable, "-X", "utf8", "scripts/extract_questions.py",
            "--question-pdf", q_path,
            "--answer-pdf", a_path,
            "--source", "national",
            "--year", str(year),
            "--output-dir", OUTPUT_DIR,
        ]
        if level:
            cmd.extend(["--level", level])

        try:
            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300,
                encoding="utf-8", errors="replace", env=env,
            )
            if result.returncode == 0:
                # 提取最后几行摘要
                lines = result.stdout.strip().split('\n')
                for line in lines[-5:]:
                    if '新题' in line or '总计' in line or '完成' in line:
                        print(f"  {line.strip()}")
                success += 1
            else:
                print(f"  [ERROR] 返回码 {result.returncode}")
                if result.stderr:
                    print(f"  {result.stderr[:200]}")
                failed += 1
        except subprocess.TimeoutExpired:
            print(f"  [TIMEOUT] 超时")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"批量处理完成: 成功 {success}, 失败 {failed}, 跳过 {skipped}")


if __name__ == "__main__":
    main()
