'use client';

import { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, XCircle, ChevronDown, BookOpen, FileText, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';
import { parseShenlunAnswer, scoreMatch } from '@/lib/shenlunAnswer';
import EnhancedShenlunBody from './EnhancedShenlunBody';
import type { Question } from '@/types/question';

interface Props {
  question: Question;
  userAnswer: string;
}

export default function ShenlunAnalysis({ question, userAnswer }: Props) {
  const rawAnswer = typeof question.answer === 'string'
    ? question.answer
    : (question.answer as string[]).join('\n');

  const parsed = useMemo(() => parseShenlunAnswer(rawAnswer), [rawAnswer]);

  // D-6 #4: 优先用 question.keyPoints（D-6 预计算入库），无则 fallback 运行时抽取
  const allKeywords = useMemo(() => {
    const staticKw = (question as Question & { keyPoints?: string[] }).keyPoints;
    if (Array.isArray(staticKw) && staticKw.length > 0) {
      return staticKw;
    }
    const s = new Set<string>();
    for (const b of parsed.blocks) for (const k of b.points) s.add(k);
    return [...s];
  }, [parsed, question]);

  const score = useMemo(() => scoreMatch(userAnswer, allKeywords), [userAnswer, allKeywords]);

  const [expanded, setExpanded] = useState<Record<number, boolean>>(() =>
    parsed.blocks.reduce((acc, _, i) => ({ ...acc, [i]: i < 2 }), {})
  );
  const [essayTab, setEssayTab] = useState<'model' | 'analysis'>('model');

  const ratePct = Math.round(score.rate * 100);

  return (
    <div className="space-y-4">
      {/* 作答评估 */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1], delay: 0 }}
        className="rounded-xl border border-border bg-card overflow-hidden"
      >
        <div className="flex items-center gap-2 border-b border-border bg-card-hover px-5 py-3">
          <Sparkles size={16} className="text-primary" />
          <h3 className="text-sm font-semibold">作答评估</h3>
        </div>
        <div className="p-5 space-y-4">
          {allKeywords.length === 0 ? (
            <p className="text-sm text-muted">
              本题答案结构较自由，未抽出可比对要点。参考答案请见下方。
            </p>
          ) : (
            <>
              <div>
                <div className="mb-1 flex items-baseline justify-between">
                  <span className="text-sm font-medium">
                    命中 <span className="text-primary text-lg font-semibold">{score.hit.length}</span>
                    {' / '}{allKeywords.length} 个要点
                  </span>
                  <span className="text-sm text-muted">{ratePct}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-border overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${ratePct}%` }}
                    transition={{ duration: 0.6, ease: 'easeOut' }}
                    className={cn(
                      'h-full rounded-full',
                      ratePct >= 70
                        ? 'bg-gradient-to-r from-success/80 to-success'
                        : ratePct >= 40
                          ? 'bg-gradient-to-r from-brand-500 to-seal-500'
                          : 'bg-gradient-to-r from-seal-500 to-seal-700'
                    )}
                  />
                </div>
              </div>

              {score.hit.length > 0 && (
                <div>
                  <p className="mb-1.5 text-xs text-muted">命中要点</p>
                  <div className="flex flex-wrap gap-1.5">
                    {score.hit.map((k) => (
                      <span key={k} className="inline-flex items-center gap-1 rounded-full bg-success/15 px-2 py-0.5 text-xs text-success border border-success/40">
                        <CheckCircle2 size={12} /> {k}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {score.miss.length > 0 && (
                <div>
                  <p className="mb-1.5 text-xs text-muted">未命中要点</p>
                  <div className="flex flex-wrap gap-1.5">
                    {score.miss.map((k) => (
                      <span key={k} className="inline-flex items-center gap-1 rounded-full bg-danger/15 px-2 py-0.5 text-xs text-danger border border-danger/40">
                        <XCircle size={12} /> {k}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <p className="text-xs text-muted">
                评估仅基于关键词文字匹配，申论考察的观点深度与论证结构请对照下方参考答案自评。
              </p>
            </>
          )}

          <details className="rounded-lg border border-border bg-background/50">
            <summary className="cursor-pointer select-none px-3 py-2 text-xs text-muted hover:text-foreground">
              查看我的作答（{userAnswer.length} 字）
            </summary>
            <pre className="max-h-48 overflow-auto whitespace-pre-wrap break-words px-3 pb-3 text-xs leading-relaxed text-foreground">
              {userAnswer || '（未作答）'}
            </pre>
          </details>
        </div>
      </motion.div>

      {/* 参考答案（分块折叠） */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1], delay: 0.08 }}
        className="rounded-xl border border-border bg-card overflow-hidden"
      >
        <div className="flex items-center gap-2 border-b border-border bg-card-hover px-5 py-3">
          <BookOpen size={16} className="text-primary" />
          <h3 className="text-sm font-semibold">参考答案</h3>
        </div>
        <div className="divide-y divide-border">
          {parsed.blocks.map((block, i) => (
            <div key={i}>
              <button
                onClick={() => setExpanded((s) => ({ ...s, [i]: !s[i] }))}
                className="flex w-full items-center justify-between px-5 py-3 text-left hover:bg-card-hover transition-colors"
              >
                <span className="text-sm font-medium">{block.title}</span>
                <motion.div animate={{ rotate: expanded[i] ? 180 : 0 }}>
                  <ChevronDown size={16} className="text-muted" />
                </motion.div>
              </button>
              <AnimatePresence initial={false}>
                {expanded[i] && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.25 }}
                    className="overflow-hidden"
                  >
                    <div className="px-5 pb-4 text-sm">
                      <EnhancedShenlunBody text={block.bodyMd} keywords={block.points} />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </motion.div>

      {/* 范文 + 文章分析 tab（仅作文题有） */}
      {parsed.essayModel && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1], delay: 0.16 }}
          className="rounded-xl border border-border bg-card overflow-hidden"
        >
          <div className="flex items-center gap-2 border-b border-border bg-card-hover px-5 py-3">
            <FileText size={16} className="text-primary" />
            <h3 className="text-sm font-semibold">范文解读</h3>
          </div>
          <div className="flex border-b border-border">
            {([
              { k: 'model', label: '范文' },
              { k: 'analysis', label: '文章分析' },
            ] as const).map(({ k, label }) => (
              <button
                key={k}
                onClick={() => setEssayTab(k)}
                className={cn(
                  'flex-1 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors',
                  essayTab === k
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted hover:text-foreground'
                )}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="p-5 text-sm">
            <EnhancedShenlunBody
              text={essayTab === 'model' ? parsed.essayModel : (parsed.essayAnalysis || '暂无分析')}
              keywords={allKeywords}
            />
          </div>
        </motion.div>
      )}
    </div>
  );
}
