# 🧠 ClipMind — 智能剪贴板助手

> Windows 平台 AI 增强型智能剪贴板工具。记录你的每一次复制,让剪贴板成为你的个人知识库。

![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Platform](https://img.shields.io/badge/Platform-Windows_10%2F11-9cf)

## ✨ 功能特性

- **📋 剪贴板历史记录** — 自动监听 Ctrl+C,保存文本、代码、图片
- **🧠 智能内容识别** — 自动识别内容类型(文本/代码/图片)与代码语言(Python、JS、SQL、Go 等 14 种)
- **🔍 全文搜索** — SQLite FTS 全文检索,秒级搜历史内容
- **⚡ 全局快捷键** — 任意软件中按 `Ctrl+Shift+V` 呼出搜索窗口
- **📌 标签管理** — 自定义标签 + 自动推荐类型标签
- **⭐ 收藏功能** — 一键收藏重要内容
- **📎 复制恢复** — 点击历史记录即恢复剪贴板,直接 Ctrl+V 粘贴
- **🖼️ 图片支持** — 截图自动保存并生成缩略图
- **🔒 数据本地存储** — 所有数据保存在本地,不上传任何剪贴板内容

## 🖥️ 界面预览

```
+--------------------------------+
| 🔍 搜索剪贴板内容              |
+--------------------------------+
| 📝 Python代码    10分钟前       |
| 🐛 Bug日志      30分钟前        |
| 🌏 旅行资料     昨天            |
| 📷 图片截图     昨天            |
+--------------------------------+
```

## 📦 安装

### 方式一:直接运行 exe(推荐)

从 [Releases](https://github.com/ltc1995/ClipMind/releases) 下载 `ClipMind.exe`,双击运行即可。数据保存在 exe 同目录的 `data/` 文件夹。

### 方式二:源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/ltc1995/ClipMind.git
cd ClipMind

# 2. 安装依赖(建议使用虚拟环境)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. 运行
python main.py
```

## 🚀 使用说明

| 操作 | 方法 |
|------|------|
| 复制内容 | 正常 Ctrl+C,ClipMind 自动后台保存 |
| 呼出搜索窗口 | 任意软件中按 `Ctrl+Shift+V` |
| 恢复复制 | 点击历史记录 → 直接 Ctrl+V 粘贴 |
| 收藏内容 | 点击 ⭐ 标记 |
| 添加标签 | 在记录详情中添加 `#标签` |

程序启动后常驻系统托盘,CPU 占用 < 1%,内存占用 < 100MB。

## 🔨 打包为 exe

```bash
# 一键打包(生成 dist/ClipMind.exe)
build_clipmind.bat
```

或手动执行:

```bash
pip install pyinstaller
pyinstaller ClipMind.spec
```

## 📁 项目结构

```
ClipMind/
├── main.py               # 程序入口
├── ui/                   # 界面(主窗口/搜索窗口/设置/关于)
├── clipboard/            # 剪贴板监听与管理
├── database/             # SQLite 数据库与模型
├── search/               # 全文搜索引擎
├── utils/                # 配置/快捷键/自启动/更新检查
├── resources/icons/      # 应用图标
└── scripts/              # 开发工具脚本
```

## 🛠️ 技术栈

| 模块 | 技术 |
|------|------|
| 语言 | Python 3.9+ |
| GUI | PySide6(Qt) |
| 数据库 | SQLite + FTS5 全文搜索 |
| 剪贴板监听 | Qt 原生剪贴板 + 定时轮询 |
| 打包 | PyInstaller |

## 🗺️ 路线图

- [x] **MVP**:历史记录 / 搜索 / 快捷键 / 标签 / 收藏 / 打包发布
- [ ] **V2 - AI 增强**:自动总结、AI 分类、自然语言搜索
- [ ] **V2 - OCR**:截图文字识别自动归类
- [ ] **V2 - 云同步**

## 📄 许可证

[MIT](LICENSE) © 2026 林天骋

---

💡 **提示**:ClipMind 存储你的剪贴板历史(含截图),数据完全保存在本地,请勿将 `data/` 目录分享或提交到仓库。
