import type { Metadata, Viewport } from 'next';
import { Geist, Geist_Mono, Libre_Bodoni, Public_Sans } from 'next/font/google';
import Navbar from '@/components/layout/Navbar';
import BackgroundLayer from '@/components/weather/BackgroundLayer';
import './globals.css';

const geistSans = Geist({
  subsets: ['latin'],
  variable: '--font-geist-sans',
  display: 'swap',
});

const geistMono = Geist_Mono({
  subsets: ['latin'],
  variable: '--font-geist-mono',
  display: 'swap',
});

// D-18a P2b-1 字体 4 阶配对：
// - 中文 display：LXGW WenKai（CDN，<head> link）
// - 英文/数字 display：Libre Bodoni（magazine/editorial，hero/标题/页码）
// - 英文 body：Public Sans（搭配 Libre Bodoni，正文）
// - tabular numbers：Geist Mono（已用）
const libreBodoni = Libre_Bodoni({
  subsets: ['latin'],
  variable: '--font-libre-bodoni',
  display: 'swap',
  weight: ['400', '500', '700'],
});

const publicSans = Public_Sans({
  subsets: ['latin'],
  variable: '--font-public-sans',
  display: 'swap',
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000'),
  title: 'Ace the CSE — 公务员考试学习平台',
  description:
    '全功能公务员考试学习平台，涵盖行测、申论历年真题，支持国考、省考、事业编等多种考试类型。',
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: 'any' },
      { url: '/logo.svg', type: 'image/svg+xml' },
    ],
    apple: '/logo.svg',
  },
  manifest: '/manifest.webmanifest',
  openGraph: {
    title: 'Ace the CSE — 公务员考试学习平台',
    description: '行测 · 申论 · 历年真题，国考 / 省考 / 事业编联考',
    locale: 'zh_CN',
    type: 'website',
    images: [{ url: '/og-image.svg', width: 1200, height: 630, alt: 'Ace the CSE' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Ace the CSE — 公务员考试学习平台',
    description: '行测 · 申论 · 历年真题',
    images: ['/og-image.svg'],
  },
};

export const viewport: Viewport = {
  colorScheme: 'dark',
  themeColor: '#1e3a5f',
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="zh-CN"
      className={`h-full antialiased ${geistSans.variable} ${geistMono.variable} ${libreBodoni.variable} ${publicSans.variable}`}
    >
      <head>
        <link rel="preconnect" href="https://cdn.jsdelivr.net" crossOrigin="anonymous" />
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/lxgw-wenkai-webfont@1.7.0/style.css"
        />
      </head>
      <body className="min-h-full flex flex-col bg-transparent text-white">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-brand focus:px-4 focus:py-2 focus:text-white"
        >
          跳到主要内容
        </a>
        <BackgroundLayer />
        <Navbar />
        <main id="main-content" className="relative z-10 flex-1 pb-16 md:pb-0">{children}</main>
      </body>
    </html>
  );
}
