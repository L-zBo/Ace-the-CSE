'use client';

import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Check, X, RotateCcw, BookOpen } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useIdiomStore, type IdiomStatus } from '@/stores/idiomStore';
import { getIdiomDetail, type IdiomDetailRecord } from '@/lib/idiomDetails';
import type { IdiomCardData } from './IdiomCard';

interface IdiomDetailDialogProps {
  idiom: IdiomCardData | null;
  open: boolean;
  onClose: () => void;
}

const ACTIONS: { status: IdiomStatus; label: string; Icon: typeof X; className: string }[] = [
  {
    status: 'unknown',
    label: '不会',
    Icon: X,
    className: 'border-seal-400/35 bg-seal-500/15 text-seal-200 hover:bg-seal-500/25',
  },
  {
    status: 'reviewing',
    label: '复习',
    Icon: RotateCcw,
    className: 'border-warning/35 bg-warning/15 text-warning hover:bg-warning/25',
  },
  {
    status: 'mastered',
    label: '掌握',
    Icon: Check,
    className: 'border-success/35 bg-success/15 text-success hover:bg-success/25',
  },
];

function statusLabel(status: IdiomStatus | null) {
  if (status === 'unknown') return '不会';
  if (status === 'reviewing') return '复习中';
  if (status === 'mastered') return '已掌握';
  return '未标记';
}

function IdiomDetailContent({
  idiom,
  status,
  onClose,
}: {
  idiom: IdiomCardData;
  status: IdiomStatus | null;
  onClose: () => void;
}) {
  const mark = useIdiomStore((s) => s.mark);
  const [detail, setDetail] = useState<IdiomDetailRecord | null | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;
    getIdiomDetail(idiom.word).then((record) => {
      if (cancelled) return;
      setDetail(record);
    });
    return () => {
      cancelled = true;
    };
  }, [idiom.word]);

  const meaning = detail?.meaning.trim() ?? '';
  const examples = detail?.examples ?? [];
  const isLoading = detail === undefined;

  return (
    <>
      <div className="flex items-start justify-between gap-4 border-b border-white/10 bg-gradient-to-br from-brand-900/70 to-slate-950 px-5 py-5 sm:px-7">
        <div className="min-w-0">
          <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-white/55">
            <span className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-2.5 py-1">
              <BookOpen size={13} />
              出现{idiom.frequency}次
            </span>
            {status && (
              <span className="rounded-full border border-primary/30 bg-primary/15 px-2.5 py-1 text-primary">
                {statusLabel(status)}
              </span>
            )}
          </div>
          <h2 className="text-4xl font-bold leading-none tracking-normal sm:text-6xl">
            {idiom.word}
          </h2>
        </div>
        <button
          type="button"
          title="关闭"
          aria-label="关闭"
          onClick={onClose}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/5 text-white/80 transition-colors hover:bg-white/12 hover:text-white"
        >
          <X size={19} />
        </button>
      </div>

      <div className="grid gap-4 overflow-y-auto px-5 py-5 sm:grid-cols-[0.85fr_1.15fr] sm:px-7">
        <section className="space-y-4">
          <div>
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-white/45">
              词义
            </h3>
            <div className="rounded-xl border border-white/10 bg-white/[0.04] p-4">
              {isLoading ? (
                <p className="text-sm leading-7 text-white/45">正在加载词义…</p>
              ) : meaning ? (
                <p className="text-sm leading-7 text-white/85">{meaning}</p>
              ) : (
                <p className="text-sm leading-7 text-white/55">
                  暂未匹配到可靠词义。这个词会保留在词卡里，后续需要补独立释义数据。
                </p>
              )}
            </div>
          </div>

          <div>
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-white/45">
              记忆状态
            </h3>
            <div className="grid grid-cols-2 gap-2 text-xs text-white/65">
              <div className="rounded-xl border border-white/10 bg-white/[0.04] p-3">
                <div className="text-white/45">出现频次</div>
                <div className="mt-1 text-lg font-semibold text-white">{idiom.frequency}次</div>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/[0.04] p-3">
                <div className="text-white/45">当前状态</div>
                <div className="mt-1 text-lg font-semibold text-white">{statusLabel(status)}</div>
              </div>
            </div>
          </div>
        </section>

        <section className="space-y-4">
          <div>
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-white/45">
              真题运用
            </h3>
            <div className="space-y-3">
              {isLoading ? (
                <p className="rounded-xl border border-white/10 bg-white/[0.04] p-4 text-sm leading-7 text-white/45">
                  正在加载真题运用…
                </p>
              ) : examples.length > 0 ? (
                examples.slice(0, 3).map((item, index) => (
                  <div
                    key={`${item.text}-${index}`}
                    className="rounded-xl border border-white/10 bg-white/[0.04] p-4"
                  >
                    <div className="mb-2 text-xs font-medium text-brand-200">
                      真题运用{index + 1}
                    </div>
                    <p className="text-sm leading-7 text-white/82">{item.text}</p>
                    {item.answerText && (
                      <p className="mt-2 text-xs leading-6 text-white/45">{item.answerText}</p>
                    )}
                  </div>
                ))
              ) : (
                <p className="rounded-xl border border-dashed border-white/10 bg-white/[0.04] p-4 text-sm leading-7 text-white/55">
                  暂无可单独展示的真题运用。
                </p>
              )}
            </div>
          </div>
        </section>
      </div>

      <div className="flex flex-wrap justify-end gap-2 border-t border-white/10 bg-slate-950/95 px-5 py-4 sm:px-7">
        {ACTIONS.map(({ status: s, label, Icon, className }) => (
          <button
            key={s}
            type="button"
            onClick={() => mark(idiom.word, s)}
            className={cn(
              'inline-flex h-10 items-center gap-1.5 rounded-lg border px-4 text-sm font-medium transition-colors',
              className,
              status === s && 'ring-1 ring-white/45',
            )}
          >
            <Icon size={15} />
            {label}
          </button>
        ))}
      </div>
    </>
  );
}

export function IdiomDetailDialog({ idiom, open, onClose }: IdiomDetailDialogProps) {
  const status = useIdiomStore((s) => (idiom ? s.records[idiom.word]?.status ?? null : null));

  useEffect(() => {
    if (!open) return;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => {
      document.body.style.overflow = prevOverflow;
      window.removeEventListener('keydown', handleKey);
    };
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && idiom && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={`${idiom.word}词卡详情`}
          className="fixed inset-0 z-[80] flex items-center justify-center p-3 sm:p-4"
        >
          <motion.div
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          <motion.div
            key={idiom.word}
            initial={{ opacity: 0, scale: 0.96, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 8 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="relative max-h-[92vh] w-full max-w-5xl overflow-hidden rounded-2xl border border-white/10 bg-slate-950 text-white shadow-2xl shadow-black/45"
          >
            <IdiomDetailContent idiom={idiom} status={status} onClose={onClose} />
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
