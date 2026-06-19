'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { BookOpen, Shuffle, PlayCircle, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';
import {
  XINGCE_CATEGORY_NAMES,
  SHENLUN_CATEGORY_NAMES,
  SUBJECT_NAMES,
  type Subject,
  type XingceCategory,
  type ShenlunCategory,
} from '@/types/question';
import { filterQuestions, getAllQuestions } from '@/lib/questionLoader';
import { usePracticeStore } from '@/stores/practiceStore';
import { calcPercentage, cn } from '@/lib/utils';
import { filterAnswerable } from '@/lib/placeholder';

function Chip({
  active,
  onClick,
  children,
  disabled,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'rounded-full px-3.5 py-1.5 text-sm font-medium transition-[transform,box-shadow,background-color,border-color] active:scale-95',
        disabled
          ? 'cursor-not-allowed opacity-30'
          : active
            ? 'bg-primary text-white shadow-md shadow-primary/30'
            : 'bg-card text-muted hover:bg-card-hover hover:text-foreground'
      )}
    >
      {children}
    </button>
  );
}

export default function PracticePage() {
  const router = useRouter();
  const [selectedSubject, setSelectedSubject] = useState<Subject | ''>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedYear, setSelectedYear] = useState<number | ''>('');
  const [selectedLevel, setSelectedLevel] = useState<string>('');

  const { completedQuestions, answers, setQueue, clearQueue } =
    usePracticeStore();

  const categories =
    selectedSubject === 'xingce'
      ? XINGCE_CATEGORY_NAMES
      : selectedSubject === 'shenlun'
        ? SHENLUN_CATEGORY_NAMES
        : {};

  const filteredQuestions = useMemo(() => {
    return filterAnswerable(filterQuestions({
      subject: selectedSubject || undefined,
      category:
        (selectedCategory as XingceCategory | ShenlunCategory) || undefined,
      year: selectedYear || undefined,
      level: (selectedLevel || undefined) as
        | import('@/types/question').ExamLevel
        | undefined,
    }));
  }, [selectedSubject, selectedCategory, selectedYear, selectedLevel]);

  const allQuestions = useMemo(() => filterAnswerable(getAllQuestions()), []);

  const categoryStats = useMemo(() => {
    const stats: Record<
      string,
      { total: number; completed: number; correct: number }
    > = {};
    for (const q of allQuestions) {
      const key = `${q.subject}/${q.category}`;
      if (!stats[key]) stats[key] = { total: 0, completed: 0, correct: 0 };
      stats[key].total++;
      if (completedQuestions.includes(q.id)) {
        stats[key].completed++;
        const userAnswer = answers[q.id];
        if (
          userAnswer &&
          JSON.stringify(userAnswer) === JSON.stringify(q.answer)
        ) {
          stats[key].correct++;
        }
      }
    }
    return stats;
  }, [allQuestions, completedQuestions, answers]);

  const start = (shuffle: boolean) => {
    if (filteredQuestions.length === 0) return;
    let list = [...filteredQuestions];
    if (shuffle) list = list.sort(() => Math.random() - 0.5);
    clearQueue();
    setQueue(list.map((q) => q.id));
    router.push(`/practice/${list[0].id}`);
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
      <div className="mb-6 flex items-center gap-3">
        <BookOpen size={24} className="text-primary" />
        <h1 className="text-2xl font-bold">全部题库</h1>
        <span className="ml-auto rounded-full bg-primary/10 px-3 py-1 text-sm font-semibold text-primary">
          {filteredQuestions.length} 题
        </span>
      </div>

      {/* ── 筛选器：chip 风格 ── */}
      <div className="mb-6 space-y-4 rounded-2xl border border-border bg-card/50 p-5 backdrop-blur-sm">
        {/* 科目 */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="mr-1 w-16 text-xs font-semibold uppercase tracking-wider text-muted">
            科目
          </span>
          <Chip
            active={selectedSubject === ''}
            onClick={() => {
              setSelectedSubject('');
              setSelectedCategory('');
            }}
          >
            全部
          </Chip>
          {Object.entries(SUBJECT_NAMES).map(([k, v]) => (
            <Chip
              key={k}
              active={selectedSubject === k}
              onClick={() => {
                setSelectedSubject(k as Subject);
                setSelectedCategory('');
              }}
            >
              {v}
            </Chip>
          ))}
        </div>

        {/* 分类 */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="mr-1 w-16 text-xs font-semibold uppercase tracking-wider text-muted">
            分类
          </span>
          <Chip
            active={selectedCategory === ''}
            onClick={() => setSelectedCategory('')}
            disabled={!selectedSubject}
          >
            全部
          </Chip>
          {Object.entries(categories).map(([k, v]) => (
            <Chip
              key={k}
              active={selectedCategory === k}
              onClick={() => setSelectedCategory(k)}
              disabled={!selectedSubject}
            >
              {v as string}
            </Chip>
          ))}
        </div>

        {/* 年份 */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="mr-1 w-16 text-xs font-semibold uppercase tracking-wider text-muted">
            年份
          </span>
          <Chip active={selectedYear === ''} onClick={() => setSelectedYear('')}>
            全部
          </Chip>
          {[2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015].map((year) => (
            <Chip
              key={year}
              active={selectedYear === year}
              onClick={() => setSelectedYear(year)}
            >
              {year}
            </Chip>
          ))}
        </div>

        {/* 级别 */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="mr-1 w-16 text-xs font-semibold uppercase tracking-wider text-muted">
            级别
          </span>
          <Chip active={selectedLevel === ''} onClick={() => setSelectedLevel('')}>
            全部
          </Chip>
          <Chip
            active={selectedLevel === 'fushengjia'}
            onClick={() => setSelectedLevel('fushengjia')}
          >
            副省级
          </Chip>
          <Chip
            active={selectedLevel === 'dishi'}
            onClick={() => setSelectedLevel('dishi')}
          >
            地市级
          </Chip>
          <Chip
            active={selectedLevel === 'xingzhengzhifa'}
            onClick={() => setSelectedLevel('xingzhengzhifa')}
          >
            行政执法
          </Chip>
        </div>
      </div>

      <div className="mb-6 flex items-center justify-between rounded-xl border border-warning/40 bg-warning/10 px-4 py-2.5 text-xs text-warning">
        <span>
          📍 本页是综合混合筛选。按<b>来源</b>（国考/省考/事业编）筛选请用<Link href="/" className="ml-1 underline hover:no-underline">首页</Link>三大入口。
        </span>
      </div>

      {/* 启动按钮 */}
      <div className="mb-10 flex gap-3">
        <button
          onClick={() => start(false)}
          disabled={filteredQuestions.length === 0}
          className="group flex flex-1 items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3 font-semibold text-white shadow-lg shadow-primary/30 transition-[transform,box-shadow,background-color,border-color] hover:bg-primary-dark hover:shadow-xl hover:shadow-primary/40 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
        >
          <PlayCircle
            size={18}
            className="transition-transform group-hover:scale-110"
          />
          顺序练习
        </button>
        <button
          onClick={() => start(true)}
          disabled={filteredQuestions.length === 0}
          className="group flex flex-1 items-center justify-center gap-2 rounded-xl border-2 border-primary/40 bg-primary/5 px-5 py-3 font-semibold text-primary transition-[transform,box-shadow,background-color,border-color] hover:border-primary hover:bg-primary/10 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 sm:flex-none sm:px-8"
        >
          <Shuffle
            size={18}
            className="transition-transform group-hover:rotate-180"
          />
          随机练习
        </button>
      </div>

      {/* Category cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="col-span-full">
          <h2 className="mb-3 text-lg font-semibold">行测</h2>
        </div>
        {Object.entries(XINGCE_CATEGORY_NAMES).map(([key, name]) => {
          const stat =
            categoryStats[`xingce/${key}`] || {
              total: 0,
              completed: 0,
              correct: 0,
            };
          const accuracy = calcPercentage(stat.correct, stat.completed);
          const iconMask = `url(/icons/category-${key}.svg) center/contain no-repeat`;
          return (
            <motion.div
              key={key}
              whileHover={{ y: -3 }}
              whileTap={{ scale: 0.98 }}
              className="rounded-xl border border-border bg-card p-4 shadow-sm transition-[transform,box-shadow,background-color,border-color] hover:border-primary/30 hover:shadow-md"
            >
              <Link
                href={`/practice?subject=xingce&category=${key}`}
                className="block"
              >
                <div className="mb-2 flex items-center gap-3">
                  <span
                    aria-hidden
                    className="inline-block h-8 w-8 shrink-0 bg-primary"
                    style={{ WebkitMask: iconMask, mask: iconMask }}
                  />
                  <h3 className="font-semibold">{name}</h3>
                </div>
                <div className="mb-2 flex items-center gap-4 text-sm text-muted">
                  <span>{stat.total} 题</span>
                  <span className="flex items-center gap-1">
                    <CheckCircle2 size={14} className="text-success" />
                    已做 {stat.completed}
                  </span>
                  {stat.completed > 0 && <span>正确率 {accuracy}%</span>}
                </div>
                <div className="h-1.5 rounded-full bg-border">
                  <div
                    className="h-full rounded-full bg-primary transition-[transform,box-shadow,background-color,border-color]"
                    style={{
                      width: `${calcPercentage(stat.completed, stat.total)}%`,
                    }}
                  />
                </div>
              </Link>
            </motion.div>
          );
        })}

        <div className="col-span-full mt-4">
          <h2 className="mb-3 text-lg font-semibold">申论</h2>
        </div>
        {Object.entries(SHENLUN_CATEGORY_NAMES).map(([key, name]) => {
          const stat =
            categoryStats[`shenlun/${key}`] || {
              total: 0,
              completed: 0,
              correct: 0,
            };
          const accuracy = calcPercentage(stat.correct, stat.completed);
          const iconMask = `url(/icons/category-${key}.svg) center/contain no-repeat`;
          return (
            <motion.div
              key={key}
              whileHover={{ y: -3 }}
              whileTap={{ scale: 0.98 }}
              className="rounded-xl border border-border bg-card p-4 shadow-sm transition-[transform,box-shadow,background-color,border-color] hover:border-success/30 hover:shadow-md"
            >
              <Link
                href={`/practice?subject=shenlun&category=${key}`}
                className="block"
              >
                <div className="mb-2 flex items-center gap-3">
                  <span
                    aria-hidden
                    className="inline-block h-8 w-8 shrink-0 bg-success"
                    style={{ WebkitMask: iconMask, mask: iconMask }}
                  />
                  <h3 className="font-semibold">{name}</h3>
                </div>
                <div className="mb-2 flex items-center gap-4 text-sm text-muted">
                  <span>{stat.total} 题</span>
                  <span className="flex items-center gap-1">
                    <CheckCircle2 size={14} className="text-success" />
                    已做 {stat.completed}
                  </span>
                  {stat.completed > 0 && <span>正确率 {accuracy}%</span>}
                </div>
                <div className="h-1.5 rounded-full bg-border">
                  <div
                    className="h-full rounded-full bg-success transition-[transform,box-shadow,background-color,border-color]"
                    style={{
                      width: `${calcPercentage(stat.completed, stat.total)}%`,
                    }}
                  />
                </div>
              </Link>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
