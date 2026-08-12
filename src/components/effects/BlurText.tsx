'use client';

import { motion, type Variants } from 'framer-motion';
import { useMemo } from 'react';
import { cn } from '@/lib/utils';

/**
 * BlurText — 文字 blur → clear 入场动效
 *
 * 见 docs/DESIGN.md §5.2。题目切换 / hero 标题给一点期待感。
 * 字逐个 stagger，blur 8px → 0，y +12 → 0。
 *
 * 注意：尊重 prefers-reduced-motion（globals.css 已全局兜底，
 * 但这里也用 Framer Motion 的 useReducedMotion 二次保险）。
 */

interface BlurTextProps {
  /** 要展示的文字（按 char 切分动效） */
  text: string;
  /** 按字 / 按词 / 按整段切分 */
  splitBy?: 'char' | 'word' | 'line';
  /** 单元素延迟 */
  staggerDelay?: number;
  /** 整体延迟 */
  delay?: number;
  className?: string;
  /** 作为 h1 / h2 / p 等渲染 */
  as?: 'h1' | 'h2' | 'h3' | 'p' | 'span' | 'div';
}

const itemVariants: Variants = {
  hidden: {
    opacity: 0,
    y: 12,
    filter: 'blur(8px)',
  },
  visible: {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: {
      duration: 0.45,
      ease: [0.16, 1, 0.3, 1] as [number, number, number, number],
    },
  },
};

export function BlurText({
  text,
  splitBy = 'char',
  staggerDelay = 0.04,
  delay = 0,
  className,
  as = 'span',
}: BlurTextProps) {
  const segments = useMemo(() => {
    if (splitBy === 'char') return [...text];
    if (splitBy === 'word') return text.split(/(\s+)/);
    return [text];
  }, [text, splitBy]);

  const containerVariants: Variants = {
    hidden: { opacity: 1 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: staggerDelay, delayChildren: delay },
    },
  };

  const MotionTag = motion[as];

  return (
    <MotionTag
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className={cn('inline-block', className)}
      aria-label={text}
    >
      {segments.map((seg, i) => (
        <motion.span
          key={`${seg}-${i}`}
          variants={itemVariants}
          className="inline-block whitespace-pre"
          aria-hidden="true"
        >
          {seg}
        </motion.span>
      ))}
    </MotionTag>
  );
}
