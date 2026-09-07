# Todo Agent (Python + Vue 3)

这是一个现代化的 TODO 智能体应用，结合大语言模型（LLM）实现自然语言任务规划与意图解析，支持原生桌面窗口、交互式终端 CLI 与 Web 浏览器三种使用模式。

---

## 🚀 启动方式汇总

本项目支持多种启动方式，您可以根据使用场景选择：

### 方式一：原生桌面 GUI 窗口（非浏览器模式，推荐）

无需打开系统外部浏览器，直接以独立的桌面客户端窗口运行（基于 `pywebview`）：

- **通过 Python 脚本直接启动**：
  ```bash
  uv run python run.py
  # 或显式指定 gui 参数
  uv run python run.py gui
  ```
- **通过一键批处理脚本（Windows）**：
  ```cmd
  run.bat
  ```
  *(若尚未生成可执行文件，该脚本会自动执行打包并拉起客户端)*
- **直接运行打包好的可执行文件**：
  ```cmd
  .\release\todo-agent.exe
  ```

---

### 方式二：交互式智能终端 CLI（非浏览器模式）

完全脱离图形界面在终端中交互，支持自然语言意图识别与 Slash 快捷命令（基于 `prompt-toolkit` + `rich`）：

- **使用 `uv` 启动**：
  ```bash
  uv run todo-cli
  # 或
  uv run python run.py cli
  ```
- **使用 `pnpm` 启动**：
  ```bash
  pnpm run cli
  ```
- **常用 CLI 指令**：
  - 进入交互终端后可直接输入自然语言（如：`提醒我明天下午3点开周会`）。
  - 快捷指令：`/help`、`/list`、`/add <内容>`、`/done <ID>`、`/delete <ID>`、`/prompt` 等。

---

### 方式三：Web 浏览器开发与联调模式

适合进行前端界面开发调试或直接在浏览器中使用：

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

## 🛠️ 项目构建与测试

### 1. 前端构建与测试
```bash
pnpm run build          # 构建前端生产静态资源 (dist)
pnpm test               # 运行前端单元测试
```

### 2. 桌面客户端打包
```bash
pnpm run build:exe      # 打包生成 release/todo-agent.exe 独立可执行程序
```

### 3. 后端单元测试
```bash
uv run --extra dev pytest backend/tests
```

---

## 📁 架构分层

- **前端 UI**：Vue 3 + Vite + TypeScript + Lucide Icons
- **后端架构**：Python 3 (基于 `uv` 包管理器)
  - `backend/api/`：FastAPI 路由组与通用 RPC 适配器
  - `backend/service/`：业务逻辑层、LLM 智能体意图解析引擎
  - `backend/repository/`：SQLite 数据访问层（Todo、User、Config、AI Session）
  - `backend/cli.py`：基于 Prompt Toolkit + Rich 的交互式命令行终端
  - `backend/main.py`：原生桌面 GUI、后端 Server 与 CLI 多入口调度

