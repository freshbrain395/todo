# Todo Agent (Tauri 2.0 + Vue 3 + Rust)

这是一个基于 Rust (Tauri 2.0) 与 Vue 3 + TypeScript 开发的现代化 TODO 智能体桌面应用。

## 架构说明

- **前端 UI**：Vue 3 + Vite + TypeScript + Lucide Icons
- **后端 / 原生逻辑**：Rust (Tauri 2.0)
- **数据持久化**：SQLite 数据库
- **智能体引擎**：基于 Rust 实现的多 LLM 意图解析与工具调用

## 开发与运行

本项目使用 [pnpm](https://pnpm.io/) 进行 JavaScript/TypeScript 依赖管理。

### 1. 安装前端依赖

```bash
pnpm install
```

### 2. 运行前端开发服务器 (Web 预览)

```bash
pnpm run dev
```

### 3. 构建前端产物

```bash
pnpm run build
```

### 4. 运行 Tauri 桌面客户端 (开发模式)

```bash
pnpm run tauri dev
```

### 5. 构建 Tauri 桌面安装包 (Release)

```bash
pnpm run tauri build
```
