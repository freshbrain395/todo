# Todo Agent (Python + Vue 3)

[English](README.md) | [简体中文](README_zh.md)

---

A modern LLM-powered TODO agent application designed with natural language task planning and intent parsing. It supports three execution modes: Native Desktop GUI, Interactive Terminal CLI, and Web Browser.

---

### 🚀 Getting Started

Choose from multiple launch modes depending on your workflow:

#### Mode 1: Native Desktop GUI Window (Recommended)

Runs directly as an independent desktop window using `pywebview` without opening an external browser:

- **Launch via Python script directly**:
  ```bash
  uv run python run.py
  # or explicitly pass the gui argument
  uv run python run.py gui
  ```
- **Launch via Windows batch script**:
  ```cmd
  run.bat
  ```
  *(If the binary has not been built yet, this script will automatically package and launch it)*
- **Run the packaged standalone executable**:
  ```cmd
  .\release\todo-agent.exe
  ```

---

#### Mode 2: Interactive Terminal CLI

Run completely inside your terminal without GUI overhead. Supports natural language intent understanding and slash commands powered by `prompt-toolkit` and `rich`:

- **Launch via `uv`**:
  ```bash
  uv run todo-cli
  # or
  uv run python run.py cli
  ```
- **Launch via `pnpm`**:
  ```bash
  pnpm run cli
  ```
- **Common CLI Commands**:
  - Input plain natural language directly (e.g., `Remind me to attend the team meeting tomorrow at 3 PM`).
  - Slash commands: `/help`, `/list`, `/add <text>`, `/done <ID>`, `/delete <ID>`, `/prompt`, `/model`, `/provider`, etc.

---

#### Mode 3: Web Browser Development & Debugging

Ideal for frontend development, debugging, or using inside a browser:

- **Launch both Frontend and Backend concurrently (Recommended)**:
  ```bash
  # 1. Install dependencies (first time only)
  pnpm install

  # 2. Concurrently run backend (:8000) and frontend (:1420)
  pnpm dev
  ```
- **Launch Frontend only**:
  ```bash
  pnpm run dev:frontend
  ```
- **Launch FastAPI Backend only**:
  ```bash
  uv run todo-server
  # or
  pnpm run dev:backend
  ```

---

### 🛠️ Build and Testing

#### 1. Frontend Build & Test
```bash
pnpm run build          # Build static web production assets (front/dist)
pnpm test               # Run frontend unit tests
```

#### 2. Desktop Client Packaging
```bash
pnpm run build:exe      # Package standalone release/todo-agent.exe
```

#### 3. Backend Unit Tests
```bash
uv run python -m pytest backend/tests
```

---

### 📁 Project Architecture

- **Frontend** (`front/`): Vue 3 + Vite + TypeScript + Lucide Icons
- **Backend** (`backend/`): Python 3 (managed with `uv`)
  - `backend/api/`: FastAPI route handlers and RPC bridge
  - `backend/service/`: Business domain logic, LLM agent intent parsing
  - `backend/repository/`: SQLite storage layer (Todo, Config, AI Session)
  - `backend/cli.py`: Interactive CLI with Prompt Toolkit and Rich
  - `backend/main.py`: Entrypoint dispatcher for Desktop GUI, Server, and CLI


