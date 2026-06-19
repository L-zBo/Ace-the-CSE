'use client';

import { Heart } from 'lucide-react';
import { Badge } from '@/components/ui';
import { cn } from '@/lib/utils';

interface QuestionHeaderProps {
  categoryName: string;
  sourceLabel: string;
  difficultyName: string;
  isFavorite: boolean;
  onToggleFavorite: () => void;
  currentIndex: number;
  total: number;
}

export function QuestionHeader({
  categoryName,
  sourceLabel,
  difficultyName,
  isFavorite,
  onToggleFavorite,
  currentIndex,
  total,
}: QuestionHeaderProps) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="brand">{categoryName}</Badge>
        <span className="text-sm text-foreground-muted">{sourceLabel}</span>
        <Badge variant="warning">{difficultyName}</Badge>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <button
          type="button"
          onClick={onToggleFavorite}
          aria-label={isFavorite ? '取消收藏本题' : '收藏本题'}
          aria-pressed={isFavorite}
          className={cn(
            'inline-flex h-9 w-9 items-center justify-center rounded-lg transition-colors duration-200',
            'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand',
            isFavorite
              ? 'text-seal-red hover:bg-seal-red/10'
              : 'text-foreground-muted hover:bg-white/5 hover:text-seal-red-soft',
          )}
        >
          <Heart
            size={18}
            fill={isFavorite ? 'currentColor' : 'none'}
            aria-hidden="true"
          />
        </button>
        <span
          className="flex items-baseline gap-1 tabular-nums"
          aria-label={`第 ${currentIndex + 1} 题，共 ${total} 题`}
        >
          <span className="font-display-en text-2xl font-bold leading-none text-brand-300">
            {String(currentIndex + 1).padStart(2, '0')}
          </span>
          <span className="text-xs text-foreground-faint">/ {total}</span>
        </span>
      </div>
    </div>
  );
}
