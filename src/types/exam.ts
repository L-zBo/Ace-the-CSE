import type { Question, ExamSource, Subject } from './question';

// 考试配置
export interface ExamConfig {
  id: string;
  title: string;
  subject: Subject;
  source: ExamSource;
  region?: string;
  year: number;
  duration: number; // 分钟
  totalQuestions: number;
  questions: Question[];
}

// 答题状态
export type AnswerStatus = 'unanswered' | 'answered' | 'marked' | 'current';

// 单题答题记录
export interface ExamAnswer {
  questionId: string;
  userAnswer: string | string[] | null;
  isMarked: boolean;
  timeSpent: number; // 秒
}

// 考试进行状态
export interface ExamSession {
  examId: string;
  config: ExamConfig;
  answers: Record<string, ExamAnswer>;
  currentIndex: number;
  startTime: number;
  remainingTime: number; // 秒
  isSubmitted: boolean;
}

// 考试结果
export interface ExamResult {
  examId: string;
  title: string;
  subject: Subject;
  source: ExamSource;
  year: number;
  totalQuestions: number;
  correctCount: number;
  wrongCount: number;
  unansweredCount: number;
  score: number;
  accuracy: number;
  totalTime: number; // 秒
  submittedAt: string;
  categoryScores: Record<string, { correct: number; total: number }>;
}
