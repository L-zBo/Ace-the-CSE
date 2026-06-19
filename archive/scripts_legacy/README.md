# 冷门/归档脚本目录

本目录存放已完成历史使命的脚本。**保留代码以便回溯，但不再用于现行流水线**。

## 已归档（D-5 #7, 2026-05-03）

| 脚本 | 用途 | 状态 |
|---|---|---|
| `fix_2015_options.py` | C 阶段 #3：修 2015 国考两套 10 题选项异常 → [图形选项]×4 | 已完成 |
| `fix_2023_answers.py` | C 阶段 #2：从 2023 国考三套答案 PDF 抽 answer + explanation 注入 JSON | 已完成（被 `fix_provincial_answers.py` 通用化取代） |
| `fix_2023_misalign.py` | C 阶段收尾：修 2023 国考 6 题历史错位 bug | 已完成 |
| `fix_scattered_answers.py` | C 阶段散点：扫 2015-2022 国考 11 卷剩余 23 ans + 10 exp | 已完成（被 `fix_provincial_answers.py` 取代） |
| `compare_pdf_engines.py` | 早期 PDF 提取引擎对比（pdfminer / fitz / pdfplumber） | 调研已完成，定型用 `fitz` |

## 何时复活

如果未来需要：
- 单卷一次性快速修复 → 复制相关脚本作为模板
- 对照不同 PDF 引擎效果 → 跑 `compare_pdf_engines.py`
- 排查老 commit 的修复逻辑 → 直接 git log 这些文件

## 现行流水线脚本（在 `scripts/`）

参见 `archive/reports/d5_*` 系列报告与 `scripts/audit_*` 工具。
