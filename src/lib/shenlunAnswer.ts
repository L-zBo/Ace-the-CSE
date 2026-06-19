/**
 * 申论 answer 字段文本解析 / 关键词提取 / 命中率评分。
 *
 * 数据结构散乱 — 只做轻量识别：
 *   - 有 【问题X参考答案】 模板：按题号拆块
 *   - 有 【标题的优点】 等分析标记：把作文题末块拆成 essayModel + essayAnalysis
 *   - 都没有：单块兜底
 */

export interface AnswerBlock {
  title: string;
  bodyMd: string;
  points: string[];
}

export interface ParsedAnswer {
  blocks: AnswerBlock[];
  essayModel?: string;
  essayAnalysis?: string;
}

const ZH_NUM = '一二三四五六七八九十';

export function parseShenlunAnswer(raw: string): ParsedAnswer {
  if (!raw || !raw.trim()) {
    return { blocks: [{ title: '参考答案', bodyMd: '', points: [] }] };
  }

  // PDF 抽文字常在逻辑行末加 \n 而段落间 \n\n；合并单换行让 regex 能抓跨行要点。
  const normalized = raw.replace(/([^\n])\n(?!\n|【|\s*\d+[.．、])/g, '$1');

  const headerRegex = new RegExp(`【(问题[${ZH_NUM}]+参考答案)】`, 'g');
  const hits: { title: string; start: number; end: number }[] = [];
  let m: RegExpExecArray | null;
  while ((m = headerRegex.exec(normalized))) {
    hits.push({
      title: m[1].replace('参考答案', ''),
      start: m.index,
      end: m.index + m[0].length,
    });
  }

  let blocks: AnswerBlock[];
  if (hits.length === 0) {
    blocks = [{ title: '参考答案', bodyMd: normalized.trim(), points: extractKeywords(normalized) }];
  } else {
    blocks = hits.map((h, i) => {
      const bodyStart = h.end;
      const bodyEnd = i + 1 < hits.length ? hits[i + 1].start : normalized.length;
      const bodyMd = normalized.slice(bodyStart, bodyEnd).trim();
      return { title: h.title, bodyMd, points: extractKeywords(bodyMd) };
    });
  }

  // 尝试把末块里的"范文 + 文章分析"拆出来（作文题常见）
  let essayModel: string | undefined;
  let essayAnalysis: string | undefined;
  const last = blocks[blocks.length - 1];
  const analysisMarker = /【(标题的优点|开头的优点|论述段\d+的优点|论述段之间的关系|结尾的优点)/;
  const idx = last.bodyMd.search(analysisMarker);
  if (idx > 50) {
    essayModel = last.bodyMd.slice(0, idx).replace(/\n?文章分析\s*$/m, '').trim();
    essayAnalysis = last.bodyMd.slice(idx).trim();
    last.bodyMd = '（正文与分析见下方「范文」「文章分析」标签）';
    last.points = []; // 作文题不生成要点（文字自由，命中无意义）
  }

  return { blocks, essayModel, essayAnalysis };
}

const STOP_WORDS = new Set([
  '参考答案', '问题', '我们', '可以', '应该', '通过', '以及', '并且', '因此',
  '这些', '这种', '具有', '进行', '方面', '对策', '一是', '二是', '三是', '四是', '五是',
  '内容', '工作', '发展', '建设', '重要', '充分', '不断', '积极', '加强', '提供',
  '实现', '推动', '完善', '进一步', '相关', '有关', '同时', '目前',
  '他们', '她们', '我是', '如果', '但是', '虽然', '普通', '平凡', '需要', '存在',
  '才能', '一种', '一个', '表现', '成为', '非常', '开展', '利用',
]);

export function extractKeywords(raw: string): string[] {
  if (!raw) return [];
  const kws: string[] = [];
  const seen = new Set<string>();

  // 要点标题：行首"1. XXX。" 或 "一、XXX："
  const pointRegex = /(?:^|\n)\s*(?:\d+|[一二三四五六七八九十]+)[.．、：]\s*([^。；，：\n]{3,12})[。；，：]/g;
  let m: RegExpExecArray | null;
  while ((m = pointRegex.exec(raw))) {
    const kw = m[1].trim().replace(/\s+/g, '');
    if (kw.length < 3 || kw.length > 12) continue;
    if (STOP_WORDS.has(kw)) continue;
    if (/[。\n]/.test(kw)) continue; // 带换行/句号的噪声
    if (seen.has(kw)) continue;
    seen.add(kw);
    kws.push(kw);
    if (kws.length >= 5) return kws; // 每块最多 5 个要点
  }

  if (kws.length >= 2) return kws;

  // 兜底：按词频抽 2-5 字中文短语 Top 5（TF）
  const freq = new Map<string, number>();
  const phraseRegex = /[\u4e00-\u9fa5]{2,5}/g;
  while ((m = phraseRegex.exec(raw))) {
    const p = m[0];
    if (STOP_WORDS.has(p)) continue;
    freq.set(p, (freq.get(p) || 0) + 1);
  }
  const sorted = [...freq.entries()].sort((a, b) => b[1] - a[1]);
  for (const [p, c] of sorted) {
    if (c < 2) break;
    if (!seen.has(p)) {
      seen.add(p);
      kws.push(p);
      if (kws.length >= 5) break;
    }
  }
  return kws;
}

export interface ScoreResult {
  hit: string[];
  miss: string[];
  rate: number;
}

/**
 * 用户文本命中判断：关键词按标点（、，,/／|）切 subparts，命中任一 subpart 即算命中。
 * 示例："接近、启发村民" 拆成 ["接近", "启发村民"]，用户写 "接近村民" 能命中（含 "接近"）。
 */
export function scoreMatch(userText: string, keywords: string[]): ScoreResult {
  if (!keywords.length) return { hit: [], miss: [], rate: 0 };
  const hit: string[] = [];
  const miss: string[] = [];
  const text = userText || '';
  for (const k of keywords) {
    const parts = k.split(/[、，,／\/|；]/).map((s) => s.trim()).filter((s) => s.length >= 2);
    const matched = parts.length > 0
      ? parts.some((p) => text.includes(p))
      : text.includes(k);
    if (matched) hit.push(k);
    else miss.push(k);
  }
  return { hit, miss, rate: hit.length / keywords.length };
}
