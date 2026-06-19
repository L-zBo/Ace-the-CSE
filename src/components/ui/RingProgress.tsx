'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

/**
 * RingProgress — 环形进度图（D-18a P3e 升级）
 *
 * 给学习计划完成度 / 自定义比例 用。SVG 双 circle 叠加（背景 + 前景），
 * stroke-dasharray 控制弧长，motion 给前景 strokeDashoffset 入场动画。
 *
 * 用法：
 *   <RingProgress percentage={68} size={96} />
 */
interface RingProgressProps {
  /** 0-100 */
  percentage: number;
  /** 整体直径 px，默认 96 */
  size?: number;
  /** 描边宽度 px，默认 8 */
  strokeWidth?: number;
  /** 前景渐变（CSS gradient string），默认墨蓝→印章红 */
  className?: string;
  /** 中心标签覆写，默认百分比数字 */
  label?: React.ReactNode;
  /** 中心 sub-label（小字） */
  subLabel?: React.ReactNode;
}

export function RingProgress({
  percentage,
  size = 96,
  strokeWidth = 8,
  className,
  label,
  subLabel,
}: RingProgressProps) {
  const clamped = Math.max(0, Math.min(100, percentage));
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (clamped / 100) * circumference;
  const gradientId = `ring-progress-grad-${size}`;

  return (
    <div
      role="img"
      aria-label={`进度 ${clamped}%`}
      className={cn('relative inline-flex items-center justify-center', className)}
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="-rotate-90">
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--brand)" />
            <stop offset="100%" stopColor="var(--seal-red)" />
          </linearGradient>
        </defs>
        {/* 背景圈 */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="var(--border)"
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* 前景圈（卷面气质渐变）*/}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={`url(#${gradientId})`}
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display-en text-xl font-bold leading-none tabular-nums text-foreground">
          {label ?? `${clamped}%`}
        </span>
        {subLabel && (
          <span className="mt-0.5 text-[10px] text-foreground-muted">{subLabel}</span>
        )}
      </div>
    </div>
  );
}
