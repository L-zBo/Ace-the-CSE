import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Spinner — 加载旋转图标
 *
 * 用于按钮内 loading 状态以外的场景（页面加载、卡片内 loading）。
 */

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  /** 给 a11y 屏幕阅读器的文案 */
  label?: string;
}

const sizeMap = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
};

export function Spinner({ size = 'md', className, label = '加载中' }: SpinnerProps) {
  return (
    <Loader2
      role="status"
      aria-label={label}
      className={cn('animate-spin text-foreground-muted', sizeMap[size], className)}
    />
  );
}
