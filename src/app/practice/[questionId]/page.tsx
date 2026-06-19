import { getAllQuestions } from '@/lib/questionLoader';
import QuestionPageClient from './QuestionPageClient';

export function generateStaticParams() {
  return getAllQuestions().map((q) => ({ questionId: q.id }));
}

export default function QuestionPage() {
  return <QuestionPageClient />;
}
