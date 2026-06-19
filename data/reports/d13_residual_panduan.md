# D-13 panduan 残余文件清单

自动 batch 后还需人工或硬限保留的文件：

- `institution_2020_a.json` qns=['057', '065', '067', '068', '069', '070', '071', '073', '085']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2021_b.json` qns=['070', '071', '072', '073', '074', '076', '078', '091', '096']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2023_b.json` qns=['071', '072', '073', '074', '075', '076', '077']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2023_c.json` qns=['071', '072', '073', '074', '075', '076', '096']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2021_e.json` qns=['071', '072', '073', '075', '078', '079']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2022_a.json` qns=['056', '066', '067', '069', '070', '072']  → **事业编联考 baijing 不覆盖（硬限）**
- `provincial_shanghai_2021.json` qns=['034', '053', '057', '059', '061', '089']  → **多候选无足够相似 paper [102, 100, 97]**
- `institution_2020_e.json` qns=['071', '072', '073', '079', '093']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2021_a.json` qns=['066', '067', '068', '069', '070']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2021_c.json` qns=['065', '075', '078', '071', '072']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2023_e.json` qns=['071', '072', '073', '074', '075']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2020_c.json` qns=['060', '063', '064', '002']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2022_c.json` qns=['063', '074', '075', '076']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2024_b.json` qns=['075', '076', '077', '078']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2024_c.json` qns=['071', '072', '073', '074']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2022_e.json` qns=['097', '076', '077']  → **事业编联考 baijing 不覆盖（硬限）**
- `provincial_hainan_2024.json` qns=['070', '071', '084']  → **run_one 失败: g 脏数据残留：
   provincial-hainan-xingce-panduan-2024-072 选项 A 含「暂缺」
   provincial-hainan-xingce-panduan-2024-072 选项 B 含「暂缺」
   provincial-hainan-xingce-panduan-2024-072 选项 C 含「暂缺」
!! 已 git restore，请人工调查**
- `provincial_heilongjiang_2024.json` qns=['089', '090', '091']  → **多候选无足够相似 paper [623, 622]**
- `provincial_qinghai_2024.json` qns=['091', '092', '099']  → **run_one 失败: 含「暂缺」
   provincial-qinghai-xingce-panduan-2024-090 选项 B 含「暂缺」
   provincial-qinghai-xingce-panduan-2024-090 选项 C 含「暂缺」
   provincial-qinghai-xingce-panduan-2024-090 选项 D 含「暂缺」
!! 已 git restore，请人工调查**
- `institution_2022_b.json` qns=['079', '081']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2024_a.json` qns=['065', '066']  → **事业编联考 baijing 不覆盖（硬限）**
- `institution_2024_e.json` qns=['068', '075']  → **事业编联考 baijing 不覆盖（硬限）**
- `provincial_jiangsu_2020.json` qns=['085', '087']  → **多候选无足够相似 paper [258, 257, 256]**
- `provincial_shanxi_2024.json` qns=['095', '096']  → **多候选无足够相似 paper [701, 699]**
- `provincial_xinjiang_2021.json` qns=['096', '097']  → **多候选无足够相似 paper [656, 655, 654]**
- `provincial_xinjiang_2024.json` qns=['088', '096']  → **多候选无足够相似 paper [651, 649]**
- `institution_2023_a.json` qns=['092']  → **事业编联考 baijing 不覆盖（硬限）**
- `provincial_gansu_2024.json` qns=['091']  → **run_one 失败: 选项 B 含「暂缺」
   provincial-gansu-xingce-panduan-2024-078 选项 C 含「暂缺」
   provincial-gansu-xingce-panduan-2024-087 选项 A 含「暂缺」
   provincial-gansu-xingce-panduan-2024-087 选项 B 含「暂缺」
!! 已 git restore，请人工调查**
- `provincial_guangdong_2024.json` qns=['069']  → **run_one 失败: [D-13 #225] 广东 2024 panduan dry-run …
  fixed=0  skipped=1
!! 0 修复 — 跳过本卷**
- `provincial_shanghai_2020.json` qns=['089']  → **多候选无足够相似 paper [107, 105, 104]**
- `provincial_zhejiang_2020.json` qns=['032']  → **多候选无足够相似 paper [228, 227]**

成功 44 卷见 git log。
