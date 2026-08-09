import { getQuestionIndex } from '@/lib/questionIndex';
import QuestionPageClient from './QuestionPageClient';

// 题库有 2 万+ 道题，全部预渲染会让 `next build` 在本机磁盘上超时。
// 页面本身是纯客户端渲染（QuestionPageClient 走 useParams 取题号），预渲染只产出空壳 HTML，
// 所以普通构建下不预渲染任何一条，交给 dynamicParams（默认 true）按需生成。
// 只有打 Capacitor 安卓包（NEXT_STATIC_EXPORT=1，`output: "export"`）时才必须全量展开。
//
// 注意：dynamicParams 只能是字面量，不能写成表达式，Next 会静态解析 segment config。
// 这里保持默认 true 即可，不显式导出。
const isStaticExport = process.env.NEXT_STATIC_EXPORT === '1';

export function generateStaticParams() {
  if (!isStaticExport) return [];
  // 只要题号，走轻量索引即可，不必加载题库正文。
  return getQuestionIndex().map((m) => ({ questionId: m.id }));
}

export default function QuestionPage() {
  return <QuestionPageClient />;
}
