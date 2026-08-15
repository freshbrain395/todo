# Todo Agent (Python + Vue 3)

这是一个现代化的 TODO 智能体应用，支持 Web 前端、FastAPI 接口服务与交互式智能终端 CLI。

## 架构说明

- **后端架构**：Python 3 (基于 [uv](https://docs.astral.sh/uv/) 管理，分层架构：`api/`、`service/`、`repository/`、`cli/`)
- **Web 服务**：FastAPI + Uvicorn + Pydantic (提供 RESTful 与通用 RPC 接口)
- **数据持久化**：SQLite 数据库
- **AI 智能体引擎**：支持多厂商 LLM（SiliconFlow、DeepSeek、Ollama 等）自然语言意图识别与任务自动调度
- **交互式 CLI**：基于 Prompt Toolkit + Rich，支持 Slash Commands 补全、彩色可视化与 Agent 会话
- **前端 UI**：Vue 3 + Vite + TypeScript + Lucide Icons

---

## 启动与运行

### 1. Python 后端与 CLI（使用 `uv` 管理）

```bash
# 启动 FastAPI HTTP/RPC 接口服务 (默认端口 8000)
uv run todo-server
# 或
uv run python -m backend.main

# 启动交互式智能终端 CLI
uv run todo-cli

# 快速执行 CLI 命令
uv run todo-cli --list
uv run todo-cli add "学习 Python FastAPI 与 UV"

# 运行后端单元测试
uv run --extra dev pytest backend/tests
```

### 2. 前端界面（使用 `pnpm` 管理）

```bash
# 安装前端依赖
pnpm install

# 启动前端开发服务器
pnpm run dev

# 构建前端产物
pnpm run build
```
