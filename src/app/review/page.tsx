'use client';

import { useState, useMemo, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { RotateCcw, Filter, CheckCircle2, Trash2 } from 'lucide-react';
import { useMistakeStore } from '@/stores/mistakeStore';
import { loadQuestionsByIds } from '@/lib/questionLoader';
import type { Question } from '@/types/question';
import {
  XINGCE_CATEGORY_NAMES,
  SHENLUN_CATEGORY_NAMES,
  SUBJECT_NAMES,
  type Subject,
} from '@/types/question';
import { Badge, Button, Card, ConfirmDialog, EmptyState, Skeleton, useToast } from '@/components/ui';
import { CountUp } from '@/components/effects/CountUp';
import { cn } from '@/lib/utils';

// 错题自动毕业阈值：连续答对 ≥2 次自动 mastered（与 mistakeStore 一致）
const MASTERY_THRESHOLD = 2;

export default function ReviewPage() {
  const { mistakes, markMastered, removeMistake } = useMistakeStore();
  const toast = useToast();
  const [filterSubject, setFilterSubject] = useState<Subject | ''>('');
  const [showMastered, setShowMastered] = useState(false);
  const [pendingRemove, setPendingRemove] = useState<string | null>(null);

  const filtered = useMemo(() => {
    let list = [...mistakes];
    if (!showMastered) list = list.filter((m) => !m.isMastered);
    if (filterSubject) list = list.filter((m) => m.subject === filterSubject);
    return list.sort(
      (a, b) => new Date(b.lastWrongDate).getTime() - new Date(a.lastWrongDate).getTime()
    );
  }, [mistakes, filterSubject, showMastered]);

  // 错题正文按需加载：只拉错题所在的那几份试卷，不碰整个题库。
  const mistakeIds = useMemo(
    () => filtered.map((m) => m.questionId).join(','),
    [filtered],
  );
  // 同样存 { key, map } 并派生，避免在 effect 里同步 setState
  const [loadedQuestions, setLoadedQuestions] = useState<{
    key: string;
    map: Record<string, Question>;
  } | null>(null);

  useEffect(() => {
    if (!mistakeIds) return;
    let cancelled = false;
    loadQuestionsByIds(mistakeIds.split(',')).then((list) => {
      if (cancelled) return;
      setLoadedQuestions({
        key: mistakeIds,
        map: Object.fromEntries(list.map((q) => [q.id, q])),
      });
    });
    return () => {
      cancelled = true;
    };
  }, [mistakeIds]);

  const questionMap =
    loadedQuestions?.key === mistakeIds ? loadedQuestions.map : {};
  const loadingQuestions = !!mistakeIds && loadedQuestions?.key !== mistakeIds;

  const allCategoryNames = { ...XINGCE_CATEGORY_NAMES, ...SHENLUN_CATEGORY_NAMES };
  const activeCount = mistakes.filter((m) => !m.isMastered).length;

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
      <header className="mb-6 flex items-center gap-3">
        <RotateCcw size={24} className="text-seal-500" aria-hidden="true" />
        <h1 className="font-display-zh text-2xl font-bold text-foreground">错题本</h1>
        <Badge variant="seal" className="tabular-nums">
          <CountUp to={activeCount} duration={600} /> 道待复习
        </Badge>
      </header>

      {/* 筛选区：chip 列 + 显示已掌握开关 */}
      <div className="mb-6 flex flex-wrap items-center gap-2">
        <Filter size={16} className="text-foreground-muted" aria-hidden="true" />
        <button
          type="button"
          onClick={() => setFilterSubject('')}
          className={cn(
            'rounded-full px-3 py-1 text-xs font-medium transition-colors',
            filterSubject === ''
              ? 'border border-brand bg-brand/15 text-brand-300'
              : 'border border-border bg-card text-foreground-muted hover:border-border-strong hover:text-foreground',
          )}
        >
          全部科目
        </button>
        {Object.entries(SUBJECT_NAMES).map(([k, v]) => (
          <button
            key={k}
            type="button"
            onClick={() => setFilterSubject(k as Subject)}
            className={cn(
              'rounded-full px-3 py-1 text-xs font-medium transition-colors',
              filterSubject === k
                ? 'border border-brand bg-brand/15 text-brand-300'
                : 'border border-border bg-card text-foreground-muted hover:border-border-strong hover:text-foreground',
            )}
          >
            {v}
          </button>
        ))}
        <label className="ml-auto flex items-center gap-2 text-xs text-foreground-muted">
          <input
            type="checkbox"
            checked={showMastered}
            onChange={(e) => setShowMastered(e.target.checked)}
            className="h-4 w-4 rounded accent-brand"
          />
          显示已掌握
        </label>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={CheckCircle2}
          title={mistakes.length === 0 ? '还没有错题记录' : '所有错题都已掌握！'}
          description={
            mistakes.length === 0
              ? '去刷题练习吧，做错的题会自动收集到这里'
              : '继续保持，定期回顾巩固'
          }
          action={
            <Link href="/practice">
              <Button variant="primary" size="md">
                去刷题
              </Button>
            </Link>
          }
        />
      ) : (
        <div className="space-y-3">
          {filtered.map((mistake, idx) => {
            const q = questionMap[mistake.questionId];
            if (!q) {
              // 正文还没到（或该题已从题库移除）：加载中给骨架屏，避免列表看起来是空的
              return loadingQuestions ? (
                <Skeleton key={mistake.questionId} className="h-24 rounded-xl" />
              ) : null;
            }
            const masteryPct = Math.min(
              100,
              Math.round(((mistake.consecutiveCorrect ?? 0) / MASTERY_THRESHOLD) * 100),
            );
            return (
              <motion.div
                key={mistake.questionId}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: Math.min(idx * 0.03, 0.3), duration: 0.3 }}
              >
                <Card className="rounded-xl" compact>
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2 text-sm">
                      <Badge variant="brand">
                        {allCategoryNames[q.category as keyof typeof allCategoryNames]}
                      </Badge>
                      <span className="text-xs text-foreground-muted">{q.sourceLabel}</span>
                      <Badge variant="seal" className="tabular-nums">
                        错 {mistake.wrongCount} 次
                      </Badge>
                      {mistake.isMastered && <Badge variant="success">已掌握</Badge>}
                    </div>
                    <div className="flex shrink-0 items-center gap-1">
                      {!mistake.isMastered && (
                        <button
                          type="button"
                          onClick={() => {
                            markMastered(mistake.questionId);
                            toast.success('已标记为掌握，不再出现在待复习列表');
                          }}
                          aria-label="标记为已掌握"
                          title="标记为已掌握"
                          className="rounded-lg p-1.5 text-foreground-muted transition-colors hover:bg-success/10 hover:text-success focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
                        >
                          <CheckCircle2 size={16} aria-hidden="true" />
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => setPendingRemove(mistake.questionId)}
                        aria-label="删除错题"
                        title="删除"
                        className="rounded-lg p-1.5 text-foreground-muted transition-colors hover:bg-danger/10 hover:text-danger focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
                      >
                        <Trash2 size={16} aria-hidden="true" />
                      </button>
                    </div>
                  </div>
                  <Link
                    href={`/practice/${q.id}`}
                    className="block rounded-md transition-colors hover:text-brand-300"
                  >
                    <p className="line-clamp-2 text-sm leading-relaxed text-foreground-secondary">
                      {q.content}
                    </p>
                  </Link>
                  {/* 掌握度进度条（D-18a P3a 升级）— 连续答对 N/2 自动毕业 */}
                  {!mistake.isMastered && (
                    <div className="mt-3">
                      <div className="mb-1 flex items-center justify-between text-[10px] text-foreground-muted">
                        <span>掌握度</span>
                        <span className="tabular-nums">
                          {mistake.consecutiveCorrect ?? 0} / {MASTERY_THRESHOLD} 次连对自动毕业
                        </span>
                      </div>
                      <div className="h-1 overflow-hidden rounded-full bg-border">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${masteryPct}%` }}
                          transition={{ duration: 0.6, ease: 'easeOut' }}
                          className="h-full rounded-full bg-gradient-to-r from-brand-500 to-success"
                        />
                      </div>
                    </div>
                  )}
                </Card>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* 删除二次确认（D-18a P3a 升级 — 替代 window.confirm）*/}
      <ConfirmDialog
        open={pendingRemove !== null}
        onClose={() => setPendingRemove(null)}
        onConfirm={() => {
          if (pendingRemove) {
            removeMistake(pendingRemove);
            toast.success('已删除这道错题');
          }
        }}
        title="确认删除这道错题？"
        description="删除后不可恢复。如果还没完全掌握，建议保留继续复习。"
        confirmLabel="删除"
        cancelLabel="保留"
        confirmVariant="danger"
      />
    </div>
  );
}
