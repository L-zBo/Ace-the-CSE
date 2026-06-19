'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowLeft, Landmark, Shuffle, PlayCircle } from 'lucide-react';
import { getAllQuestions } from '@/lib/questionLoader';
import { XINGCE_CATEGORY_NAMES, type XingceCategory } from '@/types/question';
import { usePracticeStore } from '@/stores/practiceStore';
import { useMistakeStore } from '@/stores/mistakeStore';
import { cn } from '@/lib/utils';
import { filterAnswerable } from '@/lib/placeholder';

const LEVEL_LABELS: Record<string, string> = {
  fushengjia: '副省级',
  dishi: '地市级',
  xingzhengzhifa: '行政执法',
  '': '综合',
};

function Chip({ active, onClick, disabled, children, tone = 'blue' }: {
  active: boolean; onClick: () => void; disabled?: boolean; children: React.ReactNode;
  tone?: 'blue' | 'mo' | 'white';
}) {
  const activeStyle = {
    blue: 'bg-brand text-white shadow-md shadow-brand/30',
    mo: 'bg-brand text-white shadow-md shadow-mo-blue',
    white: 'bg-white text-black shadow-md',
  }[tone];
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'rounded-full px-3.5 py-1.5 text-sm font-medium transition-[transform,box-shadow,background-color,border-color] active:scale-95',
        disabled
          ? 'cursor-not-allowed opacity-30'
          : active
            ? activeStyle
            : 'bg-white/10 text-white/70 hover:bg-white/20 hover:text-white'
      )}
    >
      {children}
    </button>
  );
}

export default function NationalPage() {
  const router = useRouter();
  const all = getAllQuestions();
  const nationalQs = useMemo(
    () => filterAnswerable(all.filter((q) => q.source === 'national')),
    [all]
  );
  const { setQueue, clearQueue } = usePracticeStore();

  const [year, setYear] = useState<number | ''>('');
  const [level, setLevel] = useState<string>('');
  const [cat, setCat] = useState<XingceCategory | ''>('');

  // helper: 从 id 取 level (id: national-xingce-{category}-{year}-{level}-NNN, 若无 level 则只有 6 段)
  const getLevel = (id: string) => {
    const parts = id.split('-');
    return parts.length >= 7 ? parts[5] : '';
  };

  const yearList = useMemo(
    () => Array.from(new Set(nationalQs.map((q) => q.year))).sort((a, b) => b - a),
    [nationalQs]
  );

  const levelList = useMemo(() => {
    const s = new Set<string>();
    for (const q of nationalQs) s.add(getLevel(q.id));
    return Array.from(s);
  }, [nationalQs]);

  const filtered = useMemo(() => {
    return nationalQs.filter(
      (q) =>
        (!year || q.year === year) &&
        (level === '' || getLevel(q.id) === level) &&
        (!cat || q.category === cat)
    );
  }, [nationalQs, year, level, cat]);

  // 完成度统计（D-18a P3c 升级）— 用 mistakeStore 推断"该筛选范围已做过几题、正确率几何"
  // 已做题 ≈ 错题 store 命中该范围的题集（因每个做过的错题都会进 mistakeStore）
  const mistakes = useMistakeStore((s) => s.mistakes);
  const progress = useMemo(() => {
    const filteredIds = new Set(filtered.map((q) => q.id));
    let known = 0;
    let wrong = 0;
    let mastered = 0;
    for (const m of mistakes) {
      if (filteredIds.has(m.questionId)) {
        known++;
        if (m.isMastered) mastered++;
        else wrong++;
      }
    }
    const accuracy = known > 0 ? Math.round((mastered / known) * 100) : 0;
    return { totalKnown: known, wrong, mastered, accuracy };
  }, [mistakes, filtered]);

  const start = (shuffle = false) => {
    let list = [...filtered];
    if (list.length === 0) return;
    if (shuffle) list = list.sort(() => Math.random() - 0.5);
    clearQueue();
    setQueue(list.map((q) => q.id));
    router.push(`/practice/${list[0].id}`);
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <Link
        href="/"
        className="mb-6 inline-flex items-center gap-2 text-sm text-white/60 transition hover:text-white"
      >
        <ArrowLeft size={16} /> 返回首页
      </Link>

      <div className="mb-8 flex items-center gap-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl gradient-mo-blue shadow-lg shadow-mo-blue">
          <Landmark size={28} className="text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-white">国考</h1>
          <p className="text-sm text-white/60">
            {nationalQs.length} 题 · {yearList.length} 年真题
          </p>
        </div>
      </div>

      {/* 筛选器 */}
      <div className="mb-6 space-y-4 rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-sm">
        {/* 年份 */}
        <div className="flex flex-wrap items-start gap-2">
          <span className="mr-1 mt-1.5 w-14 shrink-0 text-xs font-semibold uppercase tracking-wider text-white/40">
            年份
          </span>
          <div className="flex flex-wrap gap-2">
            <Chip tone="blue" active={year === ''} onClick={() => setYear('')}>
              全部
            </Chip>
            {yearList.map((y) => (
              <Chip
                key={y}
                tone="blue"
                active={year === y}
                onClick={() => setYear(y)}
              >
                {y}
              </Chip>
            ))}
          </div>
        </div>

        {/* 级别 */}
        <div className="flex flex-wrap items-start gap-2">
          <span className="mr-1 mt-1.5 w-14 shrink-0 text-xs font-semibold uppercase tracking-wider text-white/40">
            级别
          </span>
          <div className="flex flex-wrap gap-2">
            <Chip
              tone="mo"
              active={level === ''}
              onClick={() => setLevel('')}
            >
              全部
            </Chip>
            {levelList.map((lv) => (
              <Chip
                key={lv}
                tone="mo"
                active={level === lv}
                onClick={() => setLevel(lv)}
              >
                {LEVEL_LABELS[lv] || lv || '综合'}
              </Chip>
            ))}
          </div>
        </div>

        {/* 分类 */}
        <div className="flex flex-wrap items-start gap-2">
          <span className="mr-1 mt-1.5 w-14 shrink-0 text-xs font-semibold uppercase tracking-wider text-white/40">
            分类
          </span>
          <div className="flex flex-wrap gap-2">
            <Chip tone="white" active={cat === ''} onClick={() => setCat('')}>
              全部
            </Chip>
            {Object.entries(XINGCE_CATEGORY_NAMES).map(([k, v]) => (
              <Chip
                key={k}
                tone="white"
                active={cat === k}
                onClick={() => setCat(k as XingceCategory)}
              >
                {v}
              </Chip>
            ))}
          </div>
        </div>
      </div>

      {/* 摘要 + 启动 */}
      <motion.div
        key={`${year}-${level}-${cat}`}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-4 flex flex-col items-stretch gap-3 rounded-2xl border border-white/10 bg-brand/15 p-5 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <div className="text-sm text-white/60">
            {year ? `${year}年` : '全部年份'}
            {' · '}
            {level ? LEVEL_LABELS[level] || level : '全部级别'}
            {cat ? ` · ${XINGCE_CATEGORY_NAMES[cat]}` : ''}
          </div>
          <div className="mt-1 text-3xl font-bold text-white">
            <span className="font-display-en tabular-nums">{filtered.length}</span>
            <span className="ml-1 text-base font-normal text-white/50">题</span>
            {progress.totalKnown > 0 && (
              <>
                <span className="ml-3 text-sm font-normal text-white/60 tabular-nums">
                  · 已做 {progress.totalKnown}
                </span>
                <span className="ml-2 text-sm font-normal text-foreground-faint tabular-nums">
                  （正确率 {progress.accuracy}%）
                </span>
              </>
            )}
          </div>
          {/* 完成度进度条（D-18a P3c 升级）— 基于 mistakeStore 推断该范围已做题量 */}
          {filtered.length > 0 && progress.totalKnown > 0 && (
            <div className="mt-3 max-w-xs">
              <div className="mb-1 flex items-center justify-between text-[10px] text-white/50">
                <span>已练 / 范围</span>
                <span className="tabular-nums">
                  {progress.totalKnown} / {filtered.length}
                </span>
              </div>
              <div className="h-1 overflow-hidden rounded-full bg-white/10">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{
                    width: `${Math.min(100, Math.round((progress.totalKnown / filtered.length) * 100))}%`,
                  }}
                  transition={{ duration: 0.6, ease: 'easeOut' }}
                  className="h-full rounded-full bg-gradient-to-r from-brand-500 to-success"
                />
              </div>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => start(false)}
            disabled={filtered.length === 0}
            className="group flex items-center gap-1.5 rounded-xl bg-brand px-5 py-3 text-sm font-semibold text-white shadow-md shadow-brand/30 transition hover:bg-brand-soft hover:shadow-lg active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-40"
          >
            <PlayCircle
              size={16}
              className="transition-transform group-hover:scale-110"
            />
            顺序练习
          </button>
          <button
            onClick={() => start(true)}
            disabled={filtered.length === 0}
            className="group flex items-center gap-1.5 rounded-xl border-2 border-white/20 bg-white/5 px-5 py-3 text-sm font-semibold text-white transition hover:border-white/40 hover:bg-white/10 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Shuffle
              size={16}
              className="transition-transform group-hover:rotate-180"
            />
            随机练习
          </button>
        </div>
      </motion.div>
    </div>
  );
}
