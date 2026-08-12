import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    "android/app/src/main/assets/public/**",
    "data/tmp_*",
    "data/tmp_*/**",
    // 抓取源站的原始 HTML/PDF/JS 快照（含第三方压缩 JS），是溯源证据不是项目源码。
    // 2026-08-12 从 data/ 顶层归档到此处，通配符跟着搬。
    "archive/web_probes/**",
    // 数据救援迁移包里存的是取证用的来源副本（含抓下来的第三方压缩 JS），
    // 属于证据数据不是项目源码，不参与 lint。
    "data/gap_rescue_pack/**",
  ]),
]);

export default eslintConfig;
