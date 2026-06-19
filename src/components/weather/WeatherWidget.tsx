'use client';

import { useEffect, useCallback } from 'react';
import {
  useWeatherStore,
  getWeatherIcon,
  getWeatherDesc,
  getWeatherType,
} from '@/stores/weatherStore';

export default function WeatherWidget() {
  const {
    weather,
    locationPermission,
    coords,
    setWeather,
    setLocationPermission,
    setCoords,
    shouldRefetch,
  } = useWeatherStore();

  const fetchFromCoords = useCallback(
    async (lat: string, lon: string) => {
      try {
        const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,weather_code&timezone=auto`;
        const res = await fetch(url);
        const data = await res.json();
        if (data.current) {
          const code = data.current.weather_code as number;
          setWeather({
            temperature: Math.round(data.current.temperature_2m),
            weatherCode: code,
            weatherType: getWeatherType(code),
            icon: getWeatherIcon(code),
            description: getWeatherDesc(code),
          });
        }
      } catch {
        // silently fail
      }
    },
    [setWeather]
  );

  const doFetch = useCallback(() => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude.toFixed(2);
        const lon = pos.coords.longitude.toFixed(2);
        setCoords({ lat, lon });
        fetchFromCoords(lat, lon);
      },
      () => {
        // fallback to cached coords
        if (coords) {
          fetchFromCoords(coords.lat, coords.lon);
        }
      },
      { timeout: 5000 }
    );
  }, [coords, fetchFromCoords, setCoords]);

  useEffect(() => {
    if (locationPermission !== 'granted') return;
    if (!shouldRefetch() && weather) return;
    doFetch();
  }, [locationPermission, shouldRefetch, weather, doFetch]);

  if (locationPermission === 'pending') {
    return (
      <div className="flex items-center gap-2">
        <button
          onClick={() => {
            setLocationPermission('granted');
            doFetch();
          }}
          className="rounded-full border border-border bg-card/80 px-3 py-1 text-xs text-muted backdrop-blur transition-colors hover:border-primary/30 hover:text-foreground"
        >
          🌤️ 开启天气
        </button>
      </div>
    );
  }

  if (locationPermission === 'denied' || !weather) return null;

  return (
    <div className="flex items-center gap-1.5 text-sm">
      <span className="text-base">{weather.icon}</span>
      <span className="text-muted">
        {weather.description} {weather.temperature}°C
      </span>
    </div>
  );
}
