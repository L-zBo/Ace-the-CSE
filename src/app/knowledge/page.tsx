'use client';

import { useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, ChevronRight, ChevronDown, BookOpen } from 'lucide-react';
import knowledgeData from '@/data/knowledge.json';
import { useStatsStore } from '@/stores/statsStore';
import { calcPercentage } from '@/lib/utils';

interface KnowledgeNode {
  id: string;
  name: string;
  questionTags?: string[];
  children?: KnowledgeNode[];
}

function KnowledgeTree({ nodes, subject }: { nodes: KnowledgeNode[]; subject: string }) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const stats = useStatsStore();

  const toggle = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const getCategoryAccuracy = (categoryId: string) => {
    let total = 0;
    let correct = 0;
    for (const day of stats.dailyStats) {
      if (day.categories[categoryId]) {
        total += day.categories[categoryId].total;
        correct += day.categories[categoryId].correct;
      }
    }
    return { total, correct, accuracy: calcPercentage(correct, total) };
  };

  return (
    <div className="space-y-2">
      {nodes.map((node) => {
        const isOpen = expanded.has(node.id);
        const stat = getCategoryAccuracy(node.id);

        return (
          <div key={node.id}>
            <button
              onClick={() => toggle(node.id)}
              className="flex w-full items-center gap-3 rounded-xl border border-border bg-card p-4 transition-[transform,box-shadow,background-color,border-color] hover:shadow-md"
            >
              {node.children ? (
                isOpen ? (
                  <ChevronDown size={18} className="text-primary" />
                ) : (
                  <ChevronRight size={18} className="text-muted" />
                )
              ) : (
                <BookOpen size={18} className="text-muted" />
              )}
              <span className="flex-1 text-left font-medium">{node.name}</span>
              {stat.total > 0 && (
                <div className="flex items-center gap-3 text-sm">
                  <span className="text-muted">{stat.total}题</span>
                  <div className="w-20">
                    <div className="h-1.5 rounded-full bg-border">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${stat.accuracy}%` }}
                      />
                    </div>
                  </div>
                  <span className="w-10 text-right text-muted">{stat.accuracy}%</span>
                </div>
              )}
            </button>

            <AnimatePresence>
              {isOpen && node.children && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="ml-6 mt-1 space-y-1 overflow-hidden"
                >
                  {node.children.map((child) => (
                    <Link
                      key={child.id}
                      href={`/practice?subject=${subject}&category=${node.id}`}
                      className="flex items-center gap-3 rounded-lg border border-transparent bg-card-hover p-3 text-sm transition-colors hover:border-primary/20 hover:bg-primary/5"
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                      <span className="flex-1">{child.name}</span>
                      {child.questionTags && (
                        <span className="text-xs text-muted">
                          {child.questionTags.length} 个考点
                        </span>
                      )}
                    </Link>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
}

export default function KnowledgePage() {
  const [activeTab, setActiveTab] = useState<'xingce' | 'shenlun'>('xingce');

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
      <div className="mb-6 flex items-center gap-3">
        <Brain size={24} className="text-warning" aria-hidden="true" />
        <h1 className="text-2xl font-bold">知识体系</h1>
      </div>

      <p className="mb-6 text-sm text-muted">
        按知识点体系组织，点击展开查看子知识点，点击具体考点跳转刷题。
      </p>

      {/* Tab */}
      <div className="mb-6 flex gap-2">
        <button
          onClick={() => setActiveTab('xingce')}
          className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'xingce'
              ? 'bg-primary text-white'
              : 'bg-card-hover text-muted hover:text-foreground'
          }`}
        >
          行测
        </button>
        <button
          onClick={() => setActiveTab('shenlun')}
          className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'shenlun'
              ? 'bg-primary text-white'
              : 'bg-card-hover text-muted hover:text-foreground'
          }`}
        >
          申论
        </button>
      </div>

      <KnowledgeTree
        nodes={
          activeTab === 'xingce'
            ? (knowledgeData.xingce as KnowledgeNode[])
            : (knowledgeData.shenlun as KnowledgeNode[])
        }
        subject={activeTab}
      />
    </div>
  );
}
