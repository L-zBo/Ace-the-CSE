# Ace-the-CSE 数据补缺迁移包

这个文件夹用于把本机已经完成的数据补缺迁移到另一台仍处于旧数据状态的电脑。

## 当前范围

- 行测原始不可作答缺口：58 题
- 已确认补回并写入数据文件：8 题
- 已记录数据说明纠错：1 题（`institution_2022_c` 第 `050` 题，仍不可作答）
- 当前仍不可作答：50 题
- 申论材料字段补齐：先从现有申论正文拆出 507 个数据文件副本，后续又从本地 PDF 回源补齐剩余 140 条；当前 652 条申论记录均有 `material` 字段。

详细登记见 `rescue_register.json`。

## 文件结构

- `rescue_register.json`：补缺登记总表，记录原始缺口、已补题、剩余缺口、申论数据存放位置和迁移文件映射。
- `files/`：已经补好的数据文件副本，路径保持项目相对路径。
- `snapshots/`：补缺后的审计快照。
- `sources/`：本轮补缺使用的来源副本、文本抽取和来源说明。
  - `sources/unresolved_xingce_2026-06-17.md`：继续核查剩余 50 题后的未补原因和证据链。
  - `sources/unresolved_xingce_2026-06-19.md`：申论补齐后对剩余 50 题的跟进核查。
  - `sources/unresolved_xingce_2026-08-08.md`：2026-08-08 复查新公开源的结果（仍无新源，50 题不变）。
  - `sources/deep_probe_xingce_2026-08-09.md`：跨卷同源分析 + 一手全卷取证。证伪「按题号倒推」路线，
    更正事业编 2022 C 类第 050 题的错误认定，判定吉林 2024 共 13 题结构性无解。
  - `sources/institution_2022c_fullpaper_2026-08-09/`：事业编 2022 C 类一手全卷（贵州兴文 docx）与厚职网 2022 快照。
  - `sources/cross_paper_answer_fix_2026-08-11.md`：用跨卷同题反查答案矛盾，回本卷 PDF 复核后订正 18 道答案的
    完整证据链与改动清单。附一条认知更正：`material/` 里的「答案及解析」PDF 是培训机构整理版，
    不同机构会给出相反答案，「PDF 与库内一致」不构成独立证据。
  - `sources/explanation_block_cleanup_2026-08-11.md`：解析块清洗改进与剩余 100 道的根因诊断。
    修掉 `repair_explanations_from_pdf.py` 一个与自身 docstring 不符的 bug（会擅自改 answer），
    新增第三类排版切块器（4 种）与结论句式（7 种）。查明 `align_failed` 的死因是
    「一个 JSON 混装多套卷」的数据模型缺陷，以及几份合集 PDF 文件名标着 2024 实际只到 2023。
  - `sources/*_xingguang.pdf` / `sources/*_xingguang.txt`：星光公考公开 PDF 及抽取文本，用于证明北京、吉林、甘肃、内蒙古的目标题号仍是占位。
  - `sources/shenlun_material_normalization_2026-06-18.md`：申论材料字段规范化说明与 PDF 回填前的 140 条缺口来源。
  - `sources/shenlun_material_pdf_rescue_2026-06-18.md`：本轮从本地 PDF 回源补齐 140 条申论 `material` 的方法、结果和迁移说明。
  - `sources/shenlun_material_pdf_rescue_audit_after_2026-06-18.json`：PDF 回填后的审计快照。
- `apply_gap_rescue.ps1`：在项目根目录执行，可把 `files/` 中的文件复制回同路径。

## 迁移方式

把整个 `data/gap_rescue_pack` 文件夹复制到另一台电脑的项目根目录下，然后在项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File data/gap_rescue_pack/apply_gap_rescue.ps1
```

脚本只覆盖 `files/` 中的补缺/规范化数据文件，不会改 `package.json`、`start.bat` 或前端代码。

迁移后建议运行：

```powershell
python scripts/d17_list_unanswerable.py
python scripts/audit_shenlun_material.py
```

预期结果：行测不可作答数量为 50；申论 `material` 覆盖为 652 / 652，缺口为 0。

## 未补缺口说明

剩余 50 题不是简单漏清洗。继续核查后，公开可访问来源仍显示新疆 2023、北京 2023、吉林 2024、甘肃 2024、内蒙古 2023 和事业单位 C 类 2022 的对应题号为缺失、征集、默认 A、暂无收集到或关键条件打码。

详见 `sources/unresolved_xingce_2026-06-17.md`。后续只有找到完整题干、选项、答案和可解释来源闭环，才允许继续补题。
