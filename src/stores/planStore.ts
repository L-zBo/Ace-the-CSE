import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { StudyPlan } from '@/types/user';
import { generateId, getTodayString } from '@/lib/utils';

interface PlanState {
  plans: StudyPlan[];
  activePlanId: string | null;

  createPlan: (plan: Omit<StudyPlan, 'id' | 'completedDays' | 'isActive'>) => void;
  setActivePlan: (planId: string) => void;
  checkIn: (planId: string) => void;
  deletePlan: (planId: string) => void;
  getActivePlan: () => StudyPlan | null;
}

export const usePlanStore = create<PlanState>()(
  persist(
    (set, get) => ({
      plans: [],
      activePlanId: null,

      createPlan: (planData) => {
        const plan: StudyPlan = {
          ...planData,
          id: generateId(),
          completedDays: [],
          isActive: true,
        };
        set((state) => ({
          plans: [...state.plans.map((p) => ({ ...p, isActive: false })), plan],
          activePlanId: plan.id,
        }));
      },

      setActivePlan: (planId) => {
        set((state) => ({
          plans: state.plans.map((p) => ({
            ...p,
            isActive: p.id === planId,
          })),
          activePlanId: planId,
        }));
      },

      checkIn: (planId) => {
        const today = getTodayString();
        set((state) => ({
          plans: state.plans.map((p) =>
            p.id === planId && !p.completedDays.includes(today)
              ? { ...p, completedDays: [...p.completedDays, today] }
              : p
          ),
        }));
      },

      deletePlan: (planId) => {
        set((state) => ({
          plans: state.plans.filter((p) => p.id !== planId),
          activePlanId:
            state.activePlanId === planId ? null : state.activePlanId,
        }));
      },

      getActivePlan: () => {
        const state = get();
        return state.plans.find((p) => p.id === state.activePlanId) || null;
      },
    }),
    { name: 'ace-plans' }
  )
);
