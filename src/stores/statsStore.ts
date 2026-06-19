import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserStats } from '@/types/user';
import { getTodayString } from '@/lib/utils';

interface StatsState extends UserStats {
  recordPractice: (params: {
    category: string;
    isCorrect: boolean;
    timeSpent: number;
  }) => void;
  updateStreak: () => void;
}

export const useStatsStore = create<StatsState>()(
  persist(
    (set, get) => ({
      totalPracticed: 0,
      totalCorrect: 0,
      streakDays: 0,
      longestStreak: 0,
      lastPracticeDate: '',
      dailyStats: [],
      examResults: [],

      recordPractice: ({ category, isCorrect, timeSpent }) => {
        const today = getTodayString();
        const state = get();

        let dailyStats = [...state.dailyStats];
        let todayStats = dailyStats.find((d) => d.date === today);

        if (!todayStats) {
          todayStats = {
            date: today,
            totalQuestions: 0,
            correctCount: 0,
            timeSpent: 0,
            categories: {},
          };
          dailyStats.push(todayStats);
        } else {
          dailyStats = dailyStats.map((d) =>
            d.date === today ? { ...d } : d
          );
          todayStats = dailyStats.find((d) => d.date === today)!;
        }

        todayStats.totalQuestions += 1;
        todayStats.correctCount += isCorrect ? 1 : 0;
        todayStats.timeSpent += timeSpent;

        if (!todayStats.categories[category]) {
          todayStats.categories[category] = { total: 0, correct: 0 };
        }
        todayStats.categories[category].total += 1;
        todayStats.categories[category].correct += isCorrect ? 1 : 0;

        set({
          totalPracticed: state.totalPracticed + 1,
          totalCorrect: state.totalCorrect + (isCorrect ? 1 : 0),
          dailyStats,
          lastPracticeDate: today,
        });

        // 更新连续打卡
        get().updateStreak();
      },

      updateStreak: () => {
        const state = get();
        const today = getTodayString();
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const yesterdayStr = getTodayString.call(null) !== today ? '' :
          `${yesterday.getFullYear()}-${String(yesterday.getMonth() + 1).padStart(2, '0')}-${String(yesterday.getDate()).padStart(2, '0')}`;

        let streak = state.streakDays;
        if (state.lastPracticeDate === today) {
          if (streak === 0) streak = 1;
        } else if (state.lastPracticeDate === yesterdayStr) {
          streak += 1;
        } else {
          streak = 1;
        }

        set({
          streakDays: streak,
          longestStreak: Math.max(streak, state.longestStreak),
        });
      },
    }),
    { name: 'ace-stats' }
  )
);
