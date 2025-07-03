# 部署指南

## 概述

本指南介绍如何将 OpenEarable 2.0 文档网站部署到各种平台，包括 GitHub Pages、Netlify、Vercel 等。

## 构建生产版本

在部署之前，需要构建生产版本的文档：

```bash
# 进入项目目录
cd my_site

# 构建文档
teedoc build

# 构建完成后，静态文件位于 out/ 目录
```

## GitHub Pages 部署

### 方法一：GitHub Actions 自动部署

1. **创建 GitHub Actions 工作流**

   在项目根目录创建 `.github/workflows/deploy.yml`：

   ```yaml
   name: Deploy to GitHub Pages

   on:
     push:
       branches: [ main ]
     pull_request:
       branches: [ main ]

   jobs:
     build-and-deploy:
       runs-on: ubuntu-latest
       steps:
       - uses: actions/checkout@v3
       
       - name: Setup Python
         uses: actions/setup-python@v4
         with:
           python-version: '3.9'
       
       - name: Install dependencies
         run: |
           cd docs
           pip install -r requirements.txt
       
       - name: Build documentation
         run: |
           cd docs/my_site
           teedoc build
       
       - name: Deploy to GitHub Pages
         uses: peaceiris/actions-gh-pages@v3
         with:
           github_token: ${{ secrets.GITHUB_TOKEN }}
           publish_dir: ./docs/my_site/out
   ```

2. **配置 GitHub Pages**
   - 进入 GitHub 仓库设置
   - 找到 "Pages" 选项
   - 选择 "Deploy from a branch"
   - 选择 "gh-pages" 分支

### 方法二：手动部署

1. **构建文档**
   ```bash
   cd docs/my_site
   teedoc build
   ```

2. **推送到 gh-pages 分支**
   ```bash
   # 创建并切换到 gh-pages 分支
   git checkout --orphan gh-pages
   
   # 复制构建文件
   cp -r docs/my_site/out/* .
   
   # 提交并推送
   git add .
   git commit -m "Deploy documentation"
   git push origin gh-pages
   ```

## Netlify 部署

### 方法一：Git 集成部署

1. **连接 GitHub 仓库**
   - 登录 Netlify
   - 选择 "New site from Git"
   - 连接 GitHub 仓库

2. **配置构建设置**
   - Build command: `cd docs && pip install -r requirements.txt && cd my_site && teedoc build`
   - Publish directory: `docs/my_site/out`
   - Base directory: `/`

3. **创建 netlify.toml**
   ```toml
   [build]
     command = "cd docs && pip install -r requirements.txt && cd my_site && teedoc build"
     publish = "docs/my_site/out"

   [build.environment]
     PYTHON_VERSION = "3.9"
   ```

### 方法二：手动部署

1. **构建文档**
   ```bash
   cd docs/my_site
   teedoc build
   ```

2. **上传到 Netlify**
   - 将 `out/` 目录打包为 zip 文件
   - 在 Netlify 控制台手动上传

## Vercel 部署

1. **创建 vercel.json**
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "docs/my_site/build.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "/docs/my_site/out/$1"
       }
     ]
   }
   ```

2. **创建构建脚本**
   ```python
   # docs/my_site/build.py
   import subprocess
   import os

   os.chdir('docs')
   subprocess.run(['pip', 'install', '-r', 'requirements.txt'])
   os.chdir('my_site')
   subprocess.run(['teedoc', 'build'])
   ```

## 自定义域名

### 配置 CNAME

1. **添加 CNAME 文件**
   ```bash
   # 在 out/ 目录创建 CNAME 文件
   echo "docs.openearable.com" > docs/my_site/out/CNAME
   ```

2. **配置 DNS**
   - 在域名服务商添加 CNAME 记录
   - 指向 GitHub Pages 或部署平台的域名

### 更新配置

修改 `site_config.json`：
```json
{
  "site_domain": "docs.openearable.com",
  "site_protocol": "https",
  "site_root_url": "/"
}
```

## 性能优化

### 启用压缩

大多数托管平台都支持 Gzip 压缩，确保已启用：

```json
// netlify.toml
[[headers]]
  for = "/*"
  [headers.values]
    Content-Encoding = "gzip"
```

### CDN 加速

使用 CDN 加速静态资源：

```json
// site_config.json
{
  "plugins": {
    "teedoc-plugin-assets": {
      "config": {
        "header_items": [
          "<link rel=\"preload\" href=\"/static/css/main.css\" as=\"style\">",
          "<link rel=\"dns-prefetch\" href=\"//fonts.googleapis.com\">"
        ]
      }
    }
  }
}
```

## 监控和维护

### 构建状态监控

- 设置 GitHub Actions 通知
- 监控部署状态
- 配置错误报告

### 定期更新

```bash
# 更新依赖
pip install --upgrade teedoc

# 重新构建
teedoc build
```

## 故障排除

### 常见问题

**问题**：构建失败
**解决**：检查 Python 版本和依赖包版本

**问题**：样式丢失
**解决**：检查静态文件路径配置

**问题**：搜索不工作
**解决**：确保搜索索引文件已正确生成

### 调试技巧

1. **本地测试**
   ```bash
   # 本地构建测试
   teedoc build
   teedoc serve
   ```

2. **检查日志**
   ```bash
   # 查看构建日志
   teedoc build --verbose
   ```

3. **验证配置**
   ```bash
   # 验证配置文件
   python -m json.tool site_config.json
   ```

## 备份和恢复

### 备份策略

1. **源码备份**：定期推送到 Git 仓库
2. **构建备份**：保存构建产物
3. **配置备份**：备份重要配置文件

### 恢复流程

1. **从 Git 恢复**
   ```bash
   git clone <repository>
   cd docs
   pip install -r requirements.txt
   cd my_site
   teedoc build
   ```

2. **重新部署**
   ```bash
   # 根据选择的部署方式重新部署
   ```

## 参考资源

- [GitHub Pages 文档](https://docs.github.com/en/pages)
- [Netlify 文档](https://docs.netlify.com/)
- [Vercel 文档](https://vercel.com/docs)
- [TeeDoc 部署指南](https://teedoc.github.io/)
