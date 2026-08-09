// 题库访问层：元数据走同步索引，正文按试卷懒加载。
//
// ⚠️ 架构变更（2026-08-09）
// 旧版本这里是自动生成的 2847 行文件，用 1381 条静态 import 把整个题库塞进 bundle：
//   - 单个客户端 chunk 62.5 MB（用户打开 /practice 就要下这么多 JS）
//   - dev 进程常驻 6 GB，长时间运行后渲染 worker OOM
//   - 生产构建编译约 16 分钟
// 旧文件在 git 历史里：git show <本次提交>^:src/lib/questionLoader.ts
//
// 现在拆成两层：
//   - src/lib/questionIndex.ts  同步元数据（约 1.3 MB，够列表/筛选/统计用）
//   - 本模块                     按 paperKey dynamic import() 拉正文，用到才下载
//
// 因此取正文的接口一律是异步的。只要元数据就用 questionIndex，别在这里 await。

import type { Question } from '@/types/question';
import {
  getQuestionIndex,
  getMetaById,
  filterIndex,
  type IndexFilter,
  type QuestionMeta,
} from './questionIndex';

export type { QuestionMeta, IndexFilter };
export {
  getQuestionIndex,
  getAnswerableIndex,
  getMetaById,
  filterIndex,
  getAvailableYears,
  getAvailableSources,
  getCategoryStats,
} from './questionIndex';

// 已加载试卷缓存。同一试卷只解析一次，翻页时不会重复下载。
const paperCache = new Map<string, Question[]>();
const inflight = new Map<string, Promise<Question[]>>();

/**
 * 加载单份试卷的全部题目。
 *
 * paperKey 形如 `xingce/changshi/national_2024_dishi`，来自 QuestionMeta.paperKey。
 * 这里故意用模板字符串而不是 1380 条显式 import：webpack 会为 ../data 下的 JSON
 * 建 context 并逐个切分 chunk，效果一样但不用维护一张巨表。
 */
export async function loadPaper(paperKey: string): Promise<Question[]> {
  const cached = paperCache.get(paperKey);
  if (cached) return cached;

  const pending = inflight.get(paperKey);
  if (pending) return pending;

  const task = import(`../data/${paperKey}.json`)
    .then((mod) => {
      const list = ((mod as { default: unknown }).default ?? mod) as Question[];
      paperCache.set(paperKey, list);
      inflight.delete(paperKey);
      return list;
    })
    .catch((err) => {
      inflight.delete(paperKey);
      console.error(`[questionLoader] 加载试卷失败: ${paperKey}`, err);
      return [] as Question[];
    });

  inflight.set(paperKey, task);
  return task;
}

/** 按 id 取单题正文。找不到元数据直接返回 undefined，不会去翻整个题库。 */
export async function loadQuestionById(
  id: string,
): Promise<Question | undefined> {
  const meta = getMetaById(id);
  if (!meta) return undefined;
  const paper = await loadPaper(meta.paperKey);
  return paper.find((q) => q.id === id);
}

/**
 * 批量取正文。按试卷分组后并行加载，返回顺序与传入的 ids 一致；
 * 查不到的 id 会被丢弃（不会塞 undefined 进数组）。
 */
export async function loadQuestionsByIds(ids: string[]): Promise<Question[]> {
  const needed = new Set<string>();
  for (const id of ids) {
    const meta = getMetaById(id);
    if (meta) needed.add(meta.paperKey);
  }
  await Promise.all(Array.from(needed).map(loadPaper));

  const out: Question[] = [];
  for (const id of ids) {
    const meta = getMetaById(id);
    if (!meta) continue;
    const q = paperCache.get(meta.paperKey)?.find((item) => item.id === id);
    if (q) out.push(q);
  }
  return out;
}

/** 先按元数据筛选，再把命中的题目正文一次性拉回来。 */
export async function loadFilteredQuestions(
  params: IndexFilter,
): Promise<Question[]> {
  return loadQuestionsByIds(filterIndex(params).map((m) => m.id));
}

/**
 * 全量题目正文 —— 会把 1380 份试卷全部拉进内存，**只给构建期用**
 * （静态导出时枚举动态路由）。前端任何页面都不要调它。
 */
export async function loadAllQuestions(): Promise<Question[]> {
  const keys = Array.from(new Set(getQuestionIndex().map((m) => m.paperKey)));
  const papers = await Promise.all(keys.map(loadPaper));
  return papers.flat();
}
