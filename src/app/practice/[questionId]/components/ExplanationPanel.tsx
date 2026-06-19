'use client';

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { Lightbulb } from 'lucide-react';
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ScrollFloat } from '@/components/effects';
import { formatExplanation } from '@/lib/explanationFormatter';
import { markdownComponents } from '@/lib/markdownComponents';
import { wrapFillBlank } from '@/lib/questionDisplay';

interface ExplanationPanelProps {
  explanation: string;
}

const OPTION_LABEL_RE = /^([ABCDE])\s*项[:：]?$/;

/**
 * 解析里点 "A 项" 滚动到对应选项（D-18a P2d-2 选项联动）
 * 触发：strong 子节点首条是 "A 项 / B 项 / C 项 / D 项 / E 项"
 */
function scrollToOption(label: string) {
  if (typeof document === 'undefined') return;
  const el = document.getElementById(`option-${label}`);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    el.classList.add('ring-2', 'ring-seal-red');
    setTimeout(() => {
      el.classList.remove('ring-2', 'ring-seal-red');
    }, 1500);
  }
}

function extractOptionLabel(children: React.ReactNode): string | null {
  let text = '';
  const walk = (node: React.ReactNode): void => {
    if (typeof node === 'string') text += node;
    else if (Array.isArray(node)) node.forEach(walk);
    else if (
      node &&
      typeof node === 'object' &&
      'props' in node &&
      (node as { props?: { children?: React.ReactNode } }).props?.children !== undefined
    ) {
      walk((node as { props: { children: React.ReactNode } }).props.children);
    }
  };
  walk(children);
  const m = text.trim().match(OPTION_LABEL_RE);
  return m ? m[1] : null;
}

export function ExplanationPanel({ explanation }: ExplanationPanelProps) {
  const formatted = formatExplanation(explanation);

  const explanationComponents: Components = useMemo(
    () => ({
      ...markdownComponents,
      strong: ({ children, ...props }) => {
        const label = extractOptionLabel(children);
        if (label) {
          return (
            <button
              type="button"
              onClick={() => scrollToOption(label)}
              aria-label={`滚动到选项 ${label}`}
              className="explanation-option-jump"
              {...(props as React.ButtonHTMLAttributes<HTMLButtonElement>)}
            >
              {wrapFillBlank(children)}
            </button>
          );
        }
        return <strong {...props}>{wrapFillBlank(children)}</strong>;
      },
    }),
    [],
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      className="mb-6 overflow-hidden rounded-xl border border-border bg-card backdrop-blur-md shadow-md"
    >
      <div className="flex items-center gap-2 border-b border-border bg-surface-2/40 px-5 py-3">
        <Lightbulb size={16} className="text-warning" aria-hidden="true" />
        <h3 className="font-display-zh text-sm font-semibold text-foreground">
          答案解析
        </h3>
      </div>
      <ScrollFloat amount={0.05} duration={0.45}>
        <div className="markdown-content explanation-body prose prose-sm max-w-none prose-invert p-5 text-base leading-relaxed">
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={explanationComponents}>
            {formatted}
          </ReactMarkdown>
        </div>
      </ScrollFloat>
    </motion.div>
  );
}
