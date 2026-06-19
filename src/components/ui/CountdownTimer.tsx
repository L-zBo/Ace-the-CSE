'use client';

import { Clock } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatTime } from '@/lib/utils';

/**
 * CountdownTimer — 模考倒计时显示组件（D-18a P3d 升级）
 *
 * 双阈值警示：
 * - remainingTime < 300s（5 分钟）：danger 红色闪烁
 * - remainingTime < 600s（10 分钟）：warning 黄色
 * - 其他：中性 card-hover
 *
 * 与 ExamSessionClient 解耦后可在其他考试场景复用。
 *
 * 用法：
 *   <CountdownTimer remainingSeconds={remainingTime} />
 */
interface CountdownTimerProps {
  /** 剩余秒数 */
  remainingSeconds: number;
  /** 自定义 className */
  className?: string;
  /** 是否在低剩余时间触发 animate-pulse，默认 true */
  pulseOnDanger?: boolean;
}

const DANGER_THRESHOLD = 300;
const WARNING_THRESHOLD = 600;

export function CountdownTimer({
  remainingSeconds,
  className,
  pulseOnDanger = true,
}: CountdownTimerProps) {
  const isDanger = remainingSeconds < DANGER_THRESHOLD;
  const isWarning = !isDanger && remainingSeconds < WARNING_THRESHOLD;

  return (
    <div
      role="timer"
      aria-live="polite"
      aria-label={`剩余时间 ${formatTime(remainingSeconds)}`}
      className={cn(
        'flex items-center gap-1.5 rounded-lg px-3 py-1 text-sm font-mono font-bold tabular-nums',
        isDanger
          ? cn('bg-danger/15 text-danger', pulseOnDanger && 'animate-pulse')
          : isWarning
            ? 'bg-warning/15 text-warning'
            : 'bg-card-hover text-foreground',
        className,
      )}
    >
      <Clock size={14} aria-hidden="true" />
      {formatTime(remainingSeconds)}
    </div>
  );
}
