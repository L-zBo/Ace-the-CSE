'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowLeft, Building2, Shuffle, PlayCircle } from 'lucide-react';
import { getAllQuestions } from '@/lib/questionLoader';
import { XINGCE_CATEGORY_NAMES, type XingceCategory } from '@/types/question';
import { usePracticeStore } from '@/stores/practiceStore';
import { useMistakeStore } from '@/stores/mistakeStore';
import { cn } from '@/lib/utils';
import { filterAnswerable } from '@/lib/placeholder';

const CLASS_META: Record<string, string> = {
  a: 'A 类（综合管理）',
  b: 'B 类（社会科学专技）',
  c: 'C 类（自然科学专技）',
  d: 'D 类（中小学教师）',
  e: 'E 类（医疗卫生）',
};

function Chip({ active, onClick, disabled, children, tone = 'amber' }: {
  active: boolean; onClick: () => void; disabled?: boolean; children: React.ReactNode;
  tone?: 'amber' | 'blue' | 'white';
}) {
  const activeStyle = {
    amber: 'bg-warning text-white shadow-md shadow-warning/30',
    blue: 'bg-brand text-white shadow-md shadow-brand/30',
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

export default function InstitutionPage() {
  const router = useRouter();
  const { setQueue, clearQueue } = usePracticeStore();
  const all = getAllQuestions();
  const instQs = useMemo(
    () => filterAnswerable(all.filter((q) => q.source === 'institution')),
    [all]
  );

  const [cls, setCls] = useState<string>('');
  const [year, setYear] = useState<number | ''>('');
  const [cat, setCat] = useState<XingceCategory | ''>('');

  const classList = useMemo(() => {
    const m = new Map<string, number>();
    for (const q of instQs) {
      const parts = q.id.split('-');
      const lv = parts[4] || '';
      m.set(lv, (m.get(lv) || 0) + 1);
    }
    return ['a', 'b', 'c', 'd', 'e'].map((k) => ({
      k,
      count: m.get(k) || 0,
    }));
  }, [instQs]);

  const yearList = useMemo(() => {
    const src = cls
      ? instQs.filter((q) => q.id.split('-')[4] === cls)
      : instQs;
    return Array.from(new Set(src.map((q) => q.year))).sort((a, b) => b - a);
  }, [instQs, cls]);

  const filtered = useMemo(() => {
    return instQs.filter((q) => {
      const lv = q.id.split('-')[4];
      return (
        (!cls || lv === cls) &&
        (!year || q.year === year) &&
        (!cat || q.category === cat)
      );
    });
  }, [instQs, cls, year, cat]);

  // 完成度统计（D-18a P3c 升级）— 用 mistakeStore 推断该筛选范围已做题量
  const mistakes = useMistakeStore((s) => s.mistakes);
  const progress = useMemo(() => {
    const filteredIds = new Set(filtered.map((q) => q.id));
    let known = 0;
    let mastered = 0;
    for (const m of mistakes) {
      if (filteredIds.has(m.questionId)) {
        known++;
        if (m.isMastered) mastered++;
      }
    }
    const accuracy = known > 0 ? Math.round((mastered / known) * 100) : 0;
    return { totalKnown: known, mastered, accuracy };
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
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl gradient-cinnabar shadow-cinnabar">
          <Building2 size={28} className="text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-white">事业编</h1>
          <p className="text-sm text-white/60">
            {instQs.length} 题 · A/B/C/D/E 类
          </p>
        </div>
      </div>

      {/* 筛选器 */}
      <div className="mb-6 space-y-4 rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-sm">
        {/* 类别 */}
        <div className="flex flex-wrap items-start gap-2">
          <span className="mr-1 mt-1.5 w-14 shrink-0 text-xs font-semibold uppercase tracking-wider text-white/40">
            类别
          </span>
          <div className="flex flex-wrap gap-2">
            <Chip
              tone="amber"
              active={cls === ''}
              onClick={() => {
                setCls('');
                setYear('');
              }}
            >
              全部
            </Chip>
            {classList.map(({ k, count }) => (
              <Chip
                key={k}
                tone="amber"
                active={cls === k}
                disabled={count === 0}
                onClick={() => {
                  setCls(k);
                  setYear('');
                }}
              >
                {CLASS_META[k]}
                <span className="ml-1 opacity-70">({count})</span>
              </Chip>
            ))}
          </div>
        </div>

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
        key={`${cls}-${year}-${cat}`}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-4 flex flex-col items-stretch gap-3 rounded-2xl border border-white/10 bg-seal-red/10 p-5 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <div className="text-sm text-white/60">
            {cls ? CLASS_META[cls] : '全部类别'}
            {' · '}
            {year ? `${year}年` : '全部年份'}
            {cat ? ` · ${XINGCE_CATEGORY_NAMES[cat]}` : ''}
          </div>
          <div className="mt-1 text-3xl font-bold text-white">
            <span className="font-display-en tabular-nums">{filtered.length}</span>
            <span className="ml-1 text-base font-normal text-white/50">题</span>
            {progress.totalKnown > 0 && (
              <span className="ml-3 text-sm font-normal text-white/60 tabular-nums">
                · 已做 {progress.totalKnown} · 正确率 {progress.accuracy}%
              </span>
            )}
          </div>
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
                  className="h-full rounded-full bg-gradient-to-r from-warning to-seal-500"
                />
              </div>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => start(false)}
            disabled={filtered.length === 0}
            className="group flex items-center gap-1.5 rounded-xl bg-warning px-5 py-3 text-sm font-semibold text-white shadow-md shadow-warning/30 transition hover:brightness-110 hover:shadow-lg active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-40"
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
