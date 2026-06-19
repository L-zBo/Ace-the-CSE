#!/usr/bin/env python3
"""
最终方案：轻量级文件索引 + ID规则反推
策略：利用题目ID命名规律（institution-xingce-changshi-2020-a-001）反推文件路径
索引仅记录：文件路径、题目数量、文件级元数据
"""

import json
from pathlib import Path

DATA_DIR = Path("src/data")
OUTPUT_INDEX = Path("src/lib/questionIndex.json")
OUTPUT_LOADER = Path("src/lib/questionLoader.ts")


def scan_question_files():
    """扫描所有题目文件"""
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

                # 仅记录文件级信息，不存储ID列表
                sample = questions[0]
                file_index.append({
                    "path": f"{category}/{json_file.stem}",
                    "count": len(questions),
                    # 文件级元数据
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
    """生成轻量级索引"""
    data = {
        "total": total_questions,
        "files": file_index,
    }
    OUTPUT_INDEX.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_INDEX, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    size_kb = OUTPUT_INDEX.stat().st_size / 1024
    print(f"生成文件索引: {OUTPUT_INDEX} ({size_kb:.1f} KB, {len(file_index)} 文件, {total_questions} 题)")


def generate_loader_ts(total_questions, file_count):
    """生成最终版加载器"""
    code = f'''import type {{ Question, Subject, XingceCategory, ShenlunCategory, ExamSource, ExamLevel }} from '@/types/question';
import questionIndex from './questionIndex.json';

// ═══ 自动生成 ═══ 请勿手动编辑 ═══
// 题目总数: {total_questions} 题
// 文件数: {file_count} 个
// 加载策略: 按需动态import，利用ID规则反推文件路径
// 生成命令: python scripts/generate_loader_final.py

interface FileIndex {{
  path: string;
  count: number;
  subject?: Subject;
  category?: XingceCategory | ShenlunCategory;
  source?: ExamSource;
  year?: number;
  region?: string;
  level?: ExamLevel;
}}

const index: {{ total: number; files: FileIndex[] }} = questionIndex as any;

// 缓存已加载的文件
const loadedFiles = new Map<string, Question[]>();

// 从题目ID反推文件路径
// 例: "institution-xingce-changshi-2020-a-001" -> "changshi/institution_2020_a"
function getFilePathFromId(id: string): string | null {{
  const parts = id.split('-');
  if (parts.length < 4) return null;

  const source = parts[0]; // institution/national/provincial
  const subject = parts[1]; // xingce/shenlun
  const category = parts[2]; // changshi/panduan/...

  // 去掉最后的题号，重组文件名
  const fileParts = parts.slice(0, -1);
  const filename = fileParts.slice(0).join('_'); // institution_xingce_changshi_2020_a

  // 移除subject部分（文件路径不含xingce/shenlun）
  const cleanFilename = filename.replace(`_${{subject}}`, '');

  return `${{category}}/${{cleanFilename}}`;
}}

// 动态加载题目文件
async function loadFile(filePath: string): Promise<Question[]> {{
  if (loadedFiles.has(filePath)) {{
    return loadedFiles.get(filePath)!;
  }}
  const [category, filename] = filePath.split('/');
  try {{
    const module = await import(`@/data/xingce/${{category}}/${{filename}}.json`);
    const questions = module.default as Question[];
    loadedFiles.set(filePath, questions);
    return questions;
  }} catch (err) {{
    console.error(`Failed to load ${{filePath}}:`, err);
    return [];
  }}
}}

// ========== 导出API ==========

// 按ID获取题目（动态加载）
export async function getQuestionById(id: string): Promise<Question | undefined> {{
  const filePath = getFilePathFromId(id);
  if (!filePath) return undefined;
  const questions = await loadFile(filePath);
  return questions.find(q => q.id === id);
}}

// 筛选题目（返回符合条件的文件路径）
export function filterFiles(params: {{
  subject?: Subject;
  category?: XingceCategory | ShenlunCategory;
  source?: ExamSource;
  level?: ExamLevel;
  year?: number;
  region?: string;
}}): FileIndex[] {{
  let files = index.files;
  if (params.subject) files = files.filter(f => f.subject === params.subject);
  if (params.category) files = files.filter(f => f.category === params.category);
  if (params.source) files = files.filter(f => f.source === params.source);
  if (params.level) files = files.filter(f => f.level === params.level);
  if (params.year) files = files.filter(f => f.year === params.year);
  if (params.region) files = files.filter(f => f.region === params.region);
  return files;
}}

// 批量加载题目（按筛选条件）
export async function filterQuestions(params: {{
  subject?: Subject;
  category?: XingceCategory | ShenlunCategory;
  source?: ExamSource;
  level?: ExamLevel;
  year?: number;
  region?: string;
}}): Promise<Question[]> {{
  const files = filterFiles(params);
  await Promise.all(files.map(f => loadFile(f.path)));
  const allQuestions = Array.from(loadedFiles.values()).flat();

  // 二次过滤（确保精确匹配）
  return allQuestions.filter(q => {{
    if (params.subject && q.subject !== params.subject) return false;
    if (params.category && q.category !== params.category) return false;
    if (params.source && q.source !== params.source) return false;
    if (params.level && q.level !== params.level) return false;
    if (params.year && q.year !== params.year) return false;
    if (params.region && q.region !== params.region) return false;
    return true;
  }});
}}

// 获取所有题目（完整加载，谨慎调用）
export async function getAllQuestions(): Promise<Question[]> {{
  await Promise.all(index.files.map(f => loadFile(f.path)));
  return Array.from(loadedFiles.values()).flat();
}}

// 获取统计信息（基于索引，无需加载题目）
export function getCategoryStats(): Record<string, number> {{
  const stats: Record<string, number> = {{}};
  for (const file of index.files) {{
    const key = `${{file.subject}}/${{file.category}}`;
    stats[key] = (stats[key] || 0) + file.count;
  }}
  return stats;
}}

export function getAvailableYears(): number[] {{
  const years = new Set(index.files.map(f => f.year).filter(Boolean) as number[]);
  return Array.from(years).sort((a, b) => b - a);
}}

export function getAvailableSources(): ExamSource[] {{
  const sources = new Set(index.files.map(f => f.source).filter(Boolean));
  return Array.from(sources) as ExamSource[];
}}

export function getTotalCount(): number {{
  return index.total;
}}

export function getFileCount(): number {{
  return index.files.length;
}}
'''

    OUTPUT_LOADER.write_text(code, encoding='utf-8')
    print(f"生成动态加载器: {OUTPUT_LOADER}")


if __name__ == "__main__":
    print("扫描题库文件...")
    file_index, total_questions = scan_question_files()

    print(f"统计: {total_questions} 题, {len(file_index)} 文件")

    generate_index_json(file_index, total_questions)
    generate_loader_ts(total_questions, len(file_index))

    old_size = Path('src/lib/questionLoader.ts.bak').stat().st_size / 1024 if Path('src/lib/questionLoader.ts.bak').exists() else 0
    new_size = OUTPUT_INDEX.stat().st_size / 1024
    print(f"完成！索引大小: {new_size:.1f} KB (原loader约2800+ KB)")
