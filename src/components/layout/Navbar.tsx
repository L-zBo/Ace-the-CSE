'use client';

import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import {
  BookOpen,
  ClipboardCheck,
  BarChart3,
  RotateCcw,
  Brain,
  CalendarCheck,
  Newspaper,
  Library,
  StickyNote,
  Menu,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import WeatherWidget from '@/components/weather/WeatherWidget';

const navItems = [
  { href: '/practice', label: '刷题练习', icon: BookOpen },
  { href: '/exam', label: '模拟考试', icon: ClipboardCheck },
  { href: '/stats', label: '统计分析', icon: BarChart3 },
  { href: '/review', label: '错题本', icon: RotateCcw },
  { href: '/knowledge', label: '知识体系', icon: Brain },
  { href: '/idioms', label: '成语词卡', icon: Library },
  { href: '/image-notes', label: '图注笔记', icon: StickyNote },
  { href: '/plan', label: '学习计划', icon: CalendarCheck },
  { href: '/current-affairs', label: '时事热点', icon: Newspaper },
];

export default function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  // 计算"刷题练习"的实际跳转目标：
  // - 在 /practice/{source} 子页 → 保持当前页（不跳走）
  // - 在 /practice/{questionId} 题详情 → 回到对应 source 子页（按 id 前缀解析）
  // - 其他 → 跳到 /practice 综合筛选页
  const resolvePracticeHref = (path: string): string => {
    if (
      path === '/practice/national' ||
      path === '/practice/provincial' ||
      path === '/practice/institution'
    ) {
      return path;
    }
    const m = path.match(/^\/practice\/(national|provincial|institution)-/);
    if (m) return `/practice/${m[1]}`;
    return '/practice';
  };
  const practiceHref = resolvePracticeHref(pathname);

  const resolvedNavItems = navItems.map((it) =>
    it.href === '/practice' ? { ...it, href: practiceHref } : it
  );

  return (
    <>
      <nav className="sticky top-0 z-50 border-b border-white/10 bg-black/30 backdrop-blur-xl" aria-label="主导航">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          {/* Logo */}
          <Link href="/" aria-label="返回首页 — Ace the CSE" className="flex items-center gap-2.5">
            <Image
              src="/favicon.ico"
              alt="博"
              width={36}
              height={36}
              className="rounded-lg"
            />
            <span translate="no" className="hidden text-lg font-semibold text-white/90 sm:block">
              Ace the CSE
            </span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden items-center gap-1 md:flex">
            {resolvedNavItems.map((item) => {
              const Icon = item.icon;
              const isPractice = item.label === '刷题练习';
              const isActive = isPractice
                ? pathname === '/practice' || pathname.startsWith('/practice/')
                : pathname === item.href || pathname.startsWith(item.href + '/');
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-white/15 text-white'
                      : 'text-white/60 hover:bg-white/10 hover:text-white/90'
                  )}
                >
                  <Icon size={16} />
                  {item.label}
                </Link>
              );
            })}
          </div>

          {/* Weather + mobile hamburger */}
          <div className="flex items-center gap-3">
            <div className="hidden sm:block">
              <WeatherWidget />
            </div>
            <button
              className="flex h-9 w-9 items-center justify-center rounded-lg text-white/70 hover:bg-white/10 md:hidden"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label={mobileOpen ? '关闭菜单' : '打开菜单'}
              aria-expanded={mobileOpen}
              aria-controls="mobile-nav-menu"
            >
              {mobileOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div
            id="mobile-nav-menu"
            className="border-t border-white/10 bg-black/40 px-4 pb-4 backdrop-blur-xl md:hidden"
          >
            {/* Mobile weather */}
            <div className="px-3 py-2">
              <WeatherWidget />
            </div>
            {resolvedNavItems.map((item) => {
              const Icon = item.icon;
              const isPractice = item.label === '刷题练习';
              const isActive = isPractice
                ? pathname === '/practice' || pathname.startsWith('/practice/')
                : pathname === item.href || pathname.startsWith(item.href + '/');
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={cn(
                    'flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-white/15 text-white'
                      : 'text-white/60 hover:bg-white/10 hover:text-white/90'
                  )}
                >
                  <Icon size={18} />
                  {item.label}
                </Link>
              );
            })}
          </div>
        )}
      </nav>

      {/* Mobile bottom tab bar */}
      <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-white/10 bg-black/40 backdrop-blur-xl md:hidden" aria-label="底部导航">
        <div className="flex items-center justify-around py-1">
          {resolvedNavItems.slice(0, 5).map((item) => {
            const Icon = item.icon;
            const isPractice = item.label === '刷题练习';
            const isActive = isPractice
              ? pathname === '/practice' || pathname.startsWith('/practice/')
              : pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex flex-col items-center gap-0.5 px-2 py-1.5 text-xs transition-colors',
                  isActive ? 'text-white' : 'text-white/50'
                )}
              >
                <Icon size={18} aria-hidden="true" />
                <span>{item.label.slice(0, 2)}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}
