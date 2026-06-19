'use client';

import { Library, Search } from 'lucide-react';
import { useDeferredValue, useMemo, useState } from 'react';
import idiomsRaw from '@/data/idioms_raw.json';
import IdiomCard, { type IdiomCardData } from '@/components/idioms/IdiomCard';
import { IdiomDetailDialog } from '@/components/idioms/IdiomDetailDialog';
import { useIdiomStore, type IdiomStatus } from '@/stores/idiomStore';
import { cn, getTodayString } from '@/lib/utils';

type FrequencyTier = 'ultra_high' | 'high' | 'mid' | 'low';
type StatusFilter = 'all' | IdiomStatus | 'due';
type TierFilter = 'all' | FrequencyTier;

interface IdiomRecordExt extends IdiomCardData {
  frequencyTier: FrequencyTier;
  pinyin: string;
  pinyinAbbr: string;
}

const STATUS_FILTERS: { key: StatusFilter; label: string }[] = [
  { key: 'all', label: '全部' },
  { key: 'due', label: '今日待复习' },
  { key: 'unknown', label: '不会' },
  { key: 'reviewing', label: '复习中' },
  { key: 'mastered', label: '已掌握' },
];

const TIER_FILTERS: { key: TierFilter; label: string }[] = [
  { key: 'all', label: '全部频次' },
  { key: 'ultra_high', label: '超高频 ≥10' },
  { key: 'high', label: '高频 5-9' },
  { key: 'mid', label: '中频 2-4' },
  { key: 'low', label: '低频 1' },
];

const ACCENT_CLASS: Record<'brand' | 'info', string> = {
  brand: 'border-brand-soft/60 bg-brand/30 shadow-mo-blue',
  info: 'border-info/60 bg-info/25 shadow-md',
};

const PAGE_SIZE = 60;

const idioms = idiomsRaw as IdiomRecordExt[];

function levenshtein(a: string, b: string): number {
  if (a === b) return 0;
  if (!a.length) return b.length;
  if (!b.length) return a.length;
  const m = a.length;
  const n = b.length;
  let prev = Array.from({ length: n + 1 }, (_, i) => i);
  let curr = new Array(n + 1).fill(0);
  for (let i = 1; i <= m; i++) {
    curr[0] = i;
    for (let j = 1; j <= n; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      curr[j] = Math.min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost);
    }
    [prev, curr] = [curr, prev];
  }
  return prev[n];
}

function matchSearch(item: IdiomRecordExt, kw: string): boolean {
  if (!kw) return true;
  const k = kw.trim().toLowerCase();
  if (!k) return true;

  if (item.word.includes(kw)) return true;
  if (/^[a-z]+$/i.test(k) && item.pinyinAbbr && item.pinyinAbbr.includes(k)) return true;
  if (item.pinyin && item.pinyin.replace(/\s+/g, '').includes(k)) return true;
  if (item.originalContext.includes(kw)) return true;
  if (item.originalExplanation.includes(kw)) return true;

  // 编辑距离 ≤ 1 的模糊命中。仅 3-6 字关键词启用，避免在长词上 O(n*m) 退化。
  if (kw.length >= 3 && kw.length <= 6 && levenshtein(item.word, kw) <= 1) return true;

  return false;
}

export default function IdiomsPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [tierFilter, setTierFilter] = useState<TierFilter>('all');
  const [page, setPage] = useState(1);
  const [activeIdiom, setActiveIdiom] = useState<IdiomCardData | null>(null);

  const deferredSearch = useDeferredValue(search);
  const records = useIdiomStore((s) => s.records);

  const { counts, dueCount } = useMemo(() => {
    const today = getTodayString();
    const c: Record<IdiomStatus, number> = { unknown: 0, reviewing: 0, mastered: 0 };
    let due = 0;
    for (const r of Object.values(records)) {
      c[r.status] += 1;
      if (r.status !== 'mastered' && r.nextReviewDate <= today) due += 1;
    }
    return { counts: c, dueCount: due };
  }, [records]);

  const filtered = useMemo(() => {
    const today = getTodayString();
    return idioms.filter((it) => {
      if (tierFilter !== 'all' && it.frequencyTier !== tierFilter) return false;

      if (statusFilter !== 'all') {
        const r = records[it.word];
        if (statusFilter === 'due') {
          if (!r || r.status === 'mastered' || r.nextReviewDate > today) return false;
        } else if (r?.status !== statusFilter) {
          return false;
        }
      }

      return matchSearch(it, deferredSearch);
    });
  }, [deferredSearch, statusFilter, tierFilter, records]);

  const visible = useMemo(
    () => filtered.slice(0, page * PAGE_SIZE),
    [filtered, page]
  );

  const reset = (fn: () => void) => {
    fn();
    setPage(1);
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500/30 to-seal-500/30">
            <Library size={22} className="text-brand-300" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-white sm:text-2xl">
              成语词卡
            </h1>
            <p className="text-xs text-white/60 sm:text-sm">
              逻辑填空高频成语 · {idioms.length}词 · 点开看词义和真题运用
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 text-xs">
          <div className="rounded-lg bg-seal-500/15 px-3 py-2 text-seal-300">
            不会 {counts.unknown}
          </div>
          <div className="rounded-lg bg-warning/15 px-3 py-2 text-warning">
            复习 {counts.reviewing}
          </div>
          <div className="rounded-lg bg-success/15 px-3 py-2 text-success">
            掌握 {counts.mastered}
          </div>
          {dueCount > 0 && (
            <div className="rounded-lg bg-brand-500/15 px-3 py-2 text-brand-300">
              今日待复习 {dueCount}
            </div>
          )}
        </div>
      </div>

      <div className="relative mb-3">
        <Search
          size={16}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-white/40"
        />
        <input
          type="text"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          placeholder="搜索：词面/拼音首字母（如yyjr）/语境关键词/错字模糊"
          className="w-full rounded-xl border border-white/10 bg-white/5 py-2.5 pl-9 pr-4 text-sm text-white placeholder-white/30 outline-none transition-colors focus:border-brand-soft/50 focus:bg-white/10"
        />
      </div>
      <p className="mb-4 px-1 text-[11px] text-white/40">
        💡 输入英文字母查拼音首字母（yyjr→夜以继日）/中文词查词面或语境/错1字也能模糊命中
      </p>

      <div className="mb-5 space-y-2">
        <FilterRow
          filters={STATUS_FILTERS}
          active={statusFilter}
          onChange={(k) => reset(() => setStatusFilter(k))}
          accent="brand"
        />
        <FilterRow
          filters={TIER_FILTERS}
          active={tierFilter}
          onChange={(k) => reset(() => setTierFilter(k))}
          accent="info"
        />
      </div>

      {visible.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-white/10 py-20 text-center text-white/40">
          没找到符合条件的成语
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {visible.map((it) => (
              <IdiomCard key={it.word} idiom={it} onOpenDetail={setActiveIdiom} />
            ))}
          </div>

          {visible.length < filtered.length && (
            <div className="mt-6 flex justify-center">
              <button
                onClick={() => setPage((p) => p + 1)}
                className="rounded-xl border border-white/10 bg-white/5 px-5 py-2.5 text-sm text-white/70 transition-colors hover:bg-white/10"
              >
                加载更多（剩余 {filtered.length - visible.length}）
              </button>
            </div>
          )}

          <div className="mt-4 text-center text-xs text-white/30">
            显示 {visible.length} / {filtered.length} 条
          </div>
        </>
      )}

      <IdiomDetailDialog
        idiom={activeIdiom}
        open={!!activeIdiom}
        onClose={() => setActiveIdiom(null)}
      />
    </div>
  );
}

interface FilterRowProps<K extends string> {
  filters: { key: K; label: string }[];
  active: K;
  onChange: (key: K) => void;
  accent: 'brand' | 'info';
}

function FilterRow<K extends string>({ filters, active, onChange, accent }: FilterRowProps<K>) {
  return (
    <div className="flex flex-wrap gap-2">
      {filters.map((f) => (
        <button
          key={f.key}
          onClick={() => onChange(f.key)}
          className={cn(
            'rounded-full border px-3 py-1 text-xs font-medium transition-[transform,box-shadow,background-color,border-color]',
            active === f.key
              ? cn('text-white shadow-sm', ACCENT_CLASS[accent])
              : 'border-white/10 bg-white/5 text-white/60 hover:border-white/20 hover:bg-white/10'
          )}
        >
          {f.label}
        </button>
      ))}
    </div>
  );
}
