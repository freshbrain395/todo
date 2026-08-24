# Todo Agent (Python + Vue 3)

这是一个现代化的 TODO 智能体应用，支持 Web 前端界面、FastAPI 接口服务与交互式智能终端 CLI。

## 🌟 一键启动前后端

使用 `pnpm` 一键同时启动 Python 后端服务与 Vite 前端界面：

```bash
# 1. 安装前端依赖
pnpm install

# 2. 一键启动前后端（后端 8000 端口 + 前端 1420 端口）
pnpm dev
```

---

## 🛠️ 项目管理与常用命令

### 1. 前端管理（使用 `pnpm`）

- **一键启动前后端服务**：
  ```bash
  pnpm dev
  ```
- **仅启动前端 Web 开发服务器**：
  ```bash
  pnpm run dev:frontend
  ```
- **构建前端生产产物**：
  ```bash
  pnpm run build
  ```
- **运行前端单元测试**：
  ```bash
  pnpm test
  ```

---

### 2. Python 后端与 CLI（使用 `uv`）

- **仅启动 FastAPI 后端服务**：
  ```bash
  uv run todo-server
  # 或
  pnpm run dev:backend
  ```
- **启动交互式智能终端 CLI**：
  ```bash
  uv run todo-cli
  # 或
  pnpm run cli
  ```
  进入交互终端后可直接输入自然语言，或使用 `/help`、`/list`、`/add`、`/done`、`/prompt` 等 Slash 快捷命令。
- **运行后端 Python 测试**：
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
