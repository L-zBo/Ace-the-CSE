'use client';

import { useMemo, useSyncExternalStore } from 'react';
import { ImageIcon, StickyNote, Trash2 } from 'lucide-react';
import { AnnotatableImage } from '@/components/questions/AnnotatableImage';
import {
  readImageNote,
  removeImageNote,
  readImageNoteIndexSnapshot,
  subscribeImageNoteChanges,
  type ImageNoteRecord,
} from '@/lib/imageNotes';

export default function ImageNotesPage() {
  const snapshot = useSyncExternalStore(
    subscribeImageNoteChanges,
    readImageNoteIndexSnapshot,
    () => '[]',
  );
  const notes = useMemo(() => {
    try {
      const parsed = JSON.parse(snapshot);
      return Array.isArray(parsed) ? (parsed as ImageNoteRecord[]) : [];
    } catch {
      return [];
    }
  }, [snapshot]);

  const handleRemove = (storageKey: string) => {
    removeImageNote(storageKey);
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500/25 to-brand-500/25">
            <StickyNote size={22} className="text-emerald-200" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-white sm:text-2xl">
              图注笔记
            </h1>
            <p className="text-xs text-white/60 sm:text-sm">
              本机已保存{notes.length}张题图批注，同一图片关联的小题会共用同一份笔记
            </p>
          </div>
        </div>
      </div>

      {notes.length === 0 ? (
        <div className="flex min-h-[360px] flex-col items-center justify-center rounded-2xl border border-dashed border-white/12 bg-white/[0.03] px-6 text-center">
          <ImageIcon size={34} className="mb-3 text-white/35" />
          <h2 className="mb-1 text-base font-semibold text-white/80">还没有保存过题图批注</h2>
          <p className="max-w-md text-sm leading-7 text-white/45">
            在题目页双击题图打开浮窗，画完后会自动保存；保存后会出现在这里。
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {notes.map((note) => {
            const overlay = readImageNote(note.storageKey);
            return (
              <article
                key={note.storageKey}
                className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] p-4 shadow-xl shadow-black/20 backdrop-blur-md"
              >
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h2 className="truncate text-sm font-semibold text-white">{note.alt}</h2>
                    <p className="mt-1 text-xs text-white/45">
                      {new Date(note.updatedAt).toLocaleString('zh-CN')}
                      {note.sourceKeys.length > 0 ? ` · 关联${note.sourceKeys.length}题` : ''}
                    </p>
                  </div>
                  <button
                    type="button"
                    title="删除这份批注"
                    aria-label="删除这份批注"
                    onClick={() => handleRemove(note.storageKey)}
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/5 text-white/60 transition-colors hover:bg-danger/15 hover:text-danger"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>

                <div className="relative mb-3 overflow-hidden rounded-xl bg-white">
                  <AnnotatableImage
                    src={note.src}
                    alt={note.alt}
                    sourceKey={note.sourceKeys[0]}
                    frameClassName="border-0 bg-transparent p-0"
                    className="max-h-[360px]"
                  />
                  {overlay && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={overlay}
                      alt=""
                      aria-hidden="true"
                      className="pointer-events-none absolute inset-0 h-full w-full object-contain"
                    />
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
