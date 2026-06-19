# archive/ 归档说明

本目录收纳项目推进过程中产生的、**当前主流程已不再依赖**的中间产物。
保留的目的是事后追溯，不是继续作为日常工具使用。

## 目录结构

```
archive/
├── reports/                        # 一次性审计/总结报告
│   ├── 2025_fix_summary.md           — 2025 国考修复阶段性总结
│   ├── audit_report.md/.json         — 早期图片审计快照（被 .gitignore 持续重写）
│   ├── extracted_missing_questions.json — 2025 国考补抽中间数据
│   ├── incomplete_options.json       — 选项不全审计输出
│   ├── national_count_audit.md       — C 阶段 #1 国考题数审计
│   └── options_completeness_audit.md — 选项完整度审计
├── data_backup_2025_before_fix/    # 2025 国考修复前的 JSON 备份
├── tmp_artifacts/                  # 排障过程中产生的 PNG / JSON 中间产物（原 tmp/，已 gitignored）
└── scripts/                        # 一次性脚本归档总仓（54 个）
    ├── LEGACY_README_OLD.md           — 原 scripts/legacy/README.md 留底
    ├── figures/                      — B 阶段图片裁剪/拼接/清洗 10 个脚本
    ├── national_classification/      — C 阶段 #1 国考分类 / level 修复 4 个脚本
    ├── empty_fields/                 — B 阶段空答案 / 空选项修复 6 个脚本
    ├── audits_legacy/                — 已被 scripts/audit_xingce.py 取代的早期审计 5 个脚本
    ├── national_2025_debug/          — 2025 国考阶段排障 17 个脚本（原 scripts/legacy/）
    └── national_year_checks/         — 国考各年份核查 12 个脚本（原 scripts/legacy/）
```

## 归档原则

- 已被统一脚本能力覆盖（`extract_questions.py` / `audit_xingce.py` / `batch_*_xingce.py` / `compare_pdf_engines.py`）
- 没有被项目其余代码、测试或运行入口引用（已 grep 确认）
- 主要用于某一年度、某一卷别、某一阶段临时排障

## 当前主流程脚本（在 `scripts/` 下，不要往这里搬）

| 脚本 | 作用 |
|---|---|
| `extract_questions.py` | 国考/省考/事业编行测 PDF 抽题统一入口 |
| `extract_figures.py` | 题图提取统一入口 |
| `extract_shenlun.py` | 申论抽题入口 |
| `audit_xingce.py` | 题量/模块/缺号/重复/选项完整性审计 |
| `audit_figures.py` | 图片质量审计（产 audit_report.md） |
| `batch_national_xingce.py` | 国考批量抽取 |
| `batch_provincial_xingce.py` | 省考批量抽取 |
| `batch_institution_xingce.py` | 事业编批量抽取 |
| `batch_extract_figures.py` | 图片批量提取 |
| `compare_pdf_engines.py` | 多 PDF 引擎对照 |
| `generate_loader.py` | 重抽完后重生成 questionLoader.ts |

`scripts/legacy/` 已被合并进本目录的 `scripts/national_2025_debug/` 和 `scripts/national_year_checks/`，原 README 保留为 `scripts/LEGACY_README_OLD.md`。后续清理优先看 `archive/`，不要先动 `scripts/` 主流程脚本。
