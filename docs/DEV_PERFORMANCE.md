# Ace-the-CSE 项目开发指南

## 开发服务器启动慢的问题

### 原因
- 20,741道题的题库数据，1380个JSON文件静态导入
- questionLoader.ts 有2847行，257KB大小
- Turbopack首次编译需要解析所有import
- F盘被识别为"慢文件系统"

### 解决方案

#### 方案1：直接用静态导出（推荐）
如果只是本地预览，不用启动dev server：

```bash
# 构建静态导出（只需构建一次）
npm run build

# 用本地HTTP服务器预览（秒开）
npx serve out
# 或
python -m http.server 3000 --directory out
```

访问 http://localhost:3000 即可，无需等待编译。

#### 方案2：清理缓存重启
```bash
# 清理.next缓存
rm -rf .next
rm -rf node_modules/.cache

# 重新启动（首次会慢，后续会快）
npm run dev
```

#### 方案3：只开发单个页面
修改 `src/app/page.tsx` 等单个文件时，Turbopack会快速热更新。
避免修改 `questionLoader.ts` 或添加新的题库JSON文件。

#### 方案4：增加Node内存限制
在 `package.json` 修改：

```json
{
  "scripts": {
    "dev": "NODE_OPTIONS='--max-old-space-size=4096' next dev",
    "build": "NODE_OPTIONS='--max-old-space-size=4096' next build --webpack"
  }
}
```

### 性能对比
- **dev server首次启动**：60秒超时
- **静态导出 + serve**：< 1秒启动
- **dev server热更新**：< 3秒（改单个文件后）

### 最佳实践
- **开发UI**：用 `npm run build` + `npx serve out`
- **开发数据**：修改完JSON后重新build
- **调试逻辑**：dev server慢但支持热更新

## 其他优化建议

### 1. 将.next移到C盘（SSD）
```bash
# 创建符号链接，让.next目录在快速磁盘上
mkdir C:\Users\17504\.next-cache\Ace-the-CSE
rm -rf F:\Project_test\Ace-the-CSE\.next
ln -s C:\Users\17504\.next-cache\Ace-the-CSE F:\Project_test\Ace-the-CSE\.next
```

### 2. 排除大文件的监听
创建 `.watchmanconfig`：
```json
{
  "ignore_dirs": [
    ".next",
    "node_modules",
    "out",
    "data/tmp_github_aat",
    "data/tmp_github_fenbi"
  ]
}
```

### 3. 使用SSD作为工作目录
如果F盘是机械硬盘，考虑将整个项目迁移到C盘SSD。
