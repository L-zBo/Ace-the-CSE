import type { Subject, XingceCategory, ShenlunCategory } from './question';

// 做题记录
export interface PracticeRecord {
  questionId: string;
  subject: Subject;
  category: XingceCategory | ShenlunCategory;
  userAnswer: string | string[];
  isCorrect: boolean;
  timeSpent: number;
  practiceDate: string; // ISO date string
}

// 错题记录
export interface MistakeRecord {
  questionId: string;
  subject: Subject;
  category: XingceCategory | ShenlunCategory;
  wrongCount: number;
  consecutiveCorrect: number;
  lastWrongDate: string;
  isMastered: boolean;
}

// 每日统计
export interface DailyStats {
  date: string; // YYYY-MM-DD
  totalQuestions: number;
  correctCount: number;
  timeSpent: number; // 秒
  categories: Record<string, { total: number; correct: number }>;
}

// 学习计划
export interface StudyPlan {
  id: string;
  name: string;
  type: 'sprint_30' | 'systematic_60' | 'comprehensive_90' | 'custom';
  startDate: string;
  endDate: string;
  dailyTarget: number;
  focusAreas: (XingceCategory | ShenlunCategory)[];
  completedDays: string[];
  isActive: boolean;
}

// 学习计划每日任务
export interface DailyTask {
  date: string;
  targetCount: number;
  completedCount: number;
  categories: {
    category: XingceCategory | ShenlunCategory;
    targetCount: number;
    completedCount: number;
  }[];
}

// 用户整体统计
export interface UserStats {
  totalPracticed: number;
  totalCorrect: number;
  streakDays: number;
  longestStreak: number;
  lastPracticeDate: string;
  dailyStats: DailyStats[];
  examResults: import('./exam').ExamResult[];
}
