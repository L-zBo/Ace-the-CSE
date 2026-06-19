import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { MistakeRecord } from '@/types/user';
import type { Subject, XingceCategory, ShenlunCategory } from '@/types/question';
import { getTodayString } from '@/lib/utils';

interface MistakeState {
  mistakes: MistakeRecord[];

  addMistake: (params: {
    questionId: string;
    subject: Subject;
    category: XingceCategory | ShenlunCategory;
  }) => void;
  recordCorrect: (questionId: string) => void;
  markMastered: (questionId: string) => void;
  removeMistake: (questionId: string) => void;
  getActiveMistakes: () => MistakeRecord[];
  getMistakesByCategory: (category: string) => MistakeRecord[];
}

export const useMistakeStore = create<MistakeState>()(
  persist(
    (set, get) => ({
      mistakes: [],

      addMistake: ({ questionId, subject, category }) => {
        const state = get();
        const existing = state.mistakes.find(
          (m) => m.questionId === questionId
        );

        if (existing) {
          set({
            mistakes: state.mistakes.map((m) =>
              m.questionId === questionId
                ? {
                    ...m,
                    wrongCount: m.wrongCount + 1,
                    consecutiveCorrect: 0,
                    lastWrongDate: getTodayString(),
                    isMastered: false,
                  }
                : m
            ),
          });
        } else {
          set({
            mistakes: [
              ...state.mistakes,
              {
                questionId,
                subject,
                category,
                wrongCount: 1,
                consecutiveCorrect: 0,
                lastWrongDate: getTodayString(),
                isMastered: false,
              },
            ],
          });
        }
      },

      recordCorrect: (questionId) => {
        set((state) => ({
          mistakes: state.mistakes.map((m) =>
            m.questionId === questionId
              ? {
                  ...m,
                  consecutiveCorrect: m.consecutiveCorrect + 1,
                  isMastered: m.consecutiveCorrect + 1 >= 2,
                }
              : m
          ),
        }));
      },

      markMastered: (questionId) => {
        set((state) => ({
          mistakes: state.mistakes.map((m) =>
            m.questionId === questionId ? { ...m, isMastered: true } : m
          ),
        }));
      },

      removeMistake: (questionId) => {
        set((state) => ({
          mistakes: state.mistakes.filter((m) => m.questionId !== questionId),
        }));
      },

      getActiveMistakes: () => {
        return get().mistakes.filter((m) => !m.isMastered);
      },

      getMistakesByCategory: (category) => {
        return get().mistakes.filter(
          (m) => m.category === category && !m.isMastered
        );
      },
    }),
    { name: 'ace-mistakes' }
  )
);
