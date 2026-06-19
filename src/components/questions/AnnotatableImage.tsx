'use client';

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useSyncExternalStore,
  useState,
  type ReactNode,
} from 'react';
import { createPortal } from 'react-dom';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Eraser,
  Maximize2,
  Minus,
  Pencil,
  Plus,
  Save,
  StickyNote,
  Trash2,
  Undo2,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  getImageNoteStorageKey,
  readImageNote,
  removeImageNote,
  readImageNoteSnapshot,
  upsertImageNoteIndex,
} from '@/lib/imageNotes';

type DrawTool = 'pen' | 'eraser';

interface AnnotatableImageProps {
  src: string;
  alt: string;
  className?: string;
  frameClassName?: string;
  sourceKey?: string;
}

const COLORS = ['#ef4444', '#f59e0b', '#22c55e', '#38bdf8', '#111827'];
const BRUSH_SIZES = [3, 5, 8, 12];

export function AnnotatableImage({
  src,
  alt,
  className,
  frameClassName,
  sourceKey,
}: AnnotatableImageProps) {
  const [open, setOpen] = useState(false);
  const [loadError, setLoadError] = useState(false);
  const storageKey = useMemo(() => getImageNoteStorageKey(src), [src]);
  const noteSnapshot = useSyncExternalStore(
    subscribeImageNoteStore,
    () => readImageNoteSnapshot(storageKey),
    () => '',
  );
  const hasSavedNote = !!noteSnapshot;

  if (loadError) {
    return (
      <div
        role="status"
        className={cn(
          'rounded-xl border border-dashed border-border px-4 py-6 text-center text-sm text-foreground-muted',
          frameClassName,
        )}
      >
        本题为图形/数列/资料分析题，原PDF图片缺失，暂无法显示。
      </div>
    );
  }

  return (
    <>
      <div
        role="button"
        tabIndex={0}
        title="双击打开浮窗批注"
        aria-label={`${alt}，双击打开浮窗批注`}
        className={cn(
          'group relative rounded-xl border border-border bg-white/[0.03] p-3 backdrop-blur-sm outline-none transition-colors hover:border-primary/35 focus-visible:ring-2 focus-visible:ring-primary/60',
          frameClassName,
        )}
        onDoubleClick={() => setOpen(true)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setOpen(true);
          }
        }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={src}
          alt={alt}
          loading="lazy"
          decoding="async"
          className={cn('mx-auto h-auto max-h-[70vh] max-w-full rounded-lg object-contain', className)}
          onError={() => setLoadError(true)}
        />

        <div className="absolute right-5 top-5 flex gap-2">
          {hasSavedNote && (
            <span className="inline-flex h-9 items-center gap-1 rounded-full border border-emerald-300/25 bg-emerald-500/20 px-3 text-xs font-medium text-emerald-100 shadow-lg backdrop-blur">
              <StickyNote size={14} />
              已保存批注
            </span>
          )}
          <button
            type="button"
            title="打开批注浮窗"
            aria-label="打开批注浮窗"
            onClick={(e) => {
              e.stopPropagation();
              setOpen(true);
            }}
            className="flex h-9 w-9 items-center justify-center rounded-full border border-white/15 bg-black/60 text-white shadow-lg backdrop-blur transition-colors hover:bg-black/75 focus:outline-none focus:ring-2 focus:ring-primary/70"
          >
            <Maximize2 size={17} />
          </button>
        </div>
      </div>

      <ImageNoteDialog
        open={open}
        src={src}
        alt={alt}
        storageKey={storageKey}
        sourceKey={sourceKey}
        onClose={() => setOpen(false)}
        onSaved={() => {}}
        onCleared={() => {}}
      />
    </>
  );
}

function subscribeImageNoteStore(callback: () => void) {
  return (() => {
    if (typeof window === 'undefined') return () => {};
    window.addEventListener('storage', callback);
    window.addEventListener('ace-image-notes-change', callback);
    return () => {
      window.removeEventListener('storage', callback);
      window.removeEventListener('ace-image-notes-change', callback);
    };
  })();
}

interface ImageNoteDialogProps {
  open: boolean;
  src: string;
  alt: string;
  storageKey: string;
  sourceKey?: string;
  onClose: () => void;
  onSaved: () => void;
  onCleared: () => void;
}

function ImageNoteDialog({
  open,
  src,
  alt,
  storageKey,
  sourceKey,
  onClose,
  onSaved,
  onCleared,
}: ImageNoteDialogProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const drawingRef = useRef(false);
  const lastPointRef = useRef<{ x: number; y: number } | null>(null);

  const [tool, setTool] = useState<DrawTool>('pen');
  const [color, setColor] = useState(COLORS[0]);
  const [brushSize, setBrushSize] = useState(5);
  const [zoom, setZoom] = useState(1);
  const [naturalSize, setNaturalSize] = useState({ width: 0, height: 0 });
  const [baseScale, setBaseScale] = useState(1);
  const [undoStack, setUndoStack] = useState<string[]>([]);
  const [imageLoadFailed, setImageLoadFailed] = useState(false);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    const frame = window.requestAnimationFrame(() => {
      setZoom(1);
      setBaseScale(1);
      setUndoStack([]);
      setNaturalSize({ width: 0, height: 0 });
      setImageLoadFailed(false);
      setSavedAt(null);
      drawingRef.current = false;
      lastPointRef.current = null;
    });
    const image = new Image();
    image.onload = () => {
      setNaturalSize({
        width: image.naturalWidth,
        height: image.naturalHeight,
      });
    };
    image.onerror = () => {
      setImageLoadFailed(true);
    };
    image.src = src;
    return () => {
      window.cancelAnimationFrame(frame);
    };
  }, [open, src]);

  const displaySize = useMemo(() => {
    if (!naturalSize.width || !naturalSize.height) return { width: 0, height: 0 };
    return {
      width: naturalSize.width * baseScale * zoom,
      height: naturalSize.height * baseScale * zoom,
    };
  }, [baseScale, naturalSize, zoom]);

  const saveIndex = useCallback(() => {
    upsertImageNoteIndex({
      storageKey,
      src,
      alt,
      sourceKeys: sourceKey ? [sourceKey] : [],
    });
  }, [alt, sourceKey, src, storageKey]);

  const loadSavedNote = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const saved = readImageNote(storageKey);
    if (!saved) return;
    const note = new Image();
    note.onload = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(note, 0, 0, canvas.width, canvas.height);
    };
    note.src = saved;
  }, [storageKey]);

  const persistNote = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    try {
      window.localStorage.setItem(storageKey, canvas.toDataURL('image/png'));
      saveIndex();
      setSavedAt(new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }));
      onSaved();
    } catch {
      // 批注过大或浏览器禁用存储时不阻断作答。
    }
  }, [onSaved, saveIndex, storageKey]);

  const restoreSnapshot = useCallback(
    (dataUrl: string) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      const snapshot = new Image();
      snapshot.onload = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(snapshot, 0, 0, canvas.width, canvas.height);
        persistNote();
      };
      snapshot.src = dataUrl;
    },
    [persistNote],
  );

  const pushUndo = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const snapshot = canvas.toDataURL('image/png');
    setUndoStack((prev) => [...prev.slice(-19), snapshot]);
  }, []);

  const resizeToViewport = useCallback(() => {
    if (!naturalSize.width || !naturalSize.height) return;
    const maxWidth = Math.max(300, Math.min(window.innerWidth - 48, 980));
    const maxHeight = Math.max(260, window.innerHeight - 220);
    setBaseScale(Math.min(1, maxWidth / naturalSize.width, maxHeight / naturalSize.height));
  }, [naturalSize]);

  const undo = useCallback(() => {
    setUndoStack((prev) => {
      const last = prev.at(-1);
      if (!last) return prev;
      restoreSnapshot(last);
      return prev.slice(0, -1);
    });
  }, [restoreSnapshot]);

  useEffect(() => {
    if (!open) return;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') {
        e.preventDefault();
        undo();
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => {
      document.body.style.overflow = prevOverflow;
      window.removeEventListener('keydown', handleKey);
    };
  }, [onClose, undo, open]);

  useEffect(() => {
    if (!open) return;
    window.addEventListener('resize', resizeToViewport);
    const frame = window.requestAnimationFrame(() => resizeToViewport());
    return () => {
      window.cancelAnimationFrame(frame);
      window.removeEventListener('resize', resizeToViewport);
    };
  }, [open, resizeToViewport]);

  useEffect(() => {
    if (!open || !naturalSize.width || !naturalSize.height) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.width = naturalSize.width;
    canvas.height = naturalSize.height;
    loadSavedNote();
  }, [loadSavedNote, naturalSize, open]);

  function pointFromEvent(e: React.PointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    return {
      x: ((e.clientX - rect.left) / rect.width) * canvas.width,
      y: ((e.clientY - rect.top) / rect.height) * canvas.height,
    };
  }

  function drawTo(point: { x: number; y: number }) {
    const canvas = canvasRef.current;
    const last = lastPointRef.current;
    if (!canvas || !last) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const visualScale = displaySize.width ? displaySize.width / canvas.width : 1;
    ctx.save();
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.lineWidth = Math.max(1, brushSize / visualScale);
    ctx.strokeStyle = color;
    ctx.globalCompositeOperation = tool === 'eraser' ? 'destination-out' : 'source-over';
    ctx.beginPath();
    ctx.moveTo(last.x, last.y);
    ctx.lineTo(point.x, point.y);
    ctx.stroke();
    ctx.restore();
    lastPointRef.current = point;
  }

  function clearNote() {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    pushUndo();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    removeImageNote(storageKey);
    setSavedAt(null);
    onCleared();
  }

  if (!open || typeof document === 'undefined') return null;

  return createPortal(
    <AnimatePresence>
      <div
        role="dialog"
        aria-modal="true"
        aria-label="题图批注"
        className="fixed inset-0 z-[100] flex items-center justify-center bg-black/55 p-3 text-white backdrop-blur-sm sm:p-6"
      >
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0"
          onClick={onClose}
        />

        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 16 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: 10 }}
          transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="relative z-10 flex max-h-[92vh] w-full max-w-6xl flex-col overflow-hidden rounded-2xl border border-white/12 bg-slate-950 shadow-2xl shadow-black/60"
        >
          <div className="flex flex-col gap-3 border-b border-white/10 bg-slate-950/95 px-4 py-3 sm:px-5 lg:flex-row lg:items-center lg:justify-between">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <StickyNote size={16} className="shrink-0 text-primary" />
                <div className="truncate text-sm font-semibold text-white">{alt}</div>
              </div>
              <div className="mt-1 text-xs text-white/45">
                批注按图片单独保存，同一张图关联多个小题时会共用这一份笔记
                {savedAt ? ` · 已保存${savedAt}` : ''}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <IconToggle active={tool === 'pen'} label="画笔" onClick={() => setTool('pen')}>
                <Pencil size={17} />
              </IconToggle>
              <IconToggle active={tool === 'eraser'} label="橡皮" onClick={() => setTool('eraser')}>
                <Eraser size={17} />
              </IconToggle>

              <div className="flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-1.5 py-1">
                {COLORS.map((c) => (
                  <button
                    key={c}
                    type="button"
                    aria-label={`颜色${c}`}
                    title={`颜色${c}`}
                    onClick={() => {
                      setColor(c);
                      setTool('pen');
                    }}
                    className={cn(
                      'h-6 w-6 rounded-full border transition-transform',
                      color === c
                        ? 'scale-110 border-white ring-2 ring-white/50'
                        : 'border-white/25 hover:scale-105',
                    )}
                    style={{ backgroundColor: c }}
                  />
                ))}
              </div>

              <div className="flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-1.5 py-1">
                {BRUSH_SIZES.map((size) => (
                  <button
                    key={size}
                    type="button"
                    aria-label={`线宽${size}`}
                    title={`线宽${size}`}
                    onClick={() => setBrushSize(size)}
                    className={cn(
                      'flex h-6 w-6 items-center justify-center rounded-full transition-colors',
                      brushSize === size ? 'bg-white text-slate-950' : 'text-white/70 hover:bg-white/10',
                    )}
                  >
                    <span
                      className="rounded-full bg-current"
                      style={{ width: size + 2, height: size + 2 }}
                    />
                  </button>
                ))}
              </div>

              <IconButton label="缩小" onClick={() => setZoom((z) => Math.max(0.55, z - 0.15))}>
                <Minus size={17} />
              </IconButton>
              <span className="w-12 text-center text-xs tabular-nums text-white/60">
                {Math.round(zoom * 100)}%
              </span>
              <IconButton label="放大" onClick={() => setZoom((z) => Math.min(3, z + 0.15))}>
                <Plus size={17} />
              </IconButton>
              <IconButton label="保存" onClick={persistNote}>
                <Save size={17} />
              </IconButton>
              <IconButton label="撤销" onClick={undo} disabled={!undoStack.length}>
                <Undo2 size={17} />
              </IconButton>
              <IconButton label="清空批注" onClick={clearNote}>
                <Trash2 size={17} />
              </IconButton>
              <IconButton label="关闭" onClick={onClose}>
                <X size={18} />
              </IconButton>
            </div>
          </div>

          <div className="flex-1 overflow-auto bg-slate-900/65 p-3 sm:p-5">
            <div
              className="mx-auto rounded-xl bg-white shadow-2xl shadow-black/40"
              style={{
                width: displaySize.width || 'min(100%, 720px)',
                height: displaySize.height || undefined,
                minHeight: displaySize.height ? undefined : 360,
              }}
            >
              {imageLoadFailed ? (
                <div className="flex h-full min-h-[360px] items-center justify-center rounded-xl text-sm text-slate-500">
                  题图加载失败
                </div>
              ) : displaySize.width && displaySize.height ? (
                <div className="relative h-full w-full touch-none select-none">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={src}
                    alt={alt}
                    className="block h-full w-full rounded-xl object-contain"
                    draggable={false}
                  />
                  <canvas
                    ref={canvasRef}
                    className="absolute inset-0 h-full w-full rounded-xl"
                    onPointerDown={(e) => {
                      e.currentTarget.setPointerCapture(e.pointerId);
                      pushUndo();
                      drawingRef.current = true;
                      lastPointRef.current = pointFromEvent(e);
                    }}
                    onPointerMove={(e) => {
                      if (!drawingRef.current) return;
                      const point = pointFromEvent(e);
                      if (point) drawTo(point);
                    }}
                    onPointerUp={(e) => {
                      e.currentTarget.releasePointerCapture(e.pointerId);
                      drawingRef.current = false;
                      lastPointRef.current = null;
                      persistNote();
                    }}
                    onPointerCancel={() => {
                      drawingRef.current = false;
                      lastPointRef.current = null;
                      persistNote();
                    }}
                  />
                </div>
              ) : (
                <div className="flex h-full min-h-[360px] items-center justify-center rounded-xl text-sm text-slate-500">
                  正在加载题图...
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>,
    document.body,
  );
}

interface IconButtonProps {
  label: string;
  disabled?: boolean;
  onClick: () => void;
  children: ReactNode;
}

function IconButton({ label, disabled, onClick, children }: IconButtonProps) {
  return (
    <button
      type="button"
      title={label}
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      className="flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-white/5 text-white transition-colors hover:bg-white/12 disabled:cursor-not-allowed disabled:opacity-35"
    >
      {children}
    </button>
  );
}

function IconToggle({ label, active, onClick, children }: IconButtonProps & { active: boolean }) {
  return (
    <button
      type="button"
      title={label}
      aria-label={label}
      onClick={onClick}
      className={cn(
        'flex h-9 w-9 items-center justify-center rounded-full border transition-colors',
        active
          ? 'border-primary/70 bg-primary text-white shadow-md shadow-primary/25'
          : 'border-white/10 bg-white/5 text-white hover:bg-white/12',
      )}
    >
      {children}
    </button>
  );
}
