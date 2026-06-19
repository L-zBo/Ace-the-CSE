import { type HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

/**
 * Skeleton — 加载占位
 *
 * 见 DESIGN.md §4.4。脉冲动画占位，替代白屏加载。
 *
 * 用法：
 *   <Skeleton className="h-4 w-full" />
 *   <Skeleton className="h-24" />
 */

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  /** 圆角变体 */
  rounded?: 'sm' | 'md' | 'lg' | 'full';
}

const roundedClasses = {
  sm: 'rounded',
  md: 'rounded-lg',
  lg: 'rounded-xl',
  full: 'rounded-full',
};

export function Skeleton({ className, rounded = 'md', ...props }: SkeletonProps) {
  return (
    <div
      role="status"
      aria-busy="true"
      aria-label="加载中"
      className={cn(
        'animate-pulse bg-white/8 border border-white/5',
        roundedClasses[rounded],
        className,
      )}
      {...props}
    />
  );
}
