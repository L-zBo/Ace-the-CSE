# D-5 收官总进度报告（2026-05-03）

## 全库终态

### 行测（xingce）

| 类型 | 总题 | 缺 ans | 缺 exp | 空 options | 空 content | 完整率 |
|---|---|---|---|---|---|---|
| **国考** | 3,435 | **0** | **0** | **0** | **0** | **100.00%** ✅ |
| **省考** | 14,663 | 145 | 127 | 136 | 60 | 99.01% |
| **事业编** | 2,007 | 24 | 25 | 35 | 7 | 98.80% |
| **全库** | **20,105** | **169** | **152** | **171** | **67** | **99.16%** |
| 图片 | 792 PNG | missing=0 | orphans=0 | — | — | 维度 4 全清零 ✅ |

### 申论（shenlun）

- **652 题**（5 类：duice/fenxi/guanche/guina/xiezuo）
- answer + explanation **100% 覆盖**
- 前端 D-5 #8 增强渲染：6 类语义片段颜色高亮（详见下文）

## D-5 阶段净收益（vs D-4 末）

| 指标 | D-4 末 | D-5 末 | Δ |
|---|---|---|---|
| 全库完整率（缺 ans） | 99.15% (170 缺) | **99.16% (169 缺)** | +0.01 pp |
| 缺 explanation | 153 | **152** | -1 |
| 空 options | 189 | **171** | -18 |
| **空 content（新维度）** | 138 | **67** | **-71** |
| **水印污染（新维度）** | 1956 处 | **0 处** | **全清** |
| q000 占位脏数据 | 0 | 0 | (D-4 已清) |

## D-5 各步成果

| # | 任务 | 成果 |
|---|---|---|
| #0 | 启动调研 | 申论 652 题 + 5 类型确认；前端已有 ShenlunAnalysis 命中评估 |
| #1 | 全库 6 维体检 | 暴露 138 空 content + 1846 水印 + 6 PNG 严重异常 |
| #1.1 | 救空 content | 138 → 65（**73 题救出**），ABCD 锚定切块 + 头部页码清理 |
| #1.2 | 清洗水印 | 1956 处 → 0（content 189 + 选项 272 + 解析 1495） |
| #2 | PNG 质量审 | 792 张全完整无损坏，6 张严重异常待重抽 |
| #3 | 省考 146 诊断 | qinghai_2024 q072 救 1（HEAD_BRACKET_NX_EXT），剩为 PDF 极限 |
| #4 | 事业编 24 极限确认 | +0 ans / +3 exp（institution_2023_b/c/e 各 1） |
| #5 | exp 与 ans 同缺确认 | 151 题双缺，1 题孤点（institution_2023_c q014）略过 |
| #6 | 空选项救 18 | 严格 fingerprint 校验后 18/154 注入（5/5 抽样 0 错配） |
| #7 | 冷门脚本归档 | 5 个 C 阶段脚本 → archive/scripts_legacy/，scripts/ 33→28 |
| #8 | 申论解析增强 | 6 类语义高亮 + 衬线字体 + 暗色模式（详见下文） |

## 关键工程产出

### 申论解析渲染（D-5 #8）

新组件 `src/app/practice/[questionId]/EnhancedShenlunBody.tsx`：

| 类别 | 示例 | 视觉 |
|---|---|---|
| `shenlun-frame` 框架词 | 一是 / 二是 / 首先 / 其次 / 同时 | 蓝色加粗 + 左竖线 + 浅蓝底 |
| `shenlun-policy` 政策术语 | 高质量发展 / 乡村振兴 / 共同富裕 | 玫红加粗 + 虚下划线 |
| `shenlun-transition` 转折总结 | 因此 / 综上 / 总之 / 可见 | 绿色加粗 |
| `shenlun-keyword` 动态关键词 | 来自 keyPoints | 黄色高亮背景 |
| `shenlun-num` 数字+单位 | 25% / 3.2亿元 / 2025年 | 青色等宽字体 chip |
| `shenlun-numbered` 数字编号 | 1. / 2. / ① / (一) | 紫蓝 chip |

行级识别：
- 数字编号行 → 编号 chip + 内容
- (一)/一、 小节标题 → 加底边框 + primary 色
- 普通段落 → 首行缩进 2 字符 + 衬线字体（Source Han Serif SC）

样式实现：`src/app/globals.css` 加 `.shenlun-*` class + 暗色模式版本。
不引入新依赖（ReactMarkdown 改自定义渲染）。

### 空 content 救援（D-5 #1.1）

新脚本 `scripts/fix_empty_content.py`：
- `find_question_pdf`: glob `material/.../行测.../题目/*.pdf`（注意 `【】` 在 glob pattern 里被当字符类，必须宽 glob + 字符串过滤）
- `ABCD_BLOCK_RE`: 以连续 `A./B./C./D.` 4 选项段为锚（应对 hlj 2022 等 PDF 题号穿插在题干和选项之间的怪异排版）
- `_clean_stem_head`: 剥头部上一题选项跨页残尾，按"年份/下列/根据/某/习近平"等题干典型起头模式截取（修了 `^|` alternation 空匹配 bug）
- 去首部页码 N/M 与独立数字行

### 水印清洗（D-5 #1.2）

新脚本 `scripts/clean_watermarks.py`：
- 11 种水印 pattern：`公考事业编学习资料加微信AS73982` / `事业单位联考真题` / `老师微信：AS73982` / `· N ·` / `TB：Seeyee` 等
- 整理多余空白行
- 一次性清 1956 处实例 → 0

### 体检与诊断工具（D-5 持续工作）

- `scripts/audit_d5_full.py` 全库 6 维体检（V1-V6）+ Markdown 报告
- `scripts/audit_png_quality.py` 792 张 PNG 实质质量审（尺寸/文件大小/比例）
- `scripts/diagnose_provincial_146.py` 逐题在答案 PDF + 真题 PDF 上下文判定可救性
- `scripts/scan_dim5_consistency.py` 题号-内容一致性扫描（含算法局限说明）
- `scripts/fix_empty_options_d5.py` 严格 fingerprint 校验注入选项

## 剩余 169 缺 ans 分布

省考 145 题：
- ~110 PDF 写'暂缺/题目缺失'（极限）
- ~30 题号越界（极限）
- ~5 PDF 写'本题无正确答案'（极限）
- ~少数极小（接近极限）

事业编 24 题：
- 5 暂缺/缺失（PDF 真无）
- 11 类比 PDF 库无对应题
- 4 '关于 X' 短题指纹模糊
- 4 水印污染重（清洗后仍指纹不命中 = PDF 库无对应）

## D-6 候选

1. 6 张 PNG 严重异常重抽（national_2025_dishi q115/126, sichuan_2021 q098 等）
2. 65 题剩余空 content（多扫描版需 GPU OCR）
3. 35 题 V2_partial_empty_options（ABCD 部分空）
4. 申论 keyPoints 字段静态化（当前从 answer 动态抽取，可预计算入库）
5. dim5 真题 PDF 库构建用于精准一致性检测
6. 找新版 PDF 数据源覆盖 ~140 PDF 自身缺题

报告生成：2026-05-03 / 国考 100% 闭环 / 全库 99.16% / 申论 100%
