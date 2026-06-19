# D-13 changshi 残余文件清单

自动 batch 后还需人工或硬限保留的文件：

- `institution_2022_e.json` qns=['005', '016', '017', '019']  → **事业编联考 baijing 不覆盖（硬限）**
- `provincial_guangdong_2024.json` qns=['002', '003', '004', '005']  → **run_one 失败: [D-13 #42] 广东 2024 changshi dry-run …
  fixed=0  skipped=4
!! 0 修复 — 跳过本卷**
- `provincial_sichuan_2021.json` qns=['006', '007', '010', '012']  → **多候选无足够相似 paper [297, 295]**
- `provincial_zhejiang_2022.json` qns=['014', '018', '019', '029']  → **多候选无足够相似 paper [214, 212]**
- `provincial_heilongjiang_2021.json` qns=['006', '012', '019']  → **多候选无足够相似 paper [630, 628]**
- `provincial_zhejiang_2023.json` qns=['103', '024', '114']  → **多候选无足够相似 paper [209, 207, 206]**
- `institution_2022_b.json` qns=['033', '034']  → **事业编联考 baijing 不覆盖（硬限）**
- `provincial_gansu_2024.json` qns=['018', '019']  → **run_one 失败: [D-13 #45] 甘肃 2024 changshi dry-run …
  fixed=0  skipped=2
!! 0 修复 — 跳过本卷**
- `provincial_guangdong_2020.json` qns=['077', '083']  → **多候选无足够相似 paper [152, 146]**
- `provincial_shandong_2022.json` qns=['008', '009']  → **run_one 失败: [D-13 #50] 山东 2022 changshi dry-run …
  fixed=0  skipped=2
!! 0 修复 — 跳过本卷**
- `institution_2021_a.json` qns=['045']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2021_c.json` qns=['014']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2022_c.json` qns=['019']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2023_b.json` qns=['006']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2023_c.json` qns=['013']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2024_a.json` qns=['019']  → **事业编联考 baijing 不覆盖（硬限）**
- `provincial_beijing_2023.json` qns=['018']  → **run_one 失败: [D-13 #52] 北京 2023 changshi dry-run …
  fixed=0  skipped=1
!! 0 修复 — 跳过本卷**
- `provincial_shandong_2025.json` qns=['020']  → **run_one 失败: [D-13 #53] 山东 2025 changshi dry-run …
  fixed=0  skipped=1
!! 0 修复 — 跳过本卷**
- `provincial_shanghai_2021.json` qns=['035']  → **多候选无足够相似 paper [102, 100, 97]**
- `provincial_shanxi_2023.json` qns=['069']  → **run_one 失败: [D-13 #53] 山西 2023 changshi dry-run …
  fixed=0  skipped=1
!! 0 修复 — 跳过本卷**
- `provincial_shanxi_2024.json` qns=['020']  → **多候选无足够相似 paper [701, 699]**
- `provincial_zhejiang_2024.json` qns=['020']  → **多候选无足够相似 paper [204, 203, 200]**

成功 11 卷见 git log。
