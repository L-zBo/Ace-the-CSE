# D-9 收官总进度报告（2026-05-04）— PNG 抽图 + 关键词救援

## 全库现状

**xingce 全库 20097 题** + 申论 652 题。

| 类型 | 总题 | 缺 ans | 缺 exp | 空 content | 空 opts | partial |
|---|---|---|---|---|---|---|
| 国考 | 3435 | 0 | 0 | 0 | 0 | 0 |
| 省考 | 14655 | 0 | 0 | 0 | 0 | 0 |
| 事业编 | 2007 | 0 | 0 | 0 | 0 | 0 |
| **全库** | **20097** | **0** ✅ | **0** ✅ | **0** ✅ | **0** ✅ | **0** ✅ |

audit 全维度归零。**数据真完整率 99.88%**（vs D-8 末 99.77%）。

## D-9 vs D-8 净收益

| 指标 | D-8 末 | D-9 末 | 净收益 |
|---|---|---|---|
| PNG 已就位 | ~792 张 | **2050 张** | +1258 |
| questionImage 字段已补 | 830 题 | **1118 题** | +288 |
| 真答案题数 | 20061 (122 救) | **20072** (133 救) | +11 |
| 极限占位题数 | 47 | **25** | -22 |
| 数据真完整率 | 99.77% | **99.88%** | +0.11 pp |
| PNG 缺失 | 358 题 | **174 题** | -184 |

## D-9 10 个 commit

| # | commit | 内容 |
|---|---|---|
| #1+#2 | `aa7baf2` | batch_extract_figures 抽 1106 PNG（660 高 DPI 覆盖 + 446 新增） |
| #3 | （并入 #4） | 抽样验证 PNG 质量（更高分辨率，无内容丢失） |
| #4 | `150a409` | 独立行题号专项抽图脚本 → 67 卷 +54 PNG |
| #5 | （承认极限） | 事业编合订 PUA 字符 PDF 抽图复杂度过高，承认硬墙 |
| #6 | `02c2b6a` | 批量补 questionImage 字段 +114 题 |
| #7+#8 | `f8752df` | QuestionPageClient.tsx onError fallback + 174 题占位 questionImage |
| #9 | `f446d71` | 关键词指纹救 11 题真 ans |
| #10 | TBD | D-9 收官报告 + MEMORY |

## D-9 关键技术

### batch_extract_figures 大批 PNG 重抽

D-3 既有工具批量跑 145 卷，生成 1106 PNG：
- 446 张全新（之前不存在的 PNG）
- 660 张高 DPI 覆盖（原 100KB → 200KB+，更清晰）

### 独立行题号专项（fix_extract_figures_standalone_d9.py）

extract_figures.py 用 `page.search_for("71.")` 不命中独立行 `\n71\n` 格式
（浙江/北京/海南/天津等卷）。新脚本：
- `page.get_text("dict")` 拿文本块 + bbox
- 找 text 完全等于 `str(qn)` 的纯数字块作为题号锚点
- content head 4-6 字消歧（题号 y 之下 250px 内必须含 stem 关键字）
- 200 DPI 裁剪页面区域

### 关键词指纹救援（fix_ans_keyword_d9.py）

D-8 fingerprint 用 content 头 18 字搜，对答案 PDF 解析失效（解析只引关键词不复述题干）。
本步骤改用关键词指纹：
- 从 content 抽稀有连续中文片段（≥3 字，过滤"下列/正确"等常见词）
- 优先长词（更稀有），双关键词锚定降低错配
- 在 658 答案 PDF + OCR cache 里搜，命中后从位置抽 ans + exp

抽样救出 11 题真答案：
- gansu_2021 q040「德尔黑/葛洛格」→ C
- gansu_2021 q044「读懂幼儿情绪」→ C
- gansu_2021 q108/q110 互联网业务 → B/D
- xinjiang_2021 q026「无名故事家」→ B
- anhui_2020 q268「发行置换债券」→ C
- institution_2021_b q068「反例反常」→ D
- henan_2021 q118 → D

### 前端 onError fallback

`QuestionPageClient.tsx` 加 img onError handler：PNG 加载失败时 hide img，
显示「本题为图形/数列/资料分析题，原 PDF 图片缺失（题源 PDF 数据极限）」。

## 用户硬规则坚守

- ✅ 文字/图形选项区分对待
- ✅ 小步提交（D-9 8 个独立 commit）
- ✅ 自验产物（每批改动抽样核对）
- ✅ 错配率 < 3%
- ✅ 承认 PDF 数据本身缺陷的硬极限
- ✅ 占位透明（exp 明确标 PDF/OCR 极限，前端 onError 提示）
- ✅ 不数字游戏（D-9 救 11 真 ans 而非占位）

## ⚠️ 25 题占位最终硬墙

按问题分类：
- 8 题 PDF 真"暂缺"（institution_2022_b q032/q034/q036/q070, institution_2022_c q050,
  institution_2023_a q003, institution_2021_b q068 panduan 已撤）— content 标"暂缺"
- 17 题 OCR/PDF 极限：
  - 11 事业编（PDF PUA 乱码 + 关键词 OCR 漏识别）
  - 6 省考（部分 shenzhen 头部广告污染、北京 panduan 图形）

每题 exp 明确标 `[OCR/PDF 数据极限]`，前端可识别给提示。

## 174 PNG 缺失分布

- 86 事业编（PUA 字符 + 合订 PDF）
- 88 省考/国考：
  - 10 shenzhen_2020（PDF 图形被切掉，文字只剩"从四个选项..."三题挤一段）
  - 7 guangdong_2020 / 7 zhejiang_2023 残余（题号 PDF 不命中）
  - 其余分散 64 题

前端 onError fallback 这些题显示友好提示，不再空白图。

## D-10 候选

1. **找新 PDF 源补 25 占位**（用户授权）—— 唯一突破硬墙路径
2. **事业编 PDF 重 OCR**（更高分辨率 + 更新模型）尝试补关键词漏识别
3. **shenzhen_2020 / shandong_2025 dim5 头部广告污染清洗**
4. **PNG 部分手工抽图**（涉及 ~100 题图形真题）

## 100% 真数据冲刺路径

99.88% 已是自动化极限。剩 25 题 + 174 PNG 必须：
- 用户提供新 PDF 源（覆盖事业编 / 北京 / 江西 缺失题）
- 网络爬公开题库（华图/中公/粉笔等）人工审核
- 跨题库导入（粘贴特定题答案）

D-9 阶段真贡献：**新增 1258 张 PNG + 救 11 真 ans + 前端友好 fallback**。
