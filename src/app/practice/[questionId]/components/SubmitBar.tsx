'use client';

import { CheckCircle2, RotateCcw, XCircle } from 'lucide-react';
import { Button } from '@/components/ui';
import { cn } from '@/lib/utils';

type SubmitBarMode = 'pending' | 'submitted-correct' | 'submitted-wrong' | 'submitted-essay';

interface SubmitBarProps {
  mode: SubmitBarMode;
  /** pending 态：是否禁用提交（无选中 / 占位无法作答） */
  disabled?: boolean;
  /** pending 态：提交按钮 title（如不可作答原因） */
  disabledReason?: string;
  /** 占位无法作答时按钮文案改写 */
  unanswerable?: boolean;
  /** 已提交错误时显示正确答案 */
  correctAnswer?: string | string[];
  onSubmit: () => void;
  onReset: () => void;
}

export function SubmitBar({
  mode,
  disabled,
  disabledReason,
  unanswerable,
  correctAnswer,
  onSubmit,
  onReset,
}: SubmitBarProps) {
  if (mode === 'pending') {
    return (
      <div className="mb-6">
        <Button
          variant="primary"
          size="lg"
          onClick={onSubmit}
          disabled={disabled}
          title={disabledReason}
        >
          {unanswerable ? '不可作答（源数据缺失）' : '提交答案'}
        </Button>
      </div>
    );
  }

  const answerText = Array.isArray(correctAnswer)
    ? correctAnswer.join(' / ')
    : correctAnswer;

  return (
    <div className="mb-6 flex flex-wrap items-center gap-3" aria-live="polite">
      <span
        className={cn(
          'inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold backdrop-blur-md border',
          mode === 'submitted-essay' &&
            'border-info/40 bg-info/10 text-info',
          mode === 'submitted-correct' &&
            'border-success/40 bg-success/10 text-success',
          mode === 'submitted-wrong' &&
            'border-danger/40 bg-danger/10 text-danger',
        )}
      >
        {mode === 'submitted-essay' && '已提交（点评见下方）'}
        {mode === 'submitted-correct' && (
          <>
            <CheckCircle2 size={16} aria-hidden="true" />
            回答正确
          </>
        )}
        {mode === 'submitted-wrong' && (
          <>
            <XCircle size={16} aria-hidden="true" />
            回答错误，正确答案：{answerText}
          </>
        )}
      </span>
      <Button
        variant="secondary"
        size="md"
        onClick={onReset}
        leftIcon={<RotateCcw size={14} aria-hidden="true" />}
      >
        重做
      </Button>
    </div>
  );
}
