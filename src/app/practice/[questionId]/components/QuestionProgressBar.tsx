'use client';

import { motion } from 'framer-motion';

interface QuestionProgressBarProps {
  currentIndex: number;
  total: number;
}

export function QuestionProgressBar({ currentIndex, total }: QuestionProgressBarProps) {
  const percent = total > 0 ? ((currentIndex + 1) / total) * 100 : 0;
  return (
    <div
      className="mb-6 h-1 overflow-hidden rounded-full bg-white/10"
      role="progressbar"
      aria-label="练习进度"
      aria-valuenow={currentIndex + 1}
      aria-valuemin={1}
      aria-valuemax={total}
    >
      <motion.div
        className="h-full rounded-full bg-gradient-to-r from-brand-deep via-brand to-brand-soft"
        initial={false}
        animate={{ width: `${percent}%` }}
        transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
      />
    </div>
  );
}
