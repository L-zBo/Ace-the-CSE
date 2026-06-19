'use client';

import { motion } from 'framer-motion';
import { AlertTriangle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { AnnotatableImage } from '@/components/questions/AnnotatableImage';
import { Card } from '@/components/ui/Card';
import { markdownComponents } from '@/lib/markdownComponents';
import { isRecoveredText, stripDerivedMarker } from '@/lib/placeholder';
import { splitStemAndPrompt } from '@/lib/questionDisplay';

interface QuestionStemProps {
  /** 题目唯一 id，用作 key 触发切题入场动效 */
  questionId: string;
  /** 题干 markdown 文本 */
  content: string;
  /** 申论给定材料 markdown 文本 */
  material?: string;
  /** 题干源数据缺失（占位） */
  stemBad: boolean;
  /** 题目附图（图形推理/资料分析等） */
  questionImage?: string;
  /** 当前图片已在同组上一题显示过时，仅保留可打开入口 */
  imageRepeatedFromPrevious?: boolean;
  /** 题目标签（alt 用） */
  sourceLabel: string;
}

const stemVariants = {
  hidden: { opacity: 0, y: 8, filter: 'blur(4px)' },
  visible: {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] },
  },
};

export function QuestionStem({
  questionId,
  content,
  material,
  stemBad,
  questionImage,
  imageRepeatedFromPrevious = false,
  sourceLabel,
}: QuestionStemProps) {
  const recovered = !stemBad && isRecoveredText(content);
  const displayContent = recovered ? stripDerivedMarker(content) : content;
  const { stem: stemBody, prompt } = stemBad
    ? { stem: '', prompt: null }
    : splitStemAndPrompt(displayContent);

  return (
    <>
      {material && (
        <Card className="mb-4 rounded-xl">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-foreground-muted">
            给定材料
          </h3>
          <div className="markdown-content prose prose-sm max-w-none prose-invert">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
              {material}
            </ReactMarkdown>
          </div>
        </Card>
      )}

      <motion.div
        key={questionId}
        variants={stemVariants}
        initial="hidden"
        animate="visible"
        className="mb-6"
      >
        <Card className="rounded-xl border-l-4 border-l-seal-red">
          <div className="markdown-content text-lg leading-[1.8] text-foreground">
            {stemBad ? (
              <p className="rounded-lg border border-dashed border-border bg-surface-2/40 px-4 py-6 text-center text-sm text-foreground-muted">
                （题干源数据缺失，无法显示）
              </p>
            ) : recovered ? (
              <div className="space-y-2">
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                  {stemBody}
                </ReactMarkdown>
                <p className="flex items-center gap-1.5 text-xs text-warning">
                  <AlertTriangle size={12} aria-hidden="true" />
                  题干由源数据救援补全，可能与原题措辞略有出入
                </p>
              </div>
            ) : (
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                {stemBody}
              </ReactMarkdown>
            )}
          </div>

          {prompt && (
            <div className="question-prompt markdown-content" role="group" aria-label="提问">
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                {prompt}
              </ReactMarkdown>
            </div>
          )}
        </Card>

        {questionImage && !imageRepeatedFromPrevious && (
          <AnnotatableImage
            src={questionImage}
            alt={`题图 ${sourceLabel}`}
            sourceKey={questionId}
            frameClassName="mt-4"
          />
        )}

        {questionImage && imageRepeatedFromPrevious && (
          <div className="mt-4 rounded-xl border border-border bg-card/70 px-4 py-3 text-sm text-foreground-muted">
            本题沿用上一小题题图；题图批注按图片保存，可在上一题图或图注笔记中继续查看。
          </div>
        )}
      </motion.div>
    </>
  );
}
