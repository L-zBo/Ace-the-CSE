# D-4 收官总进度报告（2026-05-03）

## 全库终态

| 类型 | 总题 | 缺 ans | 缺 exp | 空 opts | 完整率 |
|---|---|---|---|---|---|
| **国考** | 3,435 | **0** | **0** | **0** | **100.00%** ✅ |
| **省考** | 14,663 | 146 | 128 | 154 | 99.00% |
| **事业编** | 2,007 | 24 | 25 | 35 | 98.80% |
| **全库** | **20,105** | **170** | **153** | **189** | **99.15%** |
| 图片 | 792 PNG | missing=0 | orphans=0 | — | 维度 4 全清零 ✅ |

## D-4 阶段成果（vs D-3 末）

- 缺 ans: **313 → 170**（净救 **143 题**）
- 完整率: **98.4% → 99.15%**（+0.75 pp）
- 空选项: 196 → 189（净救 7 题，含 D-4 #4 删 3 个 q0 脏数据 + #7 注入 5 题选项 - #5 注入 +1 题但 build_library 整顿）

## D-4 各步收益

| # | 任务 | 净救 ans | 备注 |
|---|---|---|---|
| #1 | OCR 切 CUDA GPU (4060 Ti) | 0 | 单页 1.5s vs CPU 6s, ~4x 加速 |
| #2 | GPU OCR 复核省考 5 卷扫描版 | 0 | 确认 18 题为 PDF 自身缺失 |
| #3 | GPU OCR 兜底事业编 PDF 空白页 | +84 | 跑 8 PDF, 497 页 OCR ~12 min |
| #4 | HEAD_BRACKET_NX_EXT/ANS_NEW_TYPO | +9 | √/× 判断题 + C/A 双答案 + PDF 笔误 |
|   | 删 3 个 q0 占位脏数据 | -3 题净 | 资料分析"材料前导段"非真题 |
| #5 | 事业编 fp 门槛降为 4 + 水印清洗 + 冒号统一 | +47 | 类比推理 4-7 字短题 + AS73982 水印 |
| #6 | 维度 5 一致性扫描（标限制） | 0 | 算法局限：需真题 PDF 库（D-5 候选） |
| #7 | 事业编空选项从真题 PDF 抽 ABCD | 0 | 但填了 5 题选项 |

## 关键工程产出

### OCR GPU 化（D-4 #1）

- `scripts/ocr_engine.py`：`make_engine(use_gpu=True)` 统一工厂
  - `EngineConfig.onnxruntime.use_cuda=True` + `cuda_ep_cfg.device_id=0`
  - 自动检测 CUDA EP 不可用回落 CPU + 告警
- `pip install onnxruntime-gpu==1.25.1`（CUDA 12 系，自动适配 driver 12.7）
- RTX 4060 Ti 单页 1.5s 稳定速度（CPU 约 6s）

### Regex 工具栈（D-4 累计 11 种 HEAD + 11 种 ANS）

新加：
- `HEAD_BRACKET_NX_EXT`: 兼容 `【解析N—正确答案√/×】` / `【解析N—正确答案C/A】`
- `ANS_NEW_TYPO`: 兼容 PDF 笔误 `因此，选项X 选项`
- `_normalize_ans_token()`: `√→A` / `×→B` / `C/A→C` 取首

### 事业编工具栈

- `fix_institution_answers.py --use-ocr`: GPU OCR 兜底空白/CID 乱码页
  - OCR 缓存 `archive/reports/ocr_institution_{cls}_{kind}.txt` (8 个文件)
  - D 类（PDF 全 CID 乱码且无 JSON 数据）跳过节约时间
  - normalize_content + WATERMARK_PAT 清洗 `公考事业编学习资料加微信AS73982`
  - fingerprint 门槛 10 → 4 救类比推理
  - 全角/半角冒号统一 `：/:/∶` → `∶`

- `fix_institution_options.py`: 真题 PDF 选项库（1182 题）+ 注入

### 一致性扫描（仅报告）

- `scripts/scan_dim5_consistency.py` + `archive/reports/dim5_consistency_d4.md`
  - 11381 可疑题，明确标"绝大多数为误报"（答案 PDF 不复述题干）
  - 真正可信检测需建『真题 PDF』库

## 剩余 170 缺 ans 分布与可救性

### 省考 146 题（按 archive/reports/provincial_gap_d3.md）

- ~110 PDF 标"暂缺/题目缺失"——硬极限
- ~30 PDF 题号越界（PDF 实际最大题号小于 JSON 题号）——硬极限
- ~5 PDF 写"本题无正确答案"——硬极限
- ~5 块存在但 ans regex 还抽不到（gansu_2022 q63 / shanghai_2020 q74 等）：
  - q63 PDF 解释末尾"x=-182 y=58"无答案字母
  - q74 PDF 写"故本题没有正确答案"
  - 接近硬极限

### 事业编 24 题

- 5 暂缺/缺失/题目缺失（PDF 真无）
- 11 类比推理 PDF 库无对应题（不同年/类）
- 4 "关于 X" 短题指纹不够精确
- 4 水印污染重，清洗后 fingerprint 仍不命中
- 1 题号孤碎

## D-5 候选（如继续推进）

1. **省考真题 PDF 库**：构建 119 卷真题 PDF 索引，做精确维度 5 一致性 + 选项抽取
2. **事业编 id 跨年份冲突**：institution_2020_c 同 JSON 多 q005 等（year/month 切分 bug）
3. **空选项 184 题**：上一步建好真题库后批量补
4. **再啃 ~25 题硬极限**：找新版 PDF 源 / 网络答案对照（需用户授权）

报告生成：2026-05-03 / 国考闭环 / 全库 99.15%
