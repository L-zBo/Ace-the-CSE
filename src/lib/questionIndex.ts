// 题目索引：只含列表页 / 筛选 / 统计需要的元数据，不含正文。
//
// 为什么存在：旧 questionLoader 用 1381 条静态 import 把整个题库打进 bundle，
// 单个客户端 chunk 62.5 MB、dev 进程常驻 6 GB。正文改由 questionLoader 按试卷
// 懒加载，本模块只提供同步可用的轻量元数据（约 1.3 MB）。
//
// 数据由 python scripts/generate_question_index.py 生成，请勿手改 JSON。

import raw from '@/data/index/question-index.json';
import type {
  Subject,
  XingceCategory,
  ShenlunCategory,
  ExamSource,
  ExamLevel,
} from '@/types/question';

export interface QuestionMeta {
  id: string;
  subject: Subject;
  category: XingceCategory | ShenlunCategory;
  source: ExamSource;
  level?: ExamLevel;
  year: number;
  region?: string;
  /** 短答案（行测客观题）。申论不自动判分，为空串。 */
  answer: string;
  /** 所属试卷，形如 `xingce/changshi/national_2024_dishi`，用于懒加载定位。 */
  paperKey: string;
  /** 占位题且无兜底图 —— 与 placeholder.ts 的 isUnanswerable 等价 */
  unanswerable: boolean;
  hasImage: boolean;
}

interface RawPaper {
  k: string;
  s: string;
  c: string;
  o: string | null;
  l: string | null;
  y: number | null;
  r: string | null;
}

type RawRow = [string, number, string, number, string?];

const FLAG_UNANSWERABLE = 1;
const FLAG_HAS_IMAGE = 2;

const papers = raw.papers as RawPaper[];
const rows = raw.questions as unknown as RawRow[];

// 一次性展开成对象数组。1380 个试卷字段共享，避免每题重复存字符串。
const index: QuestionMeta[] = rows.map((row) => {
  const p = papers[row[1]];
  return {
    id: row[0],
    subject: p.s as Subject,
    category: (row[4] ?? p.c) as XingceCategory | ShenlunCategory,
    source: p.o as ExamSource,
    level: (p.l ?? undefined) as ExamLevel | undefined,
    year: p.y ?? 0,
    region: p.r ?? undefined,
    answer: row[2],
    paperKey: p.k,
    unanswerable: (row[3] & FLAG_UNANSWERABLE) !== 0,
    hasImage: (row[3] & FLAG_HAS_IMAGE) !== 0,
  };
});

const byId = new Map<string, QuestionMeta>(index.map((m) => [m.id, m]));

/** 全部题目元数据（同步）。注意：不含题干/选项/解析。 */
export function getQuestionIndex(): QuestionMeta[] {
  return index;
}

/** 可作答题目元数据 —— 等价于旧代码的 filterAnswerable(getAllQuestions())。 */
export function getAnswerableIndex(): QuestionMeta[] {
  return index.filter((m) => !m.unanswerable);
}

export function getMetaById(id: string): QuestionMeta | undefined {
  return byId.get(id);
}

export interface IndexFilter {
  subject?: Subject;
  category?: XingceCategory | ShenlunCategory;
  source?: ExamSource;
  level?: ExamLevel;
  year?: number;
  region?: string;
  /** 默认 false；true 时排除不可作答题 */
  answerableOnly?: boolean;
}

export function filterIndex(params: IndexFilter): QuestionMeta[] {
  return index.filter((m) => {
    if (params.subject && m.subject !== params.subject) return false;
    if (params.category && m.category !== params.category) return false;
    if (params.source && m.source !== params.source) return false;
    if (params.level && m.level !== params.level) return false;
    if (params.year && m.year !== params.year) return false;
    if (params.region && m.region !== params.region) return false;
    if (params.answerableOnly && m.unanswerable) return false;
    return true;
  });
}

export function getAvailableYears(): number[] {
  return Array.from(new Set(index.map((m) => m.year))).sort((a, b) => b - a);
}

export function getAvailableSources(): ExamSource[] {
  return Array.from(new Set(index.map((m) => m.source))) as ExamSource[];
}

export function getCategoryStats(): Record<string, number> {
  const stats: Record<string, number> = {};
  for (const m of index) {
    const key = `${m.subject}/${m.category}`;
    stats[key] = (stats[key] || 0) + 1;
  }
  return stats;
}
