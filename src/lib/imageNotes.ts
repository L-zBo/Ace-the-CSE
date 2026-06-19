export interface ImageNoteRecord {
  storageKey: string;
  src: string;
  alt: string;
  sourceKeys: string[];
  updatedAt: string;
}

const NOTE_PREFIX = 'ace-question-image-note:';
const INDEX_KEY = 'ace-question-image-notes:index';
export const IMAGE_NOTES_CHANGE_EVENT = 'ace-image-notes-change';

function canUseStorage() {
  return typeof window !== 'undefined' && !!window.localStorage;
}

export function getImageNoteStorageKey(src: string) {
  return `${NOTE_PREFIX}${src}`;
}

export function readImageNote(storageKey: string): string | null {
  if (!canUseStorage()) return null;
  try {
    return window.localStorage.getItem(storageKey);
  } catch {
    return null;
  }
}

export function readImageNoteSnapshot(storageKey: string): string {
  return readImageNote(storageKey) ?? '';
}

export function readImageNoteIndexSnapshot(): string {
  if (!canUseStorage()) return '[]';
  try {
    return window.localStorage.getItem(INDEX_KEY) ?? '[]';
  } catch {
    return '[]';
  }
}

export function readImageNoteIndex(): ImageNoteRecord[] {
  try {
    const raw = readImageNoteIndexSnapshot();
    const parsed = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((item): item is ImageNoteRecord => {
        return (
          !!item &&
          typeof item.storageKey === 'string' &&
          typeof item.src === 'string' &&
          typeof item.alt === 'string' &&
          Array.isArray(item.sourceKeys) &&
          typeof item.updatedAt === 'string'
        );
      })
      .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
  } catch {
    return [];
  }
}

export function upsertImageNoteIndex(record: Omit<ImageNoteRecord, 'updatedAt'>) {
  if (!canUseStorage()) return;
  const current = readImageNoteIndex();
  const existing = current.find((item) => item.storageKey === record.storageKey);
  const sourceKeys = Array.from(
    new Set([...(existing?.sourceKeys ?? []), ...record.sourceKeys].filter(Boolean)),
  );
  const nextRecord: ImageNoteRecord = {
    ...record,
    sourceKeys,
    updatedAt: new Date().toISOString(),
  };
  const next = [
    nextRecord,
    ...current.filter((item) => item.storageKey !== record.storageKey),
  ];
  try {
    window.localStorage.setItem(INDEX_KEY, JSON.stringify(next));
    window.dispatchEvent(new Event(IMAGE_NOTES_CHANGE_EVENT));
  } catch {
    // 本地存储不可用时不阻断用户作答。
  }
}

export function removeImageNote(storageKey: string) {
  if (!canUseStorage()) return;
  try {
    window.localStorage.removeItem(storageKey);
    const next = readImageNoteIndex().filter((item) => item.storageKey !== storageKey);
    window.localStorage.setItem(INDEX_KEY, JSON.stringify(next));
    window.dispatchEvent(new Event(IMAGE_NOTES_CHANGE_EVENT));
  } catch {
    // ignore
  }
}

export function subscribeImageNoteChanges(callback: () => void) {
  if (typeof window === 'undefined') return () => {};
  window.addEventListener('storage', callback);
  window.addEventListener(IMAGE_NOTES_CHANGE_EVENT, callback);
  return () => {
    window.removeEventListener('storage', callback);
    window.removeEventListener(IMAGE_NOTES_CHANGE_EVENT, callback);
  };
}
