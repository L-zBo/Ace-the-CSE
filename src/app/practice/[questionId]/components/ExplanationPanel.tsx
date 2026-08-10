'use client';

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, Lightbulb } from 'lucide-react';
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ScrollFloat } from '@/components/effects';
import { formatExplanation } from '@/lib/explanationFormatter';
import { markdownComponents } from '@/lib/markdownComponents';
import { wrapFillBlank } from '@/lib/questionDisplay';

interface ExplanationPanelProps {
  explanation: string;
  /** 本题答案。用于识别「解析结论与答案矛盾」并给出提示。 */
  answer?: string | string[];
}

const OPTION_LABEL_RE = /^([ABCDE])\s*项[:：]?$/;
const CONCLUSION_RE = /故正确答案为\s*([A-D]+)/g;

/**
 * 解析结论与本题答案是否打架。
 *
 * 全库还有约 90 道题，answer 与解析里的「故正确答案为X」对不上 —— 成因是
 * PDF 抽取跨题串行，官方 PDF 也校不出来（详见 reports/explanation_repair.json）。
 * 补不回正确解析时，至少要让用户知道这段解析可能不是这道题的，
 * 而不是让人照着错解析去理解题目。
 */
function conflicts(explanation: string, answer?: string | string[]): boolean {
  if (!explanation || !answer) return false;
  const ans = Array.isArray(answer) ? answer.join('') : answer;
  if (!/^[A-D]+$/.test(ans)) return false;
  const hits = [...explanation.matchAll(CONCLUSION_RE)].map((m) => m[1]);
  if (hits.length === 0) return false;
  return !hits.includes(ans);
}

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

export function ExplanationPanel({ explanation, answer }: ExplanationPanelProps) {
  const formatted = formatExplanation(explanation);
  const mismatched = useMemo(
    () => conflicts(explanation, answer),
    [explanation, answer],
  );

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
        {mismatched && (
          <div className="mx-5 mt-4 flex items-start gap-2 rounded-lg border border-warning/40 bg-warning/10 px-3 py-2">
            <AlertTriangle
              size={15}
              className="mt-0.5 shrink-0 text-warning"
              aria-hidden="true"
            />
            <p className="text-xs leading-relaxed text-foreground-secondary">
              这段解析的结论与本题答案对不上，多半是原始 PDF
              抽取时串到了别的题。<strong className="text-foreground">请以上方答案为准</strong>
              ，解析内容仅供参考。
            </p>
          </div>
        )}
        <div className="markdown-content explanation-body prose prose-sm max-w-none prose-invert p-5 text-base leading-relaxed">
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={explanationComponents}>
            {formatted}
          </ReactMarkdown>
        </div>
      </ScrollFloat>
    </motion.div>
  );
}
