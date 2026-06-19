import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// 合并 class names（智能处理 Tailwind 冲突：bg-red-500 bg-blue-500 → bg-blue-500）
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// 格式化时间 (秒 -> mm:ss 或 hh:mm:ss)
export function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) {
    return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

// 格式化日期
export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

// 今日日期字符串
export function getTodayString(): string {
  return formatDate(new Date());
}

// 计算百分比
export function calcPercentage(part: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((part / total) * 100);
}

// 生成唯一 ID
export function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2);
}

// 打乱数组
export function shuffle<T>(array: T[]): T[] {
  const arr = [...array];
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}
