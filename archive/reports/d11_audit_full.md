# D-11 #1 全库审计扫描报告

**扫描日期**: 2026-05-04  
**总文件数**: 728  
**总题数**: 20097  
**总问题数**: 14452

## 按严重程度

- **HIGH**: 16
- **MEDIUM**: 112
- **LOW**: 14324

## 按问题类型（高频前 15）

- `topic_mismatch`: 12387
- `opt_order_disorder`: 1937
- `content_noise`: 90
- `opt_label_anomaly`: 11
- `content_too_long`: 11
- `opt_too_long`: 9
- `opt_count_anomaly`: 4
- `answer_label_missing`: 2
- `explanation_poison`: 1

## HIGH 严重度题目清单（前 50）

- `institution-xingce-panduan-2020-c-061` (opt_count_anomaly): options 个数 = 2 (expected 4)
- `institution-xingce-panduan-2020-c-062` (opt_count_anomaly): options 个数 = 2 (expected 4)
- `institution-xingce-panduan-2020-c-063` (opt_count_anomaly): options 个数 = 2 (expected 4)
- `institution-xingce-panduan-2020-c-063` (answer_label_missing): answer = 'B' 含 ['B'] 不在 options labels ['A', 'C'] 中
- `institution-xingce-panduan-2020-c-064` (opt_count_anomaly): options 个数 = 2 (expected 4)
- `institution-xingce-panduan-2020-c-064` (answer_label_missing): answer = 'D' 含 ['D'] 不在 options labels ['A', 'C'] 中
- `institution-xingce-panduan-2020-c-095` (opt_too_long): option D 长度 = 299（疑似混入别题）
- `institution-xingce-panduan-2022-b-092` (opt_too_long): option D 长度 = 374（疑似混入别题）
- `institution-xingce-shuliang-2022-b-055` (opt_too_long): option D 长度 = 306（疑似混入别题）
- `national-xingce-yanyu-2017-fushengjia-037` (opt_too_long): option D 长度 = 250（疑似混入别题）
- `national-xingce-yanyu-2019-fushengjia-043` (opt_too_long): option A 长度 = 275（疑似混入别题）
- `national-xingce-yanyu-2019-fushengjia-043` (opt_too_long): option D 长度 = 258（疑似混入别题）
- `provincial-beijing-xingce-yanyu-2022-050` (opt_too_long): option D 长度 = 1093（疑似混入别题）
- `provincial-qinghai-xingce-yanyu-2024-042` (explanation_poison): explanation 含 '学习强国' 但 content 不含（D-9 指纹注入嫌疑）
- `provincial-xinjiang-xingce-yanyu-2021-031` (opt_too_long): option D 长度 = 274（疑似混入别题）
- `provincial-jiangsu-xingce-ziliao-2024-130` (opt_too_long): option D 长度 = 209（疑似混入别题）
