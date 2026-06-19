/**
 * 解析（explanation）富文本预格式化（D-18a P2d-2）
 *
 * 把原始解析文本里常见结构识别后转成 markdown 富格式：
 * - `【解析】xx` / `【答案】xx` / `【点拨】xx` → 加换行 + 加粗头部
 * - `A 项：xx` / `B项：xx` → 各占独立段落 + 加粗头部
 * - `故正确答案为 X` 类总结句 → 转 blockquote 强调段
 *
 * 输入：原始 explanation 字符串
 * 输出：markdown 富格式字符串（仍是 markdown，由 ReactMarkdown 渲染）
 *
 * 不命中任何规则 → 原样返回（向后兼容已写好的解析）
 */
export function formatExplanation(text: string): string {
  if (!text) return text;
  let s = text;

  // 1. 【XX】头标记 → 加换行分段 + 加粗
  //    匹配：【解析|答案|点拨|拓展|注意|考点|思路|要点|提示|注】
  s = s.replace(
    /\s*【(解析|答案|点拨|拓展|注意|考点|思路|要点|提示|注释|注)】\s*/g,
    '\n\n**【$1】** ',
  );

  // 2. 选项分析 A 项：xx / A 项 xx → 各占独立段落 + 加粗头部
  //    实际数据 A/C/D 项常带冒号、B 项常省冒号直接接内容（数据 inconsistency），
  //    两种都识别。`[:：]?` 可有可无，整体包入加粗。
  s = s.replace(
    /([。！？])\s*([ABCDE]\s*项[:：]?)/g,
    '$1\n\n**$2**',
  );

  // 3. 总结句"故正确答案为 X" / "因此答案选 X" → 转 blockquote 强调
  s = s.replace(
    /\s*(故正确答案[为是][ABCDE][。\.]?|因此[，,]?\s*答案[选为是][ABCDE][。\.]?|本题(?:正确)?答案[选为是][ABCDE][。\.]?)\s*$/,
    '\n\n> **$1**',
  );

  // 清掉文本首部多余的换行
  return s.replace(/^\n+/, '').trim();
}
