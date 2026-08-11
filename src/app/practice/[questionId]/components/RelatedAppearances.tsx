'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { History, ChevronRight } from 'lucide-react';
import {
  loadRelatedAppearances,
  type RelatedAppearance,
} from '@/lib/relatedQuestions';

interface RelatedAppearancesProps {
  questionId: string;
}

/** 超过这个条数就折叠，事业编题池里有的题能出现十几次 */
const PREVIEW_COUNT = 4;

/**
 * 「这道题还在哪儿考过」。
 *
 * 数据源是跨卷同题关联（src/lib/relatedQuestions.ts），约 300 KB，
 * 所以放在这里按需 import —— 只有真正做到有关联的题才会下载。
 */
export function RelatedAppearances({ questionId }: RelatedAppearancesProps) {
  // 存 { id, list } 而不是裸数组：切题时靠 id 比对立刻失效，
  // 不用在 effect 里同步 setState 清空。
  const [loaded, setLoaded] = useState<{
    id: string;
    list: RelatedAppearance[];
  } | null>(null);
  // 展开态同样绑到题目 id 上：切到下一题自然收起，
  // 不用在 effect 里 setExpanded(false)（那会触发级联渲染）。
  const [expandedFor, setExpandedFor] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    loadRelatedAppearances(questionId).then((list) => {
      if (!cancelled) setLoaded({ id: questionId, list });
    });
    return () => {
      cancelled = true;
    };
  }, [questionId]);

  const list = loaded?.id === questionId ? loaded.list : [];
  if (list.length === 0) return null;

  const expanded = expandedFor === questionId;
  const shown = expanded ? list : list.slice(0, PREVIEW_COUNT);
  const rest = list.length - shown.length;

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      className="mb-6 overflow-hidden rounded-xl border border-border bg-card shadow-md"
      aria-label="这道题的其他出处"
    >
      <div className="flex items-center gap-2 border-b border-border bg-surface-2/40 px-5 py-3">
        <History size={16} className="text-info" aria-hidden="true" />
        <h3 className="font-display-zh text-sm font-semibold text-foreground">
          这道题还考过 {list.length} 次
        </h3>
      </div>

      <ul className="divide-y divide-border/60">
        {shown.map((item) => (
          <li key={item.id}>
            <Link
              href={`/practice/${item.id}`}
              className="flex items-center justify-between gap-3 px-5 py-3 text-sm transition-colors hover:bg-surface-2/60"
            >
              <span className="text-foreground-secondary">
                {item.paperLabel}
                {item.qno > 0 && (
                  <span className="ml-1 text-foreground-muted">第 {item.qno} 题</span>
                )}
              </span>
              <ChevronRight
                size={15}
                className="shrink-0 text-foreground-muted"
                aria-hidden="true"
              />
            </Link>
          </li>
        ))}
      </ul>

      {rest > 0 && (
        <button
          type="button"
          onClick={() => setExpandedFor(questionId)}
          className="w-full border-t border-border/60 px-5 py-2.5 text-xs text-foreground-muted transition-colors hover:bg-surface-2/60 hover:text-foreground-secondary"
        >
          展开其余 {rest} 处
        </button>
      )}

      <p className="border-t border-border/60 bg-surface-2/20 px-5 py-2 text-xs leading-relaxed text-foreground-muted">
        同一道真题被多省多年重复使用。按题干与选项完全一致比对得出，图形题因无法用文字比对不参与。
      </p>
    </motion.section>
  );
}
