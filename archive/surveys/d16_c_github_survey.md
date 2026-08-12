# D-16 C 工程：GitHub/HuggingFace 公考题库 repo 系统调研

**调研日期**：2026-05-16
**调研目标**：找还没扒过的开源公考题库 repo，重点救 D-16 末 99 题硬伤卷
（xinjiang/jilin/beijing 2023 + gansu/ningxia 2024）

## 结论速览

**GitHub 上没有可救 D-16 硬伤卷的开源结构化数据集**。最相关的 502 stars 仓库
收录截止 2022 年，与我们 2023-2024 硬伤卷完全错位。HuggingFace 已知的
ANGO-S1（D-16 L-0 探过失败）是唯一相关数据集。

不过调研中意外发现潜在新源**小麦公考网站**（2008-2024 真题，含吉林/浙江/山东等），
可作为 D-17 候选。

## 详细调研

### 1. Yaoyuan-Zhang319/AdministrativeAptitudeTest (DaleksInGHB/gwy 的 source)

| 字段 | 值 |
|---|---|
| stars | 502 |
| pushed_at | 2024-05-29 |
| 总大小 | 1.6 MB |
| 数据格式 | **原 PDF** 试卷 + 答案 |
| 描述 | 近二十年公考行测真题，国考+省考+选调生 |

目录结构：`国考/` + `省考以及市考/` (33 省/市) + `选调/`

**硬伤卷年份匹配**：

| 硬伤卷 | repo 最新收录年份 | 是否能救 |
|---|---|---|
| xinjiang 2023（19 题） | 2022 | ❌ |
| jilin 2024（13 题） | 2022 | ❌ |
| beijing 2023（12 题） | 2022 | ❌ |
| gansu 2024（8 题） | 2021 | ❌ |
| ningxia 2024（4 题） | 待查 | 大概率 ❌ |

数据形式都是 PDF（无 OCR 后的 JSON），即使年份对得上也得重新解析。

**裁定**：与 D-16 末需求**完全错位**，不进推荐。

### 2. coder2gwy/coder2gwy（27581 stars）

`描述`：互联网首份程序员考公指南。
`内容`：上岸经历 / 基本认识 / 最佳实践 / 相关 / 遇到问题 — **不含题库**。
**裁定**：指南类，与本项目无关。

### 3. miss-mumu/developer2gwy（10892 stars）

同上，程序员考公指南，**不含结构化题库**。

### 4. hwlvipone/yunduanqiqu（434 stars, push 2024-10）

资料汇总 repo，分享网盘链接（夸克网盘/阿里云盘 PDF），**不是结构化数据**。
即使下载下来还需要重做 OCR 提取流水线，ROI 低。

### 5. hwlvipone/-（同作者另一个大合集）

同样是网盘链接合集。

### 6. cf12436/gwy, Hacker233/sharemore52, iSylleo/civil-service-exam-1

均为资料/思维导图汇总，**不含题库数据**。

### 7. HuggingFace 数据集搜索

`公考 / 行测 / civil service exam china` 关键词：

- **AngoHF/ANGO-S1** — 已 D-16 L-0 详查，**失败**：事业编 0 题、图形题预处理移除、
  与 lib 134 省考占位仅命中 4 题（2.5%）
- 其他相关：M3KE / Chinese_Paper_QA / Luotuo-QA-A-CoQA-Chinese / chinese-semantic-textual-similarity —
  **均非公考真题**

## 意外发现（D-17 候选）

### 小麦公考网站（xiaomaigongkao.com）

WebSearch 中提到：
> 提供国家及各省份（西藏、河南、吉林、浙江、山东等）历年行测真题，
> 年份涵盖 2008 年至 2024 年。

**可能价值**：
- 包含 2024 年数据（D-15 用的 gkzenti 也只到 2025 但与 lib 命中率有限）
- 显式提到吉林（D-16 末硬伤 13 题）
- 网站抓取需要 D-13 baijing / D-15 gkzenti 类似工程量（4-8h）

**D-17 候选**：用 d13_run_one.py 类似流程抓小麦公考整卷，针对硬伤卷
（xinjiang/jilin/beijing 2023 + gansu/ningxia 2024）尝试救援。

### 星光公考（xingguanggongkao.com）

D-16 L-5 真题站精搜调研已扒，单题救援命中率约 60% 但残余题碎、图形/数学题
选项图片化救不出。**重新尝试整卷抓**可能比单题精搜 ROI 高，与小麦公考并列。

## D-16 收官状态（保持）

99 题真不可作答题在 H 工程后已从前端列表过滤掉，用户体验已优化。
GitHub 调研无新开源数据可救，**D-16 至此真收官**。

D-17 启动时可优先评估小麦公考新源接管的 ROI。
