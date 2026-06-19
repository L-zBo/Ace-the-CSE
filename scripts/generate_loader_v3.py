#!/usr/bin/env python3
"""
生成题库文件索引（按文件聚合，大幅减少体积）
策略：仅记录文件路径和该文件包含的题目ID列表
"""

import json
from pathlib import Path

DATA_DIR = Path("src/data")
OUTPUT_INDEX = Path("src/lib/questionIndex.json")
OUTPUT_LOADER = Path("src/lib/questionLoaderDynamic.ts")


def scan_question_files():
    """扫描所有题目文件，按文件聚合"""
    file_index = []
    total_questions = 0

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

                if not questions:
                    continue

                # 提取该文件所有题目的ID和基本属性
                ids = [q["id"] for q in questions]
                sample = questions[0]  # 同文件题目属性相同，取第一个作为代表

                file_index.append({
                    "path": f"{category}/{json_file.stem}",
                    "count": len(questions),
                    "ids": ids,
                    # 文件级元数据（该文件所有题共享）
                    "subject": sample.get("subject"),
                    "category": sample.get("category"),
                    "source": sample.get("source"),
                    "year": sample.get("year"),
                    "region": sample.get("region"),
                    "level": sample.get("level"),
                })
                total_questions += len(questions)

    return file_index, total_questions


def generate_index_json(file_index, total_questions):
    """生成 questionIndex.json"""
    data = {
        "total": total_questions,
        "files": file_index,
    }
    OUTPUT_INDEX.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_INDEX, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    size_kb = OUTPUT_INDEX.stat().st_size / 1024
    print(f"生成文件索引: {OUTPUT_INDEX} ({size_kb:.1f} KB, {len(file_index)} 文件)")


def generate_loader_ts(total_questions):
    """生成动态加载器"""
    lines = [
        "import type { Question, Subject, XingceCategory, ShenlunCategory, ExamSource, ExamLevel } from '@/types/question';",
        "import questionIndex from './questionIndex.json';",
        "",
        "// ═══ 自动生成 ═══ 请勿手动编辑 ═══",
        f"// 题目总数: {total_questions} 题",
        "// 加载策略: 按文件动态加载（首屏仅加载索引）",
        "// 生成命令: python scripts/generate_loader_v3.py",
        "",
        "interface FileIndex {",
        "  path: string;",
        "  count: number;",
        "  ids: string[];",
        "  subject?: Subject;",
        "  category?: XingceCategory | ShenlunCategory;",
        "  source?: ExamSource;",
        "  year?: number;",
        "  region?: string;",
        "  level?: ExamLevel;",
        "}",
        "",
        "const index: { total: number; files: FileIndex[] } = questionIndex as any;",
        "",
        "// 题目ID到文件路径的映射（懒加载构建）",
        "let idToFileMap: Map<string, string> | null = null;",
        "",
        "function buildIdMap() {",
        "  if (idToFileMap) return idToFileMap;",
        "  idToFileMap = new Map();",
        "  for (const file of index.files) {",
        "    for (const id of file.ids) {",
        "      idToFileMap.set(id, file.path);",
        "    }",
        "  }",
        "  return idToFileMap;",
        "}",
        "",
        "// 缓存已加载的文件",
        "const loadedFiles = new Map<string, Question[]>();",
        "",
        "// 动态加载题目文件",
        "async function loadFile(filePath: string): Promise<Question[]> {",
        "  if (loadedFiles.has(filePath)) {",
        "    return loadedFiles.get(filePath)!;",
        "  }",
        "  const [category, filename] = filePath.split('/');",
        "  const module = await import(`@/data/xingce/${category}/${filename}.json`);",
        "  const questions = module.default as Question[];",
        "  loadedFiles.set(filePath, questions);",
        "  return questions;",
        "}",
        "",
        "// ========== 导出API ==========",
        "",
        "// 获取所有题目ID（用于SSG路由生成）",
        "export function getAllQuestionIds(): string[] {",
        "  return index.files.flatMap(f => f.ids);",
        "}",
        "",
        "// 按ID获取题目（动态加载）",
        "export async function getQuestionById(id: string): Promise<Question | undefined> {",
        "  const map = buildIdMap();",
        "  const filePath = map.get(id);",
        "  if (!filePath) return undefined;",
        "  const questions = await loadFile(filePath);",
        "  return questions.find(q => q.id === id);",
        "}",
        "",
        "// 筛选题目（基于索引，返回符合条件的ID列表）",
        "export function filterQuestionIds(params: {",
        "  subject?: Subject;",
        "  category?: XingceCategory | ShenlunCategory;",
        "  source?: ExamSource;",
        "  level?: ExamLevel;",
        "  year?: number;",
        "  region?: string;",
        "}): string[] {",
        "  let files = index.files;",
        "  if (params.subject) files = files.filter(f => f.subject === params.subject);",
        "  if (params.category) files = files.filter(f => f.category === params.category);",
        "  if (params.source) files = files.filter(f => f.source === params.source);",
        "  if (params.level) files = files.filter(f => f.level === params.level);",
        "  if (params.year) files = files.filter(f => f.year === params.year);",
        "  if (params.region) files = files.filter(f => f.region === params.region);",
        "  return files.flatMap(f => f.ids);",
        "}",
        "",
        "// 批量加载题目（给定ID列表）",
        "export async function loadQuestionsByIds(ids: string[]): Promise<Question[]> {",
        "  const map = buildIdMap();",
        "  const filesToLoad = new Set(ids.map(id => map.get(id)).filter(Boolean) as string[]);",
        "  await Promise.all(Array.from(filesToLoad).map(loadFile));",
        "  const questions = Array.from(loadedFiles.values()).flat();",
        "  const idSet = new Set(ids);",
        "  return questions.filter(q => idSet.has(q.id));",
        "}",
        "",
        "// 获取统计信息（基于索引）",
        "export function getCategoryStats(): Record<string, number> {",
        "  const stats: Record<string, number> = {};",
        "  for (const file of index.files) {",
        "    const key = `${file.subject}/${file.category}`;",
        "    stats[key] = (stats[key] || 0) + file.count;",
        "  }",
        "  return stats;",
        "}",
        "",
        "export function getAvailableYears(): number[] {",
        "  const years = new Set(index.files.map(f => f.year).filter(Boolean) as number[]);",
        "  return Array.from(years).sort((a, b) => b - a);",
        "}",
        "",
        "export function getAvailableSources(): ExamSource[] {",
        "  const sources = new Set(index.files.map(f => f.source).filter(Boolean));",
        "  return Array.from(sources) as ExamSource[];",
        "}",
        "",
        "// ========== 兼容旧API（用于迁移阶段） ==========",
        "",
        "// 同步获取所有题目（用于SSG generateStaticParams）",
        "export function getAllQuestions(): { id: string }[] {",
        "  return getAllQuestionIds().map(id => ({ id }));",
        "}",
        "",
        "// 异步获取所有题目（完整内容，仅在必要时调用）",
        "export async function getAllQuestionsAsync(): Promise<Question[]> {",
        "  const allIds = getAllQuestionIds();",
        "  return loadQuestionsByIds(allIds);",
        "}",
        "",
        "// 筛选题目（异步版本，返回完整题目）",
        "export async function filterQuestions(params: {",
        "  subject?: Subject;",
        "  category?: XingceCategory | ShenlunCategory;",
        "  source?: ExamSource;",
        "  level?: ExamLevel;",
        "  year?: number;",
        "  region?: string;",
        "}): Promise<Question[]> {",
        "  const ids = filterQuestionIds(params);",
        "  return loadQuestionsByIds(ids);",
        "}",
    ]

    OUTPUT_LOADER.write_text('\n'.join(lines), encoding='utf-8')
    print(f"生成动态加载器: {OUTPUT_LOADER}")


if __name__ == "__main__":
    print("扫描题库文件...")
    file_index, total_questions = scan_question_files()
    print(f"统计: {total_questions} 题, {len(file_index)} 文件")

    generate_index_json(file_index, total_questions)
    generate_loader_ts(total_questions)

    print("完成！")
