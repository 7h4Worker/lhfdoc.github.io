# TeeDoc 快速启动指南

## 简介

TeeDoc 是一个基于 Python 的静态文档生成器，可以将 Markdown 文档转换为美观的静态网站。本指南将帮助你快速启动 OpenEarable 2.0 项目的文档网站。

## 环境要求

- Python 3.7 或更高版本
- pip 包管理器

## 快速启动

### 方法一：使用启动脚本（推荐）

我们提供了自动化的启动脚本，可以一键完成环境配置和文档构建。

#### Windows 用户

```bash
# 双击运行或在命令行中执行
.\启动TeeDoc服务器.bat
```

#### Linux/macOS 用户

```bash
# 给脚本添加执行权限
chmod +x 启动TeeDoc服务器.sh

# 运行脚本
./启动TeeDoc服务器.sh
```

### 方法二：手动启动

如果你希望手动控制每个步骤，可以按照以下步骤操作：

1. **创建虚拟环境**
   ```bash
   python -m venv venv
   ```

2. **激活虚拟环境**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **安装依赖包**
   ```bash
   pip install -r requirements.txt
   ```

4. **构建文档**
   ```bash
   cd my_site
   teedoc build
   ```

5. **启动服务器**
   ```bash
   teedoc serve
   ```

## 访问文档

启动成功后，在浏览器中访问：
- 本地地址：http://127.0.0.1:2333
- 或者：http://localhost:2333

!!! tip "小贴士"
    首次启动可能需要几分钟时间安装依赖包，请耐心等待。

## 文档结构

```
my_site/
├── site_config.json    # 网站主配置文件
├── docs/               # 文档目录
│   ├── guide/         # 项目指南
│   │   ├── config.json
│   │   ├── sidebar.yaml
│   │   └── *.md
│   └── modules/       # 模块文档
│       ├── config.json
│       ├── sidebar.yaml
│       └── *.md
├── static/            # 静态资源
└── out/               # 构建输出目录
```

## 编辑文档

1. **添加新文档**：在对应目录下创建 `.md` 文件
2. **修改导航**：编辑 `sidebar.yaml` 文件
3. **更新配置**：修改 `config.json` 文件
4. **重新构建**：运行 `teedoc build` 命令

## 常见问题

### 启动失败

**问题**：提示 Python 未找到
**解决**：确保已安装 Python 3.7+ 并添加到系统 PATH

**问题**：端口被占用
**解决**：修改 `site_config.json` 中的端口配置

### 构建错误

**问题**：Markdown 语法错误
**解决**：检查 `.md` 文件的语法，特别是代码块和表格

**问题**：配置文件错误
**解决**：检查 `config.json` 和 `sidebar.yaml` 的 JSON/YAML 语法

## 更多功能

- **搜索功能**：支持全文搜索
- **主题切换**：支持暗色/亮色主题
- **多语言**：支持中英文切换
- **响应式设计**：适配移动设备

## 参考资源

- [TeeDoc 官方文档](https://teedoc.github.io/)
- [Markdown 语法参考](https://www.markdownguide.org/)
- [OpenEarable 项目主页](https://github.com/OpenEarable)
