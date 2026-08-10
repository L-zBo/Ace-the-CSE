'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertTriangle, Info, X, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Toast — 右上角轻量反馈浮层（DESIGN.md §4.4 / §3.4 z-[60]）
 *
 * DESIGN.md 一直把 Toast 列为「缺基础组件」。删错题、清空记录这类操作做完
 * 之后页面只是静悄悄少一行，用户不知道到底成没成 —— 这个组件补的就是这段。
 *
 * 用法：
 *   // layout 里挂一次
 *   <ToastProvider>{children}</ToastProvider>
 *
 *   // 任意 client 组件里
 *   const toast = useToast();
 *   toast.success('已删除这道错题');
 *   toast.error('保存失败，请重试');
 *
 * 无障碍：容器是 aria-live="polite" 的 region，屏幕阅读器会播报；
 * 每条 toast 3 秒自动消失，鼠标悬停时暂停计时（避免刚看到就没了）。
 */

export type ToastVariant = 'success' | 'error' | 'warning' | 'info';

export interface ToastItem {
  id: number;
  variant: ToastVariant;
  message: string;
  /** 毫秒；0 表示不自动关闭 */
  duration: number;
}

interface ToastApi {
  show: (message: string, variant?: ToastVariant, duration?: number) => number;
  success: (message: string, duration?: number) => number;
  error: (message: string, duration?: number) => number;
  warning: (message: string, duration?: number) => number;
  info: (message: string, duration?: number) => number;
  dismiss: (id: number) => void;
}

const DEFAULT_DURATION = 3000;
const MAX_VISIBLE = 3;

const ToastContext = createContext<ToastApi | null>(null);

const variantStyle: Record<ToastVariant, { ring: string; icon: ReactNode }> = {
  success: {
    ring: 'border-success/40',
    icon: <CheckCircle2 size={18} className="text-success" aria-hidden="true" />,
  },
  error: {
    ring: 'border-danger/40',
    icon: <XCircle size={18} className="text-danger" aria-hidden="true" />,
  },
  warning: {
    ring: 'border-warning/40',
    icon: <AlertTriangle size={18} className="text-warning" aria-hidden="true" />,
  },
  info: {
    ring: 'border-info/40',
    icon: <Info size={18} className="text-info" aria-hidden="true" />,
  },
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const seq = useRef(0);

  const dismiss = useCallback((id: number) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const show = useCallback(
    (message: string, variant: ToastVariant = 'info', duration = DEFAULT_DURATION) => {
      seq.current += 1;
      const id = seq.current;
      // 只保留最近 MAX_VISIBLE 条，连点不会糊满屏
      setItems((prev) => [...prev, { id, variant, message, duration }].slice(-MAX_VISIBLE));
      return id;
    },
    [],
  );

  const api = useMemo<ToastApi>(
    () => ({
      show,
      dismiss,
      success: (m, d) => show(m, 'success', d),
      error: (m, d) => show(m, 'error', d),
      warning: (m, d) => show(m, 'warning', d),
      info: (m, d) => show(m, 'info', d),
    }),
    [show, dismiss],
  );

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div
        aria-live="polite"
        aria-atomic="false"
        // top-20 让开顶部 Navbar：z-[60] 本来就盖得住，但盖住导航链接 3 秒挺烦人
        className="pointer-events-none fixed right-4 top-20 z-[60] flex w-[min(22rem,calc(100vw-2rem))] flex-col gap-2"
      >
        <AnimatePresence initial={false}>
          {items.map((t) => (
            <ToastCard key={t.id} item={t} onDismiss={dismiss} />
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

function ToastCard({
  item,
  onDismiss,
}: {
  item: ToastItem;
  onDismiss: (id: number) => void;
}) {
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (paused || item.duration <= 0) return;
    const timer = window.setTimeout(() => onDismiss(item.id), item.duration);
    return () => window.clearTimeout(timer);
  }, [paused, item.duration, item.id, onDismiss]);

  const style = variantStyle[item.variant];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 24, scale: 0.96 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 24, scale: 0.96 }}
      transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      className={cn(
        'pointer-events-auto flex items-start gap-2.5 rounded-xl border bg-card p-3 shadow-lg backdrop-blur-md',
        style.ring,
      )}
    >
      <span className="mt-0.5 shrink-0">{style.icon}</span>
      <p className="flex-1 text-sm leading-relaxed text-foreground-secondary">{item.message}</p>
      <button
        type="button"
        onClick={() => onDismiss(item.id)}
        aria-label="关闭通知"
        className="-mr-1 -mt-1 shrink-0 rounded-md p-1 text-foreground-muted transition-colors hover:bg-white/10 hover:text-foreground"
      >
        <X size={14} aria-hidden="true" />
      </button>
    </motion.div>
  );
}

/** 在 ToastProvider 之外调用会抛错 —— 静默降级只会让人以为提示没写。 */
export function useToast(): ToastApi {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error('useToast 必须在 <ToastProvider> 内使用（已挂在 app/layout.tsx）');
  }
  return ctx;
}
