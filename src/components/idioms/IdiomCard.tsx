'use client';

import { motion } from 'framer-motion';
import { Check, Maximize2, RotateCcw, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { getIdiomDetail, type IdiomDetailRecord } from '@/lib/idiomDetails';
import { useIdiomStore, type IdiomStatus } from '@/stores/idiomStore';

export interface IdiomCardData {
  word: string;
  frequency: number;
  sources: string[];
  originalContext: string;
  originalExplanation: string;
}

interface IdiomCardProps {
  idiom: IdiomCardData;
  onOpenDetail?: (idiom: IdiomCardData) => void;
}

const STATUS_RING: Record<IdiomStatus | 'none', string> = {
  none: 'border-white/15',
  unknown: 'border-seal-400/60 ring-1 ring-seal-400/40',
  reviewing: 'border-warning/60 ring-1 ring-warning/40',
  mastered: 'border-success/60 ring-1 ring-success/40',
};

const STATUS_BADGE: Record<IdiomStatus, { label: string; className: string }> = {
  unknown: { label: '不会', className: 'bg-seal-500/20 text-seal-300' },
  reviewing: { label: '复习中', className: 'bg-warning/20 text-warning' },
  mastered: { label: '已掌握', className: 'bg-success/20 text-success' },
};

const ACTIONS: { status: IdiomStatus; label: string; Icon: typeof X; className: string }[] = [
  {
    status: 'unknown',
    label: '不会',
    Icon: X,
    className: 'border-seal-400/30 bg-seal-500/12 text-seal-200 hover:bg-seal-500/22',
  },
  {
    status: 'reviewing',
    label: '复习',
    Icon: RotateCcw,
    className: 'border-warning/30 bg-warning/12 text-warning hover:bg-warning/22',
  },
  {
    status: 'mastered',
    label: '掌握',
    Icon: Check,
    className: 'border-success/30 bg-success/12 text-success hover:bg-success/22',
  },
];

export default function IdiomCard({ idiom, onOpenDetail }: IdiomCardProps) {
  const [flipped, setFlipped] = useState(false);
  const [detail, setDetail] = useState<IdiomDetailRecord | null | undefined>(undefined);
  const status = useIdiomStore((s) => s.records[idiom.word]?.status ?? null);
  const mark = useIdiomStore((s) => s.mark);

  const ringClass = STATUS_RING[status ?? 'none'];
  const badge = status ? STATUS_BADGE[status] : null;
  const previewExample = detail?.examples?.find((item) => item.text.trim())?.text ?? '';

  useEffect(() => {
    if (!flipped || detail !== undefined) return;

    let cancelled = false;
    getIdiomDetail(idiom.word).then((record) => {
      if (cancelled) return;
      setDetail(record);
    });

    return () => {
      cancelled = true;
    };
  }, [detail, flipped, idiom.word]);

  return (
    <motion.article
      className={cn(
        'group flex h-64 w-full flex-col overflow-hidden rounded-2xl border-2 bg-gradient-to-br from-brand-800/82 to-brand-950/92 p-3 shadow-xl backdrop-blur-md',
        ringClass
      )}
      whileHover={{ scale: 1.02 }}
    >
      <div
        role="button"
        tabIndex={0}
        aria-pressed={flipped}
        aria-label={`${idiom.word}词卡，${flipped ? '当前显示背面，按空格或回车翻回' : '当前显示正面，按空格或回车翻面'}`}
        onClick={() => setFlipped((v) => !v)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setFlipped((v) => !v);
          }
        }}
        className="relative min-h-0 flex-1 [perspective:1200px]"
      >
        <motion.div
          className="relative h-full w-full [transform-style:preserve-3d]"
          animate={{ rotateY: flipped ? 180 : 0 }}
          transition={{ type: 'spring', stiffness: 280, damping: 24 }}
          style={{ transformStyle: 'preserve-3d' }}
        >
          <div
            className={cn(
              'absolute inset-0 overflow-hidden rounded-xl border-2 bg-gradient-to-br from-brand-800/80 to-brand-950/90 p-3 shadow-inner [backface-visibility:hidden]',
              ringClass
            )}
          >
            <button
              type="button"
              aria-label={`打开${idiom.word}详情`}
              title="打开详情"
              onClick={(e) => {
                e.stopPropagation();
                onOpenDetail?.(idiom);
              }}
              className="absolute right-2 top-2 inline-flex h-7 w-7 items-center justify-center rounded-full border border-white/10 bg-black/20 text-white/70 transition-colors hover:bg-white/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300/60"
            >
              <Maximize2 size={14} />
            </button>

            <div className="flex h-full flex-col">
              <div className="flex items-start justify-between gap-2 pr-9">
                <span className="shrink-0 rounded-full bg-brand-500/18 px-2 py-0.5 text-[10px] font-medium text-brand-200">
                  频次{idiom.frequency}
                </span>
                {badge ? (
                  <span
                    className={cn(
                      'shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium',
                      badge.className
                    )}
                  >
                    {badge.label}
                  </span>
                ) : (
                  <span className="shrink-0 rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-medium text-white/40">
                    未标记
                  </span>
                )}
              </div>

              <div className="flex min-h-0 flex-1 flex-col items-center justify-center text-center">
                <div className="max-w-full break-words text-center text-3xl font-bold tracking-normal text-white sm:text-4xl">
                  {idiom.word}
                </div>
                <p className="mt-3 text-[11px] text-white/45 sm:text-xs">
                  点击翻面看词义
                </p>
              </div>
            </div>
          </div>

          <div
            className={cn(
              'absolute inset-0 overflow-hidden rounded-xl border-2 bg-gradient-to-br from-brand-950/94 to-brand-800/92 p-3 shadow-inner [backface-visibility:hidden] [transform:rotateY(180deg)]',
              ringClass
            )}
          >
            <button
              type="button"
              aria-label={`打开${idiom.word}详情`}
              title="打开详情"
              onClick={(e) => {
                e.stopPropagation();
                onOpenDetail?.(idiom);
              }}
              className="absolute right-2 top-2 inline-flex h-7 w-7 items-center justify-center rounded-full border border-white/10 bg-black/20 text-white/70 transition-colors hover:bg-white/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300/60"
            >
              <Maximize2 size={14} />
            </button>

            <div className="flex h-full flex-col">
              <div className="flex items-start justify-between gap-2 pr-9">
                <span className="shrink-0 rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-medium text-white/55">
                  词义预览
                </span>
                {badge ? (
                  <span
                    className={cn(
                      'shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium',
                      badge.className
                    )}
                  >
                    {badge.label}
                  </span>
                ) : (
                  <span className="shrink-0 rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-medium text-white/40">
                    待标记
                  </span>
                )}
              </div>

              <div className="mt-3 flex min-h-0 flex-1 flex-col gap-3">
                <div className="rounded-xl border border-white/10 bg-black/15 p-3">
                  <div className="mb-1 text-[10px] uppercase tracking-wider text-white/40">
                    词义
                  </div>
                  {flipped && detail === undefined ? (
                    <p className="text-sm leading-6 text-white/45">正在加载词义…</p>
                  ) : detail?.meaning ? (
                    <p className="text-sm leading-6 text-white/86">{detail.meaning}</p>
                  ) : (
                    <p className="text-sm leading-6 text-white/55">
                      暂无独立词义数据，右上角可打开完整详情。
                    </p>
                  )}
                </div>

                <div className="rounded-xl border border-white/10 bg-black/10 p-3">
                  <div className="mb-1 text-[10px] uppercase tracking-wider text-white/40">
                    真题运用
                  </div>
                  {flipped && detail === undefined ? (
                    <p className="text-sm leading-6 text-white/45">正在加载例句…</p>
                  ) : previewExample ? (
                    <p className="text-sm leading-6 text-white/76">{previewExample}</p>
                  ) : (
                    <p className="text-sm leading-6 text-white/55">
                      暂无可展示的例句。
                    </p>
                  )}
                </div>
              </div>

              <p className="mt-2 text-[11px] text-white/38">
                点击空白处翻回，右上角看完整详情
              </p>
            </div>
          </div>
        </motion.div>
      </div>

      <div className="grid w-full grid-cols-3 gap-2 pt-3">
        {ACTIONS.map(({ status: s, label, Icon, className }) => (
          <button
            key={s}
            type="button"
            aria-label={`标记${idiom.word}为${label}`}
            title={label}
            onClick={(e) => {
              e.stopPropagation();
              mark(idiom.word, s);
            }}
            className={cn(
              'inline-flex h-9 min-w-0 items-center justify-center gap-1 rounded-lg border px-1.5 text-[11px] font-medium transition-[background-color,border-color,box-shadow,color] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300/60 sm:text-xs',
              className,
              status === s && 'ring-1 ring-white/45'
            )}
          >
            <Icon size={13} className="shrink-0" />
            <span className="truncate">{label}</span>
          </button>
        ))}
      </div>
    </motion.article>
  );
}
