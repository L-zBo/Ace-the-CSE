'use client';

import { ChevronLeft, ChevronRight, List } from 'lucide-react';
import { cn } from '@/lib/utils';

interface QuestionNavBarProps {
  canPrev: boolean;
  canNext: boolean;
  isSubmitted: boolean;
  onPrev: () => void;
  onNext: () => void;
  onBackToList: () => void;
}

export function QuestionNavBar({
  canPrev,
  canNext,
  isSubmitted,
  onPrev,
  onNext,
  onBackToList,
}: QuestionNavBarProps) {
  return (
    <div
      className={cn(
        'sticky bottom-4 z-20 flex items-center justify-between gap-2',
        'rounded-2xl border border-border bg-card/95 p-2 shadow-xl backdrop-blur-md',
        'sm:static sm:border-0 sm:bg-transparent sm:p-0 sm:shadow-none sm:backdrop-blur-none',
      )}
    >
      <NavButton
        direction="prev"
        disabled={!canPrev}
        onClick={onPrev}
        variant="outline"
      />
      <button
        type="button"
        onClick={onBackToList}
        title="返回题库列表"
        className={cn(
          'inline-flex items-center justify-center gap-1.5 rounded-xl px-4 py-3 text-sm font-medium',
          'border-2 border-border bg-card text-foreground-muted backdrop-blur-md',
          'transition-[transform,box-shadow,background-color,border-color] duration-200',
          'hover:border-brand-soft/60 hover:bg-brand/5 hover:text-foreground active:scale-[0.97]',
          'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand',
        )}
      >
        <List size={18} aria-hidden="true" />
        <span className="hidden sm:inline">题目列表</span>
      </button>
      <NavButton
        direction="next"
        disabled={!canNext}
        onClick={onNext}
        variant={isSubmitted ? 'primary' : 'outline'}
      />
    </div>
  );
}

interface NavButtonProps {
  direction: 'prev' | 'next';
  disabled: boolean;
  onClick: () => void;
  variant: 'primary' | 'outline';
}

function NavButton({ direction, disabled, onClick, variant }: NavButtonProps) {
  const isNext = direction === 'next';
  const Icon = isNext ? ChevronRight : ChevronLeft;
  const label = isNext ? '下一题' : '上一题';
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'group inline-flex flex-1 items-center justify-center gap-1.5 rounded-xl px-4 py-3 text-sm font-semibold',
        'transition-[transform,box-shadow,background-color,border-color,filter] duration-200',
        'active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-30',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand',
        'sm:flex-none sm:px-6',
        variant === 'primary' &&
          'gradient-mo-blue text-white shadow-mo-blue hover:brightness-110 hover:shadow-xl',
        variant === 'outline' &&
          'border-2 border-border bg-card backdrop-blur-md hover:border-brand-soft/60 hover:bg-brand/5',
      )}
    >
      {!isNext && (
        <Icon
          size={18}
          aria-hidden="true"
          className="transition-transform group-hover:-translate-x-0.5"
        />
      )}
      {label}
      {isNext && (
        <Icon
          size={18}
          aria-hidden="true"
          className="transition-transform group-hover:translate-x-0.5"
        />
      )}
    </button>
  );
}
