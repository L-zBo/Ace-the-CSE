'use client';

import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'framer-motion';
import {
  BookOpen,
  ClipboardCheck,
  BarChart3,
  RotateCcw,
  Brain,
  CalendarCheck,
  Newspaper,
  TrendingUp,
  Target,
  Flame,
  Landmark,
  MapPinned,
  Building2,
  ArrowRight,
  Library,
} from 'lucide-react';
import { useStatsStore } from '@/stores/statsStore';
import { useMistakeStore } from '@/stores/mistakeStore';
import { calcPercentage, getTodayString } from '@/lib/utils';
import { EXAM_BANK_THEMES, type BankTheme } from '@/lib/examBankTheme';
import { BlurText, CountUp, GradientText } from '@/components/effects';
import questionStats from '@/data/questionStats.json';

interface ExamBank {
  href: string;
  icon: typeof Landmark;
  title: string;
  subtitle: string;
  desc: string;
  theme: BankTheme;
}

const examBanks: ExamBank[] = [
  {
    href: '/practice/national',
    icon: Landmark,
    title: '国考',
    subtitle: '国家公务员考试',
    desc: '副省级 · 地市级 · 行政执法',
    theme: 'mo-blue',
  },
  {
    href: '/practice/provincial',
    icon: MapPinned,
    title: '省考',
    subtitle: '各省公务员考试',
    desc: '12省市 · 2020-2025',
    theme: 'emerald-deep',
  },
  {
    href: '/practice/institution',
    icon: Building2,
    title: '事业编',
    subtitle: '事业单位联考',
    desc: 'A · B · C · D · E 五类',
    theme: 'cinnabar',
  },
];

// 卷面气质色系（清除原 Tailwind 通用色 violet/fuchsia/rose/pink/cyan/teal）
// 见 docs/DESIGN.md §1.6 严禁使用 + §1.1 主色 / §1.2 语义色
// 分组：核心刷题(墨蓝家族) · 内容积累(翠绿/朱砂) · 数据管理(印章红/青/金) · 资讯(暖橙)
const features = [
  {
    href: '/practice',
    icon: BookOpen,
    title: '全部题库',
    desc: '混合 · 自定义筛选练习',
    color: 'from-[#0f2942] to-[#1e3a5f]', // 墨蓝深 → 墨蓝（主刷题）
    bg: 'bg-[#1e3a5f]/10',
  },
  {
    href: '/exam',
    icon: ClipboardCheck,
    title: '模拟考试',
    desc: '真实计时 · 考场模拟体验',
    color: 'from-[#1e3a5f] to-[#2c5282]', // 墨蓝 → 墨蓝亮（考场感）
    bg: 'bg-[#2c5282]/10',
  },
  {
    href: '/idioms',
    icon: Library,
    title: '成语词卡',
    desc: '逻辑填空高频积累 · 翻面记忆',
    color: 'from-[#064e3b] to-[#047857]', // 翠绿深 → 翠绿（积累）
    bg: 'bg-[#047857]/10',
  },
  {
    href: '/knowledge',
    icon: Brain,
    title: '知识体系',
    desc: '知识图谱 · 体系化掌握考点',
    color: 'from-[#7c1d1d] to-[#b45309]', // 朱砂 → 赭石（书院金）
    bg: 'bg-[#b45309]/10',
  },
  {
    href: '/review',
    icon: RotateCcw,
    title: '错题本',
    desc: '智能收集 · 重点攻克易错题',
    color: 'from-[#7c1d1d] to-[#c1272d]', // 印章红家族（错题 = 印章红）
    bg: 'bg-[#c1272d]/10',
  },
  {
    href: '/stats',
    icon: BarChart3,
    title: '统计分析',
    desc: '成绩趋势 · 薄弱项一目了然',
    color: 'from-[#0e7490] to-[#06b6d4]', // info 青色家族（数据 = info）
    bg: 'bg-[#06b6d4]/10',
  },
  {
    href: '/plan',
    icon: CalendarCheck,
    title: '学习计划',
    desc: '科学规划 · 每日任务打卡',
    color: 'from-[#047857] to-[#10b981]', // 翠绿亮（success / 完成）
    bg: 'bg-[#10b981]/10',
  },
  {
    href: '/current-affairs',
    icon: Newspaper,
    title: '时事热点',
    desc: '近一年大事 · 昨日要闻速览',
    color: 'from-[#92400e] to-[#d97706]', // 暖橙金（资讯 = warning amber 系）
    bg: 'bg-[#d97706]/10',
  },
];

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

export default function Home() {
  const stats = useStatsStore();
  const mistakeStore = useMistakeStore();

  const today = getTodayString();
  const todayStats = stats.dailyStats.find((d) => d.date === today);
  const todayCount = todayStats?.totalQuestions || 0;
  const todayCorrect = todayStats?.correctCount || 0;
  const todayAccuracy = calcPercentage(todayCorrect, todayCount);
  const activeMistakes = mistakeStore.mistakes.filter((m) => !m.isMastered).length;

  const bankCounts = questionStats as Record<string, number>;

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12">
      {/* Hero — 印章 SVG 水印 + Bo Logo + 渐变流动标题 */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="relative mb-10 flex flex-col items-center text-center sm:mb-14"
      >
        {/* 篆体"博"字 SVG 印章背景水印 — 卷面气质装饰锚 + asymmetric 偏移设计
           （P2b-2 SVG + P2b-5 frontend-design 非对称设计）*/}
        <Image
          aria-hidden="true"
          src="/img/decorative/seal-bo.svg"
          alt=""
          width={352}
          height={352}
          loading="eager"
          priority
          unoptimized
          className="pointer-events-none absolute right-[8%] top-[-8%] -z-10 h-[16rem] w-[16rem] select-none opacity-[0.07] sm:h-[22rem] sm:w-[22rem] motion-safe:transition-transform motion-safe:duration-500 motion-safe:hover:rotate-[5deg] motion-safe:hover:scale-105"
        />
        {/* "考"字水印 — 左下偏移，与"博"印 overlap 形成 editorial asymmetric */}
        <Image
          aria-hidden="true"
          src="/img/decorative/seal-kao.svg"
          alt=""
          width={224}
          height={224}
          unoptimized
          className="pointer-events-none absolute left-[6%] bottom-[-10%] -z-10 hidden h-[10rem] w-[10rem] select-none opacity-[0.05] sm:block sm:h-[14rem] sm:w-[14rem]"
        />
        <div className="mb-5 flex h-20 w-20 items-center justify-center rounded-2xl gradient-mo-seal shadow-lg shadow-seal-red sm:h-24 sm:w-24">
          <span translate="no" className="select-none font-black leading-none tracking-tight text-white text-[2.75rem] sm:text-[3.25rem]">
            Bo
          </span>
        </div>
        <h1 translate="no" className="font-display-zh mb-2 text-4xl font-bold tracking-tight sm:text-5xl">
          <GradientText variant="default" className="font-display-en">
            <BlurText text="Ace the CSE" splitBy="char" staggerDelay={0.05} delay={0.15} />
          </GradientText>
        </h1>
        <p className="font-display-zh max-w-md text-base text-white/70 sm:text-lg">
          公务员考试全功能学习平台 · 行测 · 申论 · 历年真题
        </p>
      </motion.div>

      {/* Today stats strip */}
      <motion.dl
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mb-10 flex flex-wrap items-center justify-center gap-6 rounded-xl border border-white/10 bg-black/30 px-6 py-4 backdrop-blur-md sm:gap-10"
      >
        <div className="flex items-center gap-2">
          <TrendingUp size={18} className="text-brand-300" aria-hidden="true" />
          <dt className="text-sm text-white/50">今日做题</dt>
          <dd className="text-lg font-bold text-white tabular-nums">
            <CountUp to={todayCount} duration={700} />
          </dd>
        </div>
        <div className="flex items-center gap-2">
          <Target size={18} className="text-success" aria-hidden="true" />
          <dt className="text-sm text-white/50">正确率</dt>
          <dd className="text-lg font-bold text-white tabular-nums">
            {todayCount > 0 ? <CountUp to={todayAccuracy} duration={700} suffix="%" /> : '—'}
          </dd>
        </div>
        <div className="flex items-center gap-2">
          <Flame size={18} className="text-warning" aria-hidden="true" />
          <dt className="text-sm text-white/50">连续打卡</dt>
          <dd className="text-lg font-bold text-white tabular-nums">
            <CountUp to={stats.streakDays} duration={700} suffix="天" />
          </dd>
        </div>
        <div className="flex items-center gap-2">
          <RotateCcw size={18} className="text-seal-300" aria-hidden="true" />
          <dt className="text-sm text-white/50">待复习</dt>
          <dd className="text-lg font-bold text-white tabular-nums">
            <CountUp to={activeMistakes} duration={700} />
          </dd>
        </div>
      </motion.dl>

      {/* ── 题库选择（主入口）── */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="mb-10"
      >
        <h2 className="font-display-zh mb-4 flex items-center justify-center gap-3 text-center text-sm font-semibold tracking-widest text-white/60">
          <span aria-hidden="true" className="h-px w-8 bg-gradient-to-r from-transparent to-white/30" />
          选择题库
          <span aria-hidden="true" className="h-px w-8 bg-gradient-to-l from-transparent to-white/30" />
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 sm:gap-5">
          {examBanks.map((b) => {
            const Icon = b.icon;
            const count = bankCounts[b.href.split('/').pop() || ''] || 0;
            const disabled = count === 0;
            return (
              <motion.div key={b.href} variants={item}>
                <Link
                  href={disabled ? '#' : b.href}
                  onClick={(e) => disabled && e.preventDefault()}
                  aria-disabled={disabled}
                  className={`group relative flex h-full flex-col overflow-hidden rounded-2xl ${EXAM_BANK_THEMES[b.theme].bgClass} p-6 shadow-xl ${EXAM_BANK_THEMES[b.theme].shadowClass} transition-[transform,box-shadow,background-color,border-color] ${
                    disabled
                      ? 'cursor-not-allowed opacity-60'
                      : 'hover:shadow-2xl'
                  }`}
                >
                  <div className="absolute -right-4 -top-4 opacity-20 transition-transform group-hover:scale-110">
                    <Icon size={88} strokeWidth={1.2} />
                  </div>
                  <div className="relative z-10">
                    <Icon size={32} className="mb-3 text-white" />
                    <div className="mb-1 text-2xl font-bold text-white">{b.title}</div>
                    <div className="mb-1 text-sm text-white/80">{b.subtitle}</div>
                    <div className="mb-4 text-xs text-white/70">{b.desc}</div>
                    <div className="flex items-center justify-between">
                      <span className="rounded-full bg-black/25 px-3 py-1 text-xs font-semibold text-white backdrop-blur-sm">
                        {disabled ? '敬请期待' : `${count} 题`}
                      </span>
                      {!disabled && (
                        <ArrowRight
                          size={20}
                          className="text-white transition-transform group-hover:translate-x-1"
                        />
                      )}
                    </div>
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </div>
      </motion.div>

      {/* ── 其他功能 ── */}
      <h2 className="font-display-zh mb-4 flex items-center justify-center gap-3 text-center text-sm font-semibold tracking-widest text-white/60">
        <span aria-hidden="true" className="h-px w-8 bg-gradient-to-r from-transparent to-white/30" />
        更多功能
        <span aria-hidden="true" className="h-px w-8 bg-gradient-to-l from-transparent to-white/30" />
      </h2>
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 sm:gap-5"
      >
        {features.map((f) => {
          const Icon = f.icon;
          return (
            <motion.div key={f.href} variants={item}>
              <Link
                href={f.href}
                className={`group flex flex-col items-center rounded-2xl border border-white/10 ${f.bg} p-5 text-center backdrop-blur-sm transition-[transform,box-shadow,background-color,border-color] hover:border-white/25 hover:bg-white/15 hover:shadow-lg hover:shadow-black/30 active:scale-[0.98] sm:p-7`}
              >
                <div
                  className={`mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${f.color} text-white shadow-md transition-transform group-hover:scale-110 sm:h-14 sm:w-14`}
                >
                  <Icon size={24} />
                </div>
                <h3 className="mb-1 text-base font-semibold text-white sm:text-lg">
                  {f.title}
                </h3>
                <p className="text-xs text-white/50 sm:text-sm">{f.desc}</p>
              </Link>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Quick start hint */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="mt-10 text-center"
      >
        <p className="text-sm text-white/40">
          包含国考 · 省考 · 事业编历年真题，持续更新中
        </p>
      </motion.div>
    </div>
  );
}

