// 地区 / 层级中文名。数据来自 src/lib/regions.json —— 与 Python 脚本共用同一份
// 真相源，避免前端显示「浙江」而脚本写出「zhejiang」这类两头不一致。
//
// 新增省份请改 regions.json，不要在这里硬编码。

import raw from './regions.json';

export const PROVINCE_NAMES: Record<string, string> = raw.provinces;
export const LEVEL_NAMES: Record<string, string> = raw.levels;

/** 拿不到中文名时原样返回，宁可显示拼音也不显示空白。 */
export function provinceName(key?: string | null): string {
  if (!key) return '';
  return PROVINCE_NAMES[key] ?? key;
}

export function levelName(key?: string | null): string {
  if (!key) return '';
  return LEVEL_NAMES[key] ?? key;
}
