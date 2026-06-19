'use client';

import { animate, useInView, useMotionValue, useTransform } from 'framer-motion';
import { useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';

/**
 * CountUp — 数字滚动到目标值
 *
 * 见 DESIGN.md §5.3。统计页 / 首页今日数据数字滚动。
 * easeOutCubic 800ms（短促有节制，不刷屏）。
 */

interface CountUpProps {
  /** 目标值 */
  to: number;
  /** 起始值，默认 0 */
  from?: number;
  /** 滚动时长（ms），默认 800 */
  duration?: number;
  /** 小数位数 */
  decimals?: number;
  /** 千位分隔符 */
  thousandSeparator?: boolean;
  /** 后缀（如 % / 题 / 天） */
  suffix?: string;
  /** 前缀（如 ¥） */
  prefix?: string;
  className?: string;
  /** 是否在进入视口时才开始（默认 true，避免首屏外的浪费） */
  startOnView?: boolean;
}

export function CountUp({
  to,
  from = 0,
  duration = 800,
  decimals = 0,
  thousandSeparator = false,
  suffix = '',
  prefix = '',
  className,
  startOnView = true,
}: CountUpProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: '0px 0px -50px 0px' });
  const count = useMotionValue(from);
  const rounded = useTransform(count, (v) => {
    const fixed = v.toFixed(decimals);
    if (thousandSeparator) {
      const [int, dec] = fixed.split('.');
      return `${int.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}${dec ? `.${dec}` : ''}`;
    }
    return fixed;
  });

  useEffect(() => {
    if (startOnView && !inView) return;
    const controls = animate(count, to, {
      duration: duration / 1000,
      ease: [0.33, 1, 0.68, 1], // easeOutCubic
    });
    return controls.stop;
  }, [count, to, duration, inView, startOnView]);

  useEffect(() => {
    return rounded.on('change', (v) => {
      if (ref.current) ref.current.textContent = `${prefix}${v}${suffix}`;
    });
  }, [rounded, prefix, suffix]);

  return (
    <span
      ref={ref}
      className={cn('tabular-nums', className)}
      aria-label={`${prefix}${to}${suffix}`}
    >
      {prefix}
      {from.toFixed(decimals)}
      {suffix}
    </span>
  );
}
