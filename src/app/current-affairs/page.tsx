'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Newspaper,
  Clock,
  ChevronDown,
  ChevronUp,
  Tag,
  CalendarDays,
  AlertCircle,
  ExternalLink,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import currentAffairsData from '@/data/current-affairs.json';

// 9 分类色：用 brand/seal/success/warning/info/danger token，保留差异化设计
const CATEGORY_COLORS: Record<string, string> = {
  '政治': 'bg-seal-500/15 text-seal-300 border border-seal-500/40',
  '政策': 'bg-brand-500/15 text-brand-300 border border-brand-500/40',
  '经济': 'bg-warning/15 text-warning border border-warning/40',
  '法律': 'bg-seal-700/15 text-seal-300 border border-seal-700/40',
  '社会': 'bg-success/15 text-success border border-success/40',
  '外交': 'bg-info/15 text-info border border-info/40',
  '生态': 'bg-success/10 text-success/80 border border-success/30',
  '科技': 'bg-brand-300/15 text-brand-300 border border-brand-300/40',
  '公考': 'bg-brand-700/15 text-brand-400 border border-brand-700/40',
};

function CategoryBadge({ category }: { category: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium',
        CATEGORY_COLORS[category] || 'bg-card text-foreground-muted border border-border'
      )}
    >
      <Tag size={10} />
      {category}
    </span>
  );
}

// 每条新闻点击后跳到外链：item.url 优先，否则回退到百度搜"title"。
// 新闻 JSON 后续可选填 `url: "https://..."` 走直跳。
function resolveNewsUrl(item: { title: string; url?: string }): string {
  if (item.url) return item.url;
  return `https://www.baidu.com/s?wd=${encodeURIComponent(item.title)}`;
}

function NewsLinkTitle({
  item,
  className,
}: {
  item: { title: string; url?: string };
  className?: string;
}) {
  return (
    <a
      href={resolveNewsUrl(item)}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        'group inline-flex items-start gap-1 transition-colors hover:text-primary',
        className
      )}
    >
      <span className="underline-offset-2 group-hover:underline">{item.title}</span>
      <ExternalLink
        size={12}
        className="mt-0.5 shrink-0 text-muted opacity-0 transition-opacity group-hover:opacity-100"
      />
    </a>
  );
}

export default function CurrentAffairsPage() {
  const [expandedMonth, setExpandedMonth] = useState<string | null>(
    currentAffairsData.yearly[0]?.month || null
  );

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl gradient-cinnabar text-white shadow-cinnabar">
            <Newspaper size={20} />
          </div>
          <h1 className="text-2xl font-bold sm:text-3xl">时事热点</h1>
        </div>
        <p className="text-sm text-muted">
          公考常识判断必备 · 近一年重大时事整理 · 每日更新
        </p>
      </motion.div>

      {/* Yesterday section */}
      <motion.section
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-8"
      >
        <div className="mb-4 flex items-center gap-2">
          <AlertCircle size={18} className="text-accent" />
          <h2 className="text-lg font-semibold">昨日要闻</h2>
          <span className="ml-auto text-xs text-muted">
            {getYesterdayDate()}
          </span>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {currentAffairsData.yesterday.map((item, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 + idx * 0.05 }}
              className="rounded-xl border border-border bg-card/80 p-4 backdrop-blur-sm transition-[transform,box-shadow,background-color,border-color] hover:border-primary/20 hover:shadow-md"
            >
              <div className="mb-2 flex items-start justify-between gap-2">
                <h3 className="text-sm font-semibold leading-snug">
                  <NewsLinkTitle item={item} />
                </h3>
                <span className="shrink-0 flex items-center gap-1 text-xs text-muted">
                  <Clock size={10} />
                  {item.time}
                </span>
              </div>
              <p className="mb-2 text-xs leading-relaxed text-muted">
                {item.summary}
              </p>
              <CategoryBadge category={item.category} />
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* Yearly timeline */}
      <motion.section
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <div className="mb-4 flex items-center gap-2">
          <CalendarDays size={18} className="text-primary" />
          <h2 className="text-lg font-semibold">近一年大事记</h2>
        </div>
        <div className="space-y-3">
          {currentAffairsData.yearly.map((monthData) => {
            const isExpanded = expandedMonth === monthData.month;
            return (
              <div
                key={monthData.month}
                className="overflow-hidden rounded-xl border border-border bg-card/80 backdrop-blur-sm"
              >
                <button
                  onClick={() =>
                    setExpandedMonth(isExpanded ? null : monthData.month)
                  }
                  className="flex w-full items-center justify-between px-5 py-3.5 text-left transition-colors hover:bg-card-hover/50"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-base font-bold">
                      {formatMonth(monthData.month)}
                    </span>
                    <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                      {monthData.events.length} 条
                    </span>
                  </div>
                  {isExpanded ? (
                    <ChevronUp size={18} className="text-muted" />
                  ) : (
                    <ChevronDown size={18} className="text-muted" />
                  )}
                </button>
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.25 }}
                      className="overflow-hidden"
                    >
                      {/* 时间轴布局（D-18a P3e 升级）— 左侧时间点 + 竖线 + 右侧内容 */}
                      <ol className="relative border-t border-border px-5 py-4 space-y-4">
                        {/* 时间轴竖线（从第一个点到最后一个点）*/}
                        <span
                          aria-hidden="true"
                          className="absolute left-[1.65rem] top-6 bottom-4 w-px bg-gradient-to-b from-brand-500/40 via-border to-transparent"
                        />
                        {monthData.events.map((event, idx) => (
                          <li
                            key={idx}
                            className="relative pl-7"
                          >
                            {/* 时间点小圆 */}
                            <span
                              aria-hidden="true"
                              className={cn(
                                'absolute left-0 top-1.5 flex h-3 w-3 items-center justify-center rounded-full ring-2 ring-card',
                                event.importance === 'high'
                                  ? 'bg-seal-500'
                                  : 'bg-brand-400',
                              )}
                            />
                            <div
                              className={cn(
                                'rounded-lg p-3 transition-colors',
                                event.importance === 'high'
                                  ? 'bg-primary/5 border-l-3 border-l-primary'
                                  : 'bg-transparent border-l-3 border-l-border'
                              )}
                            >
                              <div className="mb-1 flex items-center gap-2 flex-wrap">
                                <span className="font-display-en text-xs tabular-nums text-foreground-secondary">
                                  {event.date}
                                </span>
                                <CategoryBadge category={event.category} />
                                {event.importance === 'high' && (
                                  <span className="rounded bg-danger/10 px-1.5 py-0.5 text-[10px] font-bold text-danger">
                                    重要
                                  </span>
                                )}
                              </div>
                              <h4 className="mb-1 text-sm font-semibold">
                                <NewsLinkTitle item={event} />
                              </h4>
                              <p className="text-xs leading-relaxed text-muted">
                                {event.summary}
                              </p>
                            </div>
                          </li>
                        ))}
                      </ol>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      </motion.section>

      {/* Footer hint */}
      <div className="mt-8 text-center">
        <p className="text-xs text-muted">
          时事内容仅供学习参考 · 建议结合官方权威媒体深入了解
        </p>
      </div>
    </div>
  );
}

function getYesterdayDate(): string {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`;
}

function formatMonth(monthStr: string): string {
  const [year, month] = monthStr.split('-');
  return `${year}年${parseInt(month)}月`;
}
