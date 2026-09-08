# Todo Agent (Python + Vue 3)

[English](README.md) | [简体中文](README_zh.md)

---

A modern LLM-powered TODO agent application designed with natural language task planning and intent parsing. It supports three execution modes: Native Desktop GUI, Interactive Terminal CLI, and Web Browser.

---

### 🌟 Unified Experience Architecture

```text
Todo Agent
│
├── 🖥️ Desktop Shortcut
│      └── Double click → Native GUI Window
│
└── 💻 Command Line (Automatically registered in PATH)
       ├── todo
       │    └── CLI Chat Mode (Chat + Todo AI Agent)
       │
       ├── todo gui
       │    └── Launch Native Desktop Window
       │
       ├── todo web
       │    └── Launch Web Server & auto-open default browser
       │
       └── todo server
            └── Run backend API service in background
```

---

### 📦 Windows One-Click Installer & Deployment

After building the standalone binary `release/todo.exe`, you can install and configure it in one click:

- **One-Click Install**: Run `scripts/install.bat` (or execute `scripts/install.ps1` in PowerShell):
  - Deploys executable to `%LOCALAPPDATA%\Programs\Todo Agent\`
  - Creates Desktop shortcut pointing directly to GUI
  - Creates Start Menu shortcut
  - Adds the directory to user `PATH` (run `todo` directly from any prompt)
- **Safe Data Storage**:
  - SQLite database and configurations are isolated in `%APPDATA%\Todo Agent\` (survives upgrades and reinstallation)
- **Clean Uninstall**: Run `powershell scripts/uninstall.ps1` to clean up shortcuts and PATH while preserving user data.

---

### 🚀 Usage & Launch Modes

#### Mode 1: Unified Command Line (`todo`)
- `todo`: Enter **Chat + Todo Agent** directly (natural language, no need for `/chat`)
- `todo gui`: Launch native desktop client
- `todo web`: Launch web service and open default browser
- `todo server`: Start backend FastAPI server only

#### Mode 2: Desktop GUI
- Double click the **Todo Agent** desktop shortcut
- Or run: `uv run python run.py gui`
- Or run batch script: `run.bat`

#### Mode 3: Developer Live Reload
```bash
pnpm dev              # Concurrently run FastAPI server & Vite frontend
pnpm run dev:frontend # Frontend only
pnpm run dev:backend  # Backend only
```

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


