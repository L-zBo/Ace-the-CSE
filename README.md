# Ace the CSE

> 公务员考试刷题平台 —— 行测 + 申论双线题库，自研 PDF 真题提取流水线。

Web 为主（Next.js），另有 Capacitor 安卓壳。视觉基因是**墨蓝 + 印章红 + 霞鹜文楷**，
形容词锚：考场 / 卷面 / 印章 / 书院 / 沉稳 / 笃定。

---

## 快速开始

**Windows 用户直接双击 `start.bat`**（项目的正常启动入口）。它会检查 Node、按需
`npm install`，然后在 `http://localhost:3000` 起 dev server。

命令行等价方式：

```bash
npm install
npm run dev          # = next dev --webpack
```

> ⚠️ **必须走 webpack**。Turbopack 目前在本项目上会 panic，所以 `dev` 和 `build`
> 都固定带 `--webpack`。`dev:turbopack` 只是保留的备用脚本，正常不要用。

### npm scripts

| 脚本 | 命令 | 说明 |
|---|---|---|
| `dev` | `next dev --webpack` | 开发服务器（默认，`start.bat` 走这条） |
| `dev:webpack` | `next dev --webpack` | 同上，显式版 |
| `dev:turbopack` | `next dev` | 备用，**当前会 panic** |
| `build` | `next build --webpack` | 生产构建（练习页按需渲染，不预展开题库） |
| `build:export` | `node scripts/build-export.mjs` | 静态导出到 `out/`，给 Capacitor 安卓包用，**很慢** |
| `start` | `next start` | 生产服务器 |
| `lint` | `eslint` | 当前 0 warning / 0 error |

---

## 技术栈

**前端**：Next.js 16.2.3 · React 19.2.4 · TypeScript 5 · Tailwind CSS 4.3 ·
Zustand 5 · Framer Motion 12 · Recharts 3 · react-markdown + remark-gfm · lucide-react

**移动端**：Capacitor 8.3（Android）

**数据流水线**：Python，`scripts/` 下 85 个脚本

> ⚠️ Next.js 16.2.3 与常见的 Next.js 用法有出入。写 Next 相关代码前请先读
> `node_modules/next/dist/docs/` 里的对应指南，别凭记忆写。详见 `AGENTS.md`。

---

## 数据流水线

```
PDF 真题卷
   ↓  scripts/extract_figures.py 等（PyMuPDF）
结构化 JSON 题库 + PNG 题图
   ↓  scripts/generate_question_index.py
src/data/index/question-index.json  ← 轻量元数据索引（约 1.3 MB）
   ↓  scripts/generate_cross_paper_links.py
src/data/index/cross-paper-links.json ← 跨卷同题关联（约 300 KB，答题页按需加载）
   ↓
src/lib/questionIndex.ts   同步元数据（列表 / 筛选 / 统计）
src/lib/questionLoader.ts  按试卷 dynamic import() 懒加载正文
src/lib/relatedQuestions.ts 跨卷同题关联（dynamic import）
   ↓
Next.js 前端渲染
```

### 题库访问的两层结构（重要）

改题库或写取数代码前必须理解这条约定：

| 需求 | 用什么 | 同步/异步 |
|---|---|---|
| 题号、分类、年份、来源、可否作答、题量统计 | `questionIndex` 的 `getQuestionIndex` / `filterIndex` / `getAnswerableIndex` | 同步 |
| 题干、选项、解析、申论材料 | `questionLoader` 的 `loadQuestionById` / `loadQuestionsByIds` / `loadFilteredQuestions` | **异步** |

> ⚠️ 不要为了图省事在页面里 `await loadAllQuestions()` —— 那会把 1380 份试卷全拉进内存，
> 等于退回重构前。它只给静态导出枚举路由用。

历史背景：2026-08-09 之前 `questionLoader.ts` 是自动生成的 2847 行文件，用 1381 条静态
import 把整个题库塞进 bundle，导致单个客户端 chunk **62.5 MB**、dev 进程常驻 6 GB。
旧文件在 git 历史里（`git show <本次提交>^:src/lib/questionLoader.ts`），
旧生成器已废弃并移出 `scripts/`（现存 `archive/generate_loader.deprecated-2026-08-09.py`，
带运行拦截）。**改题库后要跑的是 `scripts/generate_question_index.py`。**

### 题库规模（2026-08-08 实测）

| 项 | 数值 |
|---|---|
| 行测题量 | 20,089 |
| 申论题量 | 652 |
| JSON 文件 | 1,385 |
| 行测不可作答 | 50（可用率 99.75%） |
| 申论 `material` 覆盖 | 652 / 652 |

### 题库结构

```
src/data/
├── xingce/            行测
│   ├── changshi/      常识判断  164 文件
│   ├── panduan/       判断推理  148
│   ├── shuliang/      数量关系  141
│   ├── yanyu/         言语理解  140
│   └── ziliao/        资料分析  135
├── shenlun/           申论
│   ├── xiezuo/        写作      464
│   ├── guanche/       贯彻执行  170
│   ├── duice/         对策       16
│   ├── fenxi/         分析        1
│   └── guina/         归纳        1
├── meta/xingce_exam_manifest.json
├── current-affairs.json   时政
├── idioms_raw.json        成语
├── knowledge.json         常识知识点
└── questionStats.json
```

**考试来源**：国考 2015-2025（副省级 / 地市级 / 行政执法）、省考 12 省市 2020-2025、
事业编 A-E 五类 2020-2024。

**题目 ID**：`{source}-xingce-{category}-{year}-{region?}-{level?}-{qn:03d}`
**examKey**：`national_2025_dishi`、`provincial_jiangsu_2024`
**题图**：`public/img/questions/{examKey}/q{NN}.png`。JSON 里不写 `img` 字段，
题干或选项出现 `[见图]` / `[图形选项]` 时前端自动加载。

### 审计工具链

```bash
python scripts/audit_xingce.py            # 行测客观题统一审计
python scripts/audit_figures.py           # 题图质量扫描
python scripts/audit_shenlun_material.py  # 申论 material 字段审计
python scripts/d17_list_unanswerable.py   # 不可作答题清点
python scripts/audit_full.py              # 全库审计（字段/答案/选项/重复/水印/题图）
python scripts/generate_question_index.py # 题库改动后重建索引
python scripts/generate_cross_paper_links.py # 题库改动后重建跨卷同题关联
python scripts/verify_lazy_loader.py      # 浏览器实测关键路径（需先起 dev）
python scripts/verify_related_appearances.py # 浏览器实测跨卷关联提示（需先起 dev）

# 数据修复（都幂等，默认预览，加 --apply 落盘）
python scripts/fix_option_order.py         # 按 label 重排选项
python scripts/clean_watermarks_v2.py      # 清解析里的引流水印
python scripts/fix_explanation_crosstalk.py # 截断串进解析的邻题内容
python scripts/fix_source_label_region.py  # sourceLabel 拼音省份改中文 / 补空值
```

> 修复脚本都带「序列化后必须与原文件字节一致」的格式校验（题库 JSON 是
> **CRLF + indent=2**），格式对不上直接中止，避免产生满屏无关 diff。

> 改动 `src/data/` 下任何题库文件后，**必须重跑 `generate_question_index.py`
> 和 `generate_cross_paper_links.py`**，否则索引与题库不同步（新增题不出现、
> 删除题点开是空白），关联提示也会指向已删除的题。

### 跨卷同题关联

真题跨省、跨年共用题池，全库有 **1,706 组同题**（涉及 5,912 道题）。这本来是
审计里的 `dup_cross_paper` 脏数据，现在做成答题页的「这道题还考过 N 次」。

指纹口径比审计严格得多 —— 审计用题干前 80 字，会把图形推理的模板题干
（「从所给的四个选项中选择最合适的一个填入问号处」246 处）全判成同题。
这里用 **规范化题干 + 排序后的规范化选项** 做联合指纹，并排除：

- 占位题
- 裸字母选项（`A/B/C/D`）与 `[见图]`、`[图形选项]` 类图形题 —— 这些靠图区分，
  文本上一模一样但根本不是同一道题
- 题干 + 选项总信息量不足 40 字的

宁可漏也不错报：关联点过去发现是另一道题，比不给关联更糟。

---

## 页面结构

| 路由 | 内容 |
|---|---|
| `/` | 首页：hero + 题库入口 + 今日统计 |
| `/practice` | 练习选择：按题型 / 来源 / 年份筛选 |
| `/practice/[questionId]` | 答题页，行测客观题与申论主观题两套 UI |
| `/exam/[examId]` | 模拟考试 |
| `/review` | 复习 / 错题本 |
| `/stats` | 统计分析 |
| `/plan` | 学习计划 |
| `/idioms` | 成语词卡 |
| `/current-affairs` | 时政 |
| `/knowledge` | 常识 |
| `/image-notes` | 图片笔记 |

## 源码结构

```
src/
├── app/          路由与页面（App Router）
├── components/
│   ├── ui/       基础组件 9 个：Button Card Dialog Badge Skeleton
│   │             Spinner CountdownTimer RingProgress EmptyState
│   ├── effects/  BlurText CountUp GradientText ShinyText ScrollFloat
│   ├── layout/   Navbar
│   ├── questions/ AnnotatableImage
│   ├── idioms/   IdiomCard IdiomDetailDialog
│   └── weather/  BackgroundLayer WeatherWidget
├── data/         题库 JSON
├── lib/          questionLoader examBankTheme explanationFormatter
│                 shenlunAnswer questionDisplay imageNotes 等
├── stores/       Zustand：idiom mistake plan practice stats weather
└── types/        exam question user
```

---

## 设计系统

改 UI 前**先读 `DESIGN.md`**（388 行）。它是视觉真相源：与代码冲突时以文档为准，
改代码不改文档。

- 墨蓝 `--brand-*` 11 阶（主色 `--brand-600` `#1e3a5f`）
- 印章红 `--seal-*` 11 阶（主色 `--seal-500` `#c1272d`）
- 双模式：默认 dark，`<html data-theme="light">` 切 paper 暖底 `#fbfaf5`
- 字体四层：LXGW WenKai（中文 display）/ Libre Bodoni / Public Sans / Geist Mono
- 用色一律走 CSS 变量（`text-brand-600`、`bg-seal-500`），**禁止硬编码 hex**，
  禁止 Tailwind 默认彩虹色与紫粉渐变
- 可访问性对齐 WCAG 2.1 AA

---

## 数据规范（硬性）

1. **不许编造题库数据。** 题干、选项、答案、来源证据四者形成可验证的链条，才允许入库。
   公开源里的「默认 A」「暂缺」「征集中」「打码」一律不算证据。
2. **每次数据救援必须落档到 `data/gap_rescue_pack/`**，包含救回的数据副本、登记表和
   迁移说明，保证整个文件夹能复制到另一台机器直接应用：

```
data/gap_rescue_pack/
├── rescue_register.json     登记总表
├── files/                   补好的数据文件副本（保持项目相对路径）
├── snapshots/               审计快照
├── sources/                 来源副本与未补原因说明
└── apply_gap_rescue.ps1     在项目根执行即可回灌
```

```powershell
powershell -ExecutionPolicy Bypass -File data/gap_rescue_pack/apply_gap_rescue.ps1
```

当前剩余 50 道不可作答题的逐卷证据链见
`data/gap_rescue_pack/sources/unresolved_xingce_2026-08-08.md`。

---

## 两条构建路径

练习页 `/practice/[questionId]` 是纯客户端渲染的（`QuestionPageClient` 走 `useParams`
取题号）。预渲染它只会产出 2 万+ 个内容相同的空壳 HTML，却会让构建在本机磁盘上跑到超时。
所以构建拆成两条路径：

| | `npm run build` | `npm run build:export` |
|---|---|---|
| `output` | 默认（server） | `"export"` |
| 练习页 | 按需渲染，不预展开 | 全量预渲染 2 万+ 页 |
| 产物 | `.next/` | `out/` |
| 用途 | 日常构建、Web 部署 | Capacitor 安卓打包 |
| 耗时 | 可接受 | **很慢** |

切换靠环境变量 `NEXT_STATIC_EXPORT=1`，由 `scripts/build-export.mjs` 设置
（Windows cmd 和 bash 下写法不通用，所以用小包装器统一）。

> `generateStaticParams()` 只在 `NEXT_STATIC_EXPORT=1` 时返回全量题号，否则返回 `[]`。
> `dynamicParams` 保持默认 `true`——**注意它只能是字面量，写成表达式 Next 会报
> `Unsupported node type` 并中断构建。**

---

## 已知问题

⚠️ Turbopack 在本项目上 panic，只能用 webpack。

⚠️ 生产构建编译约 20 分钟。懒加载重构把 1380 份试卷切成了独立 chunk，
webpack 产出数量变多，编译比重构前（约 16 分钟）慢了约 4 分钟——
用一次性的构建时长换用户侧 97% 的下载量，这笔账是划算的。

⚠️ Next.js 会把项目所在的 F 盘判为「慢文件系统」并给出警告，可忽略。

⚠️ `npm run build:export`（安卓打包路径）仍然要全量展开 2 万+ 页，耗时很长。
若要进一步提速，可考虑把练习页从动态路由段改成查询参数（`/practice?q=<id>`），
这样静态导出也只需产出一个页面。

---

## 贡献约定

详见 `AGENTS.md`。要点：

- 交流与文档用简体中文；代码标识符、命令、日志、报错保留原文
- `start.bat` 不许移动 / 改名 / 删除 / 随手改
- 改已有文件前先读当前内容，改动保持最小范围，不要顺手回退别人的修改
- 临时截图、一次性脚本、审计产物不要散在仓库根目录；有价值的移进 `archive/`
- 提交前排除本地私有文件：`.vscode/`、`.spec-workflow/`、`.claude/`、
  `.playwright-mcp/`、`对话记录/`、本地截图、临时缓存、凭据
