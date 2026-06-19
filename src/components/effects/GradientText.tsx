'use client';

import { type ReactNode } from 'react';
import { cn } from '@/lib/utils';

/**
 * GradientText — 墨蓝 → 印章红渐变流动文本（D-18a P2b-3）
 *
 * 卷面气质 hero 标题专用，替代 BlurText 在 hero 场景的位置。
 * 灵感参考 react-bits GradientText，使用 background-clip:text + 关键帧
 * 位移实现，无外部依赖。
 *
 * 用法：
 *   <GradientText>Ace the CSE</GradientText>
 *   <GradientText animate={false} className="text-5xl">静态版</GradientText>
 */
interface GradientTextProps {
  children: ReactNode;
  className?: string;
  /** 渐变背景位移动画，默认开 */
  animate?: boolean;
  /** 渐变色阶变体：default = 墨蓝→印章红；ink = 墨蓝单调；seal = 印章红单调 */
  variant?: 'default' | 'ink' | 'seal';
}

const variantClasses: Record<NonNullable<GradientTextProps['variant']>, string> = {
  default: 'from-brand-600 via-brand-400 to-seal-500',
  ink: 'from-brand-900 via-brand-600 to-brand-300',
  seal: 'from-seal-700 via-seal-500 to-seal-300',
};

export function GradientText({
  children,
  className,
  animate = true,
  variant = 'default',
}: GradientTextProps) {
  return (
    <span
      className={cn(
        'inline-block bg-gradient-to-r bg-clip-text text-transparent',
        variantClasses[variant],
        animate && 'animate-gradient-shift bg-[length:200%_auto]',
        className,
      )}
    >
      {children}
    </span>
  );
}
