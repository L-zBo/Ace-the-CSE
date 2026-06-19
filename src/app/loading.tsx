export default function Loading() {
  return (
    <div className="mx-auto flex min-h-[calc(100vh-8rem)] max-w-2xl flex-col items-center justify-center px-6 py-16 text-center">
      {/* 朱砂方印旋转 — CSS only，prefers-reduced-motion 自动停止（globals.css 全局） */}
      <div className="relative mb-6 h-20 w-20" aria-label="加载中" role="status">
        <span
          aria-hidden
          className="absolute inset-0 rounded-md bg-seal-red shadow-seal-red"
          style={{ animation: 'sealSpin 1.6s linear infinite' }}
        />
        <span
          aria-hidden
          className="font-display-zh absolute inset-0 flex items-center justify-center text-3xl font-bold text-white"
        >
          阅
        </span>
        <style>{`@keyframes sealSpin{0%{transform:rotate(0)}100%{transform:rotate(360deg)}}`}</style>
      </div>

      <p className="font-display-zh text-xl text-foreground-secondary tracking-widest">
        阅卷中…
      </p>
    </div>
  );
}
