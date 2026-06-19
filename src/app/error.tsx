'use client';

import { useEffect } from 'react';
import Link from 'next/link';

export default function Error({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string };
  unstable_retry: () => void;
}) {
  useEffect(() => {
    console.error('[error boundary]', error);
  }, [error]);

  return (
    <div className="mx-auto flex min-h-[calc(100vh-8rem)] max-w-2xl flex-col items-center justify-center px-6 py-16 text-center">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 flex items-center justify-center select-none"
      >
        <span className="font-display-zh text-[28rem] font-bold leading-none text-white/[0.03]">
          错
        </span>
      </div>

      <div className="mb-6 inline-flex h-24 w-24 items-center justify-center rounded-md bg-seal-red text-white shadow-seal-red">
        <span className="font-display-zh text-3xl font-bold">!</span>
      </div>

      <h1 className="font-display-zh mb-3 text-3xl font-bold text-foreground">
        卷面解析失败
      </h1>
      <p className="mb-2 text-foreground-secondary">
        渲染时出了点意外 — 多半是临时的，重试一下试试。
      </p>

      {error.digest && (
        <p className="mb-1 text-xs text-foreground-faint">
          错误编号 <code className="rounded bg-card px-1.5 py-0.5 font-mono">{error.digest}</code>
        </p>
      )}
      {process.env.NODE_ENV !== 'production' && error.message && (
        <pre className="mb-6 mt-2 max-w-full overflow-x-auto rounded-md border border-border bg-card px-4 py-3 text-left text-sm text-danger">
          {error.message}
        </pre>
      )}

      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        <button
          onClick={() => unstable_retry()}
          className="rounded-lg bg-brand px-6 py-2.5 font-medium text-white shadow-mo-blue transition-[transform,box-shadow,background-color,border-color] hover:bg-brand-soft hover:shadow-lg"
        >
          重试本卷
        </button>
        <Link
          href="/"
          className="rounded-lg border border-border-strong px-6 py-2.5 font-medium text-foreground transition-[transform,box-shadow,background-color,border-color] hover:bg-card-hover"
        >
          回到首页
        </Link>
      </div>
    </div>
  );
}
