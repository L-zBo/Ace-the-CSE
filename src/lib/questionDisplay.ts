import type { ReactNode, Key } from 'react';
import { Fragment, createElement, isValidElement, Children } from 'react';

const FILL_BLANK_RE = /(_{3,})/g;

/**
 * 递归处理 ReactMarkdown 渲染出的 inline 子节点，把字符串里的 `_{3,}`
 * 替换为 `<span class="fill-blank">______</span>`，给逻辑填空题的横线一个
 * 卷面"待填"视觉（印章红虚线下划 + 浅金底）。
 *
 * 用法：在 ReactMarkdown 的 `components` 里，给 p/li/em/strong/td 等
 * 文本容器套 `{wrapFillBlank(children)}`。
 */
export function wrapFillBlank(children: ReactNode): ReactNode {
  return mapNodes(children, 0);
}

function mapNodes(node: ReactNode, depth: number): ReactNode {
  if (node == null || typeof node === 'boolean') return node;

  if (typeof node === 'string') {
    if (!FILL_BLANK_RE.test(node)) return node;
    FILL_BLANK_RE.lastIndex = 0;
    const parts = node.split(FILL_BLANK_RE);
    return parts.map((part, i) =>
      /^_{3,}$/.test(part) ? (
        createElement(
          'span',
          { key: `fb-${depth}-${i}`, className: 'fill-blank', 'aria-label': '填空' },
          part,
        )
      ) : (
        createElement(Fragment, { key: `fb-${depth}-${i}` }, part)
      ),
    );
  }

  if (typeof node === 'number') return node;

  if (Array.isArray(node)) {
    return node.map((child, i) => {
      const mapped = mapNodes(child, depth + 1);
      if (isValidElement(mapped) || typeof mapped === 'string' || typeof mapped === 'number') {
        return mapped;
      }
      return createElement(Fragment, { key: (child as { key?: Key })?.key ?? `n-${i}` }, mapped);
    });
  }

  if (isValidElement<{ children?: ReactNode }>(node)) {
    const childChildren = node.props?.children;
    if (childChildren == null) return node;
    const mappedChildren = Children.count(childChildren) === 0
      ? childChildren
      : mapNodes(childChildren, depth + 1);
    return createElement(node.type, { ...node.props, key: node.key }, mappedChildren);
  }

  return node;
}

/* ============================================================
 * 提问句拆分：把题干末尾的"提问短句"独立出来，前端单独渲染加视觉锚
 *
 * 行测题型典型提问句：
 *   - "依次填入划横线处最恰当的一项是：（ ）"（言语-逻辑填空）
 *   - "下列说法正确的是："（常识/言语）
 *   - "根据该法的规定，下列说法正确的是："（常识）
 *   - "这段文字意在强调："（言语-意图判断）
 *   - "分类正确的一项是（ ）。"（图形-单句，不拆）
 *
 * 拆分规则：从末尾向前找句号/问号/感叹号，紧随其后是"提问起手词"则视为
 * 提问句。整段只有单句（无前置句号）则不拆，避免把图形题单句一刀切。
 * ============================================================ */

const PROMPT_STARTERS =
  '下列|依次|关于|根据|对(?:于|此)|从所给|从上述|这段|本段|本文|对上述|对此|对该|划(?:横)?线|哪一?(?:项|个|种|组)|可以(?:得出|推[出断知论])|不(?:能|可)(?:推[出断知论]|得出)|文中|这一段|与上述|结合上(?:文|述)';

const TAIL_PROMPT_RE = new RegExp(
  `([。？?！!])\\s*((?:${PROMPT_STARTERS})[^。？?！!]{0,80})\\s*$`,
);

export interface SplitStemResult {
  /** 题干主体（含尾部句号）*/
  stem: string;
  /** 提问句（不含前置句号），未命中则为 null */
  prompt: string | null;
}

export function splitStemAndPrompt(content: string): SplitStemResult {
  if (!content) return { stem: content, prompt: null };
  const m = content.match(TAIL_PROMPT_RE);
  if (m && m.index !== undefined) {
    const stemEnd = m.index + m[1].length;
    const stem = content.slice(0, stemEnd).trim();
    const prompt = m[2].trim();
    if (stem.length > 0 && prompt.length > 0) {
      return { stem, prompt };
    }
  }
  return { stem: content, prompt: null };
}
