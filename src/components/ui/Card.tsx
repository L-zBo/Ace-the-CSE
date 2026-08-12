import { forwardRef, type HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

/**
 * Card 系列 — 卷面气质卡片
 *
 * 见 docs/DESIGN.md §4.2。玻璃态底（bg-card backdrop-blur-md），hover 抬升。
 *
 * 用法：
 *   <Card interactive>
 *     <CardHeader>
 *       <CardTitle>标题</CardTitle>
 *       <CardDescription>副标题</CardDescription>
 *     </CardHeader>
 *     <CardContent>内容</CardContent>
 *     <CardFooter>底部</CardFooter>
 *   </Card>
 */

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** 启用 hover 抬升 + 鼠标手型（用于可点击/可导航卡片） */
  interactive?: boolean;
  /** 紧凑模式，减少 padding */
  compact?: boolean;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, interactive = false, compact = false, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'rounded-2xl border border-border bg-card backdrop-blur-md',
        'shadow-md',
        compact ? 'p-4' : 'p-5 sm:p-6',
        interactive &&
          'cursor-pointer transition-[transform,box-shadow,background-color,border-color] duration-200 ease-out hover:bg-card-hover hover:border-border-strong hover:shadow-lg active:scale-[0.99]',
        className,
      )}
      {...props}
    />
  ),
);
Card.displayName = 'Card';

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('mb-4 flex flex-col gap-1.5', className)} {...props} />
  ),
);
CardHeader.displayName = 'CardHeader';

export const CardTitle = forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn(
        'font-display-zh text-lg font-semibold leading-tight tracking-tight text-foreground sm:text-xl',
        className,
      )}
      {...props}
    />
  ),
);
CardTitle.displayName = 'CardTitle';

export const CardDescription = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('text-sm text-foreground-muted leading-relaxed', className)}
      {...props}
    />
  ),
);
CardDescription.displayName = 'CardDescription';

export const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('text-foreground-secondary', className)} {...props} />
  ),
);
CardContent.displayName = 'CardContent';

export const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('mt-4 flex items-center justify-between gap-3', className)}
      {...props}
    />
  ),
);
CardFooter.displayName = 'CardFooter';
