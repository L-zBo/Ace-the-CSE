/**
 * 申论参考答案 / 文章分析增强渲染：
 *   - 框架词（一是/二是/首先/其次/同时/此外...）→ 蓝色加粗
 *   - 数字编号（1./2./N、）→ 紫色 chip 风格
 *   - 政策术语（高质量发展/新发展理念/乡村振兴...）→ 红色加粗
 *   - 关键短语（来自 keyPoints 提取）→ 黄色高亮背景
 *   - 转折/总结词（因此/综上/总之/可见）→ 绿色加粗
 *   - 数字 + 单位（25%/3.2亿元/2025年）→ 青色加粗
 */
'use client';

import React from 'react';

const FRAME_WORDS = [
  '一是', '二是', '三是', '四是', '五是',
  '首先', '其次', '再次', '最后', '同时', '此外', '另外', '其中',
  '第一', '第二', '第三', '第四', '第五',
];

const POLICY_TERMS = [
  '高质量发展', '新发展理念', '乡村振兴', '共同富裕', '碳中和', '碳达峰',
  '新型城镇化', '一带一路', '数字经济', '双循环', '人类命运共同体',
  '全过程人民民主', '中国式现代化', '美丽中国', '新质生产力',
  '习近平新时代中国特色社会主义思想',
  '科技创新', '绿色发展', '协调发展', '共享发展', '开放发展', '创新驱动',
  '党的领导', '法治', '民生', '生态文明', '依法治国',
];

const TRANSITION_WORDS = [
  '因此', '综上', '总之', '可见', '由此', '所以', '故而', '总而言之',
  '由此可见', '综上所述',
];

const NUM_UNIT_RE = /(\d{1,4}(?:\.\d+)?(?:%|％|亿元|万元|万人|千克|公里|平方公里|年|岁|人|次|个|项|条|倍|度|度C|℃))/g;

interface Pattern {
  re: RegExp;
  className: string;
}

function buildPatterns(extraKeywords: string[]): Pattern[] {
  const escape = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  // 关键词去重并按长度排序（长的优先匹配）
  const kwsSorted = Array.from(new Set(extraKeywords))
    .filter((s) => s.length >= 2 && s.length <= 16)
    .sort((a, b) => b.length - a.length);
  const patterns: Pattern[] = [];
  if (POLICY_TERMS.length) {
    patterns.push({
      re: new RegExp(POLICY_TERMS.map(escape).join('|'), 'g'),
      className: 'shenlun-policy',
    });
  }
  if (FRAME_WORDS.length) {
    patterns.push({
      re: new RegExp(`(?:${FRAME_WORDS.map(escape).join('|')})`, 'g'),
      className: 'shenlun-frame',
    });
  }
  if (TRANSITION_WORDS.length) {
    patterns.push({
      re: new RegExp(`(?:${TRANSITION_WORDS.map(escape).join('|')})`, 'g'),
      className: 'shenlun-transition',
    });
  }
  if (kwsSorted.length) {
    patterns.push({
      re: new RegExp(kwsSorted.map(escape).join('|'), 'g'),
      className: 'shenlun-keyword',
    });
  }
  patterns.push({
    re: new RegExp(NUM_UNIT_RE.source, 'g'),
    className: 'shenlun-num',
  });
  return patterns;
}

/**
 * 把 text 切分成 React 节点：匹配的 pattern 包成 span.<className>，未匹配保留原文。
 * 多个 pattern 优先级按数组顺序（前面优先）。
 */
function highlightSegments(text: string, patterns: Pattern[]): React.ReactNode[] {
  if (!text) return [text];
  // 收集所有匹配段：[start, end, className, text]
  type Hit = { s: number; e: number; cls: string; txt: string; pri: number };
  const hits: Hit[] = [];
  patterns.forEach((p, idx) => {
    p.re.lastIndex = 0;
    let m;
    while ((m = p.re.exec(text))) {
      if (m[0].length === 0) {
        p.re.lastIndex++;
        continue;
      }
      hits.push({ s: m.index, e: m.index + m[0].length, cls: p.className, txt: m[0], pri: idx });
    }
  });
  // 按起始位置排序，pri 小（即数组顺序在前）的优先
  hits.sort((a, b) => a.s - b.s || a.pri - b.pri);
  // 解决重叠：贪心保留 pri 最小（前面优先）的非重叠匹配
  const kept: Hit[] = [];
  let cur = -1;
  for (const h of hits) {
    if (h.s >= cur) {
      kept.push(h);
      cur = h.e;
    }
  }
  // 渲染
  const out: React.ReactNode[] = [];
  let p = 0;
  kept.forEach((h, i) => {
    if (h.s > p) out.push(text.slice(p, h.s));
    out.push(
      <span
        key={`${h.s}-${i}`}
        className={h.cls}
        title={h.cls === 'shenlun-keyword' ? `命中要点：${h.txt}` : undefined}
      >
        {h.txt}
      </span>
    );
    p = h.e;
  });
  if (p < text.length) out.push(text.slice(p));
  return out;
}

interface Props {
  text: string;
  keywords?: string[];
}

/**
 * 行级渲染：每行识别"数字编号行"/"框架词起头行"，套对应包装。
 * 行内文本走 highlightSegments。
 */
export default function EnhancedShenlunBody({ text, keywords = [] }: Props) {
  const patterns = React.useMemo(() => buildPatterns(keywords), [keywords]);
  if (!text) return null;
  const lines = text.split(/\r?\n/);

  // 预扫描小节标题用于 TOC（D-18a P2e-5）
  const toc: { id: string; label: string }[] = [];
  lines.forEach((rawLine, idx) => {
    const line = rawLine.replace(/\s+$/, '');
    const sectHead = line.match(
      /^\s*([一二三四五六七八九十]+\s*[、.．]|[\(（][一二三四五六七八九十]+[\)）])\s*/,
    );
    if (sectHead && line.length < 40) {
      const titleText = line.slice(sectHead[0].length).trim();
      if (titleText) {
        toc.push({ id: `shenlun-sect-${idx}`, label: titleText.slice(0, 12) });
      }
    }
  });

  const blocks: React.ReactNode[] = [];
  lines.forEach((rawLine, idx) => {
    const line = rawLine.replace(/\s+$/, '');
    if (!line.trim()) {
      blocks.push(<div key={idx} className="h-2" aria-hidden />);
      return;
    }
    // 数字编号行（"1." / "1、" / "(1)" / "①"）
    const numHead = line.match(/^\s*((?:\d+|[一二三四五六七八九十]+)[.．、]|[\(（]\d+[\)）]|[①②③④⑤⑥⑦⑧⑨⑩])\s*/);
    if (numHead) {
      const headText = numHead[1];
      const restText = line.slice(numHead[0].length);
      blocks.push(
        <div key={idx} className="shenlun-line shenlun-numbered-row">
          <span className="shenlun-numbered">{headText}</span>
          <span>{highlightSegments(restText, patterns)}</span>
        </div>
      );
      return;
    }
    // 标题/小节标题（如 "（一）" / "一、" + 短文本）
    const sectHead = line.match(/^\s*([一二三四五六七八九十]+\s*[、.．]|[\(（][一二三四五六七八九十]+[\)）])\s*/);
    if (sectHead && line.length < 40) {
      blocks.push(
        <div key={idx} id={`shenlun-sect-${idx}`} className="shenlun-section-head scroll-mt-20">
          <span className="shenlun-numbered">{sectHead[1]}</span>
          <span className="shenlun-section-title">
            {highlightSegments(line.slice(sectHead[0].length), patterns)}
          </span>
        </div>
      );
      return;
    }
    // 普通段落
    blocks.push(
      <p key={idx} className="shenlun-line">
        {highlightSegments(line, patterns)}
      </p>
    );
  });

  return (
    <div className="shenlun-body">
      {toc.length >= 2 && (
        <nav
          aria-label="范文小节锚导航"
          className="mb-3 flex flex-wrap items-center gap-1.5 rounded-lg border border-border bg-card/60 px-3 py-2 text-xs backdrop-blur-sm"
        >
          <span className="text-foreground-muted">目录：</span>
          {toc.map((item) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              onClick={(e) => {
                e.preventDefault();
                document
                  .getElementById(item.id)
                  ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }}
              className="rounded-full border border-brand-500/40 bg-brand-500/10 px-2 py-0.5 text-brand-300 transition-colors hover:bg-brand-500/20 hover:text-brand-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
            >
              {item.label}
            </a>
          ))}
        </nav>
      )}
      {blocks}
    </div>
  );
}
