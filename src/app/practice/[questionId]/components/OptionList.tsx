'use client';

import { motion } from 'framer-motion';
import { CheckCircle2, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  isDerivedOption,
  isPlaceholderOption,
  stripDerivedMarker,
} from '@/lib/placeholder';
import type { Question } from '@/types/question';

type Option = NonNullable<Question['options']>[number];

interface OptionListProps {
  options: Option[];
  /** 当前选中的 option label */
  selected: string | null;
  /** 是否已提交（决定 hover/disabled 与是否显示正误） */
  isSubmitted: boolean;
  /** 正确答案 label（单或多） */
  answer: string | string[];
  /** 图像作答模式（占位选项 + 有 questionImage 时允许凭图选） */
  imageFallback: boolean;
  onSelect: (label: string) => void;
}

/**
 * OptionList — 答题选项列表
 *
 * 5 种态：
 *  - normal: 未提交、未选中
 *  - selected: 未提交、当前选中
 *  - correct: 已提交、是答案
 *  - wrong:   已提交、用户错选
 *  - disabled-placeholder: 选项源数据缺失且非图像作答
 */
export function OptionList({
  options,
  selected,
  isSubmitted,
  answer,
  imageFallback,
  onSelect,
}: OptionListProps) {
  const answerSet = Array.isArray(answer) ? new Set(answer) : new Set([answer]);

  return (
    <div className="mb-6 space-y-3">
      {options.map((opt) => {
        const isSelected = selected === opt.label;
        const isAnswer = isSubmitted && answerSet.has(opt.label);
        const isWrong = isSubmitted && isSelected && !isAnswer;
        const isFigureOpt =
          opt.content === '[见图]' || opt.content === '[图形选项]';
        const rawOptBad = isPlaceholderOption(opt);
        const isOptBad = rawOptBad && !imageFallback;
        const isDerivedOpt = isDerivedOption(opt);
        const placeholderInImageMode = imageFallback && rawOptBad;

        return (
          <motion.button
            key={opt.label}
            id={`option-${opt.label}`}
            type="button"
            whileHover={
              !isSubmitted && !isOptBad ? { scale: 1.01, y: -1 } : undefined
            }
            whileTap={!isOptBad ? { scale: 0.98 } : undefined}
            onClick={() => !isSubmitted && !isOptBad && onSelect(opt.label)}
            disabled={isSubmitted || isOptBad}
            aria-pressed={isSelected}
            className={cn(
              'group flex w-full items-start gap-3 rounded-xl border p-4 text-left',
              'transition-[box-shadow,background-color,border-color] duration-200 ease-out',
              'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand',
              optionStateClass({
                isOptBad,
                isSubmitted,
                isSelected,
                isAnswer,
                isWrong,
              }),
            )}
          >
            <span
              className={cn(
                'mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-sm font-semibold',
                'transition-colors duration-200',
                optionLabelBadgeClass({
                  isOptBad,
                  isSubmitted,
                  isSelected,
                  isAnswer,
                  isWrong,
                }),
              )}
              aria-hidden="true"
            >
              {isSubmitted && isAnswer ? (
                <CheckCircle2 size={16} />
              ) : isWrong ? (
                <XCircle size={16} />
              ) : (
                opt.label
              )}
            </span>

            <OptionBody
              opt={opt}
              isOptBad={isOptBad}
              placeholderInImageMode={placeholderInImageMode}
              isFigureOpt={isFigureOpt}
              isDerivedOpt={isDerivedOpt}
            />
          </motion.button>
        );
      })}
    </div>
  );
}

function optionStateClass(s: {
  isOptBad: boolean;
  isSubmitted: boolean;
  isSelected: boolean;
  isAnswer: boolean;
  isWrong: boolean;
}): string {
  if (s.isOptBad) {
    return 'cursor-not-allowed border-dashed border-border bg-surface-2/30 opacity-60';
  }
  if (!s.isSubmitted) {
    return s.isSelected
      ? 'border-brand bg-brand/10 shadow-md shadow-brand/15'
      : 'border-border bg-card backdrop-blur-md hover:border-brand-soft/60 hover:bg-card-hover hover:shadow-md';
  }
  if (s.isAnswer) {
    return 'border-success bg-success/10 shadow-md shadow-success/10';
  }
  if (s.isWrong) {
    return 'border-danger bg-danger/10 shadow-md shadow-danger/10';
  }
  return 'border-border bg-card opacity-50';
}

function optionLabelBadgeClass(s: {
  isOptBad: boolean;
  isSubmitted: boolean;
  isSelected: boolean;
  isAnswer: boolean;
  isWrong: boolean;
}): string {
  if (s.isOptBad) return 'border-border text-foreground-muted';
  if (!s.isSubmitted) {
    return s.isSelected
      ? 'border-brand bg-brand text-white shadow-md shadow-brand/30'
      : 'border-white/25 bg-white/[0.06] text-foreground group-hover:border-brand-soft group-hover:bg-brand/15 group-hover:text-white';
  }
  if (s.isAnswer) return 'border-success bg-success text-white';
  if (s.isWrong) return 'border-danger bg-danger text-white';
  return 'border-border text-foreground-faint';
}

interface OptionBodyProps {
  opt: Option;
  isOptBad: boolean;
  placeholderInImageMode: boolean;
  isFigureOpt: boolean;
  isDerivedOpt: boolean;
}

function OptionBody({
  opt,
  isOptBad,
  placeholderInImageMode,
  isFigureOpt,
  isDerivedOpt,
}: OptionBodyProps) {
  if (isOptBad) {
    return (
      <span className="pt-0.5 text-sm italic text-foreground-muted">
        （选项 {opt.label} 源数据缺失）
      </span>
    );
  }
  if (placeholderInImageMode) {
    return (
      <span className="pt-0.5 text-sm text-foreground-muted">
        凭图选 {opt.label}
      </span>
    );
  }
  if (isFigureOpt) {
    return (
      <span className="pt-0.5 text-foreground-muted">
        选项 {opt.label}（见上图）
      </span>
    );
  }
  if (isDerivedOpt) {
    return (
      <span className="flex flex-1 items-start gap-2 pt-0.5">
        <span className="flex-1 text-base leading-relaxed text-foreground">
          {stripDerivedMarker(opt.content)}
        </span>
        <span
          className="shrink-0 rounded-full border border-warning/40 bg-warning/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-warning"
          title="此选项由解析文本推导，可能与原选项措辞略有出入"
        >
          解析推导
        </span>
      </span>
    );
  }
  return (
    <span className="flex-1 pt-0.5 text-base leading-relaxed text-foreground">
      {opt.content}
    </span>
  );
}
