'use client';

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, Target, Flame, BookOpen } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from 'recharts';
import { useStatsStore } from '@/stores/statsStore';
import { calcPercentage, cn } from '@/lib/utils';
import {
  XINGCE_CATEGORY_NAMES,
  SHENLUN_CATEGORY_NAMES,
} from '@/types/question';
import { Card, EmptyState } from '@/components/ui';
import { CountUp } from '@/components/effects/CountUp';

const SUMMARY_STAGGER = (i: number) => ({
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  transition: { delay: i * 0.06, duration: 0.35, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] },
});

export default function StatsPage() {
  const stats = useStatsStore();
  const overallAccuracy = calcPercentage(stats.totalCorrect, stats.totalPracticed);

  const trendData = useMemo(() => {
    const days: { date: string; count: number; accuracy: number }[] = [];
    for (let i = 13; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      const dayStats = stats.dailyStats.find((s) => s.date === dateStr);
      days.push({
        date: `${d.getMonth() + 1}/${d.getDate()}`,
        count: dayStats?.totalQuestions || 0,
        accuracy: dayStats
          ? calcPercentage(dayStats.correctCount, dayStats.totalQuestions)
          : 0,
      });
    }
    return days;
  }, [stats.dailyStats]);

  const categoryData = useMemo(() => {
    const allCategories = { ...XINGCE_CATEGORY_NAMES, ...SHENLUN_CATEGORY_NAMES };
    const data: { category: string; accuracy: number; count: number }[] = [];

    for (const [key, name] of Object.entries(allCategories)) {
      let total = 0;
      let correct = 0;
      for (const day of stats.dailyStats) {
        if (day.categories[key]) {
          total += day.categories[key].total;
          correct += day.categories[key].correct;
        }
      }
      if (total > 0) {
        data.push({
          category: name.length > 4 ? name.slice(0, 4) : name,
          accuracy: calcPercentage(correct, total),
          count: total,
        });
      }
    }
    return data;
  }, [stats.dailyStats]);

  const heatmapData = useMemo(() => {
    const days: { date: string; count: number; label: string }[] = [];
    for (let i = 34; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      const dayStats = stats.dailyStats.find((s) => s.date === dateStr);
      days.push({
        date: dateStr,
        count: dayStats?.totalQuestions || 0,
        label: `${d.getMonth() + 1}/${d.getDate()}`,
      });
    }
    return days;
  }, [stats.dailyStats]);

  // 4 阶热力色：success token + opacity 阶梯（token 化，无 Tailwind 彩虹依赖）
  const getHeatColor = (count: number) => {
    if (count === 0) return 'bg-border';
    if (count <= 5) return 'bg-success/20';
    if (count <= 15) return 'bg-success/45';
    if (count <= 30) return 'bg-success/70';
    return 'bg-success';
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
      <header className="mb-6 flex items-center gap-3">
        <BarChart3 size={24} className="text-brand-300" aria-hidden="true" />
        <h1 className="font-display-zh text-2xl font-bold text-foreground">统计分析</h1>
      </header>

      {/* Summary cards */}
      <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <motion.div {...SUMMARY_STAGGER(0)}>
          <Card compact className="rounded-xl">
            <div className="mb-2 flex items-center gap-2">
              <BookOpen size={16} className="text-brand-300" aria-hidden="true" />
              <span className="text-sm text-foreground-muted">总做题量</span>
            </div>
            <div className="font-display-en text-2xl font-bold text-foreground tabular-nums">
              <CountUp to={stats.totalPracticed} duration={700} />
            </div>
          </Card>
        </motion.div>
        <motion.div {...SUMMARY_STAGGER(1)}>
          <Card compact className="rounded-xl">
            <div className="mb-2 flex items-center gap-2">
              <Target size={16} className="text-success" aria-hidden="true" />
              <span className="text-sm text-foreground-muted">总正确率</span>
            </div>
            <div className="font-display-en text-2xl font-bold text-foreground tabular-nums">
              {stats.totalPracticed > 0 ? (
                <CountUp to={overallAccuracy} duration={700} suffix="%" />
              ) : (
                '--'
              )}
            </div>
          </Card>
        </motion.div>
        <motion.div {...SUMMARY_STAGGER(2)}>
          <Card compact className="rounded-xl">
            <div className="mb-2 flex items-center gap-2">
              <Flame size={16} className="text-warning" aria-hidden="true" />
              <span className="text-sm text-foreground-muted">连续打卡</span>
            </div>
            <div className="font-display-en text-2xl font-bold text-foreground tabular-nums">
              <CountUp to={stats.streakDays} duration={700} suffix=" 天" />
            </div>
          </Card>
        </motion.div>
        <motion.div {...SUMMARY_STAGGER(3)}>
          <Card compact className="rounded-xl">
            <div className="mb-2 flex items-center gap-2">
              <TrendingUp size={16} className="text-seal-300" aria-hidden="true" />
              <span className="text-sm text-foreground-muted">最长连续</span>
            </div>
            <div className="font-display-en text-2xl font-bold text-foreground tabular-nums">
              <CountUp to={stats.longestStreak} duration={700} suffix=" 天" />
            </div>
          </Card>
        </motion.div>
      </div>

      {stats.totalPracticed === 0 ? (
        <EmptyState
          icon={BarChart3}
          title="暂无做题记录"
          description="开始刷题后，这里会展示你的学习数据分析"
        />
      ) : (
        <>
          {/* Trend chart */}
          <Card className="mb-8 rounded-xl">
            <h3 className="mb-4 font-display-zh text-sm font-semibold text-foreground">
              近 14 天做题趋势
            </h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="date" fontSize={12} stroke="var(--foreground-muted)" />
                <YAxis fontSize={12} stroke="var(--foreground-muted)" />
                <Tooltip
                  contentStyle={{
                    background: 'var(--card)',
                    border: '1px solid var(--border)',
                    borderRadius: 8,
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="var(--brand-soft)"
                  strokeWidth={2}
                  name="做题数"
                  dot={{ r: 3 }}
                />
                <Line
                  type="monotone"
                  dataKey="accuracy"
                  stroke="var(--success)"
                  strokeWidth={2}
                  name="正确率%"
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          {/* Category radar */}
          {categoryData.length > 0 && (
            <Card className="mb-8 rounded-xl">
              <h3 className="mb-4 font-display-zh text-sm font-semibold text-foreground">
                各分类正确率
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={categoryData}>
                  <PolarGrid stroke="var(--border)" />
                  <PolarAngleAxis dataKey="category" fontSize={12} stroke="var(--foreground-muted)" />
                  <PolarRadiusAxis fontSize={10} stroke="var(--foreground-muted)" domain={[0, 100]} />
                  <Radar
                    dataKey="accuracy"
                    stroke="var(--seal-red)"
                    fill="var(--seal-red)"
                    fillOpacity={0.18}
                    name="正确率%"
                  />
                  <Tooltip
                    contentStyle={{
                      background: 'var(--card)',
                      border: '1px solid var(--border)',
                      borderRadius: 8,
                    }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </Card>
          )}

          {/* Heatmap */}
          <Card className="mb-8 rounded-xl">
            <h3 className="mb-4 font-display-zh text-sm font-semibold text-foreground">
              做题日历（最近 35 天）
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {heatmapData.map((d) => (
                <motion.div
                  key={d.date}
                  whileHover={{ scale: 1.3 }}
                  className={cn('h-5 w-5 rounded-sm cursor-default', getHeatColor(d.count))}
                  title={`${d.label}: ${d.count} 题`}
                  aria-label={`${d.label}, ${d.count} 题`}
                />
              ))}
            </div>
            <div className="mt-3 flex items-center gap-2 text-xs text-foreground-muted">
              <span>少</span>
              <span className="h-3 w-3 rounded-sm bg-border" />
              <span className="h-3 w-3 rounded-sm bg-success/20" />
              <span className="h-3 w-3 rounded-sm bg-success/45" />
              <span className="h-3 w-3 rounded-sm bg-success/70" />
              <span className="h-3 w-3 rounded-sm bg-success" />
              <span>多</span>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
