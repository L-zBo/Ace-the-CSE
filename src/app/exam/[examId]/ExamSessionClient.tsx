'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  ChevronLeft,
  ChevronRight,
  Flag,
  Send,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  SkipForward,
} from 'lucide-react';
import { cn, formatTime } from '@/lib/utils';
import { CountdownTimer } from '@/components/ui';
import { AnnotatableImage } from '@/components/questions/AnnotatableImage';
import {
  isPlaceholderQuestion,
  isPlaceholderOption,
  isPlaceholderText,
  isDerivedOption,
  stripDerivedMarker,
  isRecoveredText,
  getPlaceholderReason,
} from '@/lib/placeholder';
import type { Question } from '@/types/question';
import { XINGCE_CATEGORY_NAMES } from '@/types/question';

interface ExamData {
  id: string;
  title: string;
  duration: number;
  questions: Question[];
}

export default function ExamSessionClient() {
  const router = useRouter();
  const [examData, setExamData] = useState<ExamData | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [marked, setMarked] = useState<Set<string>>(new Set());
  const [remainingTime, setRemainingTime] = useState(0);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [showSheet, setShowSheet] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval>>(undefined);

  useEffect(() => {
    const data = sessionStorage.getItem('current-exam');
    if (data) {
      const parsed = JSON.parse(data) as ExamData;
      setExamData(parsed);
      setRemainingTime(parsed.duration * 60);
    }
  }, []);

  useEffect(() => {
    if (remainingTime <= 0 || isSubmitted) return;
    timerRef.current = setInterval(() => {
      setRemainingTime((t) => {
        if (t <= 1) {
          clearInterval(timerRef.current);
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, [remainingTime, isSubmitted]);

  // 自动交卷
  const handleSubmit = useCallback(() => {
    setIsSubmitted(true);
    clearInterval(timerRef.current);
  }, []);

  useEffect(() => {
    if (remainingTime === 0 && examData && !isSubmitted) {
      handleSubmit();
    }
  }, [remainingTime, examData, isSubmitted, handleSubmit]);

  // 键盘快捷键：1-4/A-D 选项 · ←/→/Enter 切题 · F 标记
  useEffect(() => {
    if (!examData || isSubmitted) return;
    const totalQ = examData.questions.length;
    function handleKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null;
      if (
        target?.tagName === 'INPUT' ||
        target?.tagName === 'TEXTAREA' ||
        target?.isContentEditable
      )
        return;
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (!examData) return;
      const currentQ = examData.questions[currentIndex];
      if (!currentQ) return;

      if (currentQ.type !== 'essay' && currentQ.options) {
        let label: string | null = null;
        if (/^[1-4]$/.test(e.key)) {
          label = currentQ.options[parseInt(e.key, 10) - 1]?.label ?? null;
        } else if (/^[a-dA-D]$/.test(e.key)) {
          label = e.key.toUpperCase();
        }
        if (label) {
          const opt = currentQ.options.find((o) => o.label === label);
          const isOptBad = opt && isPlaceholderOption(opt) && !currentQ.questionImage;
          if (opt && !isOptBad) {
            const picked = label;
            setAnswers((prev) => ({ ...prev, [currentQ.id]: picked }));
            e.preventDefault();
            return;
          }
        }
      }

      if (e.key === 'ArrowLeft' && currentIndex > 0) {
        setCurrentIndex((i) => Math.max(0, i - 1));
        e.preventDefault();
        return;
      }
      if ((e.key === 'ArrowRight' || e.key === 'Enter') && currentIndex < totalQ - 1) {
        setCurrentIndex((i) => Math.min(totalQ - 1, i + 1));
        e.preventDefault();
        return;
      }
      if (e.key === 'f' || e.key === 'F') {
        setMarked((prev) => {
          const next = new Set(prev);
          if (next.has(currentQ.id)) next.delete(currentQ.id);
          else next.add(currentQ.id);
          return next;
        });
        e.preventDefault();
      }
    }
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [examData, currentIndex, isSubmitted]);

  if (!examData) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-muted">加载考试数据中...</p>
      </div>
    );
  }

  const currentQ = examData.questions[currentIndex];
  const totalQ = examData.questions.length;
  const previousQ = currentIndex > 0 ? examData.questions[currentIndex - 1] : null;
  const imageRepeatedFromPrevious =
    !!currentQ?.questionImage &&
    !!previousQ?.questionImage &&
    previousQ.questionImage === currentQ.questionImage;

  // 计算成绩（占位题不计入总数 - 不可作答不应拉低分数）
  const getScore = () => {
    let correct = 0;
    const validQs = examData.questions.filter(
      (q) => !isPlaceholderQuestion(q) || !!q.questionImage
    );
    validQs.forEach((q) => {
      const userAns = answers[q.id];
      if (userAns && (Array.isArray(q.answer) ? q.answer.includes(userAns) : q.answer === userAns)) {
        correct++;
      }
    });
    const total = validQs.length || totalQ;

    // D-18a P3d 分模块得分（结构化报告卡）
    const categoryStats: Record<string, { total: number; correct: number }> = {};
    validQs.forEach((q) => {
      const cat = q.category || 'other';
      if (!categoryStats[cat]) categoryStats[cat] = { total: 0, correct: 0 };
      categoryStats[cat].total++;
      const userAns = answers[q.id];
      if (userAns && (Array.isArray(q.answer) ? q.answer.includes(userAns) : q.answer === userAns)) {
        categoryStats[cat].correct++;
      }
    });
    const categoryRows = Object.entries(categoryStats)
      .map(([cat, s]) => ({
        cat,
        total: s.total,
        correct: s.correct,
        accuracy: Math.round((s.correct / s.total) * 100),
      }))
      .sort((a, b) => b.total - a.total);

    return {
      correct,
      total,
      score: total ? Math.round((correct / total) * 100) : 0,
      categoryRows,
    };
  };

  if (isSubmitted) {
    const { correct, total, score, categoryRows } = getScore();
    return (
      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="relative rounded-2xl border border-border bg-card p-8 text-center"
        >
          {/* 完成卷封顶印章 — D-18a P2b-2 装饰 SVG 接入（卷面"已批改"感）*/}
          <Image
            aria-hidden="true"
            src="/img/decorative/seal-bo.svg"
            alt=""
            width={96}
            height={96}
            unoptimized
            className="pointer-events-none absolute right-4 top-4 h-20 w-20 select-none opacity-80 sm:h-24 sm:w-24 motion-safe:transition-transform motion-safe:duration-500 hover:rotate-[5deg] motion-safe:hover:scale-105"
          />
          <h2 className="mb-2 text-2xl font-bold">{examData.title}</h2>
          <p className="mb-6 text-muted">考试结束</p>

          <div className="mb-8 flex items-center justify-center gap-8">
            <div>
              <div className="font-display-en text-4xl font-bold text-primary tabular-nums">{score}</div>
              <div className="text-sm text-muted">得分</div>
            </div>
            <div>
              <div className="font-display-en text-4xl font-bold text-success tabular-nums">{correct}</div>
              <div className="text-sm text-muted">正确</div>
            </div>
            <div>
              <div className="font-display-en text-4xl font-bold text-danger tabular-nums">{total - correct}</div>
              <div className="text-sm text-muted">错误</div>
            </div>
            <div>
              <div className="font-display-en text-4xl font-bold text-foreground tabular-nums">{Object.keys(answers).length}</div>
              <div className="text-sm text-muted">已答</div>
            </div>
          </div>

          {/* D-18a P3d 报告卡：分模块得分（结构化）+ 用时分布占位 */}
          {categoryRows.length > 1 && (
            <div className="mb-6 rounded-xl border border-border bg-card-hover p-4 text-left">
              <h3 className="mb-3 font-display-zh text-sm font-semibold text-foreground">
                分模块得分
              </h3>
              <div className="space-y-2">
                {categoryRows.map((row) => {
                  const catName =
                    XINGCE_CATEGORY_NAMES[row.cat as keyof typeof XINGCE_CATEGORY_NAMES] || row.cat;
                  return (
                    <div key={row.cat} className="flex items-center gap-3">
                      <span className="w-16 shrink-0 text-xs text-foreground-muted">
                        {catName}
                      </span>
                      <div className="flex-1">
                        <div className="h-1.5 overflow-hidden rounded-full bg-border">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${row.accuracy}%` }}
                            transition={{ duration: 0.6, ease: 'easeOut' }}
                            className={cn(
                              'h-full rounded-full',
                              row.accuracy >= 70
                                ? 'bg-gradient-to-r from-success/80 to-success'
                                : row.accuracy >= 40
                                  ? 'bg-gradient-to-r from-brand-500 to-seal-500'
                                  : 'bg-gradient-to-r from-seal-500 to-seal-700',
                            )}
                          />
                        </div>
                      </div>
                      <span className="w-16 shrink-0 text-right text-xs tabular-nums text-foreground-secondary">
                        {row.correct} / {row.total} ({row.accuracy}%)
                      </span>
                    </div>
                  );
                })}
              </div>
              {examData.duration && (
                <div className="mt-3 border-t border-border pt-3 text-xs text-foreground-muted">
                  总时长 {examData.duration} 分钟 · 实际用时{' '}
                  <span className="tabular-nums">
                    {formatTime(Math.max(0, examData.duration * 60 - remainingTime))}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* 逐题回顾 */}
          <div className="mb-6 space-y-4 text-left">
            {examData.questions.map((q, i) => {
              const userAns = answers[q.id];
              const isCorrect = userAns && (Array.isArray(q.answer) ? q.answer.includes(userAns) : q.answer === userAns);
              return (
                <div key={q.id} className="rounded-xl border border-border p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <span className="text-sm font-medium text-muted">第{i + 1}题</span>
                    {userAns ? (
                      isCorrect ? (
                        <CheckCircle2 size={16} className="text-success" />
                      ) : (
                        <XCircle size={16} className="text-danger" />
                      )
                    ) : (
                      <span className="text-xs text-muted">未作答</span>
                    )}
                  </div>
                  <p className="mb-2 text-sm line-clamp-2">{q.content}</p>
                  <div className="text-xs text-muted">
                    你的答案：{userAns || '未作答'} | 正确答案：{q.answer}
                  </div>
                </div>
              );
            })}
          </div>

          <button
            onClick={() => router.push('/exam')}
            className="rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-white hover:bg-primary-dark"
          >
            返回考试列表
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-4 sm:px-6">
      {/* Timer bar */}
      <div className="sticky top-16 z-40 mb-4 flex items-center justify-between rounded-xl border border-border bg-card px-4 py-3">
        <span className="text-sm font-medium">{examData.title}</span>
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted">
            {currentIndex + 1} / {totalQ}
          </span>
          <CountdownTimer remainingSeconds={remainingTime} />
          <button
            onClick={() => setShowSheet(!showSheet)}
            className="rounded-lg border border-border px-3 py-1.5 text-sm font-medium transition-[transform,box-shadow,background-color,border-color] hover:border-primary/40 hover:bg-primary/5 active:scale-[0.97]"
          >
            答题卡
          </button>
          <button
            onClick={() => {
              if (confirm('确定要交卷吗？')) handleSubmit();
            }}
            className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-primary to-primary-dark px-4 py-1.5 text-sm font-semibold text-white shadow-md shadow-primary/30 transition-[transform,box-shadow,background-color,border-color] hover:shadow-lg hover:shadow-primary/40 active:scale-[0.97]"
          >
            <Send size={14} />
            交卷
          </button>
        </div>
      </div>

      <div className="flex gap-4">
        {/* Main content */}
        <div className="flex-1">
          {currentQ && (
            <>
              {currentQ.material && (
                <div className="mb-4 rounded-xl border border-border bg-card p-5">
                  <h3 className="mb-2 text-sm font-semibold text-muted">给定材料</h3>
                  <div className="markdown-content prose prose-sm max-w-none dark:prose-invert">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {currentQ.material}
                    </ReactMarkdown>
                  </div>
                </div>
              )}

              {isPlaceholderQuestion(currentQ) && !currentQ.questionImage && (
                <div className="mb-4 flex items-start gap-3 rounded-xl border border-warning/40 bg-warning/10 p-4">
                  <AlertTriangle size={18} className="mt-0.5 shrink-0 text-warning" />
                  <div className="flex-1 text-sm">
                    <p className="font-medium text-warning">本题源数据缺失，不计入分数</p>
                    <p className="mt-0.5 text-xs text-warning/80">
                      原因：{getPlaceholderReason(currentQ)}。建议跳过。
                    </p>
                  </div>
                  <button
                    onClick={() => setCurrentIndex((i) => Math.min(totalQ - 1, i + 1))}
                    disabled={currentIndex === totalQ - 1}
                    className="flex shrink-0 items-center gap-1 rounded-lg bg-warning px-3 py-1.5 text-xs font-medium text-white transition-colors hover:brightness-110 disabled:opacity-50"
                  >
                    <SkipForward size={14} /> 跳过
                  </button>
                </div>
              )}

              {isPlaceholderQuestion(currentQ) && currentQ.questionImage && (
                <div className="mb-4 flex items-start gap-3 rounded-xl border border-info/40 bg-info/10 p-4">
                  <AlertTriangle size={18} className="mt-0.5 shrink-0 text-info" />
                  <div className="flex-1 text-sm">
                    <p className="font-medium text-info">图像作答模式</p>
                    <p className="mt-0.5 text-xs text-info/80">
                      本题文字数据未抽全，请凭原题截图直接选 A / B / C / D。
                    </p>
                  </div>
                </div>
              )}

              <div className="mb-4 text-base leading-relaxed">
                {isPlaceholderText(currentQ.content) ? (
                  <p className="rounded-lg border border-dashed border-border bg-card-hover px-4 py-6 text-center text-sm text-muted">
                    （题干源数据缺失，无法显示）
                  </p>
                ) : isRecoveredText(currentQ.content) ? (
                  <div className="space-y-2">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {stripDerivedMarker(currentQ.content)}
                    </ReactMarkdown>
                    <p className="text-xs text-warning">
                      ⚠ 题干由源数据救援补全，可能与原题措辞略有出入
                    </p>
                  </div>
                ) : (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {currentQ.content}
                  </ReactMarkdown>
                )}
              </div>

              {currentQ.questionImage && !imageRepeatedFromPrevious && (
                <AnnotatableImage
                  src={currentQ.questionImage}
                  alt="题目图片"
                  sourceKey={currentQ.id}
                  frameClassName="mb-4"
                />
              )}

              {currentQ.questionImage && imageRepeatedFromPrevious && (
                <div className="mb-4 rounded-xl border border-border bg-card/70 px-4 py-3 text-sm text-muted">
                  本题沿用上一小题题图；题图批注按图片保存，可在上一题图或图注笔记中继续查看。
                </div>
              )}

              {currentQ.options && (
                <div className="mb-6 space-y-3">
                  {currentQ.options.map((opt) => {
                    const rawOptBad = isPlaceholderOption(opt);
                    // 图像作答模式：占位题但有 questionImage → 允许凭图选 ABCD
                    const isOptBad = rawOptBad && !currentQ.questionImage;
                    const isDerivedOpt = isDerivedOption(opt);
                    return (
                      <button
                        key={opt.label}
                        onClick={() =>
                          !isOptBad &&
                          setAnswers((prev) => ({ ...prev, [currentQ.id]: opt.label }))
                        }
                        disabled={isOptBad}
                        className={cn(
                          'flex w-full items-start gap-3 rounded-xl border p-4 text-left transition-[transform,box-shadow,background-color,border-color]',
                          isOptBad
                            ? 'cursor-not-allowed border-dashed border-border bg-card-hover opacity-60'
                            : answers[currentQ.id] === opt.label
                              ? 'border-primary bg-primary/5'
                              : 'border-border bg-card hover:border-primary/30'
                        )}
                      >
                        <span
                          className={cn(
                            'flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-sm font-medium',
                            isOptBad
                              ? 'border-border text-muted'
                              : answers[currentQ.id] === opt.label
                                ? 'border-primary bg-primary text-white'
                                : 'border-border'
                          )}
                        >
                          {opt.label}
                        </span>
                        {isOptBad ? (
                          <span className="pt-0.5 text-sm italic text-muted">
                            （选项 {opt.label} 源数据缺失）
                          </span>
                        ) : currentQ.questionImage && rawOptBad ? (
                          <span className="pt-0.5 text-sm text-muted">凭图选 {opt.label}</span>
                        ) : isDerivedOpt ? (
                          <span className="flex flex-1 items-start gap-2 pt-0.5">
                            <span className="flex-1">{stripDerivedMarker(opt.content)}</span>
                            <span
                              className="shrink-0 rounded-full border border-warning/40 bg-warning/15 px-2 py-0.5 text-[10px] font-medium text-warning"
                              title="此选项由解析文本推导，可能与原选项措辞略有出入"
                            >
                              解析推导
                            </span>
                          </span>
                        ) : (
                          <span className="pt-0.5">{opt.content}</span>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}

              {currentQ.type === 'essay' && (
                <textarea
                  className="mb-6 w-full rounded-xl border border-border bg-card p-4 text-sm focus:border-primary focus:outline-none"
                  rows={10}
                  placeholder="在此输入你的答案…例如：「首先，应当从制度层面切入…」"
                  value={answers[currentQ.id] || ''}
                  onChange={(e) =>
                    setAnswers((prev) => ({ ...prev, [currentQ.id]: e.target.value }))
                  }
                />
              )}

              {/* Mark & Navigate */}
              <div className="flex items-center justify-between gap-2">
                <button
                  onClick={() => {
                    setMarked((prev) => {
                      const next = new Set(prev);
                      if (next.has(currentQ.id)) next.delete(currentQ.id);
                      else next.add(currentQ.id);
                      return next;
                    });
                  }}
                  className={cn(
                    'flex items-center gap-1.5 rounded-xl border-2 px-4 py-2.5 text-sm font-medium transition-[transform,box-shadow,background-color,border-color] active:scale-[0.97]',
                    marked.has(currentQ.id)
                      ? 'border-warning bg-warning/15 text-warning shadow-sm shadow-warning/20'
                      : 'border-border hover:border-warning/50 hover:bg-warning/10'
                  )}
                >
                  <Flag size={14} />
                  {marked.has(currentQ.id) ? '已标记' : '标记'}
                </button>
                <div className="flex gap-2">
                  <button
                    onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))}
                    disabled={currentIndex === 0}
                    className="group flex items-center gap-1 rounded-xl border-2 border-border bg-card px-4 py-2.5 text-sm font-semibold transition-[transform,box-shadow,background-color,border-color] hover:border-primary/40 hover:bg-primary/5 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-30"
                  >
                    <ChevronLeft
                      size={16}
                      className="transition-transform group-hover:-translate-x-0.5"
                    />
                    上一题
                  </button>
                  <button
                    onClick={() => setCurrentIndex((i) => Math.min(totalQ - 1, i + 1))}
                    disabled={currentIndex === totalQ - 1}
                    className="group flex items-center gap-1 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-primary/30 transition-[transform,box-shadow,background-color,border-color] hover:translate-x-0.5 hover:bg-primary-dark hover:shadow-lg hover:shadow-primary/40 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-30"
                  >
                    下一题
                    <ChevronRight
                      size={16}
                      className="transition-transform group-hover:translate-x-0.5"
                    />
                  </button>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Answer sheet sidebar */}
        {showSheet && (
          <div className="hidden w-52 shrink-0 lg:block">
            <div className="sticky top-32 rounded-xl border border-border bg-card p-4">
              <h3 className="mb-3 text-sm font-semibold">答题卡</h3>
              <div className="grid grid-cols-5 gap-2">
                {examData.questions.map((q, i) => (
                  <button
                    key={q.id}
                    onClick={() => setCurrentIndex(i)}
                    className={cn(
                      'flex h-8 w-8 items-center justify-center rounded text-xs font-medium transition-colors',
                      i === currentIndex
                        ? 'bg-primary text-white'
                        : answers[q.id]
                          ? 'bg-success/20 text-success'
                          : marked.has(q.id)
                            ? 'bg-warning/20 text-warning'
                            : 'bg-card-hover text-muted hover:bg-border'
                    )}
                  >
                    {i + 1}
                  </button>
                ))}
              </div>
              <div className="mt-3 space-y-1 text-xs text-muted">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded bg-success/20" /> 已答 {Object.keys(answers).length}
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded bg-warning/20" /> 标记 {marked.size}
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded bg-card-hover" /> 未答 {totalQ - Object.keys(answers).length}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
