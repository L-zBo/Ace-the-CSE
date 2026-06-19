## 归档说明

这里存放的是项目推进过程中产生的阶段性排障脚本、一次性修复脚本和局部年份核查脚本。

这些脚本目前不再是主流程入口，保留它们只是为了后续追溯历史排查过程，而不是继续作为日常工具使用。

当前主流程以这些脚本为准：

- `[scripts/extract_questions.py]`
  统一负责国考/省考/事业编行测PDF抽取，当前已经支持覆盖式重抽、双栏选项修复、坏题补捞。
- `[scripts/audit_xingce.py]`
  统一负责题量、模块分布、缺号、重复号、选项完整性的结构化审计。
- `[scripts/batch_national_xingce.py]`
  国考批量抽取入口。
- `[scripts/batch_provincial_xingce.py]`
  省考批量抽取入口。
- `[scripts/batch_institution_xingce.py]`
  事业编批量抽取入口。
- `[scripts/compare_pdf_engines.py]`
  当前抽取器与外部PDF引擎的对照评估入口。

归档原则：

- 已被统一脚本能力覆盖
- 没有被项目其余代码、测试或运行入口引用
- 主要用于某一年度、某一卷别、某一阶段临时排障

如果以后要继续清理，优先看这里，不要先对主流程脚本下手。
