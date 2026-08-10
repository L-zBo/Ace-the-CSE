# Ace-the-CSE Design System

> 视觉真相源。本文档是 AI agent / 设计师 / 开发者改 UI 时必读的锚点。
> 跟代码冲突以本文档为准，发现冲突要改代码不改文档。

---

## 0. 设计理念（Why）

公考刷题平台不是通用 SaaS，**目标用户是 18-35 岁备考者**——他们一天在题库里停 2-4 小时，需要：

1. **专注感**：减少装饰干扰，让题目内容是视觉主角
2. **专业感**：卷面气质沉稳可信，避免"小学练习册"廉价感
3. **持久感**：长时间阅读不刺眼、动效不眩晕（WCAG 2.3.3）
4. **辨识度**：跟其他公考 APP 视觉上有区分，不复刻 Tailwind 默认 SaaS 模板

视觉基因：**墨蓝 + 印章红 + 霞鹜文楷**（卷面 + 印章 + 书法体）。
形容词锚：考场 / 卷面 / 印章 / 书院 / 沉稳 / 笃定。

---

## 1. 颜色系统

### 1.1 主色（核心，已 token 化在 globals.css）

| Token | Value | 用途 |
|---|---|---|
| `--brand` / `--primary` | `#1e3a5f` | 墨蓝主色——按钮、链接、强调、品牌 |
| `--brand-soft` | `#2c5282` | 墨蓝亮——hover/secondary |
| `--brand-deep` | `#0f2942` | 墨蓝深——渐变底色 |
| `--seal-red` | `#c1272d` | 印章红——重点字、错误状态、印章感 |
| `--seal-red-soft` | `#e85d5d` | 印章红亮——hover |
| `--seal-red-deep` | `#7c1d1d` | 印章红深 |
| `--accent` | `#f59e0b` | 警示黄（=warning）——次要 accent |
| `--ink` | `#1a1612` | 墨纸黑——深暗模式底 |

### 1.1.1 11 阶色阶（D-18a P2c-1/2 升级，由 color-palette skill 公式生成）

**墨蓝 brand 11 阶**（输入 `#1e3a5f` ≈ `hsl(214, 51%, 25%)`）：

| Token | Hex | L | 主用途 |
|---|---|---:|---|
| `--brand-50` | `#eef3f9` | 97% | paper 模式标签底、极浅 hover |
| `--brand-100` | `#dde7f1` | 94% | subtle bg、light 模式 muted surface |
| `--brand-200` | `#bcceea` | 87% | 描边、浅强调（dark 模式 badge 字色） |
| `--brand-300` | `#8eadd1` | 75% | placeholder、dark 模式 muted text |
| `--brand-400` | `#5985b9` | 62% | secondary text on light、icon |
| `--brand-500` | `#2c5282` | 48% | 中性主色（≈ 原 `--brand-soft`）|
| **`--brand-600`** | `#1e3a5f` | 40% | **主 CTA、默认 brand（≈ 原 `--brand`）** |
| `--brand-700` | `#172f4d` | 33% | hover、加深 CTA |
| `--brand-800` | `#11253c` | 27% | 深背景 |
| `--brand-900` | `#0c1d30` | 20% | 极深（≈ 原 `--brand-deep`）|
| `--brand-950` | `#060e18` | 10% | 几乎纯黑 |

**印章红 seal 11 阶**（输入 `#c1272d` ≈ `hsl(358, 65%, 46%)`）：

| Token | Hex | 主用途 |
|---|---|---|
| `--seal-50` | `#fdeded` | 极浅红底 |
| `--seal-100` | `#fbd4d4` | subtle red bg |
| `--seal-200` | `#f6a0a0` | 浅强调 |
| `--seal-300` | `#ef6f70` | dark 模式徽章字色（≈ 原 `--seal-red-soft`）|
| `--seal-400` | `#e44848` | secondary 红 |
| **`--seal-500`** | `#c1272d` | **印章红主色（= 原 `--seal-red`）** |
| `--seal-600` | `#a52126` | hover 加深 |
| `--seal-700` | `#871b1f` | 渐变底（≈ 原 `--seal-red-deep`）|
| `--seal-800` | `#6b1518` | 深 |
| `--seal-900` | `#4f0f12` | 极深 |
| `--seal-950` | `#2d080a` | 几乎黑红 |

**Tailwind 用法**：`text-brand-{50..950}` / `bg-seal-{50..950}` / `from-brand-500 to-seal-500` 等。

### 1.1.2 双模式 token（D-18a P2c-3/4 升级，WIRED + Notion 借鉴）

| 新增 Token | Hex | 用途 |
|---|---|---|
| `--ink-link` | `#0b2545` | 纯链接色（WIRED ink-blue 借鉴），与 brand-900 职能区分 |
| `--paper` | `#fbfaf5` | light 模式底色（Notion warm cream 借鉴）|
| `--paper-soft` | `#f5f2e8` | light 二级 paper（卡片 subtle 区分）|

**双模式启用**：默认 `:root` 走 dark；用户切换 `<html data-theme="light">` 时启用 paper 模式映射（globals.css `:root[data-theme="light"]` 块）。

**WCAG 对比度自查（paper 模式）**：
- `brand-900` on `paper` = **14.0:1** AAA ✅
- `brand-700` on `paper` = **11.6:1** AAA ✅
- `brand-600` on `paper` = **10.3:1** AAA ✅
- `brand-500` on `paper` = **7.4:1** AAA ✅
- `seal-500` on `paper` = **5.5:1** AA ✅
- `seal-700` on `paper` = **9.2:1** AAA ✅

### 1.2 语义色（功能性，非装饰）

| Token | Value | 严格用途 |
|---|---|---|
| `--success` | `#10b981` | 正确答案、提交成功、已掌握 |
| `--warning` | `#f59e0b` | 警示、待复习、连续打卡 |
| `--danger` | `#ef4444` | 错误答案、删除、危险操作 |
| `--info` | `#06b6d4` | 提示、统计趋势、信息播报 |

### 1.3 文字层级（4 阶）

| Token | Value | 用途 | 对比度 vs ink |
|---|---|---|---|
| `--foreground` | `#f1f5f9` | 标题、正文主字 | 14.8:1 ✅ |
| `--foreground-secondary` | `#cbd5e1` | 副标题、描述 | 10.9:1 ✅ |
| `--foreground-muted` | `#94a3b8` | 辅助、placeholder | 5.9:1 ✅ |
| `--foreground-faint` | `#64748b` | 极弱、disabled | 3.4:1 ⚠️ (非正文用) |

### 1.4 表面层（卡片底）

| Token | Value | 用途 |
|---|---|---|
| `--surface-1` / `--card` | `rgba(15, 23, 42, 0.5)` | 标准卡片底（玻璃态需配 backdrop-blur） |
| `--surface-2` / `--card-hover` | `rgba(30, 41, 59, 0.62)` | hover 抬升 / 二级卡 |
| `--border` | `rgba(255, 255, 255, 0.1)` | 标准描边 |
| `--border-strong` | `rgba(255, 255, 255, 0.2)` | 强调描边、focus ring |

### 1.5 题型 / 题库主题映射（保留 `examBankTheme.ts`）

| 题库 | theme | 主色 | 渐变 |
|---|---|---|---|
| 国考 | `mo-blue` | `#1e3a5f` | `gradient-mo-blue` |
| 省考 | `emerald-deep` | `#047857` | `gradient-emerald-deep` |
| 事业编 | `cinnabar` | `#7c1d1d` | `gradient-cinnabar` |

### 1.6 ❌ 严禁使用

- **Tailwind 默认彩虹**：`violet-500 / fuchsia-500 / rose-500 / pink-500 / cyan-500 / sky-500 / indigo-*` —— AI slop 通用色，破坏卷面气质
- **紫粉渐变** (`from-purple-* to-pink-*`)：Stable Diffusion / ChatGPT 头像观感
- **饱和度过高的色**：`yellow-300 / lime-400` 等糖果色
- **彩色 emoji** 当装饰：用 lucide-react 单色图标
- **多个不相干渐变并排**：见首页 `features` 数组当前问题（待修）

---

## 2. 字体系统

### 2.1 字体栈（已 token 化）

| 用途 | 字体栈 | 备注 |
|---|---|---|
| **中文 display**（hero / 大标题） | `LXGW WenKai` → `Source Han Serif SC` → `PingFang SC` → system | `--font-display-zh`，需配 `font-display-zh` class |
| **中文正文** | 同上栈（默认 body）+ `Noto Serif SC` 兜底 | body 全局应用 |
| **申论范文** | `Source Han Serif SC` → `Noto Serif SC` → `宋体` | 衬线强调"答案文章"质感 |
| **英文/数字** | `Geist` / `Geist Mono` | `--font-geist-sans` / `--font-geist-mono` |
| **代码 / tabular numbers** | `JetBrains Mono` / `Fira Code` | 用 `font-mono` + `tabular-nums` |

### 2.1.1 英文 4 阶配对（D-18a P2b-1 升级，ui-ux-pro-max + WIRED + Notion 借鉴）

| 角色 | 字体 | Token | 用法 |
|---|---|---|---|
| **英文/数字 display** | `Libre Bodoni`（magazine/editorial 衬线）| `--font-display-en` / `.font-display-en` | hero 数字、大字号英文标题、页码、drop cap |
| **英文 body** | `Public Sans`（现代 sans）| `--font-body-en` / `.font-body-en` | 英文正文段、UI label、metric label |
| **中文 display** | `LXGW WenKai`（已用，霞鹜文楷）| `--font-display-zh` | 中文 hero / 大标题 / 卷面气质 |
| **tabular numbers** | `Geist Mono`（已用）| `--font-geist-mono` | 数字栏、kbd、代码 |

**接入方式**（layout.tsx）：`Libre_Bodoni` + `Public_Sans` 来自 `next/font/google`，注入 CSS var `--font-libre-bodoni` / `--font-public-sans`，globals.css 包成 `--font-display-en`（叠加中文 + serif 兜底）。

**.font-display-en 工具类**：`letter-spacing: -0.02em` + `font-feature-settings: 'lnum', 'tnum'`（数字 line-figure + tabular）。

### 2.2 字号尺度（参考 Tailwind 默认 + 中文最小可读 16px）

| Token | px | rem | 用途 |
|---|---|---|---|
| `text-xs` | 12 | 0.75 | caption、tag、面包屑 |
| `text-sm` | 14 | 0.875 | 辅助说明、表格 cell |
| `text-base` | 16 | 1 | **正文（中文最小可读）** |
| `text-lg` | 18 | 1.125 | 题目正文 |
| `text-xl` | 20 | 1.25 | h3 |
| `text-2xl` | 24 | 1.5 | h2 |
| `text-3xl` | 30 | 1.875 | h1 |
| `text-4xl` | 36 | 2.25 | hero 副标 |
| `text-5xl` | 48 | 3 | hero 主标 |

### 2.3 行高 / 字距

- 中文长段：`leading-relaxed` (1.625) 或 `leading-loose` (2)
- 题目正文：`leading-[1.8]`（统一）
- 卷面气质标题：`tracking-tight` (-0.025em) 或 hero `tracking-[0.05em]`（霞鹜文楷扩展字距）

### 2.4 ❌ 严禁使用

- **Inter / Roboto / Arial / 微软雅黑**作为 hero 主字（破坏卷面气质）
- **font-family 漂移**：每个组件单独写 font-family，统一走 token
- **粗体堆砌**：`font-black` 慎用，hero 才用，正文最高 `font-semibold`

---

## 3. Radius / Shadow / Spacing / Z-Index（**新增 token**）

### 3.1 Border Radius

| Token | px | 用途 |
|---|---|---|
| `rounded-md` | 6 | input、tag、小按钮 |
| `rounded-lg` | 8 | 标准按钮、小卡片 |
| `rounded-xl` | 12 | 卡片、卡片内嵌区 |
| `rounded-2xl` | 16 | 大卡片（题库主入口） |
| `rounded-3xl` | 24 | hero 卡片、modal |
| `rounded-full` | 9999 | tag chip、头像 |

### 3.2 Shadow Elevation（新增）

新增 5 阶标准 shadow + 已有 4 个主题 shadow：

| Token | 用途 |
|---|---|
| `shadow-sm` | hover 微抬 |
| `shadow-md` | 标准卡片静态 |
| `shadow-lg` | 卡片 hover |
| `shadow-xl` | 浮层（dropdown / tooltip） |
| `shadow-2xl` | modal / dialog |
| `shadow-mo-blue` | 墨蓝品牌卡片 |
| `shadow-seal-red` | 印章红强调 |
| `shadow-emerald-deep` | 翠绿（省考主题） |
| `shadow-cinnabar` | 朱砂（事业编主题） |

### 3.3 Spacing（沿用 Tailwind 4px 基线）

- 元素内距：`p-3 / p-4 / p-5 / p-6`
- 卡片间距：`gap-4 / gap-5 / gap-6`
- 段间距：`mb-8 / mb-10 / mb-14`
- 触控目标最小 **44x44px**（WCAG 2.5.5），按钮高度最小 `h-11`

### 3.4 Z-Index（新增层级）

| 层 | z-index | 用途 |
|---|---|---|
| 背景天气 | `z-0` (BackgroundLayer) | 全屏天气动效 |
| 主内容 | `z-10` (main) | 默认页面内容 |
| Sticky nav | `z-20` | Navbar |
| Dropdown / tooltip | `z-30` | 浮层 |
| Sheet / drawer | `z-40` | 侧滑面板 |
| Modal / dialog | `z-50` | 模态弹层 |
| Toast / 通知 | `z-[60]` | 顶层通知 |
| skip link focus | `z-[100]` | a11y 跳转链接（最顶） |

### 3.5 Transition

- 标准过渡：`transition-all duration-200 ease-out`
- 卡片 hover：`transition-[transform,box-shadow,background-color,border-color] duration-200`
- 大动效（modal / sheet）：`duration-300`
- **绝不**用 `transition-all duration-500` 在普通 hover——卡顿感

---

## 4. 组件原则

### 4.1 Button

- **3 种 variant**：`primary`（墨蓝渐变实心）/ `secondary`（玻璃态描边）/ `ghost`（透明 + hover bg）
- **3 种 size**：`sm`（h-9）/ `md`（h-11，默认，触控达标）/ `lg`（h-12）
- 必须 `focus-visible:outline-2 outline-brand`（继承全局）
- 不允许：圆角按钮+方角按钮混用、不写 hover/active 状态

### 4.2 Card

- 默认底：`bg-card backdrop-blur-md border border-border`
- hover：`hover:bg-card-hover hover:border-border-strong hover:shadow-lg`
- 圆角：`rounded-2xl`（标准）/ `rounded-xl`（小卡）
- 内距：`p-5 sm:p-6`

### 4.3 输入控件

- 高度：`h-11`（触控）
- 圆角：`rounded-lg`
- 边框：`border border-border focus:border-brand`
- placeholder：`placeholder:text-foreground-muted`

### 4.4 反馈状态

- **Loading**：`Skeleton` 组件，不要白屏；按钮内 spinner `<Loader2 className="animate-spin">`
- **Empty**：lucide icon + 中性文字 + 行动 CTA，绝不空白
- **Success/Error Toast**：右上角浮层，3 秒自动消失
- **Modal Confirm**：危险操作（删除错题、清空记录）必须 Dialog 二次确认

### 4.5 题目相关业务组件（待建）

- `<QuestionCard>` 题面 + 选项 + 提交流容器
- `<OptionList>` 选项渲染（含图形选项 PNG 支持）
- `<ExplanationPanel>` 解析卡片（ReactMarkdown + 应用 .markdown-content 样式）
- `<AnswerStateBadge>` 正确/错误状态徽章

---

## 5. 动效原则（react-bits 风格借鉴）

### 5.1 入场动效（首页 + 卡片列表）

- Framer Motion stagger，`staggerChildren: 0.08`
- 单个 item：`y: 20 → 0, opacity: 0 → 1`
- 持续时间：`duration: 0.4` 内

### 5.2 题目切换

- **BlurText 入场**：每题切换给 200ms blur → clear 过渡，仪式感
- 选项 hover：`scale-[1.02]` 微弹
- 提交动效：button 短按下 `scale-95` + 加载 spinner

### 5.3 数字滚动

- 统计页 / 首页今日数据用 `CountUp` 滚动到目标值
- 持续时间 800ms，easing `easeOutCubic`

### 5.4 ❌ 严禁

- 无意义 floating / pulsing 装饰（除天气背景）
- 持续 loop 的吸睛动效（dancing icon、bouncing badge）
- `prefers-reduced-motion` 用户不应见到任何超过 0.01ms 的动画（已在 globals.css 兜底）

---

## 6. 可访问性强制约束（WCAG 2.1 AA）

- **键盘可导航**：所有交互元素 `tab` 可达 + `focus-visible` 可见
- **触控目标 ≥ 44x44px**（WCAG 2.5.5，移动端必须）
- **正文对比度 ≥ 4.5:1**，大字 ≥ 3:1（见 §1.3 token 表已标注）
- **`prefers-reduced-motion` 尊重**（已全局兜底）
- **图片 alt** / icon `aria-hidden` 区分装饰 vs 信息
- **表单 label** 关联（`htmlFor` 或 `aria-label`）
- **错误状态** 不只用颜色（红字 + icon + 文案三重）

---

## 7. 移动端 / Capacitor 适配

- **断点**：`sm: 640 / md: 768 / lg: 1024 / xl: 1280`
- **答题页移动端**：单列、选项卡片化、按钮在拇指区（底部 ≥ `pb-20`）
- **底部 nav**（待建）：`fixed bottom-0` + `safe-area-inset-bottom`
- **横屏不要乱**：题目页 `max-w-3xl` 兜底
- **PWA / Capacitor**：所有图片优先 webp + lazy loading

---

## 8. 现有问题清单（待修，对照本文档）

1. **首页 `features` 数组**：用了 Tailwind 通用色（violet/fuchsia/rose/pink/cyan/teal），违反 §1.6——需改为卷面色系
2. **答题页 `QuestionPageClient.tsx`**：100+ 行内联无组件抽象——需拆 `QuestionCard / OptionList / ExplanationPanel`
3. ~~**缺基础组件**：Button / Card / Dialog / Toast / Skeleton 全无——需建 `src/components/ui/`~~
   已建 `src/components/ui/`：Button / Card / Badge / Dialog(ConfirmDialog) / Toast / Skeleton /
   Spinner / EmptyState / CountdownTimer / RingProgress。Toast 于 2026-08-10 补齐，
   `<ToastProvider>` 挂在 `app/layout.tsx`，业务侧用 `useToast()`。
4. **缺动效组件**：title 入场无 BlurText / 数字无 CountUp——需建 `src/components/effects/`
5. **缺 radius / shadow / z-index 标准 token**：已在本文档 §3 补充，需同步 `globals.css`

---

## 9. 修改本文档的规则

- 改设计 token：必须同时改本文档 + `globals.css` + 影响的组件
- 加新组件：必须在本文档 §4 登记规范
- 加新规范：先在 PR 描述里说明动机，避免规范爆炸

**当前版本**：D-18a v2（2026-05-26）—— P2c 配色 11 阶 / P2b-1 字体 4 阶 / P2b-2 装饰 SVG / P2b-3 GradientText / P2b-4 借鉴清单。

---

## 10. 借鉴清单（D-18a P2b-4，VoltAgent/awesome-design-md）

公考刷题站不抄任何站点，但借鉴卷面气质类站的设计思路。下面是从 **WIRED**（broadsheet 编辑性）+ **Notion**（warm minimal 衬线）两个 DESIGN.md 提取的、与本项目卷面气质契合的规则，已转译为本项目落地姿势。

### 10.1 WIRED 借鉴（broadsheet editorial）

| WIRED 规则 | 本项目落地 |
|---|---|
| custom serif display | `Libre Bodoni` 英文 display + `LXGW WenKai` 中文 display（§2.1.1） |
| mono uppercase kickers（小标签）| `text-xs font-semibold uppercase tracking-wider` 已用于 QuestionStem 材料块标签 |
| paper-white broadsheet bg | `--paper #fbfaf5` light 模式底（§1.1.2） |
| ink-blue link accent | `--ink-link #0b2545` 链接色（§1.1.2），与 brand-900 职能区分 |
| broadsheet 密度（紧凑多栏）| 答题页保持单列阅读（中文长文不适合多栏），但解析页可考虑 toc + 主体双栏 → P2d 落地 |
| drop cap / 段首大字 | 题号 "1 / 3927" 可提升为 Libre Bodoni 大字装饰 → P3a 答题页接入 |
| 印刷气质留白节奏 | `leading-[1.8]` 题目正文 + `p-5 sm:p-6` Card 留白（§3.4） |

### 10.2 Notion 借鉴（warm minimal serif）

| Notion 规则 | 本项目落地 |
|---|---|
| 衬线 headings + sans body | 同上 §2.1.1 配对 |
| warm minimalism 配色 | paper #fbfaf5 暖底（非纯白），brand 11 阶（非 Tailwind 通用色） |
| 避免高对比度刺眼 | dark 模式 `--foreground #f1f5f9` on `--ink` ≈ 14.8:1（不爆白）|
| 软阴影代硬边界 | Card 用 `shadow-md` + `backdrop-blur-md` + 半透明 `border-border`（§4.2） |
| 充足卡片内边距 | Card 默认 `p-5 sm:p-6`（§3.4） |
| hover 微妙色变 | Card hover `bg-card-hover` + `border-border-strong`（不缩放、不变色相） |
| 圆角柔和 | `rounded-xl` (12px) 标准卡片 / `rounded-2xl` (16px) 大卡片（§3.1） |
| 过渡平缓自然 | 200ms ease-out（§3.5） |

### 10.3 ❌ **不借鉴**

- WIRED 的多栏 broadsheet 网格 → 中文长文阅读不适合多栏
- Notion 的极简（无装饰）→ 公考站需印章红 + 装饰 SVG 加卷面气质（§5）
- 任何站点的 logo / 字标 / 配色完全照搬 → 本项目独立视觉（墨蓝 + 印章红 + 霞鹜文楷三件套）
