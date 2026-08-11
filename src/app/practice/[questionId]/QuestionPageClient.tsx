'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { AnimatePresence, motion } from 'framer-motion';
import {
  getMetaById,
  getQuestionIndex,
  loadQuestionById,
  type QuestionMeta,
} from '@/lib/questionLoader';
import { usePracticeStore } from '@/stores/practiceStore';
import { useStatsStore } from '@/stores/statsStore';
import { useMistakeStore } from '@/stores/mistakeStore';
import {
  isPlaceholderQuestion,
  isPlaceholderOption,
  isPlaceholderText,
  getPlaceholderReason,
} from '@/lib/placeholder';
import type { Question } from '@/types/question';
import {
  XINGCE_CATEGORY_NAMES,
  SHENLUN_CATEGORY_NAMES,
  DIFFICULTY_NAMES,
} from '@/types/question';
import ShenlunAnalysis from './ShenlunAnalysis';
import { FileQuestion } from 'lucide-react';
import { Button, EmptyState } from '@/components/ui';
import {
  QuestionHeader,
  QuestionProgressBar,
  QuestionStatusBanner,
  QuestionStem,
  OptionList,
  EssayAnswerArea,
  SubmitBar,
  ExplanationPanel,
  RelatedAppearances,
  KeyboardHintBar,
  QuestionNavBar,
} from './components';

export default function QuestionPageClient() {
  const params = useParams();
  const router = useRouter();
  const questionId = params.questionId as string;

  const [draftAnswers, setDraftAnswers] = useState<Record<string, string | null>>({});
  const [clearedQuestions, setClearedQuestions] = useState<Record<string, boolean>>({});
  const [startTime] = useState(() => Date.now());

  const { answers, favorites, queue, submitAnswer, toggleFavorite, markCompleted } =
    usePracticeStore();
  const { recordPractice } = useStatsStore();
  const { addMistake, recordCorrect } = useMistakeStore();
  // 题目正文按需加载：只拉当前题所在的那份试卷。
  // 存 { id, q } 而不是裸 question，切题时靠派生立刻失效，
  // 不用在 effect 里同步 setState(null)（那会触发级联渲染）。
  const [loadedQuestion, setLoadedQuestion] = useState<{
    id: string;
    q: Question | null;
  } | null>(null);

  useEffect(() => {
    let cancelled = false;
    loadQuestionById(questionId).then((q) => {
      if (!cancelled) setLoadedQuestion({ id: questionId, q: q ?? null });
    });
    return () => {
      cancelled = true;
    };
  }, [questionId]);

  const question =
    loadedQuestion && loadedQuestion.id === questionId ? loadedQuestion.q : null;
  const storedAnswerValue = question ? (answers[question.id] ?? null) : null;
  const storedAnswer = Array.isArray(storedAnswerValue)
    ? (storedAnswerValue[0] ?? null)
    : storedAnswerValue;
  const draftAnswer = question ? (draftAnswers[question.id] ?? null) : null;
  const isCleared = question ? !!clearedQuestions[question.id] : false;
  const selectedOption = draftAnswer ?? (!isCleared ? storedAnswer : null);
  const isSubmitted = !!storedAnswer && !isCleared;
  const showAnalysis = isSubmitted;

  // 导航只需要 id 和顺序，用轻量索引就够，不必把题库正文全拉下来。
  // 若存在 queue（入口页设置的专项练习范围），按 queue 导航；否则按全库
  const navList = useMemo<QuestionMeta[]>(
    () =>
      queue.length > 0
        ? (queue
            .map((id) => getMetaById(id))
            .filter(Boolean) as QuestionMeta[])
        : getQuestionIndex(),
    [queue],
  );
  const currentIndex = navList.findIndex((q) => q.id === questionId);

  // 上一题只用来判断题图是否与本题重复（重复则不再重绘），单独懒加载即可。
  const previousId = currentIndex > 0 ? navList[currentIndex - 1].id : null;
  const [loadedPrev, setLoadedPrev] = useState<{
    id: string;
    q: Question | null;
  } | null>(null);

  useEffect(() => {
    if (!previousId) return;
    let cancelled = false;
    loadQuestionById(previousId).then((q) => {
      if (!cancelled) setLoadedPrev({ id: previousId, q: q ?? null });
    });
    return () => {
      cancelled = true;
    };
  }, [previousId]);

  const previousQuestion =
    previousId && loadedPrev?.id === previousId ? loadedPrev.q : null;

  // "题目列表"按钮回跳：按 queue 首题 id 前缀推断来源页，避免从国考/省考/事业编
  // 点进来的用户被跳回全部题库 /practice 造成上下文丢失。
  const backTarget = (() => {
    if (queue.length === 0) return '/practice';
    const src = queue[0].split('-')[0];
    if (src === 'national') return '/practice/national';
    if (src === 'provincial') return '/practice/provincial';
    if (src === 'institution') return '/practice/institution';
    return '/practice';
  })();

  const handleSubmit = useCallback(() => {
    if (!question || !selectedOption) return;

    // 申论题：保存用户文本 + 标已完成，不进错题本 / 不参与正误统计
    if (question.type === 'essay') {
      submitAnswer(question.id, selectedOption);
      markCompleted(question.id);
      setClearedQuestions((prev) => ({ ...prev, [question.id]: false }));
      return;
    }

    const isCorrect = Array.isArray(question.answer)
      ? question.answer.includes(selectedOption)
      : question.answer === selectedOption;

    const timeSpent = Math.round((Date.now() - startTime) / 1000);

    submitAnswer(question.id, selectedOption);
    markCompleted(question.id);
    recordPractice({ category: question.category, isCorrect, timeSpent });
    setClearedQuestions((prev) => ({ ...prev, [question.id]: false }));

    if (isCorrect) {
      recordCorrect(question.id);
    } else {
      addMistake({
        questionId: question.id,
        subject: question.subject,
        category: question.category,
      });
    }
  }, [
    question,
    selectedOption,
    startTime,
    submitAnswer,
    markCompleted,
    recordPractice,
    recordCorrect,
    addMistake,
  ]);

  const handleSelectOption = useCallback((label: string) => {
    if (!question) return;
    setDraftAnswers((prev) => ({ ...prev, [question.id]: label }));
    setClearedQuestions((prev) => ({ ...prev, [question.id]: false }));
  }, [question]);

  const resetQuestion = useCallback(() => {
    if (!question) return;
    setDraftAnswers((prev) => ({ ...prev, [question.id]: null }));
    setClearedQuestions((prev) => ({ ...prev, [question.id]: true }));
  }, [question]);

  const goToQuestion = useCallback(
    (direction: 'prev' | 'next') => {
      const newIndex = direction === 'prev' ? currentIndex - 1 : currentIndex + 1;
      if (newIndex >= 0 && newIndex < navList.length) {
        router.push(`/practice/${navList[newIndex].id}`);
      }
    },
    [currentIndex, navList, router],
  );

  // 键盘快捷键：1-4/A-D 选项 · Enter 提交或下一题 · ←/→ 切题 · F 收藏 · Esc 退出
  useEffect(() => {
    if (!question) return;
    function handleKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null;
      if (
        target?.tagName === 'INPUT' ||
        target?.tagName === 'TEXTAREA' ||
        target?.isContentEditable
      )
        return;
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (!question) return;

      const ph = isPlaceholderQuestion(question);
      const hasImg = ph && !!question.questionImage;

      // 选项作答（仅选择题，未提交，非锁定占位）
      if (!isSubmitted && question.type !== 'essay' && question.options) {
        let label: string | null = null;
        if (/^[1-4]$/.test(e.key)) {
          label = question.options[parseInt(e.key, 10) - 1]?.label ?? null;
        } else if (/^[a-dA-D]$/.test(e.key)) {
          label = e.key.toUpperCase();
        }
        if (label) {
          const opt = question.options.find((o) => o.label === label);
          const isOptBad = opt && isPlaceholderOption(opt) && !hasImg;
          if (opt && !isOptBad) {
            handleSelectOption(label);
            e.preventDefault();
            return;
          }
        }
      }

      if (e.key === 'Enter') {
        if (!isSubmitted) {
          if (selectedOption && !(ph && !hasImg)) {
            handleSubmit();
            e.preventDefault();
          }
        } else if (currentIndex < navList.length - 1) {
          goToQuestion('next');
          e.preventDefault();
        }
        return;
      }
      if (e.key === 'ArrowLeft' && currentIndex > 0) {
        goToQuestion('prev');
        e.preventDefault();
        return;
      }
      if (e.key === 'ArrowRight' && currentIndex < navList.length - 1) {
        goToQuestion('next');
        e.preventDefault();
        return;
      }
      if (e.key === 'f' || e.key === 'F') {
        toggleFavorite(question.id);
        e.preventDefault();
        return;
      }
      if (e.key === 'Escape') {
        router.push(backTarget);
        e.preventDefault();
      }
    }
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [
    question,
    isSubmitted,
    selectedOption,
    currentIndex,
    navList.length,
    handleSubmit,
    goToQuestion,
    toggleFavorite,
    router,
    backTarget,
    handleSelectOption,
  ]);

  if (!question) {
    // 加载完了但确实没这道题（收藏/历史里的旧链接，或该题已被清理），
    // 必须跟「还在加载」区分开 —— 否则页面永远停在「题目加载中…」。
    const notFound = loadedQuestion?.id === questionId && loadedQuestion.q === null;
    if (notFound) {
      return (
        <div className="mx-auto max-w-2xl px-4 py-16">
          <EmptyState
            icon={FileQuestion}
            title="这道题不在题库里了"
            description="它可能是重复入库后被清理的副本。可以回到练习列表继续做题。"
            action={
              <Button onClick={() => router.push(backTarget)}>返回练习</Button>
            }
          />
        </div>
      );
    }
    return (
      <div
        className="flex min-h-[50vh] items-center justify-center"
        role="status"
        aria-live="polite"
      >
        <p className="text-foreground-muted">题目加载中…</p>
      </div>
    );
  }

  const isCorrect =
    isSubmitted &&
    (Array.isArray(question.answer)
      ? question.answer.includes(selectedOption!)
      : question.answer === selectedOption);

  const isPlaceholder = isPlaceholderQuestion(question);
  const hasImageFallback = isPlaceholder && !!question.questionImage;
  const placeholderReason = isPlaceholder ? getPlaceholderReason(question) : '';
  const stemBad = isPlaceholderText(question.content);

  const categoryName =
    question.subject === 'xingce'
      ? XINGCE_CATEGORY_NAMES[
          question.category as keyof typeof XINGCE_CATEGORY_NAMES
        ]
      : SHENLUN_CATEGORY_NAMES[
          question.category as keyof typeof SHENLUN_CATEGORY_NAMES
        ];

  const submitMode = !isSubmitted
    ? 'pending'
    : question.type === 'essay'
      ? 'submitted-essay'
      : isCorrect
        ? 'submitted-correct'
        : 'submitted-wrong';

  const unanswerable = isPlaceholder && !hasImageFallback;
  const isFavorite = favorites.includes(question.id);
  const imageRepeatedFromPrevious =
    !!question.questionImage &&
    !!previousQuestion?.questionImage &&
    previousQuestion.questionImage === question.questionImage;

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
      <QuestionHeader
        categoryName={categoryName}
        sourceLabel={question.sourceLabel}
        difficultyName={DIFFICULTY_NAMES[question.difficulty]}
        isFavorite={isFavorite}
        onToggleFavorite={() => toggleFavorite(question.id)}
        currentIndex={currentIndex}
        total={navList.length}
      />

      <QuestionProgressBar currentIndex={currentIndex} total={navList.length} />

      {isPlaceholder && !hasImageFallback && (
        <QuestionStatusBanner
          mode="placeholder"
          reason={placeholderReason}
          onSkip={() => goToQuestion('next')}
          canSkip={currentIndex < navList.length - 1}
        />
      )}
      {hasImageFallback && <QuestionStatusBanner mode="imageFallback" />}

      <QuestionStem
        questionId={question.id}
        content={question.content}
        material={question.material}
        stemBad={stemBad}
        questionImage={question.questionImage}
        imageRepeatedFromPrevious={imageRepeatedFromPrevious}
        sourceLabel={question.sourceLabel}
      />

      {question.options && (
        <OptionList
          options={question.options}
          selected={selectedOption}
          isSubmitted={isSubmitted}
          answer={question.answer}
          imageFallback={hasImageFallback}
          hasFigureImage={!!question.questionImage}
          onSelect={handleSelectOption}
        />
      )}

      {question.type === 'essay' && !isSubmitted && (
        <EssayAnswerArea
          value={selectedOption || ''}
          onChange={(value) => handleSelectOption(value)}
        />
      )}

      <SubmitBar
        mode={submitMode}
        disabled={!selectedOption || unanswerable}
        disabledReason={unanswerable ? '本题源数据缺失，无法作答' : undefined}
        unanswerable={unanswerable}
        correctAnswer={question.answer}
        onSubmit={handleSubmit}
        onReset={resetQuestion}
      />

      <AnimatePresence>
        {showAnalysis && question.type === 'essay' && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            className="mb-6"
          >
            <ShenlunAnalysis
              question={question}
              userAnswer={selectedOption || ''}
            />
          </motion.div>
        )}
        {showAnalysis && question.type !== 'essay' && (
          <ExplanationPanel explanation={question.explanation} answer={question.answer} />
        )}
      </AnimatePresence>

      {/* 跨卷同题关联：只在出解析后露出，避免做题时被别处的同题剧透 */}
      {showAnalysis && <RelatedAppearances questionId={question.id} />}

      <KeyboardHintBar />

      <QuestionNavBar
        canPrev={currentIndex > 0}
        canNext={currentIndex < navList.length - 1}
        isSubmitted={isSubmitted}
        onPrev={() => goToQuestion('prev')}
        onNext={() => goToQuestion('next')}
        onBackToList={() => router.push(backTarget)}
      />
    </div>
  );
}
