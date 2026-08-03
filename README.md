# ClipMind 智能剪贴板助手

Windows 平台 AI 增强型智能剪贴板工具。

## 1. 产品定位

**一句话介绍：** ClipMind 是一个智能剪贴板管理工具，通过记录用户复制历史，并提供搜索、分类、整理能力，让 Windows 剪贴板成为用户的个人知识库。

**产品目标：** 解决 Windows 用户以下痛点：

- 复制过的重要内容容易丢失
- Windows 自带剪贴板历史功能弱
- 长文本、代码、网页资料难以管理
- 程序员经常复制代码、日志、Bug 信息，需要快速查找
- 用户希望拥有自己的个人知识库

## 2. 产品用户群

### 程序员
使用场景：保存代码片段、报错日志、命令、接口文档

### 测试工程师
使用场景：保存 Bug 信息、SQL、接口请求参数、测试数据

### 普通办公用户
使用场景：保存网页资料、聊天内容、文本

## 3. MVP 版本功能范围

> 第一版本不要依赖 AI 接口。目标：做一个稳定、快速、好用的智能剪贴板。

### Feature 1：剪贴板历史记录

**功能描述：** 监听 Windows 系统剪贴板。当用户执行 Ctrl+C 时自动保存复制内容。

**支持类型：**

- **文本** — 例如 `hello world`，保存内容、类型（文本）、时间
- **代码** — 例如 `def hello():`，自动识别类型（代码）和语言（Python）
- **图片** — 保存图片路径、创建时间、缩略图

### Feature 2：剪贴板历史列表

**UI 要求：**

```
+--------------------------------+
| 搜索剪贴板内容                    |
+--------------------------------+
| 📝 Python代码    10分钟前        |
| 🐛 Bug日志      30分钟前        |
| 🌏 旅行资料     昨天             |
| 📷 图片截图     昨天             |
+--------------------------------+
```

每条记录显示：内容预览、类型图标、创建时间、标签

### Feature 3：搜索功能

**普通搜索：** 支持关键词搜索文本内容、标签、标题。

例如：输入 `docker` → 返回 `docker compose up -d`（昨天，代码）

### Feature 4：快捷呼出窗口

**快捷键：** `Ctrl + Shift + V`

无论当前在哪个软件（Chrome、VSCode、微信），按快捷键即可弹出 ClipMind 搜索窗口。

### Feature 5：复制恢复

用户点击历史记录 → ClipMind 写入系统剪贴板 → 用户 Ctrl+V 粘贴

### Feature 6：标签管理

用户可以给内容添加标签，例如 `#python`、`#backend`、`#学习`。系统自动推荐类型标签（代码、文本、链接、图片）。

### Feature 7：收藏功能

用户可以收藏重要内容，显示 ⭐ 收藏标记。

## 4. 后续 AI 增强功能规划（V2）

> MVP 不实现，预留接口。

- **AI 功能 1：自动总结** — 输入长文章，输出摘要和标签
- **AI 功能 2：AI 分类** — 复制内容后 AI 自动分析并分类
- **AI 功能 3：智能搜索** — 自然语言搜索历史内容
- **AI 功能 4：OCR** — 截图识别文字并自动归类

## 5. 技术方案

| 模块 | 技术选型 |
|------|----------|
| 开发语言 | Python |
| GUI | PySide6（窗口、UI、快捷键） |
| 数据库 | SQLite（`clipmind.db`，表 `clipboard_items`） |
| 剪贴板监听 | PySide6/Qt 原生剪贴板 + 定时轮询 |
| 全局快捷键 | `Ctrl + Shift + V` |
| 搜索（MVP） | SQLite FTS 全文搜索 |
| 搜索（后续） | ChromaDB 向量数据库 |

### 数据库字段（clipboard_items）

`id`, `content`, `content_type`, `language`, `created_time`, `updated_time`, `is_favorite`, `tags`, `image_path`

## 6. 项目目录结构

```
ClipMind/
├── main.py
├── requirements.txt
├── ui/
│   ├── main_window.py
│   └── search_window.py
├── clipboard/
│   ├── monitor.py
│   └── manager.py
├── database/
│   ├── db.py
│   └── models.py
├── search/
│   └── search_engine.py
├── utils/
│   ├── shortcut.py
│   └── config.py
├── resources/
│   └── icons/
└── README.md
```

## 7. 开发阶段规划

### Phase 1：基础版本
目标：完成可运行软件。
任务：创建 PySide6 窗口 → 实现剪贴板监听 → 保存 SQLite → 显示历史记录 → 搜索 → 点击恢复复制

### Phase 2：体验优化
增加：开机启动、系统托盘、快捷键、UI 美化、图标

### Phase 3：商业版本
增加：AI 总结、OCR、智能分类、云同步

## 8. 非功能要求

- **性能：** 常驻后台 CPU 占用 < 1%，内存占用 < 100MB，启动时间 < 3 秒
- **数据安全：** 所有数据默认本地保存，不上传用户剪贴板内容，用户可删除历史

## 9. 打包发布

- **目标：** 生成 `ClipMind.exe`
- **要求：** Windows 10/11 支持
- **打包工具：** PyInstaller

## 10. Codex 开发要求

- 优先完成 MVP，不提前实现 AI 功能
- 保证代码模块化
- 所有配置集中管理
- 添加必要注释
- 每完成一个模块提供测试方法
- 最终生成：`requirements.txt`、`README.md`、打包脚本、exe 生成说明

## 第一阶段交付标准

完成后用户可以：

- ✅ 安装运行 ClipMind.exe
- ✅ 按 Ctrl+C 复制内容
- ✅ ClipMind 自动保存
- ✅ 打开 ClipMind 查看历史
- ✅ 搜索历史内容
- ✅ 点击历史内容恢复复制
- ✅ 软件后台常驻运行

## 项目最终目标

打造一个「Windows 用户每天都会打开的个人知识剪贴板」。

未来升级：ClipMind = Windows 版轻量个人第二大脑。
