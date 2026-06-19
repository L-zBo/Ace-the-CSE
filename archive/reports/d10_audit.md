# D-10 启动调研报告（2026-05-04）— 硬墙 25 题重分类 + 跨源救援策略

## 背景

D-9 收官报告称剩 25 题硬墙（PNG 缺 174 张已 onError fallback，单纯
`[OCR/PDF 数据极限]` 占位 ans/exp 25 题）。本次 D-10 启动前对每题
**逐题肉眼核对题干 + 选项**，发现 D-9 的"硬墙"分类**不准确**：

- D-9 假设 25 题都是「PDF 文字层为图 / OCR 漏识别 / PDF 真无答案」
- 实际 25 题里 **14 题是自家数据问题**（OCR 输出脏、选项乱序/缺失/截断、
  甚至题干被章节说明覆盖），不是真"PDF 极限"。

## 25 题硬墙重新分类

### A 类（11 题）— 题干完整，仅缺 ans/exp

可走"公开题库 + 搜索引擎双源校验"补齐答案/解析。

| ID | 题型 | 题干摘要 |
|---|---|---|
| institution-xingce-changshi-2022-a-010 | 常识 | 智能穿戴设备工作原理 |
| institution-xingce-changshi-2022-b-017 | 常识 | 智能穿戴设备（与 a-010 重复题） |
| institution-xingce-changshi-2022-e-006 | 常识 | 冷敷、热敷错误说法 |
| institution-xingce-changshi-2022-e-007 | 常识 | 人体构造错误说法 |
| institution-xingce-shuliang-2022-a-081 | 数量 | 网友 1 论证错误 |
| provincial-gansu-xingce-yanyu-2021-045 | 言语 | 唾液腺新发现标题题 |
| provincial-henan-xingce-panduan-2021-116 | 判断 | 类比：骈偶∶颠倒 |
| provincial-henan-xingce-panduan-2021-117 | 判断 | 类比：顿悟∶醍醐灌顶 |
| provincial-beijing-xingce-shuliang-2023-061 | 数量 | 张王李书数（120 本） |
| provincial-jiangsu-xingce-ziliao-2024-111 | 资料 | 2022 网络零售交易额 |

注：上述清单 11 题（含 1 道重复题），实际独立题 10 道。

### B 类（14 题）— 自家 OCR 数据脏，需替换原题

D-9 标 `[OCR/PDF 数据极限]` 但**问题不在 PDF 极限**，而是历次 OCR/抽取
留下的脏数据。需从公开题库取整题（题干 + 选项）替换。

| ID | 自家数据具体问题 |
|---|---|
| institution-xingce-changshi-2022-b-016 | content 含 `******（注：题干有缺失）` |
| institution-xingce-panduan-2021-c-073 | 仅 A/C 两选项，B/D 缺失 |
| institution-xingce-panduan-2021-c-076 | 仅 A/C 两选项，B/D 缺失 |
| institution-xingce-panduan-2021-c-077 | C/D 选项被合并污染（含别题文字） |
| institution-xingce-panduan-2021-e-074 | 选项严重错乱（B/D 含别题文字） |
| institution-xingce-panduan-2021-e-076 | D 选项含别题尾巴 |
| institution-xingce-shuliang-2021-a-047 | 选项顺序错乱（A→C→B→D） |
| institution-xingce-shuliang-2021-a-050 | A 选项是题干尾巴，BCD 是别题 |
| provincial-guangdong-xingce-ziliao-2021-091 | 选项标号错乱（C 在 B 之前） |
| provincial-guangdong-xingce-ziliao-2021-092 | 同 091 |
| provincial-guangdong-xingce-ziliao-2021-094 | D 选项含 `20 - 12 -` OCR 噪音 |
| provincial-guangdong-xingce-ziliao-2021-095 | B/C/D 选项被截断 |
| provincial-gansu-xingce-ziliao-2021-114 | 仅 A/C，B/D 完全缺失 |
| provincial-beijing-xingce-shuliang-2023-062 | 选项全是 OCR 乱码（A 含别题文字） |
| provincial-beijing-xingce-panduan-2023-082 | 题干是章节说明 `每道题包含两套图形…`，非真题 |

注：上面表 15 行去重后 14 题（changshi-2022-b-017 重复合并到 a-010 而不在此类）。

## 公开题库候选源（按可访问性 + 数据粒度排序）

| 源 | URL | 粒度 | 是否登录 | 反爬 | 备注 |
|---|---|---|---|---|---|
| 小麦公考 | xiaomaigongkao.com | 题级 | 无 | 弱 | 每题独立 URL，最佳源 |
| 上岸鸭公考 | m.gwy.com | 整卷 | 无 | 弱 | 真题 + 答案对照表 |
| 公开真题库 | gkzenti.cn | 整卷 + 题搜索 | 无 | 中 | 标题就叫"公开" |
| 星光公考 | xingguanggongkao.com | PDF | 无 | 弱 | 直接挂真题 PDF |
| 华图各省分站 | ah.huatu.com 等 | 文章 | 无 | 中 | 解析详细但散页 |
| 中公网校 | eoffcn.com | 文章 + 题库 | 部分 | 中 | 有 `/kszx/detail/` 静态页 |
| 南方公考 | gwypass.cn | 整卷 | 无 | 弱 | 综合较全 |
| 高教公考 | sanlianbook.com | 整卷 | 无 | 弱 | 真题列表 |

## 救援策略（D-10 流程）

### 第一波（A 类 11 题）— 双源补 ans/exp

1. 用 WebSearch 搜「{年份} {地区} 行测 {题型} 第{N}题 答案 解析」
2. 命中 ≥2 个公开源给出**一致**答案才采信（双源互证）
3. 解析摘要 ≤500 字，避免大段抄袭，必要时改写
4. 来源链接写入 explanation 末尾的 `[Source: …]` 注释

### 第二波（B 类 14 题）— 整题替换

1. 优先尝试小麦公考 / 上岸鸭按"年份 + 地区 + 卷别 + 题号"定位整题
2. 抓取题干 + 完整选项 + 答案 + 解析
3. **严格对比原 PDF 题号 / 题干前 10 字**，错配率 >3% 必须回滚（D-3 硬规则）
4. 替换 content + options + answer + explanation，保留 questionImage / id 不变

### 第三波（如爬不通）— 改进流程

按 D-9 备忘列出的备选：
- 事业编 PDF 重 OCR（更高分辨率 / 更好模型）
- shenzhen_2020 dim5 广告污染清洗
- PNG 缺 174 张针对性补抽

## 预期收益

| 阶段 | 救题数 | 真完整率 |
|---|---|---|
| D-9 末 | 0 | 99.88% |
| D-10 第一波（A 类） | +11 | 99.93% |
| D-10 第二波（B 类） | +14 | 100.00%（含若干公开源采信） |

如全部命中：**真完整率 100%**（首次实现）。

## 法规与版权说明

- 真题属于公开发布的考试材料，引用做学习用途适用合理使用
- 解析改写而非全文复制，规避三家培训机构原创内容
- 来源链接写入 explanation 注释，便于追溯

## D-10 commit 计划

| # | 内容 |
|---|---|
| 1 | docs(report): D-10 #1 - 25 题硬墙重分类调研（A 类 11 + B 类 14）|
| 2 | feat(scripts): D-10 #2 - 跨源救援工具骨架 |
| 3..N | fix(data): D-10 #3..N - 第一波 A 类双源补 ans/exp |
| N+1.. | fix(data): D-10 #N+1.. - 第二波 B 类整题替换 |
| 末 | docs(report): D-10 末 - 收官报告 |
