# Token Sweep 审计（D-18a P2c-5）— ✅ 收官

> ⚠️ **本文档为 D-18a 过程产物，已完成。保留作历史参考。**
>
> 创建：2026-05-26 / 收官：2026-05-26
> **最终结果**：107 处余孽 → 1 处剩余（`src/lib/utils.ts` cn 工具类型注释，不算样式）→ **99% token 化达成** 🎉
>
> 全站逐页 sweep 由 P3a-e 收口（commit 见 `d1d5f8a / bc6ffed / 0ae66a9 / ec432ec / fc42c36`）。

---

## 替换原则

1. **通用语义色** → 直接换 token
   - `text-emerald-300/400/500` → `text-success`
   - `text-red-300/400/500` / `text-rose-*` → `text-danger` / `text-seal-300`（警示）
   - `text-amber-*` / `text-yellow-*` → `text-warning`
   - `text-cyan-*` / `text-sky-*` → `text-info`
   - `text-blue-*` / `text-indigo-*` → `text-brand-{300/400/500}`
   - `text-slate-*` / `text-gray-*` → `text-foreground-{secondary/muted/faint}`

2. **多色差异化（如 idioms 多色卡片）** → 换到 11 阶色阶保差异
   - 4-6 色卡片：用 `brand-500 / seal-500 / success / warning / info / brand-300` 6 色循环
   - 保留多色 *差异化设计*，仅把 hex/Tailwind 通用色替成项目 token

3. **utils.ts** 的 1 处：cn 工具的 type 注释，**不算余孽**，可保留

4. **DESIGN.md §1.1 配色** 同步更新到 v2（说明 brand/seal 11 阶 + 双模式 token 启用方式）

---

## 剩余余孽分布（97 处 / 15 文件，按处理优先级）

### 🔴 高频组件（影响面广，P3 前优先）

| 文件 | 处数 | 备注 |
|---|---:|---|
| `src/components/idioms/IdiomCard.tsx` | 15 | 成语词卡多色，差异化设计，需保留多色但换 token |
| `src/app/practice/[questionId]/ShenlunAnalysis.tsx` | 3 | 申论分析卡，emerald/rose 命中未命中，→ success/danger |

### 🟡 P3 各页重做时一并处理

| 文件 | 处数 | 对应 P3 |
|---|---:|---|
| `src/app/exam/[examId]/ExamSessionClient.tsx` | 16 | P3d 模考页 |
| `src/app/current-affairs/page.tsx` | 12 | P3e 时事 |
| `src/app/stats/page.tsx` | 10 | P3b 统计 |
| `src/app/idioms/page.tsx` | 8 | P3e 成语 |
| `src/app/exam/page.tsx` | 6 | P3d 模考列表 |
| `src/app/plan/page.tsx` | 6 | P3e 学习计划 |
| `src/app/practice/institution/page.tsx` | 5 | P3c 题库列表 |
| `src/app/review/page.tsx` | 4 | P3a 错题本 |
| `src/app/practice/provincial/page.tsx` | 4 | P3c |
| `src/app/practice/page.tsx` | 4 | P3c |
| `src/app/practice/national/page.tsx` | 2 | P3c |
| `src/app/knowledge/page.tsx` | 1 | P3e 知识图谱 |

### 🟢 不处理

| 文件 | 处数 | 备注 |
|---|---:|---|
| `src/lib/utils.ts` | 1 | cn 工具类型注释，非样式 |

---

## 本轮（P2c-5）实际替换

| 文件 | 替换 |
|---|---|
| `src/components/ui/Badge.tsx` | `text-blue-200 → brand-200` / `text-emerald-300 → success` / `text-amber-300 → warning` / `text-red-300 → danger` / `text-cyan-300 → info` / `text-seal-red-soft → seal-300` |
| `src/components/ui/Button.tsx` | `disabled:from-slate-700 to-slate-800 → brand-800 to brand-900` / `from-[#c1272d] to-[#7c1d1d] → from-seal-500 to-seal-800`（去掉硬编码 hex） |
| `src/app/page.tsx` 首页统计图标 | `text-blue-400 → brand-300` / `text-emerald-400 → success` / `text-amber-400 → warning` / `text-rose-400 → seal-300` |

---

## DESIGN.md 同步（待 P2b 阶段）

P2b 阶段做"DESIGN.md 升级到 v2"时，把以下内容写入：

- §1.1 配色 token：列出 `--brand-{50..950}` × 2 共 22 个色阶 token + `--ink-link/--paper/--paper-soft`
- §1.2 双模式：`:root` = dark 默认，`:root[data-theme="light"]` = paper 模式映射；切换方式（Navbar ThemeToggle 待做）
- §3 严禁清单：保留"严禁 Tailwind 通用色（slate/blue/emerald/...）"，本表是当前余孽位置
