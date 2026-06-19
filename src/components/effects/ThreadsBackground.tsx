'use client';

import { useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';

/**
 * ThreadsBackground — 卷面"自习室"氛围背景（D-18a P2b-3）
 *
 * 灵感参考 react-bits Threads。canvas 渲染若干条柔和波动曲线，
 * 模拟书桌台灯下浮动的光纹。比天气动效更安静，给长时间备考用户
 * 一个低干扰背景选项。
 *
 * 注：默认 BackgroundLayer 仍走天气系统，本组件作为「可选 mode」
 * 在未来 Navbar ThemeToggle 接入时启用。
 *
 * 用法：
 *   <ThreadsBackground threadCount={6} hue={214} />
 */
interface ThreadsBackgroundProps {
  className?: string;
  /** 线条数量，默认 5 */
  threadCount?: number;
  /** 主色调（HSL hue），默认 214（墨蓝）*/
  hue?: number;
  /** 不透明度（0-1），默认 0.06 */
  opacity?: number;
}

export function ThreadsBackground({
  className,
  threadCount = 5,
  hue = 214,
  opacity = 0.06,
}: ThreadsBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    let rafId = 0;
    let phase = 0;
    let width = 0;
    let height = 0;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = canvas.clientWidth;
      height = canvas.clientHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      for (let i = 0; i < threadCount; i++) {
        const offset = (i / threadCount) * height;
        const amplitude = 24 + (i % 3) * 8;
        const freq = 0.005 + i * 0.0015;
        const speed = reducedMotion ? 0 : 0.4 + i * 0.05;

        ctx.beginPath();
        ctx.moveTo(0, offset);
        for (let x = 0; x <= width; x += 6) {
          const y = offset + Math.sin(x * freq + phase * speed) * amplitude;
          ctx.lineTo(x, y);
        }
        const lightness = 60 - i * 4;
        ctx.strokeStyle = `hsla(${hue}, 55%, ${lightness}%, ${opacity})`;
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }
      phase += 0.02;
      if (!reducedMotion) {
        rafId = requestAnimationFrame(render);
      }
    };

    resize();
    render();
    window.addEventListener('resize', resize);
    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(rafId);
    };
  }, [threadCount, hue, opacity]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={cn('pointer-events-none absolute inset-0 h-full w-full', className)}
    />
  );
}
