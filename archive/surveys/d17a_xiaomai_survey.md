# D-17a 小麦公考 PDF 救援可行性调研报告

> 日期：2026-05-16 夜
> 起点：D-16 末 99 题真不可作答 / 99.51% 可用率
> 目标：评估通过小麦公考补全残余 99 题的可行性

## TL;DR

**结论：失败。小麦公考 PDF 路线在数据层有 31 题理论命中，但在传输层
PDF 直链子域名当前不可用，整条路死。**

## 调研过程

### 第 1 步：小麦库存范围（成功）

- `xiaomaigongkao.com/QuestionNew/paperList.html` 是 server-side 渲染
- 不需要登录、不依赖 JS（D-15 之前的 curl 失败是 URL 写错）
- 列表页 server-rendered HTML 含 `paper_id` + `pdf.xiaomaijiaoyu.com/*.pdf` 直链

URL 模式：
```
列表：http://www.xiaomaigongkao.com/QuestionNew/paperList/area/{aid}/year/{yyyy}.html
详情：http://www.xiaomaigongkao.com/QuestionNew/paperBegin/paper_id/{pid}.html
PDF：http://pdf.xiaomaijiaoyu.com/{年份}{省份}行测真题{级别？}.pdf?time=...
```

### 第 2 步：D-16 末 99 题分布 → 小麦覆盖矩阵

scripts/d17_list_unanswerable.py 复刻 isUnanswerable 扫全库 →
99 题分布于 48 个 (module, paperKey)，去重到 29 个 provincial paperKey
（institution 小麦不收）。

scripts/d17_probe_xiaomai.py 批量探测 area/year 列表页 →

**17/29 paperKey 命中 / 31 题理论救援上限**：

| paperKey | 题数 | 小麦 PDF |
|---|---:|---|
| provincial_beijing_2023 | 12 | 2023北京行测真题.pdf |
| provincial_hunan_2023 | 3 | 2023年湖南行测真题.pdf |
| provincial_shanghai_2021 | 2 | 2021年上海行测真题（A/B卷）.pdf |
| provincial_guangdong_2020 | 1 | 2020年广东行测真题（县级/乡镇）.pdf |
| provincial_guangdong_2023 | 1 | 2023年广东行测真题（县级/乡镇）.pdf |
| provincial_henan_2023 | 1 | 2023年河南行测真题.pdf |
| provincial_neimenggu_2023 | 1 | 2023年内蒙古行测真题.pdf |
| provincial_shanxi_2023 | 1 | 2023年山西行测真题.pdf |
| provincial_yunnan_2023 | 1 | 2023年云南行测真题.pdf |
| provincial_shanghai_2020 | 1 | 2020年上海行测真题（A/B卷）.pdf |
| provincial_chongqing_2020 | 1 | 2020年重庆行测真题.pdf |
| provincial_jiangxi_2020 | 1 | 2020年江西行测真题（省/县/乡）.pdf |
| provincial_xinjiang_2021 | 1 | 2021年新疆行测真题.pdf |
| provincial_hunan_2020 | 1 | 2020年湖南行测真题.pdf |
| provincial_tianjin_2023 | 1 | 2023年天津行测真题.pdf |
| provincial_jiangsu_2020 | 1 | 2020年江苏行测真题（A/B/C）.pdf |
| provincial_zhejiang_2021 | 1 | 2021浙江行测真题（A/B/C卷）.pdf |
| **合计** | **31** | |

**12 paperKey 未命中**（小麦也空）：
- 全部 2024 卷：jilin / gansu / ningxia / qinghai / hainan / guangdong / hunan
- 新疆 2023（19 题大头硬伤）
- 山东 2022 / 2025 / 河北 2022 / 深圳 2023

### 第 3 步：PDF 下载尝试（失败）

`pdf.xiaomaijiaoyu.com` 走 Cloudflare CDN。所有请求返回：

```
HTTP/1.1 409 Conflict
Server: cloudflare
Content-Type: text/html; charset=UTF-8

<title>DNS resolution error | pdf.xiaomaijiaoyu.com | Cloudflare</title>
```

诊断：
- 本地 `socket.gethostbyname('pdf.xiaomaijiaoyu.com')` 返回 `getaddrinfo failed`
- Cloudflare 拦截了请求并返回 origin DNS 错误页
- 即 Cloudflare→origin server 的 DNS 配置已失效（服务端 bug，不是反爬）
- 主站 `www.xiaomaigongkao.com` DNS 正常 (60.205.226.92)

尝试过的绕过手段（**全部失败**）：
1. urllib + UA + Referer → 409
2. requests session 带 cookie + Referer + Origin → 409
3. Playwright 真浏览器 `context.request.get` → ENOTFOUND（容器 DNS 失败）
4. Playwright `page.goto` 直接打开 PDF URL → `DNS resolution error`

### 第 4 步：备选路线探查（全部失败）

| 路线 | 结果 |
|---|---|
| Wayback Machine 历史快照 | `No URL has been captured` 0 缓存 |
| paperBegin 详情页 HTML | 200 但需登录，无题干/选项/答案字段 |
| 小麦 APP 接口 | 未试（需 APK 反编译，工程量大） |
| 其他 PDF 镜像（百度/CSDN） | 未试（D-16 L-5 已实测过零碎搜效果极差） |

## 工程产物

```
scripts/d17_list_unanswerable.py    99 题分布扫描
scripts/d17_probe_xiaomai.py        小麦覆盖矩阵探测
data/d17_unanswerable.json          99 题完整分布快照
data/d17_xiaomai_coverage.json      17/29 命中明细 + PDF 直链
data/d17a_xiaomai_survey.md         本报告
data/_xm_xinjiang_2023.html         上次 prompt #5 抓回的列表 HTML（兼容遗留）
data/_xm_xj2_2023.html              同上（浏览器 UA 版）
```

## 真正得到的东西

1. **完整 99 题 paperKey 分布表**（data/d17_unanswerable.json）
   - 后续任何救援工程都能直接拿来用
   - 一目了然知道每个硬伤的位置
2. **小麦库存覆盖矩阵**（data/d17_xiaomai_coverage.json）
   - 若小麦 PDF CDN 修复，可立即跑救援
   - 也可供其他研究/调研用
3. **证否一条看似有希望的路**
   - 避免后续重复走同样的调研
   - 数据层 31 题命中 ≠ 实际可救

## D-17 后续候选

- **接受 99 不可救现状**：D-16 H 工程已把它们前端过滤，用户视角 100% 可作答
- **D-17b 其他源**：星光公考整卷抓 / 华图 PDF / 网盘聚合（D-16 L-5 已实测命中率低）
- **D-17c 等小麦修 CDN**：监控 pdf.xiaomaijiaoyu.com 是否恢复（不可控）
- **D-17d 转其他工程方向**：审计 lib / 修 paperKey 合并 bug 残余 / 优化前端 / 优化 PDF 流水线
