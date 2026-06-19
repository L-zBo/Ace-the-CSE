# 申论 material PDF 回填记录（2026-06-18）

## 本轮目标

- 对象：上一轮 `content` 规范化后仍缺 `material` 的 140 条申论记录。
- 目标：不造数据、不猜题，把剩余缺口尽量从本地真题 PDF 回源补齐。

## 方法

使用脚本：`scripts/rescue_shenlun_remaining_material.py`

闭环条件：

- 通过题目年份、来源、省份/层级等信息定位本地 PDF 候选。
- 用现有 JSON 中的 `answer` 文本反向锚定 PDF 的答案区，确认 PDF 与当前题目匹配。
- 在答案区之前的卷面文本中识别材料区和作答要求区。
- 只有能稳定拆出 `material` 与 `content` 的记录才写回。

## 执行结果

- dry-run：目标缺口 140，可回填 140，仍未解决 0。
- apply：已写回 `src/data/shenlun/**/*.json` 与迁移镜像 `data/gap_rescue_pack/files/src/data/shenlun/**/*.json`。
- 回填后审计：申论总数 652，有 `material` 652，缺 `material` 0。
- 原始目标清单：`sources/shenlun_material_pdf_rescue_targets_2026-06-18.json`。

## 迁移说明

另一台旧项目机器复制整个 `data/gap_rescue_pack` 后，在项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File data/gap_rescue_pack/apply_gap_rescue.ps1
python scripts/audit_shenlun_material.py
```

预期审计结果：`totalShenlunQs = 652`，`hasMaterial = 652`，`missingMaterial = 0`。

## 注意

`reports/shenlun_material_pdf_rescue_preview.json` 是脚本运行时的预览报告，数据写回以 `src/data/shenlun/` 和本迁移包 `files/src/data/shenlun/` 为准。后续若继续补其它题库缺口，仍必须保留题干、选项、答案和来源证据链。
