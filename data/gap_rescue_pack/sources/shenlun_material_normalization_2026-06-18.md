# 申论材料字段规范化记录（2026-06-18）

## 本轮处理

- 处理对象：`src/data/shenlun/**/*.json`
- 处理方式：只从每条记录已有的 `content` 正文中拆分字段，不新增、不改写真题材料和答案。
- 写入内容：
  - `material`：从原 `content` 中识别出的“给定资料/给定材料/阅读资料/申论材料”段。
  - `content`：保留试卷标题、注意事项和作答要求，移除已拆出的材料正文，减少前端重复展示。
  - `meta.materialRescuedBy = "D23-content-normalization"`
  - `meta.materialSource = "existing content field"`

## 审计结果

- 处理前：652 条申论记录中仅 5 条有可用 `material` 字段。
- 第一批规范化：501 条。
- 第二批规则补充后规范化：6 条。
- 处理后：652 条申论记录中 512 条有可用 `material` 字段，剩余 140 条。

处理后分布：

- `duice`：16 条，9 条有 `material`，7 条剩余。
- `fenxi`：1 条，1 条有 `material`，0 条剩余。
- `guanche`：170 条，92 条有 `material`，78 条剩余。
- `guina`：1 条，1 条有 `material`，0 条剩余。
- `xiezuo`：464 条，409 条有 `material`，55 条剩余。

对应报告：

- `sources/shenlun_material_audit_after_2026-06-18.json`
- `sources/shenlun_material_normalization_preview_2026-06-18.json`

## 剩余 140 条暂不硬拆原因

剩余记录大多属于以下情况：

- 原 `content` 里有材料开头，但旧抽取文本在作答要求前已经截断，无法稳定拆出题目要求。
- 材料和问题混排，缺少稳定章节边界，机械拆分容易把材料正文中的“问题一”等普通文本误判为作答要求。
- 少量早期地方卷没有标准“给定资料/作答要求”结构，必须回到 PDF 或可信网页逐卷核对。

## 后续 PDF 回填结果

2026-06-18 后续已按上述原则继续处理：使用 `scripts/rescue_shenlun_remaining_material.py` 逐题定位本地真题 PDF，用现有 `answer` 文本锚定答案区，再把卷面拆分为 `material` 与 `content`。

处理结果：

- 目标缺口：140 条。
- 已回填：140 条。
- 未解决：0 条。
- 回填方式：仅接受“本地 PDF 可定位 + 现有答案可锚定 + 卷面结构可拆分”的闭环，不使用猜测内容。
- 迁移镜像：`data/gap_rescue_pack/files/src/data/shenlun/`。
- 回填说明：`sources/shenlun_material_pdf_rescue_2026-06-18.md`。
- 回填后审计：`sources/shenlun_material_pdf_rescue_audit_after_2026-06-18.json`。
