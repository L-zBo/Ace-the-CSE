import type { NextConfig } from "next";

// 静态导出（`output: "export"`）只在打 Capacitor 安卓包时需要，它会强制把每一条动态路由
// 都预渲染成 HTML。练习页有 2 万+ 道题，全量展开会让 `next build` 在本机磁盘上超时。
// 因此默认走普通构建（动态路由按需渲染），只有显式设置 NEXT_STATIC_EXPORT=1 才导出 `out/`。
// 对应脚本：`npm run build`（快）/ `npm run build:export`（安卓用，慢）。
const isStaticExport = process.env.NEXT_STATIC_EXPORT === "1";

const nextConfig: NextConfig = {
  ...(isStaticExport ? { output: "export" as const } : {}),
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
