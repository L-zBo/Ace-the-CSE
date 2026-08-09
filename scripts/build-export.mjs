// 打 Capacitor 安卓包用的静态导出构建。
//
// 直接在 npm script 里写 `NEXT_STATIC_EXPORT=1 next build` 在 Windows cmd 下不成立，
// 写 `set X=1&&...` 又在 bash 下不成立，所以用这个小包装器统一设环境变量。
//
// 用法：npm run build:export
// 产物：out/（capacitor.config.ts 的 webDir 指向它）
//
// ⚠️ 这条路径会把 2 万+ 道练习题全部预渲染成 HTML，耗时很长，本机磁盘上可能跑很久。
// 日常构建请用 `npm run build`。

import { spawn } from 'node:child_process';

const child = spawn(
  process.platform === 'win32' ? 'npx.cmd' : 'npx',
  ['next', 'build', '--webpack'],
  {
    stdio: 'inherit',
    env: { ...process.env, NEXT_STATIC_EXPORT: '1' },
  },
);

child.on('exit', (code) => process.exit(code ?? 1));
