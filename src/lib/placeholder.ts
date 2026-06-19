// 占位题检测工具：识别因 OCR/源数据缺失而无法作答的题目
// 用于前端降级 UI（不再让用户看到一堆「[选项 OCR 抽取失败-D11]」原文）
//
// marker 唯一真相源在 src/lib/markers.json，TS 和 Python 都从这里读
// 避免 D-17a simplify skill 揭示的 TS+Python 双份硬编码漂移风险。

import type { Question, Option } from '@/types/question';
import markers from './markers.json';

const OCR_MARKERS = markers.placeholderMarkers;
const SOURCE_PLACEHOLDERS = markers.sourcePlaceholderShort;

export const DERIVED_MARKER = markers.recoveryMarkers.derivedFromExplanation;
export const AIPTA_MARKER = markers.recoveryMarkers.aiptaRescue;
export const WEBSEARCH_MARKER = markers.recoveryMarkers.webSearchRescue;
export const RECOVERY_MARKERS = [DERIVED_MARKER, AIPTA_MARKER, WEBSEARCH_MARKER];

// 单短串占位（避免误判长文里的「暂缺」/「缺失」是正文）
function isShortPlaceholder(s: string): boolean {
  const t = (s || '').trim();
  if (!t) return false;
  // 限定 ≤ 8 字符且整段就是占位词
  return SOURCE_PLACEHOLDERS.some((p) => t === p || t === `${p}。` || t === `${p}.`);
}

export function isPlaceholderText(s: string | undefined | null): boolean {
  if (!s) return false;
  if (OCR_MARKERS.some((m) => s.includes(m))) return true;
  if (s.includes('题目正在全力以赴征集')) return true;
  return isShortPlaceholder(s);
}

export function isPlaceholderOption(opt: Option): boolean {
  return isPlaceholderText(opt.content);
}

// derived marker 不算占位（可作答）；前端用 isDerivedOption 决定是否加角标
export function isDerivedOption(opt: Option): boolean {
  return !!opt.content && RECOVERY_MARKERS.some((m) => opt.content.includes(m));
}

export function stripDerivedMarker(s: string | undefined | null): string {
  if (!s) return '';
  let out = s;
  for (const m of RECOVERY_MARKERS) out = out.replace(m, '');
  return out.trim();
}

// 检测题干是否含数据补全 marker（L-3 可能补题干）
export function isRecoveredText(s: string | undefined | null): boolean {
  if (!s) return false;
  return RECOVERY_MARKERS.some((m) => s.includes(m));
}

// 题目级判定：题干失败 / 4 个选项至少 2 个失败 → 视为占位题（不可作答）
export function isPlaceholderQuestion(q: Question): boolean {
  if (isPlaceholderText(q.content)) return true;
  const opts = q.options || [];
  if (opts.length === 0) return false;
  const bad = opts.filter(isPlaceholderOption).length;
  // 阈值：≥2 个选项坏掉就降级（单坏选项可能用户能猜，2 个就基本无答）
  return bad >= 2;
}

export function getPlaceholderReason(q: Question): string {
  const stemBad = isPlaceholderText(q.content);
  const opts = q.options || [];
  const optBad = opts.filter(isPlaceholderOption).length;
  if (stemBad && optBad > 0) return `题干 + ${optBad} 个选项源数据缺失`;
  if (stemBad) return '题干源数据缺失';
  if (optBad >= 2) return `${optBad} 个选项源数据缺失`;
  if (optBad === 1) return '1 个选项源数据缺失';
  return '源数据缺失';
}

// D-16 H：真不可作答 = 占位题 + 无 questionImage 兜底图
// （占位题 + 有图 = K-4 图像作答模式，仍可作答）
// 用于列表 / 模考过滤，避免给用户列出无法作答的题
export function isUnanswerable(q: Question): boolean {
  return isPlaceholderQuestion(q) && !q.questionImage;
}

export function filterAnswerable<T extends Question>(qs: T[]): T[] {
  return qs.filter((q) => !isUnanswerable(q));
}
