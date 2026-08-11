// 跨卷同题关联：「这道题在 X 年 Y 卷也考过」。
//
// 真题本来就跨省、跨年共用题池，全库审计里 `dup_cross_paper` 有两千多组。
// 那不是缺陷，把它反过来当成功能：做完一道题，顺带看到它还在哪几套卷里出现过。
//
// 数据由 python scripts/generate_cross_paper_links.py 生成。指纹口径严格
// （占位题、图形题、裸字母选项一律不参与），宁可漏也不错报 —— 关联点过去
// 发现是另一道题，比不给关联更糟。
//
// 约 300 KB，只在答题页展开解析时 dynamic import，不进首屏 bundle。

export interface RelatedAppearance {
  /** 同一道题在另一份卷里的题目 id，可直接跳 /practice/{id} */
  id: string;
  /** 卷标签，形如「2020年事业编行测（a）」 */
  paperLabel: string;
  /** 该卷内的题号；0 表示原始数据里没有题号 */
  qno: number;
}

interface LinkData {
  paperLabels: string[];
  groups: [string, number, number][][];
}

interface Resolved {
  labels: string[];
  groups: [string, number, number][][];
  /** 题目 id -> 所在组下标 */
  byId: Map<string, number>;
}

let resolving: Promise<Resolved> | null = null;

function load(): Promise<Resolved> {
  if (!resolving) {
    resolving = import('@/data/index/cross-paper-links.json')
      .then((mod) => {
        const data = ((mod as { default: unknown }).default ?? mod) as LinkData;
        const byId = new Map<string, number>();
        data.groups.forEach((group, gi) => {
          for (const row of group) byId.set(row[0], gi);
        });
        return { labels: data.paperLabels, groups: data.groups, byId };
      })
      .catch((err) => {
        console.error('[relatedQuestions] 关联数据加载失败', err);
        // 失败就当没有关联，不能让答题页跟着挂
        resolving = null;
        return { labels: [], groups: [], byId: new Map<string, number>() };
      });
  }
  return resolving;
}

/**
 * 取这道题在别的卷里的出现记录（不含自己）。没有关联时返回空数组。
 */
export async function loadRelatedAppearances(
  questionId: string,
): Promise<RelatedAppearance[]> {
  if (!questionId) return [];
  const { labels, groups, byId } = await load();
  const gi = byId.get(questionId);
  if (gi === undefined) return [];
  return groups[gi]
    .filter((row) => row[0] !== questionId)
    .map((row) => ({
      id: row[0],
      paperLabel: labels[row[1]] ?? '',
      qno: row[2],
    }));
}
