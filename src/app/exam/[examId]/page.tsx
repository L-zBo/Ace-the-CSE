import ExamSessionClient from './ExamSessionClient';

export function generateStaticParams() {
  return [
    { examId: 'national-xingce-2024' },
    { examId: 'national-shenlun-2024' },
  ];
}

export default function ExamSessionPage() {
  return <ExamSessionClient />;
}
