'use client';

/* eslint-disable react-hooks/set-state-in-effect */

import { useEffect, useState, useRef, useCallback } from 'react';
import type { CSSProperties } from 'react';
import Image from 'next/image';
import {
  useWeatherStore,
  getBgGroup,
  getRandomBgUrl,
} from '@/stores/weatherStore';

function seededRandom(seed: number) {
  const x = Math.sin(seed * 9301 + 49297) * 233280;
  return x - Math.floor(x);
}

function range(seed: number, min: number, max: number) {
  return min + seededRandom(seed) * (max - min);
}

function percent(seed: number, max = 100) {
  return `${range(seed, 0, max).toFixed(3)}%`;
}

function px(seed: number, min: number, max: number) {
  return `${range(seed, min, max).toFixed(2)}px`;
}

function seconds(seed: number, min: number, max: number) {
  return `${range(seed, min, max).toFixed(3)}s`;
}

function rainStyle(index: number): CSSProperties {
  const seed = index + 1;
  return {
    left: percent(seed * 11),
    top: '-3%',
    width: '1.5px',
    height: px(seed * 13, 12, 28),
    background: `linear-gradient(transparent, rgba(174,194,224,${range(seed * 17, 0.2, 0.6).toFixed(3)}))`,
    borderRadius: '0 0 2px 2px',
    animationDuration: seconds(seed * 19, 0.3, 0.8),
    animationDelay: seconds(seed * 23, 0, 3),
  };
}

function snowStyle(index: number): CSSProperties & { '--drift': string } {
  const seed = index + 1;
  const size = px(seed * 31, 3, 8);
  return {
    left: percent(seed * 29),
    top: '-3%',
    width: size,
    height: size,
    background: `rgba(255,255,255,${range(seed * 37, 0.25, 0.7).toFixed(3)})`,
    animationDuration: seconds(seed * 41, 3.5, 8.5),
    animationDelay: seconds(seed * 43, 0, 8),
    '--drift': px(seed * 47, -20, 20),
  };
}

function starStyle(index: number, seedBase: number): CSSProperties {
  const seed = seedBase + index + 1;
  const size = px(seed * 61, 1, 3);
  return {
    left: percent(seed * 53),
    top: percent(seed * 59, 60),
    width: size,
    height: size,
    background: 'rgba(255,255,255,0.7)',
    animationDuration: seconds(seed * 67, 2, 5),
    animationDelay: seconds(seed * 71, 0, 5),
  };
}

export default function BackgroundLayer() {
  const weather = useWeatherStore((s) => s.weather);
  const [bgUrl1, setBgUrl1] = useState('');
  const [bgUrl2, setBgUrl2] = useState('');
  const [activeSlot, setActiveSlot] = useState<1 | 2>(1);
  const [mounted, setMounted] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const currentGroupRef = useRef('');

  // SSR/CSR 守门：天气/星空效果依赖客户端时间和粒子样式，
  // 必须等客户端 mount 后再渲染，否则触发 hydration mismatch（星星位置错乱）。
  useEffect(() => {
    setMounted(true);
  }, []);

  const switchBg = useCallback((group: string) => {
    const url = getRandomBgUrl(group);
    setActiveSlot((prev) => {
      if (prev === 1) {
        setBgUrl2(url);
        return 2;
      } else {
        setBgUrl1(url);
        return 1;
      }
    });
  }, []);

  // Initialize + rotate every 5 min
  useEffect(() => {
    const hour = new Date().getHours();
    const weatherType = weather?.weatherType || 'sunny';
    const group = getBgGroup(weatherType, hour);

    if (group !== currentGroupRef.current) {
      currentGroupRef.current = group;
      // set initial bg
      const url = getRandomBgUrl(group);
      setBgUrl1(url);
      setActiveSlot(1);
    }

    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      switchBg(currentGroupRef.current);
    }, 5 * 60 * 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [weather?.weatherType, switchBg]);

  // Determine overlay based on weather + time
  // mounted 前固定中性背景，避免 SSR/CSR 不一致
  const hour = mounted ? new Date().getHours() : 12;
  const isNight = hour >= 21 || hour < 5;
  const isDusk = hour >= 17 && hour < 21;
  const isMorning = hour >= 5 && hour < 8;
  const weatherType = weather?.weatherType || 'sunny';

  let overlayBg = 'rgba(8, 12, 24, 0.65)';
  if (isNight) overlayBg = 'linear-gradient(180deg, rgba(5,5,20,0.88) 0%, rgba(10,10,30,0.82) 100%)';
  else if (isDusk) overlayBg = 'linear-gradient(180deg, rgba(60,30,10,0.55) 0%, rgba(20,15,40,0.68) 100%)';
  else if (isMorning) overlayBg = 'linear-gradient(180deg, rgba(40,30,15,0.45) 0%, rgba(8,12,24,0.60) 100%)';
  else if (weatherType === 'sunny') overlayBg = 'rgba(8, 12, 24, 0.55)';
  else if (weatherType === 'rainy' || weatherType === 'stormy') overlayBg = 'rgba(8, 12, 24, 0.78)';
  else if (weatherType === 'snowy') overlayBg = 'rgba(8, 15, 30, 0.72)';
  else overlayBg = 'rgba(8, 12, 24, 0.72)';

  return (
    <div className="fixed inset-0 -z-10" style={{ background: '#080c18' }}>
      {/* Background images with crossfade */}
      {bgUrl1 && (
        <Image
          src={bgUrl1}
          alt=""
          fill
          sizes="100vw"
          unoptimized
          className="absolute inset-0 h-full w-full object-cover transition-opacity duration-[2500ms]"
          style={{ opacity: activeSlot === 1 ? 1 : 0 }}
        />
      )}
      {bgUrl2 && (
        <Image
          src={bgUrl2}
          alt=""
          fill
          sizes="100vw"
          unoptimized
          className="absolute inset-0 h-full w-full object-cover transition-opacity duration-[2500ms]"
          style={{ opacity: activeSlot === 2 ? 1 : 0 }}
        />
      )}

      {/* Overlay */}
      <div
        className="absolute inset-0 transition-[background] duration-700"
        style={{ background: overlayBg }}
      />

      {/* Weather effects — mount 后才渲染，避免随机/时间引起 hydration mismatch */}
      {mounted && <WeatherEffects weatherCode={weather?.weatherCode ?? null} />}
    </div>
  );
}

function WeatherEffects({ weatherCode }: { weatherCode: number | null }) {
  if (weatherCode === null) {
    return <TimeBasedEffects />;
  }

  const hour = new Date().getHours();
  const isNight = hour >= 21 || hour < 5;
  const isDusk = hour >= 17 && hour < 21;
  const isMorning = hour >= 5 && hour < 8;
  const code = weatherCode;

  // Rain
  if (code >= 51 && code <= 69 || code >= 80 && code <= 82 || code >= 95) {
    const drops = code >= 95 ? 80 : code >= 61 ? 60 : code >= 80 ? 50 : 25;
    const hasLightning = code >= 95;
    return (
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {Array.from({ length: drops }).map((_, i) => (
          <div
            key={i}
            className="absolute animate-rainfall"
            style={rainStyle(i)}
          />
        ))}
        {hasLightning && (
          <div className="absolute inset-0 animate-lightning" />
        )}
      </div>
    );
  }

  // Snow
  if (code >= 71 && code <= 79 || code >= 83 && code <= 86) {
    const flakes = code >= 83 ? 50 : code >= 75 ? 55 : 25;
    return (
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {Array.from({ length: flakes }).map((_, i) => (
          <div
            key={i}
            className="absolute animate-snowfall rounded-full"
            style={snowStyle(i)}
          />
        ))}
      </div>
    );
  }

  // Night stars
  if (isNight) {
    const starCount = code === 0 ? 30 : code <= 3 ? 15 : 8;
    return (
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {Array.from({ length: starCount }).map((_, i) => (
          <div
            key={i}
            className="absolute animate-starTwinkle rounded-full"
            style={starStyle(i, 1000)}
          />
        ))}
      </div>
    );
  }

  // Dusk glow
  if (isDusk) {
    return (
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div
          className="absolute bottom-0 left-0 right-0 animate-duskPulse"
          style={{
            height: '60%',
            background: 'linear-gradient(0deg, rgba(255,140,50,0.12) 0%, rgba(255,100,50,0.06) 30%, transparent 100%)',
          }}
        >
          <div
            className="absolute animate-sunPulse rounded-full"
            style={{
              bottom: '10%',
              left: '50%',
              transform: 'translateX(-50%)',
              width: '300px',
              height: '300px',
              background: 'radial-gradient(circle, rgba(255,180,80,0.15) 0%, rgba(255,120,50,0.06) 40%, transparent 70%)',
            }}
          />
        </div>
      </div>
    );
  }

  // Morning glow
  if (isMorning && code <= 3) {
    return (
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div
          className="absolute animate-morningGlow"
          style={{
            top: 0,
            right: 0,
            width: '60%',
            height: '70%',
            background: 'radial-gradient(ellipse at top right, rgba(255,220,150,0.12) 0%, rgba(255,180,100,0.05) 40%, transparent 70%)',
          }}
        />
      </div>
    );
  }

  // Sunny
  if (code === 0) {
    const noonFactor = hour >= 10 && hour <= 14 ? 1.2 : 0.8;
    const size = Math.round(300 * noonFactor);
    return (
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div
          className="absolute animate-sunPulse rounded-full"
          style={{
            top: '-60px',
            right: '-60px',
            width: `${size}px`,
            height: `${size}px`,
            background: `radial-gradient(circle, rgba(255,220,100,${(0.12 * noonFactor).toFixed(3)}) 0%, rgba(255,180,50,${(0.04 * noonFactor).toFixed(3)}) 50%, transparent 70%)`,
          }}
        />
      </div>
    );
  }

  return null;
}

function TimeBasedEffects() {
  const hour = new Date().getHours();
  const isNight = hour >= 21 || hour < 5;
  const isDusk = hour >= 17 && hour < 21;

  if (isNight) {
    return (
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {Array.from({ length: 20 }).map((_, i) => (
          <div
            key={i}
            className="absolute animate-starTwinkle rounded-full"
            style={starStyle(i, 2000)}
          />
        ))}
      </div>
    );
  }

  if (isDusk) {
    return (
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div
          className="absolute bottom-0 left-0 right-0 animate-duskPulse"
          style={{
            height: '60%',
            background: 'linear-gradient(0deg, rgba(255,140,50,0.12) 0%, rgba(255,100,50,0.06) 30%, transparent 100%)',
          }}
        />
      </div>
    );
  }

  return null;
}
