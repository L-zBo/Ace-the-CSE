import Link from 'next/link';

export const metadata = {
  title: '此题已超出考纲 — Ace the CSE',
};

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-[calc(100vh-8rem)] max-w-2xl flex-col items-center justify-center px-6 py-16 text-center">
      {/* 大「博」字水印 */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 flex items-center justify-center select-none"
      >
        <span className="font-display-zh text-[28rem] font-bold leading-none text-white/[0.03]">
          博
        </span>
      </div>

      {/* 朱砂方印 404 */}
      <div className="mb-6 inline-flex h-24 w-24 items-center justify-center rounded-md bg-seal-red text-white shadow-seal-red">
        <span className="font-display-zh text-4xl font-bold tracking-widest">404</span>
      </div>

      <h1 className="font-display-zh mb-3 text-3xl font-bold text-foreground">
        此题已超出考纲
      </h1>
      <p className="mb-1 text-foreground-secondary">
        您要找的页面找不着了 — 也许是路由变更，也许是手误。
      </p>
      <p className="mb-8 text-foreground-muted">
        别急，回卷面继续刷题就行。
      </p>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <Link
          href="/"
          className="rounded-lg bg-brand px-6 py-2.5 font-medium text-white shadow-mo-blue transition-[transform,box-shadow,background-color,border-color] hover:bg-brand-soft hover:shadow-lg"
        >
          回到首页
        </Link>
        <Link
          href="/practice"
          className="rounded-lg border border-border-strong px-6 py-2.5 font-medium text-foreground transition-[transform,box-shadow,background-color,border-color] hover:bg-card-hover"
        >
          去练习
        </Link>
      </div>
    </div>
  );
}
