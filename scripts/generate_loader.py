#!/usr/bin/env python3
"""
自动生成 questionLoader.ts
扫描 src/data/ 目录下所有 JSON 题库文件，生成 import 和注册代码。
"""

import json
import os
import re
import sys

DATA_DIR = "src/data"
OUTPUT_FILE = "src/lib/questionLoader.ts"


def scan_json_files():
    """扫描所有题库 JSON 文件"""
    entries = []

    for subject in ["xingce", "shenlun"]:
        subject_dir = os.path.join(DATA_DIR, subject)
        if not os.path.isdir(subject_dir):
            continue

        for category in os.listdir(subject_dir):
            cat_dir = os.path.join(subject_dir, category)
            if not os.path.isdir(cat_dir):
                continue

            for filename in sorted(os.listdir(cat_dir)):
                if not filename.endswith(".json"):
                    continue

                filepath = os.path.join(cat_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if not data:
                    continue

                # 生成 import 变量名: changshi_national_2024 等
                stem = filename.replace(".json", "")
                var_name = f"{category}_{stem}".replace("-", "_")
                # 确保变量名合法
                var_name = re.sub(r'[^a-zA-Z0-9_]', '_', var_name)

                # import 路径 (相对于 src/lib/)
                import_path = f"@/data/{subject}/{category}/{filename.replace('.json', '.json')}"

                # 注册表 key
                reg_key = f"{subject}/{category}/{stem}"

                entries.append({
                    "subject": subject,
                    "category": category,
                    "filename": filename,
                    "var_name": var_name,
                    "import_path": import_path,
                    "reg_key": reg_key,
                    "count": len(data),
                })

    return entries


def generate_loader(entries):
    """生成 questionLoader.ts 代码"""
    lines = []

    # Header
    lines.append("import type {")
    lines.append("  Question,")
    lines.append("  Subject,")
    lines.append("  XingceCategory,")
    lines.append("  ShenlunCategory,")
    lines.append("  ExamSource,")
    lines.append("  ExamLevel,")
    lines.append("} from '@/types/question';")
    lines.append("")
    lines.append("// ═══ 自动生成 ═══ 请勿手动编辑 ═══")
    lines.append(f"// 题库文件: {len(entries)} 个 JSON, 共 {sum(e['count'] for e in entries)} 题")
    lines.append(f"// 生成命令: python scripts/generate_loader.py")
    lines.append("")

    # Imports
    lines.append("// 题库数据导入")
    for entry in entries:
        lines.append(f"import {entry['var_name']} from '{entry['import_path']}';")

    lines.append("")

    # Question banks registry
    lines.append("// 题库注册表")
    lines.append("const questionBanks: Record<string, Question[]> = {")
    for entry in entries:
        lines.append(f"  '{entry['reg_key']}': {entry['var_name']} as Question[],")
    lines.append("};")

    lines.append("")

    # Utility functions (same as original)
    lines.append("""// 获取所有题目
export function getAllQuestions(): Question[] {
  return Object.values(questionBanks).flat();
}

// 按条件筛选题目
export function filterQuestions(params: {
  subject?: Subject;
  category?: XingceCategory | ShenlunCategory;
  source?: ExamSource;
  level?: ExamLevel;
  year?: number;
  difficulty?: number;
  region?: string;
}): Question[] {
  let questions = getAllQuestions();

  if (params.subject) {
    questions = questions.filter((q) => q.subject === params.subject);
  }
  if (params.category) {
    questions = questions.filter((q) => q.category === params.category);
  }
  if (params.source) {
    questions = questions.filter((q) => q.source === params.source);
  }
  if (params.level) {
    questions = questions.filter((q) => q.level === params.level);
  }
  if (params.year) {
    questions = questions.filter((q) => q.year === params.year);
  }
  if (params.difficulty) {
    questions = questions.filter((q) => q.difficulty === params.difficulty);
  }
  if (params.region) {
    questions = questions.filter((q) => q.region === params.region);
  }

  return questions;
}

// 按 ID 获取题目
export function getQuestionById(id: string): Question | undefined {
  return getAllQuestions().find((q) => q.id === id);
}

// 获取分类统计
export function getCategoryStats(): Record<string, number> {
  const stats: Record<string, number> = {};
  for (const q of getAllQuestions()) {
    const key = `${q.subject}/${q.category}`;
    stats[key] = (stats[key] || 0) + 1;
  }
  return stats;
}

// 获取可用年份
export function getAvailableYears(): number[] {
  const years = new Set(getAllQuestions().map((q) => q.year));
  return Array.from(years).sort((a, b) => b - a);
}

// 获取可用考试来源
export function getAvailableSources(): ExamSource[] {
  const sources = new Set(getAllQuestions().map((q) => q.source));
  return Array.from(sources) as ExamSource[];
}""")

    return "\n".join(lines) + "\n"


def main():
    print("扫描题库文件...")
    entries = scan_json_files()
    print(f"  找到 {len(entries)} 个 JSON 文件")

    total_questions = sum(e["count"] for e in entries)
    print(f"  总题量: {total_questions}")

    # 按分类统计
    cats = {}
    for e in entries:
        key = f"{e['subject']}/{e['category']}"
        cats[key] = cats.get(key, 0) + e["count"]
    for cat, cnt in sorted(cats.items()):
        print(f"    {cat}: {cnt} 题")

    print(f"\n生成 {OUTPUT_FILE}...")
    code = generate_loader(entries)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(code)

    print(f"  写入 {len(code)} 字符")
    try:
        print("✓ 完成!")
    except UnicodeEncodeError:
        print("OK done!")


if __name__ == "__main__":
    main()
