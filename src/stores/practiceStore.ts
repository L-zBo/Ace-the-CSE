import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Question } from '@/types/question';

interface PracticeState {
  // 当前练习的题目列表
  questions: Question[];
  currentIndex: number;
  // 当前练习队列（题目 ID 有序），用于入口页设定专项练习范围
  queue: string[];
  // 用户答案 questionId -> answer
  answers: Record<string, string | string[]>;
  // 收藏的题目
  favorites: string[];
  // 已完成的题目
  completedQuestions: string[];

  setQuestions: (questions: Question[]) => void;
  setCurrentIndex: (index: number) => void;
  setQueue: (ids: string[]) => void;
  clearQueue: () => void;
  submitAnswer: (questionId: string, answer: string | string[]) => void;
  toggleFavorite: (questionId: string) => void;
  markCompleted: (questionId: string) => void;
  reset: () => void;
}

export const usePracticeStore = create<PracticeState>()(
  persist(
    (set) => ({
      questions: [],
      currentIndex: 0,
      queue: [],
      answers: {},
      favorites: [],
      completedQuestions: [],

      setQuestions: (questions) => set({ questions, currentIndex: 0 }),
      setCurrentIndex: (index) => set({ currentIndex: index }),
      setQueue: (ids) => set({ queue: ids }),
      clearQueue: () => set({ queue: [] }),
      submitAnswer: (questionId, answer) =>
        set((state) => ({
          answers: { ...state.answers, [questionId]: answer },
        })),
      toggleFavorite: (questionId) =>
        set((state) => ({
          favorites: state.favorites.includes(questionId)
            ? state.favorites.filter((id) => id !== questionId)
            : [...state.favorites, questionId],
        })),
      markCompleted: (questionId) =>
        set((state) => ({
          completedQuestions: state.completedQuestions.includes(questionId)
            ? state.completedQuestions
            : [...state.completedQuestions, questionId],
        })),
      reset: () => set({ questions: [], currentIndex: 0, queue: [], answers: {} }),
    }),
    { name: 'ace-practice' }
  )
);
