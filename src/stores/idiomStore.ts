import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { getTodayString } from '@/lib/utils';

export type IdiomStatus = 'unknown' | 'reviewing' | 'mastered';

export interface IdiomRecord {
  word: string;
  status: IdiomStatus;
  reviewCount: number;
  lastReviewDate: string;
  nextReviewDate: string;
}

interface IdiomState {
  records: Record<string, IdiomRecord>;
  mark: (word: string, status: IdiomStatus) => void;
  resetWord: (word: string) => void;
}

const REVIEW_INTERVAL_DAYS: Record<IdiomStatus, number> = {
  unknown: 1,
  reviewing: 3,
  mastered: 14,
};

function addDays(dateStr: string, days: number): string {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + days);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

export const useIdiomStore = create<IdiomState>()(
  persist(
    (set) => ({
      records: {},

      mark: (word, status) =>
        set((state) => {
          const today = getTodayString();
          const prev = state.records[word];
          return {
            records: {
              ...state.records,
              [word]: {
                word,
                status,
                reviewCount: (prev?.reviewCount ?? 0) + 1,
                lastReviewDate: today,
                nextReviewDate: addDays(today, REVIEW_INTERVAL_DAYS[status]),
              },
            },
          };
        }),

      resetWord: (word) =>
        set((state) => {
          const records = { ...state.records };
          delete records[word];
          return { records };
        }),
    }),
    { name: 'ace-idioms' }
  )
);
