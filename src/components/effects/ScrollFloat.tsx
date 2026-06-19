'use client';

import { useRef, type ReactNode } from 'react';
import { motion, useInView, type UseInViewOptions } from 'framer-motion';
import { cn } from '@/lib/utils';

/**
 * ScrollFloat — 滚动到视口时"浮现"入场（D-18a P2b-3）
 *
 * 灵感参考 react-bits ScrollFloat。给长解析段落 / 申论范文段 用，
 * 配 viewport once + threshold，避免重复触发。
 *
 * 默认动效：opacity 0→1 + y 16→0 + filter blur(4px)→0，duration 0.5s。
 * reduced-motion 自动降级（globals.css 全局规则）。
 */
interface ScrollFloatProps {
  children: ReactNode;
  className?: string;
  /** 入场延迟（秒），默认 0 */
  delay?: number;
  /** 入场动画时长（秒），默认 0.5 */
  duration?: number;
  /** 触发阈值（0-1），默认 0.2 */
  amount?: UseInViewOptions['amount'];
  /** 只触发一次（默认 true，避免来回滚动时重复闪烁）*/
  once?: boolean;
}

export function ScrollFloat({
  children,
  className,
  delay = 0,
  duration = 0.5,
  amount = 0.2,
  once = true,
}: ScrollFloatProps) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { amount, once });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 16, filter: 'blur(4px)' }}
      animate={inView ? { opacity: 1, y: 0, filter: 'blur(0px)' } : {}}
      transition={{ duration, delay, ease: [0.16, 1, 0.3, 1] }}
      className={cn(className)}
    >
      {children}
    </motion.div>
  );
}
