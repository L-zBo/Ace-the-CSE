import { forwardRef, type HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

/**
 * Badge — 状态徽章 / tag chip
 *
 * 见 docs/DESIGN.md §4。语义色徽章 + 卷面色徽章。
 */

export type BadgeVariant =
  | 'default'
  | 'brand'
  | 'seal'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'outline';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

const variantClasses: Record<BadgeVariant, string> = {
  default: 'bg-white/10 text-foreground-secondary border border-white/15',
  brand: 'bg-brand/20 text-brand-200 border border-brand/40',
  seal: 'bg-seal-red/20 text-seal-300 border border-seal-red/40',
  success: 'bg-success/15 text-success border border-success/40',
  warning: 'bg-warning/15 text-warning border border-warning/40',
  danger: 'bg-danger/15 text-danger border border-danger/40',
  info: 'bg-info/15 text-info border border-info/40',
  outline: 'bg-transparent text-foreground-secondary border border-border',
};

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', ...props }, ref) => (
    <span
      ref={ref}
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium',
        'whitespace-nowrap leading-none',
        variantClasses[variant],
        className,
      )}
      {...props}
    />
  ),
);
Badge.displayName = 'Badge';
