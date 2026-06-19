'use client';

import { useEffect, type ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle } from 'lucide-react';
import { Button, type ButtonVariant } from './Button';
import { cn } from '@/lib/utils';

/**
 * ConfirmDialog — 二次确认对话框（D-18a P3a 升级）
 *
 * 替代 window.confirm() 浏览器原生 confirm，给删除/清空类危险操作
 * 一个统一的卷面气质对话框。Esc 关闭 / overlay 点击关闭 / focus trap
 * 简易版（自动 focus 主按钮）。
 *
 * 用法：
 *   const [open, setOpen] = useState(false);
 *   <Button onClick={() => setOpen(true)}>删除</Button>
 *   <ConfirmDialog
 *     open={open}
 *     onClose={() => setOpen(false)}
 *     title="确认删除？"
 *     description="该操作不可恢复"
 *     confirmLabel="删除"
 *     confirmVariant="danger"
 *     onConfirm={() => handleDelete()}
 *   />
 */
interface ConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description?: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmVariant?: ButtonVariant;
  /** 显示警示图标，默认 true（危险操作场景） */
  showIcon?: boolean;
}

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = '确认',
  cancelLabel = '取消',
  confirmVariant = 'danger',
  showIcon = true,
}: ConfirmDialogProps) {
  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="dialog-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
        >
          {/* overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />
          {/* dialog */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 4 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className={cn(
              'relative w-full max-w-md rounded-2xl border border-border bg-card backdrop-blur-md shadow-xl',
              'p-6',
            )}
          >
            <div className="flex items-start gap-3">
              {showIcon && (
                <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-seal-red/15">
                  <AlertTriangle size={18} className="text-seal-red-soft" aria-hidden="true" />
                </div>
              )}
              <div className="flex-1">
                <h2
                  id="dialog-title"
                  className="font-display-zh text-lg font-semibold text-foreground"
                >
                  {title}
                </h2>
                {description && (
                  <div className="mt-1.5 text-sm text-foreground-secondary leading-relaxed">
                    {description}
                  </div>
                )}
              </div>
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <Button variant="secondary" size="sm" onClick={onClose}>
                {cancelLabel}
              </Button>
              <Button
                variant={confirmVariant}
                size="sm"
                onClick={() => {
                  onConfirm();
                  onClose();
                }}
                autoFocus
              >
                {confirmLabel}
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
