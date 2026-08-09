'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  ClipboardCheck,
  Clock,
  FileText,
  Play,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';
import { getQuestionIndex, loadFilteredQuestions } from '@/lib/questionLoader';
import { shuffle } from '@/lib/utils';
import type { ExamLevel, ExamSource, Question } from '@/types/question';

interface ExamData {
  id: string;
  title: string;
  duration: number;
  questions: Question[];
}

interface ExamPreset {
  id: string;
  title: string;
  year: number;
  level: ExamLevel;
  questionCount: number;
  expectedCount: number;
  duration: number;
  description: string;
  ready: boolean;
}

const NATIONAL_LEVEL_NAMES: Record<string, string> = {
  fushengjia: '副省级',
  dishi: '地市级',
  xingzhengzhifa: '行政执法',
};

const NATIONAL_LEVEL_ORDER: ExamLevel[] = [
  'fushengjia',
  'dishi',
  'xingzhengzhifa',
];

function getExpectedNationalCount(level: ExamLevel) {
  if (level === 'fushengjia') return 135;
  if (level === 'dishi') return 130;
  if (level === 'xingzhengzhifa') return 130;
  return 0;
}

function getExamDescription(level: ExamLevel) {
  if (level === 'fushengjia') {
    return '135题：常识20+言语40+数量15+判断40+资料20';
  }
  if (level === 'dishi') {
    return '130题：常识20+言语40+数量10+判断40+资料20';
  }
  if (level === 'xingzhengzhifa') {
    return '130题：常识20+言语40+数量15+判断40+资料15';
  }
  return '题量待确认';
}

export default function ExamPage() {
  const router = useRouter();
  const [starting, setStarting] = useState<string | null>(null);

  const examPresets = useMemo<ExamPreset[]>(() => {
    const allQuestions = getQuestionIndex().filter(
      (q) => q.source === 'national' && q.subject === 'xingce' && q.level
    );

    const grouped = new Map<string, ExamPreset>();

    for (const question of allQuestions) {
      const level = question.level as ExamLevel;
      if (!(level in NATIONAL_LEVEL_NAMES)) {
        continue;
      }

      const key = `${question.year}-${level}`;
      const existing = grouped.get(key);
      if (existing) {
        existing.questionCount += 1;
        continue;
      }

      const expectedCount = getExpectedNationalCount(level);
      grouped.set(key, {
        id: `national-xingce-${question.year}-${level}`,
        title: `${question.year}年国考行测（${NATIONAL_LEVEL_NAMES[level]}）`,
        year: question.year,
        level,
        questionCount: 1,
        expectedCount,
        duration: 120,
        description: getExamDescription(level),
        ready: false,
      });
    }

    return Array.from(grouped.values())
      .map((preset) => ({
        ...preset,
        ready: preset.questionCount === preset.expectedCount,
      }))
      .sort((a, b) => {
        if (b.year !== a.year) return b.year - a.year;
        return (
          NATIONAL_LEVEL_ORDER.indexOf(a.level) -
          NATIONAL_LEVEL_ORDER.indexOf(b.level)
        );
      });
  }, []);

  const presetsByYear = useMemo(() => {
    return examPresets.reduce<Record<number, ExamPreset[]>>((acc, preset) => {
      if (!acc[preset.year]) {
        acc[preset.year] = [];
      }
      acc[preset.year].push(preset);
      return acc;
    }, {});
  }, [examPresets]);

  const years = useMemo(
    () => Object.keys(presetsByYear).map(Number).sort((a, b) => b - a),
    [presetsByYear]
  );

  const startExam = async (preset: ExamPreset) => {
    if (!preset.ready) return;

    setStarting(preset.id);
    // 组卷需要题目正文（要塞进 sessionStorage 给答题页用），
    // 这里按筛选结果只拉相关试卷，不会碰整个题库。
    const questions = await loadFilteredQuestions({
      answerableOnly: true,
      subject: 'xingce',
      source: 'national' as ExamSource,
      year: preset.year,
      level: preset.level,
    });
    if (questions.length === 0) {
      setStarting(null);
      return;
    }
    const shuffled = shuffle(questions);

    const payload: ExamData = {
      id: preset.id,
      title: preset.title,
      duration: preset.duration,
      questions: shuffled,
    };

    sessionStorage.setItem('current-exam', JSON.stringify(payload));
    router.push(`/exam/${preset.id}`);
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
      <div className="mb-6 flex items-center gap-3">
        <ClipboardCheck size={24} className="text-success" />
        <div>
          <h1 className="text-2xl font-bold">模拟考试</h1>
          <p className="text-sm text-muted">
            现已按年份和级别拆分国考行测试卷，避免再把不同卷子混成一个2024。
          </p>
        </div>
      </div>

      <div className="mb-8 rounded-2xl border border-border bg-card/70 p-4 text-sm text-muted">
        <div className="mb-2 flex items-center gap-2 font-medium text-foreground">
          <FileText size={16} className="text-primary" />
          当前策略
        </div>
        <p>
          只有题量达到标准的试卷才允许直接开考；题量不完整的年份会明确标成“待补齐”，防止你一脚踩进半成品卷子里。
        </p>
      </div>

      <div className="space-y-8">
        {years.map((year) => (
          <section key={year}>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">{year}年国考行测</h2>
              <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                {presetsByYear[year].length}套
              </span>
            </div>

            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              {presetsByYear[year].map((preset) => (
                <motion.div
                  key={preset.id}
                  whileHover={{ scale: preset.ready ? 1.02 : 1 }}
                  className="rounded-2xl border border-border bg-card p-6 transition-shadow hover:shadow-lg"
                >
                  <div className="mb-4 flex items-start justify-between gap-3">
                    <div>
                      <h3 className="mb-1 text-lg font-semibold">
                        {preset.title}
                      </h3>
                      <p className="text-sm text-muted">{preset.description}</p>
                    </div>
                    {preset.ready ? (
                      <span className="rounded-full bg-success/15 px-2.5 py-1 text-xs font-semibold text-success border border-success/40">
                        已齐
                      </span>
                    ) : (
                      <span className="rounded-full bg-warning/15 px-2.5 py-1 text-xs font-semibold text-warning border border-warning/40">
                        待补齐
                      </span>
                    )}
                  </div>

                  <div className="mb-4 flex flex-wrap items-center gap-3 text-sm text-muted">
                    <span className="flex items-center gap-1">
                      <Clock size={14} />
                      {preset.duration}分钟
                    </span>
                    <span>
                      {preset.questionCount}/{preset.expectedCount}题
                    </span>
                  </div>

                  <div
                    className={`mb-5 rounded-xl border px-4 py-3 text-sm ${
                      preset.ready
                        ? 'border-success/40 bg-success/10 text-success'
                        : 'border-warning/40 bg-warning/10 text-warning'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {preset.ready ? (
                        <CheckCircle2 size={16} />
                      ) : (
                        <AlertTriangle size={16} />
                      )}
                      <span className="font-medium">
                        {preset.ready
                          ? '题量完整，可直接开考'
                          : `当前仍缺${preset.expectedCount - preset.questionCount}题，暂不开放开考`}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => startExam(preset)}
                    disabled={starting === preset.id || !preset.ready}
                    className="flex w-full items-center justify-center gap-2 rounded-xl bg-success py-2.5 text-sm font-medium text-white transition-colors hover:brightness-110 disabled:cursor-not-allowed disabled:bg-success/40"
                  >
                    <Play size={16} />
                    {starting === preset.id ? '正在准备…' : '开始考试'}
                  </button>
                </motion.div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
