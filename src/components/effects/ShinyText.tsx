'use client';

import { cn } from '@/lib/utils';

/**
 * ShinyText — 印章红强调字 + 光泽扫过动效
 *
 * 见 docs/DESIGN.md §5。重点字 / hero 副标 / 重要提示用。
 * 仅 CSS 动效，无 JS 开销。
 *
 * 注意：颜色基底用印章红渐变，光泽走顶层 mask 扫过。
 */

interface ShinyTextProps {
  children: React.ReactNode;
  /** 是否启用光泽动效（默认 true） */
  shimmer?: boolean;
  /** 光泽周期（秒），默认 3 */
  duration?: number;
  /** 颜色变体 */
  variant?: 'seal' | 'brand' | 'gold';
  className?: string;
}

const variantClasses: Record<NonNullable<ShinyTextProps['variant']>, string> = {
  seal: 'bg-gradient-to-r from-[#7c1d1d] via-[#e85d5d] to-[#c1272d] bg-clip-text text-transparent',
  brand:
    'bg-gradient-to-r from-[#0f2942] via-[#2c5282] to-[#1e3a5f] bg-clip-text text-transparent',
  gold: 'bg-gradient-to-r from-[#92400e] via-[#f59e0b] to-[#d97706] bg-clip-text text-transparent',
};

export function ShinyText({
  children,
  shimmer = true,
  duration = 3,
  variant = 'seal',
  className,
}: ShinyTextProps) {
  return (
    <span
      className={cn(
        'inline-block bg-[length:200%_100%] font-semibold',
        variantClasses[variant],
        shimmer && 'animate-shiny-text',
        className,
      )}
      style={
        shimmer
          ? ({
              animationDuration: `${duration}s`,
            } as React.CSSProperties)
          : undefined
      }
    >
      {children}
    </span>
  );
}
