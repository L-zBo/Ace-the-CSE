'use client';

interface KbdProps {
  children: React.ReactNode;
}

function Kbd({ children }: KbdProps) {
  return (
    <kbd className="rounded border border-border bg-card px-1.5 py-0.5 font-mono text-[11px] text-foreground-secondary">
      {children}
    </kbd>
  );
}

export function KeyboardHintBar() {
  return (
    <p className="mb-3 hidden text-center text-xs text-foreground-faint sm:block">
      键盘：<Kbd>1-4</Kbd> 或 <Kbd>A-D</Kbd> 选项 ·{' '}
      <Kbd>Enter</Kbd> 提交/下一题 ·{' '}
      <Kbd>←</Kbd> <Kbd>→</Kbd> 切题 ·{' '}
      <Kbd>F</Kbd> 收藏 ·{' '}
      <Kbd>Esc</Kbd> 退出
    </p>
  );
}
