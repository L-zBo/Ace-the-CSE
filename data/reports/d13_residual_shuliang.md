# D-13 shuliang 残余文件清单

自动 batch 后还需人工或硬限保留的文件：

- `institution_2022_a.json` qns=['066', '067', '068', '069', '070', '076']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2021_b.json` qns=['054', '071', '072', '073', '075']  → **事业编联考 baijing 不覆盖（硬限）**
- `provincial_jiangsu_2024.json` qns=['046', '047', '049', '050', '065']  → **多候选无足够相似 paper [246, 245, 244]**
- `provincial_shenzhen_2020.json` qns=['004', '008', '009', '045', '054']  → **多候选无足够相似 paper [185, 183, 181]**
- `provincial_zhejiang_2024.json` qns=['051', '052', '053', '054', '056']  → **多候选无足够相似 paper [204, 203, 200]**
- `institution_2020_a.json` qns=['066', '067', '068', '072']  → **事业编联考 baijing 不覆盖（硬限）**
- `provincial_heilongjiang_2024.json` qns=['062', '063', '068', '070']  → **多候选无足够相似 paper [623, 622]**
- `provincial_zhejiang_2022.json` qns=['052', '053', '054', '002']  → **多候选无足够相似 paper [214, 212]**
- `institution_2022_c.json` qns=['049', '060', '050']  → **事业编联考 baijing 不覆盖（硬限）**
- `provincial_xinjiang_2024.json` qns=['052', '056', '060']  → **多候选无足够相似 paper [651, 649]**
- `institution_2021_e.json` qns=['049', '060']  → **事业编联考 baijing 不覆盖（硬限）**
- `provincial_gansu_2024.json` qns=['068', '069']  → **run_one 失败: B 含「暂缺」
   provincial-gansu-xingce-shuliang-2024-069 选项 C 含「暂缺」
   provincial-gansu-xingce-shuliang-2024-070 选项 A 含「暂缺」
   provincial-gansu-xingce-shuliang-2024-070 选项 B 含「暂缺」
!! 已 git restore，请人工调查**
- `provincial_guangdong_2020.json` qns=['041', '026']  → **多候选无足够相似 paper [152, 146]**
- `provincial_neimenggu_2020.json` qns=['062', '066']  → **多候选无足够相似 paper [696, 695]**
- `provincial_shanxi_2024.json` qns=['066', '067']  → **多候选无足够相似 paper [701, 699]**
- `provincial_sichuan_2021.json` qns=['049', '053']  → **多候选无足够相似 paper [297, 295]**
- `institution_2021_c.json` qns=['059']  → **事业编联考 baijing 不覆盖（硬限）**
- `provincial_chongqing_2020.json` qns=['064']  → **baijing 无对应卷（region=chongqing year=2020 level=）**
- `provincial_jiangsu_2020.json` qns=['047']  → **多候选无足够相似 paper [258, 257, 256]**
- `provincial_jiangxi_2020.json` qns=['063']  → **多候选无足够相似 paper [678, 676, 674]**
- `provincial_shenzhen_2023.json` qns=['046']  → **run_one 失败: [D-13 #103] 深圳 2023 shuliang dry-run …
  fixed=0  skipped=1
!! 0 修复 — 跳过本卷**
- `provincial_xinjiang_2021.json` qns=['006']  → **多候选无足够相似 paper [656, 655, 654]**

成功 46 卷见 git log。
