import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type WeatherType = 'sunny' | 'cloudy' | 'foggy' | 'rainy' | 'snowy' | 'stormy';

export interface WeatherData {
  temperature: number;
  weatherCode: number;
  weatherType: WeatherType;
  icon: string;
  description: string;
}

interface WeatherState {
  weather: WeatherData | null;
  lastFetchTime: number;
  locationPermission: 'granted' | 'denied' | 'pending';
  coords: { lat: string; lon: string } | null;
  setWeather: (data: WeatherData) => void;
  setLocationPermission: (perm: 'granted' | 'denied' | 'pending') => void;
  setCoords: (coords: { lat: string; lon: string }) => void;
  shouldRefetch: () => boolean;
}

export function getWeatherIcon(code: number): string {
  if (code === 0) return '☀️';
  if (code <= 3) return '⛅';
  if (code <= 49) return '🌫️';
  if (code <= 59) return '🌧️';
  if (code <= 69) return '🌨️';
  if (code <= 79) return '🌨️';
  if (code <= 84) return '🌧️';
  if (code <= 86) return '❄️';
  if (code <= 99) return '⛈️';
  return '🌡️';
}

export function getWeatherDesc(code: number): string {
  if (code === 0) return '晴';
  if (code <= 3) return '多云';
  if (code <= 49) return '雾';
  if (code <= 55) return '小雨';
  if (code <= 59) return '中雨';
  if (code <= 65) return '大雨';
  if (code <= 69) return '冻雨';
  if (code <= 75) return '雪';
  if (code <= 79) return '冰粒';
  if (code <= 82) return '阵雨';
  if (code <= 86) return '阵雪';
  if (code <= 99) return '雷暴';
  return '未知';
}

export function getWeatherType(code: number): WeatherType {
  if (code === 0) return 'sunny';
  if (code <= 3) return 'cloudy';
  if (code <= 49) return 'foggy';
  if (code <= 69) return 'rainy';
  if (code <= 79) return 'snowy';
  if (code <= 82) return 'rainy';
  if (code <= 86) return 'snowy';
  if (code <= 99) return 'stormy';
  return 'cloudy';
}

// Maps weather type to background image folder name
export function getBgGroup(weatherType: WeatherType, hour: number): string {
  if (hour >= 21 || hour < 5) return 'night';
  if (hour >= 17 && hour < 21) return 'dusk';
  switch (weatherType) {
    case 'sunny': return 'sunny';
    case 'cloudy':
    case 'foggy': return 'cloudy';
    case 'rainy':
    case 'stormy': return 'rain';
    case 'snowy': return 'snow';
    default: return 'cloudy';
  }
}

// Background image counts per group
export const BG_COUNTS: Record<string, number> = {
  sunny: 26,
  cloudy: 25,
  rain: 22,
  night: 20,
  dusk: 20,
  snow: 30,
};

export function getRandomBgUrl(group: string): string {
  const count = BG_COUNTS[group] || 20;
  const idx = Math.floor(Math.random() * count) + 1;
  const prefix = group === 'rain' ? 'rain' : group === 'night' ? 'night' : group === 'dusk' ? 'dusk' : group === 'snow' ? 'snow' : group === 'cloudy' ? 'cloudy' : 'sunny';
  return `/bg/${group}/${prefix}_${String(idx).padStart(2, '0')}.jpg`;
}

export const useWeatherStore = create<WeatherState>()(
  persist(
    (set, get) => ({
      weather: null,
      lastFetchTime: 0,
      locationPermission: 'pending',
      coords: null,
      setWeather: (data) => set({ weather: data, lastFetchTime: Date.now() }),
      setLocationPermission: (perm) => set({ locationPermission: perm }),
      setCoords: (coords) => set({ coords }),
      shouldRefetch: () => {
        const { lastFetchTime } = get();
        return Date.now() - lastFetchTime > 30 * 60 * 1000; // 30 min cache
      },
    }),
    { name: 'ace-weather' }
  )
);
