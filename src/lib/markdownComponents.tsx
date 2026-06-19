import type { Components } from 'react-markdown';
import { wrapFillBlank } from './questionDisplay';

/**
 * 共用 markdown 渲染配置（D-18a P2d-3）
 *
 * 给 ReactMarkdown 的 `components` prop 用。统一处理：
 * - 字符串内 `_{3,}` → `<span class="fill-blank">`（P2a-fix-1 联动）
 * - `__重点字__` → `<strong>` 由全局 `.markdown-content strong` 印章红
 *   下划线规则接管
 *
 * 用于 QuestionStem / ExplanationPanel / 任何 .markdown-content 容器。
 */
export const markdownComponents: Components = {
  p: ({ children, ...props }) => <p {...props}>{wrapFillBlank(children)}</p>,
  li: ({ children, ...props }) => <li {...props}>{wrapFillBlank(children)}</li>,
  td: ({ children, ...props }) => <td {...props}>{wrapFillBlank(children)}</td>,
  th: ({ children, ...props }) => <th {...props}>{wrapFillBlank(children)}</th>,
  strong: ({ children, ...props }) => <strong {...props}>{wrapFillBlank(children)}</strong>,
  em: ({ children, ...props }) => <em {...props}>{wrapFillBlank(children)}</em>,
  blockquote: ({ children, ...props }) => (
    <blockquote {...props}>{wrapFillBlank(children)}</blockquote>
  ),
};
