'use client';

import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Button — 卷面气质按钮
 *
 * 见 docs/DESIGN.md §4.1。3 variant × 3 size + loading + 触控 ≥ 44x44。
 */
export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'seal';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  fullWidth?: boolean;
}

const variantClasses: Record<ButtonVariant, string> = {
  // 墨蓝渐变实心 — 主 CTA
  primary:
    'gradient-mo-blue text-white shadow-mo-blue hover:brightness-110 active:brightness-95 disabled:from-brand-800 disabled:to-brand-900 disabled:shadow-none',
  // 玻璃态描边 — 次要 action
  secondary:
    'bg-card backdrop-blur-md border border-border text-foreground hover:bg-card-hover hover:border-border-strong active:scale-[0.98]',
  // 透明 — 第三级 action
  ghost:
    'bg-transparent text-foreground-secondary hover:bg-white/5 hover:text-foreground active:bg-white/10',
  // 危险红 — 删除 / 清空
  danger:
    'bg-danger/90 text-white hover:bg-danger active:brightness-95 shadow-md',
  // 印章红渐变 — 重点强调（错题、收藏）
  seal:
    'bg-gradient-to-br from-seal-500 to-seal-800 text-white shadow-seal-red hover:brightness-110 active:brightness-95',
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'h-9 px-3 text-sm gap-1.5',
  md: 'h-11 px-5 text-base gap-2', // 默认，触控 44px
  lg: 'h-12 px-6 text-base gap-2',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      loading = false,
      leftIcon,
      rightIcon,
      fullWidth = false,
      disabled,
      children,
      ...props
    },
    ref,
  ) => {
    const isDisabled = disabled || loading;
    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={cn(
          'inline-flex items-center justify-center rounded-lg font-medium',
          'transition-[transform,box-shadow,background-color,filter,border-color] duration-200 ease-out',
          'disabled:cursor-not-allowed disabled:opacity-60',
          'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand',
          variantClasses[variant],
          sizeClasses[size],
          fullWidth && 'w-full',
          className,
        )}
        {...props}
      >
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : (
          leftIcon
        )}
        {children}
        {!loading && rightIcon}
      </button>
    );
  },
);
Button.displayName = 'Button';
