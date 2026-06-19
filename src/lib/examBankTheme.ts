/** 三大考试题库主题 token — 给 examBanks 的视觉锚
 *
 * 抽到独立文件 + discriminated union，避免 page.tsx 里 bgClass/shadowClass
 * 字符串与 globals.css 中 utility class 失同步（simplify skill 警告：
 * CSS 改名时 examBanks 静默渲染无样式）。
 *
 * 添加新主题：扩 BankTheme + EXAM_BANK_THEMES，新 utility class 在
 * globals.css 同名补全。
 */

export type BankTheme = 'mo-blue' | 'emerald-deep' | 'cinnabar';

interface ExamBankThemeTokens {
  /** 主背景渐变 utility（必须在 globals.css 定义同名 class） */
  bgClass: `gradient-${BankTheme}`;
  /** 阴影色 utility */
  shadowClass: `shadow-${BankTheme}`;
}

export const EXAM_BANK_THEMES: Record<BankTheme, ExamBankThemeTokens> = {
  'mo-blue': {
    bgClass: 'gradient-mo-blue',
    shadowClass: 'shadow-mo-blue',
  },
  'emerald-deep': {
    bgClass: 'gradient-emerald-deep',
    shadowClass: 'shadow-emerald-deep',
  },
  cinnabar: {
    bgClass: 'gradient-cinnabar',
    shadowClass: 'shadow-cinnabar',
  },
};
