# D-13 ziliao 残余文件清单

自动 batch 后还需人工或硬限保留的文件：

- `provincial_hainan_2024.json` qns=['100', '105', '106', '107', '108', '109']  → **run_one 失败: jing 脏数据残留：
   provincial-hainan-xingce-ziliao-2024-110 选项 A 含「暂缺」
   provincial-hainan-xingce-ziliao-2024-110 选项 B 含「暂缺」
   provincial-hainan-xingce-ziliao-2024-110 选项 C 含「暂缺」
!! 已 git restore，请人工调查**
- `provincial_jiangsu_2024.json` qns=['113', '114', '115']  → **多候选无足够相似 paper [246, 245, 244]**
- `provincial_jiangsu_2020.json` qns=['006', '023']  → **多候选无足够相似 paper [258, 257, 256]**
- `provincial_neimenggu_2020.json` qns=['106', '107']  → **多候选无足够相似 paper [696, 695]**
- `provincial_xinjiang_2024.json` qns=['111', '113']  → **多候选无足够相似 paper [651, 649]**
- `provincial_zhejiang_2024.json` qns=['121', '104']  → **多候选无足够相似 paper [204, 203, 200]**
- `institution_2020_e.json` qns=['055']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2021_a.json` qns=['094']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2021_c.json` qns=['055']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2023_e.json` qns=['060']  → **事业编联考 baijing 不覆盖（硬限）**
- `provincial_heilongjiang_2024.json` qns=['109']  → **多候选无足够相似 paper [623, 622]**
- `provincial_neimenggu_2022.json` qns=['024']  → **run_one 失败: [D-13 #166] 内蒙古 2022 ziliao dry-run …
  fixed=0  skipped=1
!! 0 修复 — 跳过本卷**
- `provincial_shanxi_2024.json` qns=['118']  → **多候选无足够相似 paper [701, 699]**
- `provincial_sichuan_2021.json` qns=['090']  → **多候选无足够相似 paper [297, 295]**
- `provincial_xinjiang_2023.json` qns=['115']  → **run_one 失败: [D-13 #170] 新疆 2023 ziliao dry-run …
  fixed=0  skipped=1
!! 0 修复 — 跳过本卷**
- `provincial_zhejiang_2020.json` qns=['094']  → **多候选无足够相似 paper [228, 227]**
- `provincial_zhejiang_2021.json` qns=['058']  → **多候选无足够相似 paper [223, 221, 218]**
- `provincial_zhejiang_2022.json` qns=['072']  → **多候选无足够相似 paper [214, 212]**
- `provincial_zhejiang_2023.json` qns=['115']  → **run_one 失败: [D-13 #170] 浙江 2023 ziliao dry-run …
  fixed=0  skipped=1
!! 0 修复 — 跳过本卷**

成功 40 卷见 git log。
