'use client';

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Circle, ListChecks } from 'lucide-react';
import { cn } from '@/lib/utils';

interface EssayAnswerAreaProps {
  value: string;
  onChange: (next: string) => void;
}

const MILESTONES = [
  { threshold: 300, label: '速答' },
  { threshold: 500, label: '中长' },
  { threshold: 800, label: '作文' },
] as const;

// 分论点起手词：识别用户作答里的"立意/分论点"结构
const ARG_STARTERS_RE =
  /(?:^|\n|[。！？]\s*)(首先|其次|再次|然后|最后|此外|另外|一是|二是|三是|四是|五是|第一|第二|第三|第四|第五|一来|二来|三来|一方面|另一方面)/g;

export function EssayAnswerArea({ value, onChange }: EssayAnswerAreaProps) {
  const stats = useMemo(() => {
    const length = value.length;
    const paragraphs = value
      .split(/\n\s*\n/)
      .map((p) => p.trim())
      .filter((p) => p.length > 0);
    const paragraphCount = paragraphs.length;
    const avgParaLen = paragraphCount > 0 ? Math.round(length / paragraphCount) : 0;

    // 识别分论点起手词（按文中出现先后顺序，去重）
    const argMatches: string[] = [];
    const seen = new Set<string>();
    for (const m of value.matchAll(ARG_STARTERS_RE)) {
      const starter = m[1];
      if (!seen.has(starter)) {
        argMatches.push(starter);
        seen.add(starter);
      }
    }

    return { length, paragraphCount, avgParaLen, argStarters: argMatches };
  }, [value]);

  return (
    <div className="mb-6">
      <label
        htmlFor="essay-answer"
        className="mb-2 block text-sm font-medium text-foreground-secondary"
      >
        作答区（申论）
      </label>
      <textarea
        id="essay-answer"
        rows={16}
        spellCheck={false}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="在此写下你的思路与作答，例如：「首先，应当从政策导向出发…」（建议先列结构再填内容）…"
        className={cn(
          'w-full rounded-xl border border-border bg-card p-4 text-base leading-relaxed text-foreground',
          'placeholder:text-foreground-muted backdrop-blur-md',
          'focus:border-brand focus:bg-card-hover focus:outline-none focus:shadow-md focus:shadow-brand/20',
          'transition-[border-color,background-color,box-shadow] duration-200',
        )}
      />

      {/* 实时统计：字数 / 段落数 / 平均段长 + 推荐线里程碑 */}
      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-foreground-muted">
        <span className="tabular-nums" aria-live="polite">
          <span className="font-display-en text-base font-semibold text-brand-300">
            {stats.length}
          </span>
          <span className="ml-1">字</span>
        </span>
        {stats.paragraphCount > 0 && (
          <>
            <span className="text-foreground-faint">·</span>
            <span className="tabular-nums">
              {stats.paragraphCount} 段
              <span className="ml-1 text-foreground-faint">
                （平均 {stats.avgParaLen} 字/段）
              </span>
            </span>
          </>
        )}

        <span className="ml-auto flex items-center gap-2" aria-label="字数里程碑">
          {MILESTONES.map(({ threshold, label }) => {
            const reached = stats.length >= threshold;
            return (
              <motion.span
                key={threshold}
                animate={reached ? { scale: [1, 1.15, 1] } : { scale: 1 }}
                transition={{ duration: 0.4, ease: 'easeOut' }}
                className={cn(
                  'inline-flex items-center gap-1 rounded-full border px-2 py-0.5',
                  reached
                    ? 'border-seal-red/40 bg-seal-red/10 text-seal-300'
                    : 'border-border bg-transparent text-foreground-faint',
                )}
                title={`${label}（${threshold} 字）`}
              >
                {reached ? (
                  <CheckCircle2 size={11} aria-hidden="true" />
                ) : (
                  <Circle size={11} aria-hidden="true" />
                )}
                <span className="tabular-nums">{threshold}</span>
              </motion.span>
            );
          })}
        </span>
      </div>

      {/* 实时识别的分论点序列 */}
      {stats.argStarters.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-2 flex flex-wrap items-center gap-1.5 text-xs"
        >
          <ListChecks size={12} className="text-brand-300" aria-hidden="true" />
          <span className="text-foreground-muted">检测到分论点：</span>
          {stats.argStarters.map((s) => (
            <span
              key={s}
              className="rounded-full border border-brand-500/40 bg-brand-500/10 px-2 py-0.5 text-brand-300"
            >
              {s}
            </span>
          ))}
        </motion.div>
      )}
    </div>
  );
}
