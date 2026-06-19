'use client';

import { AlertTriangle, ImageIcon, SkipForward } from 'lucide-react';
import { Button } from '@/components/ui';

type BannerMode = 'placeholder' | 'imageFallback';

interface QuestionStatusBannerProps {
  mode: BannerMode;
  reason?: string;
  onSkip?: () => void;
  canSkip?: boolean;
}

export function QuestionStatusBanner({
  mode,
  reason,
  onSkip,
  canSkip = true,
}: QuestionStatusBannerProps) {
  if (mode === 'placeholder') {
    return (
      <div
        className="mb-4 flex items-start gap-3 rounded-xl border border-warning/40 bg-warning/10 p-4 backdrop-blur-sm"
        role="status"
      >
        <AlertTriangle
          size={18}
          className="mt-0.5 shrink-0 text-warning"
          aria-hidden="true"
        />
        <div className="flex-1 text-sm">
          <p className="font-medium text-foreground">本题源数据缺失，暂无法作答</p>
          <p className="mt-0.5 text-xs text-foreground-muted">
            {reason ? `原因：${reason}。` : ''}我们正在从其他题源补全，请先跳过。
          </p>
        </div>
        {onSkip && (
          <Button
            type="button"
            variant="primary"
            size="sm"
            onClick={onSkip}
            disabled={!canSkip}
            leftIcon={<SkipForward size={14} aria-hidden="true" />}
            className="shrink-0"
          >
            跳过
          </Button>
        )}
      </div>
    );
  }

  return (
    <div
      className="mb-4 flex items-start gap-3 rounded-xl border border-info/40 bg-info/10 p-4 backdrop-blur-sm"
      role="status"
    >
      <ImageIcon
        size={18}
        className="mt-0.5 shrink-0 text-info"
        aria-hidden="true"
      />
      <div className="flex-1 text-sm">
        <p className="font-medium text-foreground">图像作答模式</p>
        <p className="mt-0.5 text-xs text-foreground-muted">
          本题文字数据未抽全，但已附原题截图。请凭下方图片直接选择 A / B / C / D，提交后可对照答案与解析。
        </p>
      </div>
    </div>
  );
}
