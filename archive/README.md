# archive/ 归档说明

本目录收纳项目推进过程中产生的、**当前主流程已不再依赖**的中间产物。
保留的目的是事后追溯，不是继续作为日常工具使用。

## 目录结构

```
archive/
├── reports/                        # 一次性审计/总结报告
│   ├── 2025_fix_summary.md           — 2025 国考修复阶段性总结
│   ├── audit_report.md/.json         — 早期图片审计快照（现产物已改落 reports/audit_figures.*）
│   ├── extracted_missing_questions.json — 2025 国考补抽中间数据
│   ├── incomplete_options.json       — 选项不全审计输出
│   ├── national_count_audit.md       — C 阶段 #1 国考题数审计
│   └── options_completeness_audit.md — 选项完整度审计
├── web_probes/                     # 抓取源站的原始快照（73 个，31 MB）
│                                     HTML/PDF/TXT/JS，D13-D17 找题源阶段的取证原料。
│                                     2026-08-12 从 data/ 顶层搬来（当时散着 112 个 tmp_*）。
│                                     已确认全仓无引用；lint 在 eslint.config.mjs 里跳过本目录。
├── surveys/                        # 一次性调研文档
│   ├── d16_c_github_survey.md        — GitHub 公开题库可用性调研
│   ├── d17a_xiaomai_survey.md        — 小麦题库覆盖度调研
│   ├── d17_webapp_test_report.json   — D17 阶段网页自测输出
│   └── baijing_examkey_paperid.tsv   — 白鲸站 examKey↔paperId 对照表
├── e1_vision_poc/                  # E1 视觉抽题 POC 产物（正式版在 data/e1_vision/）
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

## 搬进 web_probes/ 前必须确认的事

`data/` 下还留着几类**不能搬**的东西，搬了会断链：

| 留在 data/ 的 | 谁在引用 |
|---|---|
| `tmp_lgwy_shandong_2022.txt` | `src/data/xingce/changshi/provincial_shandong_2022.json` 的溯源字段 |
| `tmp_xg_{gansu,hainan,ningxia}_2024.txt` | `src/data/xingce/ziliao/provincial_hainan_2024.json` 的溯源字段 |
| `tmp_figs/` | `scripts/fill_missing_figures.py` |
| `tmp_verify_question.png` / `tmp_verify_related.png` | `scripts/verify_lazy_loader.py` / `verify_related_appearances.py` |
| `tmp_github_aat/` `tmp_github_fenbi/` | `docs/DEV_PERFORMANCE.md` |
| `gap_rescue_pack/` | `AGENTS.md` 铁规矩，救援落档目录 |
| 各 `*_cache/` | 对应的 `fetch_*.py` / `d13_*.py` / `d16_*.py` |

## 当前主流程脚本（在 `scripts/` 下，不要往这里搬）

| 脚本 | 作用 |
|---|---|
| `extract_questions.py` | 国考/省考/事业编行测 PDF 抽题统一入口 |
| `extract_figures.py` | 题图提取统一入口 |
| `extract_shenlun.py` | 申论抽题入口 |
| `audit_xingce.py` | 题量/模块/缺号/重复/选项完整性审计 |
| `audit_full.py` | 全库审计（字段/答案/解析/重复/占位），产 `reports/audit_full.json` |
| `audit_figures.py` | 图片质量审计，产 `reports/audit_figures.md/.json` |
| `placeholder_lib.py` | 占位/不可作答判定的 Python 侧唯一实现（对齐 `src/lib/placeholder.ts`） |
| `generate_question_index.py` | 重抽完后重生成题目索引 |
| `generate_cross_paper_links.py` | 重抽完后重生成跨卷同题关联 |
| `batch_national_xingce.py` | 国考批量抽取 |
| `batch_provincial_xingce.py` | 省考批量抽取 |
| `batch_institution_xingce.py` | 事业编批量抽取 |
| `batch_extract_figures.py` | 图片批量提取 |
| `compare_pdf_engines.py` | 多 PDF 引擎对照 |

⚠️ `generate_loader.py` 已废弃并移入本目录（`generate_loader.deprecated-2026-08-09.py`，带运行拦截）。
跑它会把懒加载重构整个冲掉，别捡回来。

`scripts/legacy/` 已被合并进本目录的 `scripts/national_2025_debug/` 和 `scripts/national_year_checks/`，原 README 保留为 `scripts/LEGACY_README_OLD.md`。后续清理优先看 `archive/`，不要先动 `scripts/` 主流程脚本。
