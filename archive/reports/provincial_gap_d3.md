# 省考答案缺口分析（D-3 收尾 / D-4 GPU OCR 复核）

总 14666 题，缺 ans 158（98.9% 完整率）

D-4 #2 GPU OCR 复核结论：5 卷 OCR 类（chongqing_2021/gansu_2021/guangdong_2021/henan_2021/xinjiang_2021）合计 18 题，**全部经 GPU OCR 重抽确认 PDF 自身缺失**（OCR 已抽到 PDF 上能扫到的全部内容，缺题题号在 OCR 文本中找不到任何题号标志）。

| examKey | 缺 ans | 原因诊断 |
|---|---|---|
| provincial_anhui_2020 | 1 | PDF: 1题号越界(PDF最大=110) |
| provincial_beijing_2020 | 7 | PDF: PDF 标注"暂缺"×4; 5题号越界(PDF最大=129) |
| provincial_beijing_2022 | 2 | PDF: OCR/PDF 漏抽 1 题 |
| provincial_beijing_2023 | 16 | PDF: PDF 标注"暂缺"×52 |
| provincial_chongqing_2021 | 1 | PDF: GPU OCR 复核确认 PDF 缺 q9 答案 |
| provincial_chongqing_2024 | 1 | PDF: OCR/PDF 漏抽 1 题 |
| provincial_gansu_2021 | 8 | PDF: GPU OCR 复核确认 PDF 缺 q40/44/45/104/108/110/114/120 答案 |
| provincial_gansu_2022 | 1 | PDF: 块存在但 ans regex 未抽到 |
| provincial_gansu_2023 | 1 | PDF: 1题号越界(PDF最大=0) |
| provincial_gansu_2024 | 8 | PDF: PDF 标注"暂缺"×8 |
| provincial_guangdong_2021 | 5 | PDF: GPU OCR 复核确认 PDF 缺 q91-95 连号 |
| provincial_guangdong_2023 | 1 | PDF: PDF 标注"暂缺"×2 |
| provincial_guangdong_2024 | 4 | PDF: OCR/PDF 漏抽 4 题 |
| provincial_hainan_2024 | 4 | PDF: PDF 标注"暂缺"×5; 1题号越界(PDF最大=109) |
| provincial_hebei_2020 | 1 | PDF: 1题号越界(PDF最大=130) |
| provincial_hebei_2022 | 3 | PDF: PDF 标注"暂缺"×4; 1题号越界(PDF最大=129) |
| provincial_hebei_2023 | 1 | PDF: OCR/PDF 漏抽 1 题 |
| provincial_heilongjiang_2022 | 1 | PDF: 1题号越界(PDF最大=119) |
| provincial_henan_2021 | 3 | PDF: GPU OCR 复核确认 PDF 缺 q116-118 连号 |
| provincial_hubei_2020 | 1 | PDF: 1题号越界(PDF最大=125) |
| provincial_hunan_2024 | 1 | PDF: PDF 标注"暂缺"×1 |
| provincial_jiangsu_2020 | 1 | PDF: OCR/PDF 漏抽 1 题 |
| provincial_jiangsu_2024 | 5 | PDF: PDF 标注"暂缺"×6 |
| provincial_jiangxi_2020 | 15 | PDF: 15题号越界(PDF最大=120) |
| provincial_jilin_2024 | 9 | PDF: PDF 标注"暂缺"×8 |
| provincial_ningxia_2023 | 1 | PDF: 块存在但 ans regex 未抽到 |
| provincial_ningxia_2024 | 4 | PDF: PDF 标注"暂缺"×4 |
| provincial_qinghai_2024 | 4 | PDF: PDF 标注"暂缺"×6 |
| provincial_shandong_2020 | 1 | PDF: 1题号越界(PDF最大=90) |
| provincial_shandong_2022 | 1 | PDF: PDF 标注"暂缺"×2 |
| provincial_shandong_2024 | 1 | PDF: OCR/PDF 漏抽 1 题 |
| provincial_shanghai_2020 | 1 | PDF: 块存在但 ans regex 未抽到 |
| provincial_shanghai_2023 | 3 | PDF: 块存在但 ans regex 未抽到 |
| provincial_shanxi_2023 | 1 | PDF: 1题号越界(PDF最大=124) |
| provincial_shanxi_2024 | 1 | PDF: OCR/PDF 漏抽 1 题 |
| provincial_shenzhen_2020 | 20 | PDF: PDF 标注"暂缺"×1; 20题号越界(PDF最大=80) |
| provincial_sichuan_2024 | 1 | PDF: 块存在但 ans regex 未抽到 |
| provincial_tianjin_2024 | 1 | PDF: OCR/PDF 漏抽 1 题 |
| provincial_xinjiang_2021 | 1 | PDF: GPU OCR 复核确认 PDF 缺 q26 |
| provincial_xinjiang_2023 | 19 | PDF: PDF 标注"暂缺"×19 |

## D-4 可救项汇总

经 GPU OCR 复核与诊断更新后，剩余 158 题中实际**技术上可救**的为：

- **块存在但 ans regex 未抽到 (5 题)**：gansu_2022 q?, ningxia_2023 q?, shanghai_2020 q?, shanghai_2023 q?×3, sichuan_2024 q? — 加第 10 种 HEAD/ANS regex 可救

- **OCR/PDF 漏抽 (~12 题)**：beijing_2022 q?, chongqing_2024 q?, guangdong_2024 q?×4, hebei_2023 q?, jiangsu_2020 q?, shandong_2024 q?, shanxi_2024 q?, tianjin_2024 q? — 文字层 PDF 已在但切块漏，需要细看

其余约 **141 题**为 PDF 数据本身缺失（PDF 自己写"暂缺/题目缺失"或题号超出 PDF 范围），属硬性极限。

