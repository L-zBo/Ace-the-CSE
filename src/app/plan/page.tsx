'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  CalendarCheck,
  Plus,
  CheckCircle2,
  Trash2,
  Target,
  Calendar,
} from 'lucide-react';
import { usePlanStore } from '@/stores/planStore';
import { useStatsStore } from '@/stores/statsStore';
import { RingProgress } from '@/components/ui';
import { getTodayString, calcPercentage } from '@/lib/utils';
import type { StudyPlan } from '@/types/user';

const planTemplates = [
  {
    type: 'sprint_30' as const,
    name: '30天冲刺计划',
    desc: '考前强化，每天30题，重点攻克薄弱项',
    dailyTarget: 30,
    days: 30,
    color: 'from-seal-500 to-seal-700',
  },
  {
    type: 'systematic_60' as const,
    name: '60天系统复习',
    desc: '系统刷题，每天20题，全面覆盖各模块',
    dailyTarget: 20,
    days: 60,
    color: 'from-brand-500 to-brand-700',
  },
  {
    type: 'comprehensive_90' as const,
    name: '90天全面备考',
    desc: '稳扎稳打，每天15题，配合知识点学习',
    dailyTarget: 15,
    days: 90,
    color: 'from-success to-success/70',
  },
];

export default function PlanPage() {
  const { plans, createPlan, setActivePlan, checkIn, deletePlan, activePlanId } = usePlanStore();
  const stats = useStatsStore();
  const [showCreate, setShowCreate] = useState(false);

  const today = getTodayString();
  const todayStats = stats.dailyStats.find((d) => d.date === today);
  const activePlan = plans.find((p) => p.id === activePlanId);

  const handleCreatePlan = (template: typeof planTemplates[0]) => {
    const startDate = today;
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + template.days);
    const endDateStr = `${endDate.getFullYear()}-${String(endDate.getMonth() + 1).padStart(2, '0')}-${String(endDate.getDate()).padStart(2, '0')}`;

    createPlan({
      name: template.name,
      type: template.type,
      startDate,
      endDate: endDateStr,
      dailyTarget: template.dailyTarget,
      focusAreas: [],
    });
    setShowCreate(false);
  };

  const getPlanProgress = (plan: StudyPlan) => {
    const start = new Date(plan.startDate);
    const end = new Date(plan.endDate);
    const totalDays = Math.ceil((end.getTime() - start.getTime()) / (1000 * 86400));
    const completedDays = plan.completedDays.length;
    return { totalDays, completedDays, percentage: calcPercentage(completedDays, totalDays) };
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <CalendarCheck size={24} className="text-info" />
          <h1 className="text-2xl font-bold">学习计划</h1>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-dark"
        >
          <Plus size={16} />
          新建计划
        </button>
      </div>

      {/* Today overview */}
      {activePlan && (
        <div className="mb-8 rounded-xl border border-border bg-card p-5">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-semibold">今日任务 — {activePlan.name}</h3>
            <button
              onClick={() => checkIn(activePlan.id)}
              disabled={activePlan.completedDays.includes(today)}
              className="flex items-center gap-1.5 rounded-lg bg-success px-4 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-50"
            >
              <CheckCircle2 size={16} />
              {activePlan.completedDays.includes(today) ? '已打卡' : '打卡'}
            </button>
          </div>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-primary">
                {todayStats?.totalQuestions || 0}
              </div>
              <div className="text-xs text-muted">今日已做</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-accent">
                {activePlan.dailyTarget}
              </div>
              <div className="text-xs text-muted">每日目标</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-success">
                {calcPercentage(todayStats?.totalQuestions || 0, activePlan.dailyTarget)}%
              </div>
              <div className="text-xs text-muted">完成度</div>
            </div>
          </div>
          <div className="mt-4 h-2 rounded-full bg-border">
            <div
              className="h-full rounded-full bg-primary transition-[width] duration-300 ease-out"
              style={{
                width: `${Math.min(100, calcPercentage(todayStats?.totalQuestions || 0, activePlan.dailyTarget))}%`,
              }}
            />
          </div>
        </div>
      )}

      {/* Create plan templates */}
      {showCreate && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h3 className="mb-4 font-semibold">选择计划模板</h3>
          <div className="grid gap-4 sm:grid-cols-3">
            {planTemplates.map((tpl) => (
              <button
                key={tpl.type}
                onClick={() => handleCreatePlan(tpl)}
                className="rounded-xl border border-border bg-card p-5 text-left transition-[transform,box-shadow,background-color,border-color] hover:border-primary/30 hover:shadow-md"
              >
                <div
                  className={`mb-3 inline-flex rounded-lg bg-gradient-to-br ${tpl.color} p-2 text-white`}
                >
                  <Target size={20} />
                </div>
                <h4 className="mb-1 font-semibold">{tpl.name}</h4>
                <p className="mb-2 text-sm text-muted">{tpl.desc}</p>
                <div className="flex items-center gap-3 text-xs text-muted">
                  <span className="flex items-center gap-1">
                    <Calendar size={12} /> {tpl.days}天
                  </span>
                  <span>每天{tpl.dailyTarget}题</span>
                </div>
              </button>
            ))}
          </div>
        </motion.div>
      )}

      {/* Plan list */}
      {plans.length === 0 && !showCreate ? (
        <div className="flex min-h-[30vh] flex-col items-center justify-center text-center">
          <CalendarCheck size={48} className="mb-4 text-muted" />
          <h3 className="mb-2 text-lg font-semibold">还没有学习计划</h3>
          <p className="text-sm text-muted">创建一个计划，开始有规律的学习之旅</p>
        </div>
      ) : (
        <div className="space-y-4">
          {plans.map((plan) => {
            const progress = getPlanProgress(plan);
            const isActive = plan.id === activePlanId;

            return (
              <div
                key={plan.id}
                className={`rounded-xl border bg-card p-5 transition-[transform,box-shadow,background-color,border-color] ${
                  isActive ? 'border-primary shadow-md' : 'border-border'
                }`}
              >
                <div className="mb-3 flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="mb-1 flex items-center gap-2">
                      <h3 className="font-semibold">{plan.name}</h3>
                      {isActive && (
                        <span className="rounded bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                          当前计划
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-muted">
                      <span>{plan.startDate} ~ {plan.endDate}</span>
                      <span>每天 {plan.dailyTarget} 题</span>
                      <span className="tabular-nums">已打卡 {progress.completedDays} 天</span>
                    </div>
                  </div>
                  {/* D-18a P3e 升级 — 完成度环图替代线性条 */}
                  <RingProgress
                    percentage={progress.percentage}
                    size={80}
                    strokeWidth={7}
                    subLabel={`${progress.completedDays} 天`}
                  />
                </div>

                <div className="flex items-center gap-2">
                  {!isActive && (
                    <button
                      onClick={() => setActivePlan(plan.id)}
                      className="flex items-center gap-1 rounded-lg border border-border px-3 py-1 text-xs hover:bg-card-hover"
                    >
                      切换为当前
                    </button>
                  )}
                  <button
                    onClick={() => deletePlan(plan.id)}
                    aria-label="删除计划"
                    className="ml-auto rounded-lg p-1.5 text-muted hover:bg-danger/10 hover:text-danger"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
