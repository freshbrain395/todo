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

### 🚀 启动与使用方式汇总

#### 方式一：命令行统一入口（推荐）
在终端中直接使用 `todo` 命令：
- `todo`：直接进入 **Chat + Todo 智能对话** 模式（自然语言交流，无需先输入 `/chat`）
- `todo gui`：启动原生桌面 GUI 窗口
- `todo web`：启动 Web 服务并在浏览器中打开
- `todo server`：仅在后台启动 FastAPI 服务

#### 方式二：桌面原生 GUI 客户端
- 双击桌面上的 **Todo Agent** 快捷方式
- 或运行源码：`uv run python run.py gui`
- 或执行批处理：`run.bat`

#### 方式三：开发者联调模式
```bash
pnpm dev              # 一键同时启动后端与前端 Vite 开发服务
pnpm run dev:frontend # 仅启动前端 Vite 开发服务器
pnpm run dev:backend  # 仅启动 FastAPI 后端
```

- **一键启动前后端（开发推荐）**：
  ```bash
  # 1. 安装前端依赖（首次使用）
  pnpm install

  # 2. 一键启动前后端（后端 8000 端口 + 前端 1420 端口）
  pnpm dev
  ```
- **仅启动前端 Web 开发服务器**：
  ```bash
  pnpm run dev:frontend
  ```
- **仅启动 FastAPI 后端服务**：
  ```bash
  uv run todo-server
  # 或
  pnpm run dev:backend
  ```

---

### 🛠️ 项目构建与测试

#### 1. 前端构建与测试
```bash
pnpm run build          # 构建前端生产静态资源 (front/dist)
pnpm test               # 运行前端单元测试
```

#### 2. 桌面客户端打包
```bash
pnpm run build:exe      # 打包生成 release/todo-agent.exe 独立可执行程序
```

#### 3. 后端单元测试
```bash
uv run python -m pytest backend/tests
```

---

### 📁 架构分层

- **前端 UI** (`front/`)：Vue 3 + Vite + TypeScript + Lucide Icons
- **后端架构** (`backend/`)：Python 3 (基于 `uv` 包管理器)
  - `backend/api/`：FastAPI 路由组与通用 RPC 适配器
  - `backend/service/`：业务逻辑层、LLM 智能体意图解析引擎
  - `backend/repository/`：SQLite 数据访问层（Todo、Config、AI Session）
  - `backend/cli.py`：基于 Prompt Toolkit + Rich 的交互式命令行终端
  - `backend/main.py`：原生桌面 GUI、后端 Server 与 CLI 多入口调度

