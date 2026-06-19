// 考试来源
export type ExamSource = 'national' | 'provincial' | 'institution';

export type ExamLevel =
  | 'fushengjia'
  | 'dishi'
  | 'xingzhengzhifa'
  | 'a'
  | 'b'
  | 'c'
  | 'd'
  | 'e'
  | 'unknown';

// 行测五大模块
export type XingceCategory = 'changshi' | 'yanyu' | 'shuliang' | 'panduan' | 'ziliao';

// 申论五大题型
export type ShenlunCategory = 'guina' | 'duice' | 'fenxi' | 'guanche' | 'xiezuo';

// 科目
export type Subject = 'xingce' | 'shenlun';

// 题型
export type QuestionType = 'single_choice' | 'multiple_choice' | 'true_false' | 'essay';

// 选项
export interface Option {
  label: string; // A, B, C, D
  content: string;
}

// 题目
export interface Question {
  id: string;
  subject: Subject;
  category: XingceCategory | ShenlunCategory;
  type: QuestionType;
  source: ExamSource;
  level?: ExamLevel;
  region?: string;
  year: number;
  content: string;
  options?: Option[];
  answer: string | string[];
  explanation: string;
  difficulty: 1 | 2 | 3 | 4 | 5;
  knowledgePoints: string[];
  materialId?: string;
  material?: string;
  sourceLabel: string;
  questionImage?: string; // 图形推理题的题目图片路径
}

// 题库索引条目
export interface QuestionBankEntry {
  path: string;
  subject: Subject;
  category: XingceCategory | ShenlunCategory;
  source: ExamSource;
  region?: string;
  year: number;
  count: number;
}

// 题库索引
export interface QuestionBankIndex {
  totalCount: number;
  lastUpdated: string;
  entries: QuestionBankEntry[];
}

// 分类显示名称映射
export const XINGCE_CATEGORY_NAMES: Record<XingceCategory, string> = {
  changshi: '常识判断',
  yanyu: '言语理解与表达',
  shuliang: '数量关系',
  panduan: '判断推理',
  ziliao: '资料分析',
};

export const SHENLUN_CATEGORY_NAMES: Record<ShenlunCategory, string> = {
  guina: '归纳概括',
  duice: '提出对策',
  fenxi: '综合分析',
  guanche: '贯彻执行',
  xiezuo: '申论写作',
};

export const EXAM_SOURCE_NAMES: Record<ExamSource, string> = {
  national: '国考',
  provincial: '省考',
  institution: '事业编',
};

export const SUBJECT_NAMES: Record<Subject, string> = {
  xingce: '行测',
  shenlun: '申论',
};

export const DIFFICULTY_NAMES: Record<number, string> = {
  1: '简单',
  2: '较易',
  3: '中等',
  4: '较难',
  5: '困难',
};
