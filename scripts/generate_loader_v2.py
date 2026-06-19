#!/usr/bin/env python3
"""
生成题库元数据索引（仅ID/基础属性，不含题目内容）
用于快速启动和路由生成，题目内容运行时按需加载
"""

import json
import os
from pathlib import Path

DATA_DIR = Path("src/data")
OUTPUT_META = Path("src/lib/questionMeta.json")
OUTPUT_LOADER = Path("src/lib/questionLoader.ts")


def scan_questions():
    """扫描所有题目，提取轻量级元数据"""
    meta_list = []
    file_map = {}  # {category/filename: Question[]}

    for subject in ["xingce", "shenlun"]:
        subject_dir = DATA_DIR / subject
        if not subject_dir.is_dir():
            continue

        for category_dir in subject_dir.iterdir():
            if not category_dir.is_dir():
                continue
            category = category_dir.name

            for json_file in sorted(category_dir.glob("*.json")):
                with open(json_file, "r", encoding="utf-8") as f:
                    questions = json.load(f)

                file_key = f"{category}/{json_file.stem}"
                file_map[file_key] = len(questions)

                for q in questions:
                    # 仅保留用于路由/筛选的元数据，去掉题目内容/选项/解析
                    meta_list.append({
                        "id": q["id"],
                        "subject": q.get("subject"),
                        "category": q.get("category"),
                        "source": q.get("source"),
                        "year": q.get("year"),
                        "region": q.get("region"),
                        "level": q.get("level"),
                        "difficulty": q.get("difficulty"),
                        "examKey": q.get("examKey"),
                        # 记录文件位置，用于动态加载
                        "_file": file_key,
                    })

    return meta_list, file_map


def generate_meta_json(meta_list):
    """生成 questionMeta.json（轻量级索引）"""
    OUTPUT_META.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_META, "w", encoding="utf-8") as f:
        json.dump(meta_list, f, ensure_ascii=False, separators=(',', ':'))
    print(f"生成元数据索引: {OUTPUT_META} ({len(meta_list)} 题)")


def generate_loader_ts(file_map, total_questions):
    """生成 questionLoader.ts（动态加载版本）"""
    lines = [
        "import type { Question, Subject, XingceCategory, ShenlunCategory, ExamSource, ExamLevel } from '@/types/question';",
        "import questionMeta from './questionMeta.json';",
        "",
        "// ═══ 自动生成 ═══ 请勿手动编辑 ═══",
        f"// 题目元数据: {total_questions} 题",
        "// 题目内容: 运行时按需动态加载",
        "// 生成命令: python scripts/generate_loader_v2.py",
        "",
        "// 题目元数据（轻量级，仅ID和筛选属性）",
        "interface QuestionMeta {",
        "  id: string;",
        "  subject?: Subject;",
        "  category?: XingceCategory | ShenlunCategory;",
        "  source?: ExamSource;",
        "  year?: number;",
        "  region?: string;",
        "  level?: ExamLevel;",
        "  difficulty?: string;",
        "  examKey?: string;",
        "  _file: string;  // 用于动态加载",
        "}",
        "",
        "const meta: QuestionMeta[] = questionMeta as QuestionMeta[];",
        "",
        "// 缓存已加载的题目文件",
        "const loadedFiles = new Map<string, Question[]>();",
        "",
        "// 动态加载题目文件（运行时按需加载）",
        "async function loadQuestionFile(fileKey: string): Promise<Question[]> {",
        "  if (loadedFiles.has(fileKey)) {",
        "    return loadedFiles.get(fileKey)!;",
        "  }",
        "  ",
        "  const [category, filename] = fileKey.split('/');",
        "  const module = await import(`@/data/xingce/${category}/${filename}.json`);",
        "  const questions = module.default as Question[];",
        "  loadedFiles.set(fileKey, questions);",
        "  return questions;",
        "}",
        "",
        "// 获取所有题目元数据（用于路由生成/统计，不含题目内容）",
        "export function getAllQuestionsMeta(): QuestionMeta[] {",
        "  return meta;",
        "}",
        "",
        "// 获取所有题目（完整内容，首次调用会触发所有文件加载）",
        "// ⚠️ 仅在必要时调用（如需要过滤题目内容时）",
        "export async function getAllQuestions(): Promise<Question[]> {",
        "  const fileKeys = new Set(meta.map(m => m._file));",
        "  await Promise.all(Array.from(fileKeys).map(loadQuestionFile));",
        "  return Array.from(loadedFiles.values()).flat();",
        "}",
        "",
        "// 同步版本（用于SSG generateStaticParams）",
        "// ⚠️ 仅返回元数据，不含题目内容",
        "export function getAllQuestionsSync(): Pick<Question, 'id'>[] {",
        "  return meta.map(m => ({ id: m.id }));",
        "}",
        "",
        "// 按ID获取题目（动态加载对应文件）",
        "export async function getQuestionById(id: string): Promise<Question | undefined> {",
        "  const metaItem = meta.find(m => m.id === id);",
        "  if (!metaItem) return undefined;",
        "  ",
        "  const questions = await loadQuestionFile(metaItem._file);",
        "  return questions.find(q => q.id === id);",
        "}",
        "",
        "// 筛选题目（基于元数据，不加载题目内容）",
        "export function filterQuestionsMeta(params: {",
        "  subject?: Subject;",
        "  category?: XingceCategory | ShenlunCategory;",
        "  source?: ExamSource;",
        "  level?: ExamLevel;",
        "  year?: number;",
        "  region?: string;",
        "  difficulty?: string;",
        "}): QuestionMeta[] {",
        "  let result = meta;",
        "  if (params.subject) result = result.filter(q => q.subject === params.subject);",
        "  if (params.category) result = result.filter(q => q.category === params.category);",
        "  if (params.source) result = result.filter(q => q.source === params.source);",
        "  if (params.level) result = result.filter(q => q.level === params.level);",
        "  if (params.year) result = result.filter(q => q.year === params.year);",
        "  if (params.region) result = result.filter(q => q.region === params.region);",
        "  if (params.difficulty) result = result.filter(q => q.difficulty === params.difficulty);",
        "  return result;",
        "}",
        "",
        "// 获取统计信息（基于元数据，无需加载题目内容）",
        "export function getCategoryStats(): Record<string, number> {",
        "  const stats: Record<string, number> = {};",
        "  for (const q of meta) {",
        "    const key = `${q.subject}/${q.category}`;",
        "    stats[key] = (stats[key] || 0) + 1;",
        "  }",
        "  return stats;",
        "}",
        "",
        "export function getAvailableYears(): number[] {",
        "  const years = new Set(meta.map(q => q.year).filter(Boolean) as number[]);",
        "  return Array.from(years).sort((a, b) => b - a);",
        "}",
        "",
        "export function getAvailableSources(): ExamSource[] {",
        "  const sources = new Set(meta.map(q => q.source).filter(Boolean));",
        "  return Array.from(sources) as ExamSource[];",
        "}",
        "",
        "// ===== 兼容旧API（同步版本，仅用于SSG） =====",
        "// 注意：这些是旧代码兼容层，新代码应使用上面的异步版本",
        "",
        "// 同步获取所有题目（仅用于 generateStaticParams）",
        "export function getAllQuestions_SSG(): Pick<Question, 'id'>[] {",
        "  return getAllQuestionsSync();",
        "}",
    ]

    OUTPUT_LOADER.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_LOADER.write_text('\n'.join(lines), encoding='utf-8')
    print(f"生成 questionLoader: {OUTPUT_LOADER}")


if __name__ == "__main__":
    print("扫描题库...")
    meta_list, file_map = scan_questions()

    print(f"统计: {len(meta_list)} 题, {len(file_map)} 文件")

    print("生成元数据索引...")
    generate_meta_json(meta_list)

    print("生成动态加载器...")
    generate_loader_ts(file_map, len(meta_list))

    print("完成！")
    print(f"   元数据大小: {OUTPUT_META.stat().st_size / 1024:.1f} KB")
    old_size = Path('src/lib/questionLoader.ts').stat().st_size / 1024 if Path('src/lib/questionLoader.ts').exists() else 0
    print(f"   对比原文件: {old_size:.1f} KB")
