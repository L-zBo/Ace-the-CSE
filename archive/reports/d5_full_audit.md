# D-5 #1 全库完整性体检报告（2026-05-03）

**全库 20097 题**

- 国考: 3435 题
- 省考: 14655 题
- 事业编: 2007 题

## 各维度异常计数

| 维度 | 描述 | 异常数 | 性质 |
|---|---|---|---|
| V1_content_empty | 题干 content 完全为空 | **0** | 硬错 |
| V1_content_placeholder | 题干 = "暂缺"/"缺失" | **8** | PDF 自身极限 |
| V1_content_short | 题干去空格 < 10 字（疑似切碎） | **944** | 可疑 |
| V2_no_options | options 数组为空 / 不存在 | **0** | 硬错 |
| V2_all_empty_options | options 存在但全部 content 空 | **0** | 硬错 |
| V2_partial_empty_options | options 部分空（A 有 B 无等） | **0** | 可疑 |
| V3_answer_missing | answer 字段缺失 | **0** | 硬错 |
| V4_explanation_missing | explanation/analysis 缺失 | **0** | 硬错 |
| V5_option_watermark | 选项 content 含水印 | **0** | 可清洗 |
| V5_content_watermark | 题干 content 含水印 | **0** | 可清洗 |
| V5_exp_watermark | 解析 explanation 含水印 | **0** | 可清洗 |
| V6_qn_zero | 题号末尾 = 000（占位脏数据） | **0** | 应删 |

## V3 (缺 answer) 按来源分布


## V4 (缺 explanation) 按来源分布


## V5 水印污染明细（前 50）


## V6 题号 0 占位题列表（应删）

