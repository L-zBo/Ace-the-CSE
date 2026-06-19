# D-12 进度报告（2026-05-04 → 05-08）— 从外部公开题库源补 OCR 失败题

## 背景

D-11 末，HIGH 异常 1476→149（-89.9%）已完成。但 D-11 #4 标记的
[题干/选项 OCR 抽取失败-D11] 占位题仍是用户做题最痛点：

- 题干 OCR 失败: **92 题**
- 选项 OCR 失败: **529 题**（D-11 #4 + #7 累计）
- **总计 621 题**用户做不了

D-12 启动，从公开题库源补全这 621 题。

## D-12 流程（已闭环 + 已工具化）

1. `scripts/scan_d11_unrecoverable_d12.py` 扫全库 → 621 题清单 + 文件分布
2. mcp__exa fetch 整卷 PDF → 落 `data/pdf_cache/{卷名}_pdf.json`
3. `scripts/rescue_from_pdf_d12.py` 通用工具：
   - 解析 PDF 文本 → {qnum: {content, options, answer, exp}}
   - 题干前 25 字归一化模糊匹配（容忍 OCR 空格/标点差异）
   - --accept-pdf-ans 选项允许 D-8 答案错位修正
4. 写入 + commit

## D-12 已完成（24 题，8 个 commit）

| commit | qid / 题目 | 答案 | 备注 |
|---|---|---|---|
| `59c3900` D-12 #1 | shanghai-changshi-2021-005 中世纪西方哲学 | **B** | 手工 POC |
| `4ba91d0` D-12 #2a | shanghai-changshi-2021-067 易拉罐 8π+48 | **D** | 手工 |
| `4ba91d0` D-12 #2b | shanghai-panduan-2021-070 飞机场 19/33 | **D** | 手工 |
| `227a467` D-12 #3 | （启动报告 + MEMORY 备忘） | — | 文档 |
| `b8b9dd2` D-12 #4 | **批量 9 题（通用工具落地）** | — | **见下** |
| `b20a0f3` D-12 #5 | （进度报告同步到 12 题） | — | 文档 |
| `ebac99b` D-12 #6 | 通用工具升级（顿号/source-label/阈值 0.7） | — | 工具 |
| `aef963c` D-12 #7 | **四川 2022 数量 8 题救援** | — | **本会话** |
| `adf95a9` D-12 #8 | **浙江 2022 数量 4 题（含 2 题 ANS 修正）+ 全局回退** | — | **本会话** |

### D-12 #7 四川 2022 数量 8 题（OPT 100% 命中）

源：gkzenti.cn《2022 年四川下半年公务员录用考试行测》考生回忆版（fenbi）

| qid | 题目 | ans | match |
|---|---|---|---|
| sichuan-2022-shuliang-041 | 甲乙丙班期末平均 | B(77) | 100% |
| sichuan-2022-shuliang-042 | 零件车间运货 | A(18) | 100% |
| sichuan-2022-shuliang-043 | 甲乙地下坡平路上坡 | C(2小时40分) | 100% |
| sichuan-2022-shuliang-045 | 培训学时 | B(26) | 100% |
| sichuan-2022-shuliang-046 | 轮船灯塔北偏西 | A(10) | 92% |
| sichuan-2022-shuliang-048 | 等位号数字组合 | C(8) | 100% |
| sichuan-2022-shuliang-049 | 6 月销售电器 | B(600) | 100% |
| sichuan-2022-shuliang-050 | 游泳运动员相遇 | D(630) | 100% |

### D-12 #8 浙江 2022 数量 4 题（含 2 题 ANS 修正 + 工具全局回退）

源：展鸿教育《2022 年浙江省公务员录用考试试卷（A 卷）》（static.32xueyuan.com）

| qid | 题目 | 库 ans | 真 ans | match |
|---|---|---|---|---|
| zhejiang-2022-shuliang-057 | 4 位专家 3 勘探点 | C | C | 100% |
| zhejiang-2022-shuliang-059 | 乾隆回文联三位回文数概率 | D | D | 92% |
| zhejiang-2022-shuliang-010 | 同 q057（库内冗余 ID） | B → **C** | C | 100% |
| zhejiang-2022-shuliang-015 | 同 q059（库内冗余 ID） | B → **D** | D | 92% |

⏭ 跳过 4 题数列题（q051-053/q002，PDF 选项标"缺"）。

工具升级：
- 全局扫描回退：当 lib_qn ±3 范围匹配 < 70% 时全局扫描（题号偏移大的卷如 zhejiang 偏移 +50）
- 阈值收紧 0.5 → 0.7（避免低 match 误判）
- 顿号选项支持（事业编 PDF 用 `A、` 而非 `A.`）
- --source-label 参数化（不 hardcode 上海卷）

### D-12 #6 事业编 2021 B 卷尝试（成果 0，留存教训）

chinagwy.org fetch 5.22 联考 B 类整卷 100 题题干 + 选项后跑工具，
14 题待修题模糊匹配最高 64% 全部跳过——库内 institution_2021_b
与 chinagwy 5.22 联考 B 类原版**题号系统不一致**（库版本可能是
其他地区/版本，待 D-13 重新查证库 ID 归属）。

事业编 2020 A 卷同样尝试 chinagwy 整卷后发现：库 q065 题干"农具"等
与 chinagwy q66「计算器:搅拌机」类比题对不齐，**事业编整批库版本归属
存疑**，需 D-13 系统排查。

### D-12 #4 批量 9 题明细

✅ changshi 5 题 ANS 错位修正（D-8 默认 A 副作用）：

| qid | 题目 | 库 ans | 真 ans |
|---|---|---|---|
| changshi-2021-036 | 温室气体来源 | A | **D** |
| changshi-2021-070 | 盲盒概率 | D | **C** |
| changshi-2021-077 | 在线政务用户 | B | **A** |
| changshi-2021-083 | 广东其他地区城镇化率 | A | **C** |
| changshi-2021-087 | 日均回收量增长率 | D | **B** |

✅ changshi-2021-073 完整补全（D，与库内一致）
✅ panduan 3 题完整补全：q055（C）/ q056（B）/ q058（A）

⏭ 跳过 7 题（待 D-12 #5+ 处理）：
- 3 题 PDF 选项解析不全（需迭代 PDF 解析正则）
- 4 题题干模糊匹配 <50%（PDF 题号偏移大或题型差异）

## 重灾区文件 top 10（D-12 #4 后更新）

### 题干 OCR 失败
- institution_2021_b panduan: 5
- institution_2021_b shuliang: 4
- institution_2022_e changshi / 2020_e panduan / 2021_a panduan / 2023_c panduan / 2023_e panduan / 2024_c panduan: 各 3

### 选项 OCR 失败
- ~~shanghai 2021 changshi: 9~~（**已修 6 题**，剩 3）
- ~~shanghai 2021 panduan: 9~~（**已修 4 题**，剩 5）
- sichuan 2022 shuliang: 8
- institution_2020_a panduan: 7
- zhejiang 2022 shuliang: 7
- henan 2024 ziliao / ningxia 2024 ziliao: 各 7
- hainan 2024 ziliao / jiangsu 2022 ziliao / jiangxi 2023 ziliao: 各 6

## 关键发现

### 题号-卷别映射规则

库内 ID 的题号 ≠ 公开真题 B 卷题号（之前推断有误，D-12 #4 数据更新）。例：
- 库 panduan-q055 → PDF q52（match 96%）
- 库 panduan-q058 → PDF q55（match 100%）
- 库 changshi-q036 → PDF q36（match 100%，直接对齐）
- 库 changshi-q070 → PDF q70（match 100%）

**结论**：上海卷库 ID 题号 vs B 卷题号关系**不固定**，必须题干模糊匹配。

### 卷别错位（潜在问题，D-13 候选）

库内 ID 标 "changshi"（常识），实际题目可能是其他部分：
- shanghai-changshi-2021-005 内容是言语理解（B 卷第 5 题）
- 上海卷分 5 部分（言语/判断/数理/常识/综合分析），与别省的标准 5 部分不同

### 通用救援工具（D-12 #4 落地）

`scripts/rescue_from_pdf_d12.py` 能力：
1. PDF 文本解析（题号 → 完整题目结构）
2. 题干模糊匹配 + ±3 题号容差
3. PDF/库 ans 双重校验
4. --accept-pdf-ans 答案错位修正
5. --dry-run 预览
6. --lib-glob 切换目标库文件

下次会话推进路径：
```bash
# 例：处理河南 2024 ziliao
mcp__exa fetch 河南 2024 行测整卷 PDF → 存 data/pdf_cache/henan_2024_pdf.json
python scripts/rescue_from_pdf_d12.py \
  --pdf-cache data/pdf_cache/henan_2024_pdf.json \
  --lib-glob 'src/data/xingce/ziliao/provincial_henan_2024.json' \
  --accept-pdf-ans
```

### 公开真题源清单（D-12 已验证可用）

| 源 | URL | 价值 |
|---|---|---|
| 公考 PDF（永岸公考） | attachment-gwy-com.oss-cn-hangzhou.aliyuncs.com | **完整真题（A/B 类各一份）+ 解析**，最佳整卷源 |
| 星光公考 | xingguanggongkao.com/Wb/quesView/id/{N} | 题级独立 URL |
| 小麦公考 | xiaomaigongkao.com/Mobile/Ques/view/id/{N} | 题级独立 URL，含解析 |
| gwysydw.com | gwysydw.com/bs/dqgwy/news_{N}.html | 整卷收录 |

## 工作量估算

D-12 #4 工具化后：
- 单卷 fetch + 跑工具：~10 分钟 + 5 工具调用
- 命中率约 50-60%（受 PDF 解析正则和题号偏移影响）
- 621 题完整救援需要 ~30+ 张整卷 PDF + 多会话推进

## D-12 后续推进路径

### 高 ROI 优先（每文件多题，整卷一次救）

1. ~~shanghai 2021~~（剩 7 题，需迭代 PDF 解析正则）
2. **henan 2024 ziliao + ningxia 2024 ziliao**（各 7 题，资料分析整卷救援）
3. **institution_2021_b panduan + shuliang**（事业编 2021 B 类，9 题）
4. **sichuan 2022 shuliang / zhejiang 2022 shuliang**（各 7-8 题）

### 低 ROI 单点

- 各省 2024 ziliao 散题（各 4-6 题）

## 累计阶段性数字

- D-9 末: 25 占位 / 真完整率 99.88%
- D-10 末: 0 占位（22 真救 + 3 透明）/ 99.99%
- D-11 末: HIGH 1476→149（-89.9%）
- **D-12 当前: 621 透明占位 → 已救 24 题（3.9%），通用工具就位**
- **用户做题真实可用率: 96.54% → ~96.66%（+0.12 pp）**

## 用户硬规则学到的（本会话）

- **库版本归属未必跟外部源对齐**：事业编联考 ABCDE 五大类各省版本，
  chinagwy/gwysydw 这套源未必是库内对应版本，跑工具前**先 dry-run
  且阈值 ≥ 0.7**，命中率 < 50% 立即换源或弃卷
- **资料分析题靠题干前 30 字模糊匹配难命中**：题干太短同质化高，
  需要完整图表材料才能补救——本会话尝试河南 2024 资料 7 题失败
- **数量关系题救援命中率最高**：题干长且独特，模糊匹配能 100%
  对齐题号偏移大的卷别（浙江 2022 偏移 +50 也能救）

