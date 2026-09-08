# Todo Agent (Python + Vue 3)

[English](README.md) | [简体中文](README_zh.md)

---

这是一个现代化的 TODO 智能体应用，结合大语言模型（LLM）实现自然语言任务规划与意图解析，支持原生桌面窗口、交互式终端 CLI 与 Web 浏览器三种使用模式。

---

### 🌟 统一使用体验架构

```text
Todo Agent
│
├── 🖥️ 桌面图标
│      └── 双击 → 原生 GUI 桌面客户端
│
└── 💻 命令行 (已自动加入 PATH)
       ├── todo
       │    └── CLI 聊天模式 (Chat + Todo 智能助理)
       │
       ├── todo gui
       │    └── 启动原生桌面窗口
       │
       ├── todo web
       │    └── 启动 Web 服务并自动打开浏览器
       │
       └── todo server
            └── 仅在后台启动 API 服务
```

---

### 📦 Windows 一键安装与部署

在打包生成 `release/todo.exe` 后，可一键完成安装并加入系统环境变量：

- **一键安装**：双击运行 `scripts/install.bat`（或在 PowerShell 中执行 `scripts/install.ps1`）
  - 自动部署至 `%LOCALAPPDATA%\Programs\Todo Agent\`
  - 自动创建桌面快捷方式（双击直达 GUI）
  - 自动创建开始菜单入口
  - 自动将目录注册进系统用户 `PATH`，新开终端直接敲 `todo` 即可使用
- **数据存储隔离**：
  - 数据库与配置文件统一持久化至 `%APPDATA%\Todo Agent\`（升级与重装不丢失待办与 API Key）
- **一键卸载**：运行 `powershell scripts/uninstall.ps1` 即可干净清理快捷方式与 PATH，保留用户数据。

---

### 🚀 启动与使用指南

---

#### 一、普通用户如何启动

普通用户无需关心复杂的代码编译与端口配置，提供以下三种便携启动方式：

##### 1. 安装包/桌面快捷方式启动（首选）
- **一键安装**：双击运行 `scripts/install.bat`（或在 PowerShell 中执行 `powershell scripts/install.ps1`）
- 安装完成后：
  - **桌面直达**：直接双击桌面的 **Todo Agent** 快捷方式打开原生 GUI。
  - **开始菜单**：在系统开始菜单搜索 `Todo Agent` 打开。
  - **终端任意位置敲命令**：新开任意 CMD 或 PowerShell 窗口，直接输入：
    - `todo`：进入终端 AI 交互对话与待办管理模式。
    - `todo gui`：启动原生独立窗口桌面应用。
    - `todo web`：启动本地服务并自动在浏览器中打开 Web 端界面。

##### 2. 免安装脚本双击启动
- 直接双击仓库根目录下的 **`run.bat`**：
  - 首次运行会自动打包客户端，之后双击将秒级拉起原生桌面 GUI。
  - 支持带参数重编：在终端执行 `run.bat --rebuild`。

##### 3. 已安装 Python 环境的用户
如果本地已有 Python 与 uv：
```powershell
uv run python run.py gui   # 启动原生桌面应用
uv run python run.py web   # 启动浏览器 Web 界面
uv run todo                # 启动终端 CLI 交互助手
```

---

#### 二、开发者如何启动

开发者模式支持前端热重载（HMR）、后端接口即时生效与全栈联合调试。

##### 1. 环境准备
项目依赖管理规范：
- Python 环境与依赖：使用 **`uv`**
- 前端环境与依赖：使用 **`pnpm`**（Node.js >= 18）

首次克隆代码后，安装依赖：
```bash
# 1. 安装前端依赖
pnpm install

# 2. 同步 Python 虚拟环境与后端依赖
uv sync
```

##### 2. 本地开发启动命令

- **一键前后端全栈联调（推荐）**：
  ```bash
  pnpm dev
  ```
  > 同时拉起：
  > - 后端 FastAPI 接口服务：`http://127.0.0.1:8000`
  > - 前端 Vite 开发热重载服务器：`http://localhost:1420`

- **仅启动前端 Web 开发服务器**：
  ```bash
  pnpm run dev:frontend
  # 或
  pnpm --dir front dev
  ```

- **仅启动 FastAPI 后端服务**：
  ```bash
  pnpm run dev:backend
  # 或
  uv run todo server
  ```

- **调试交互式 CLI 对话终端**：
  ```bash
  pnpm run cli
  # 或
  uv run todo
  ```

- **调试原生桌面 GUI（无须提前打包 EXE）**：
  ```bash
  pnpm run gui
  # 或
  uv run python run.py gui
  ```

---

### 🛠️ 项目构建与测试

#### 1. 自动化测试
```bash
pnpm test              # 运行前端单元测试（Vitest）
pnpm run test:backend  # 运行后端单元测试（Pytest）
pnpm run test:all      # 一键运行前后端全量测试套件
```

#### 2. 前端构建
```bash
pnpm run build         # 构建前端生产静态资源 (front/dist)
```

#### 3. 桌面可执行文件与安装包打包
```bash
pnpm run build:exe        # 打包生成 release/todo.exe 单文件可执行程序
pnpm run build:installer  # 生成便携式安装包分发目录
pnpm run build:release    # 完整构建前端并打包可执行程序
```

---

### 📁 架构分层

- **前端 UI** (`front/`)：Vue 3 + Vite + TypeScript + Lucide Icons
  - `front/src/components/productivity/`：日程日历 (`CalendarView.vue`)、倒计时 (`CountdownPage.vue`)、闹钟 (`AlarmPage.vue`)、番茄钟 (`PomodoroTimer.vue`)、时钟 (`LocalClockPage.vue`) 等独立业务模块
  - `front/src/components/common/`：全局设置、桌面与搜索视图、模态框
- **后端架构** (`backend/`)：Python 3 (基于 `uv` 包管理器)
  - `backend/api/`：FastAPI 路由组与通用 RPC 适配器
  - `backend/service/`：业务逻辑层、LLM 智能体意图解析引擎
  - `backend/repository/`：SQLite 数据访问层（Todo、Config、AI Session）
  - `backend/cli.py`：基于 Prompt Toolkit + Rich 的交互式命令行终端
  - `backend/main.py`：原生桌面 GUI、后端 Server 与 CLI 多入口调度

