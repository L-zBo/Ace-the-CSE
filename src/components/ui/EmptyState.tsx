'use client';

import type { LucideIcon } from 'lucide-react';
import { Inbox } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * EmptyState — 空状态
 *
 * 见 docs/DESIGN.md §4.4。错题本空、统计空、筛选无结果时显示。
 * 必须有 icon + title + description，可选 CTA。
 */

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      role="status"
      className={cn(
        'flex flex-col items-center justify-center gap-3 py-12 px-6 text-center',
        className,
      )}
    >
      <div className="mb-2 flex h-16 w-16 items-center justify-center rounded-2xl bg-white/5 border border-white/10">
        <Icon className="h-8 w-8 text-foreground-muted" aria-hidden="true" strokeWidth={1.5} />
      </div>
      <h3 className="font-display-zh text-lg font-semibold text-foreground">{title}</h3>
      {description && (
        <p className="max-w-sm text-sm text-foreground-muted leading-relaxed">{description}</p>
      )}
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}
