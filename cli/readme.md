# Todo CLI 命令行客户端

基于 Python `prompt_toolkit` 与 `rich` 构建的高性能交互式终端客户端，提供自适应边框输入框、动态底部状态栏、斜线命令自动补全以及 AI 对话交互能力。

---

## 目录

- [环境依赖](#环境依赖)
- [快速启动](#快速启动)
  - [推荐：使用 uv 启动](#1-推荐使用-uv-启动)
  - [标准 Python 启动](#2-标准-python-启动)
- [内置命令与快捷操作](#内置命令与快捷操作)
  - [系统与控制命令](#系统与控制命令)
  - [模型供应商管理](#模型供应商管理)
- [运行机制与特性](#运行机制与特性)
- [配置文件说明 (config.json)](#配置文件说明-configjson)
- [代码目录结构](#代码目录结构)

---

## 环境依赖

- **Python 版本**：>= 3.10
- **核心依赖包**：
  - `prompt_toolkit`（终端交互、自动补全、输入框与状态栏驱动）
  - `rich`（控制台彩色文本、表格、面板输出）

如果使用 `uv`，可直接通过以下方式安装依赖：

```bash
uv pip install prompt_toolkit rich
```

---

## 快速启动

> **注意**：启动时建议在项目根目录（`todo/`）执行，以便 Python 能够正确解析 `cli` 模块命名空间。

### 1. 推荐：使用 uv 启动

在 `c:\project\python\todo` 根目录下执行：

```bash
# 作为模块直接启动（推荐）
uv run python -m cli

# 或者显式指定入口脚本
uv run python -m cli.app
```

如果在 `c:\project\python\todo\cli` 目录下：

```bash
uv run python app.py
```

---

### 2. 标准 Python 启动

在 `c:\project\python\todo` 根目录下执行：

```bash
# 作为模块直接启动
python -m cli

# 或指定 app.py
python -m cli.app
```

如果在 `c:\project\python\todo\cli` 目录下：

```bash
python app.py
```

---

## 内置命令与快捷操作

在客户端运行界面的输入框中，既可以直接输入自然语言内容与 AI 对话，也可以输入以 `/` 开头的斜线指令或快捷别名：

### 系统与控制命令

| 命令 | 别名 | 说明 |
| :--- | :--- | :--- |
| `/quit` | `/exit`, `quit`, `exit`, `:q`, `quit()`, `exit()` | 退出 CLI 应用程序 |
| `/clear` | `/cls`, `clear`, `cls`, `/clear_screen` | 清屏并重置对话上下文历史。支持子参数：<br>• `/clear screen`：仅清空终端屏幕<br>• `/clear history`：仅重置对话上下文<br>• `/clear all`（默认）：同时清空屏幕并重置上下文 |
| `/help` | - | 查看所有已注册命令与帮助提示 |

> **快捷键提示**：
> - `Ctrl + C`：提示防误触，1.5 秒内连续按下两次将安全退出程序。
> - `Tab`：在输入 `/` 时自动呼出命令自动补全菜单，支持上下方向键切换。

### 模型供应商管理

| 命令格式 | 说明 |
| :--- | :--- |
| `/provider` / `/model` | 呼出数字列表交互式选择与切换供应商（支持上下箭头及数字键），支持二级选择具体模型 |
| `/provider table` | 以格式化表格列出所有供应商列表、Base URL、模型与脱敏 API Key |
| `/provider use <id> [model]` | 快速切换当前使用的模型供应商，可直接指定模型名称 |
| `/provider set-key <id> <key>` | 为指定供应商配置或更新 API Key |
| `/provider add <id> <baseurl> <models> [key]` | 新增自定义模型供应商 |

---

## 运行机制与特性

1. **双重运行模式**：
   - **交互式 UI 模式（默认）**：调用 `run_prompt_toolkit()`，呈现带上下边框的输入框、右侧模式标识及底部状态栏。
   - **降级模式（Fallback）**：当检测到终端不支持控制台屏幕缓冲区（如非交互式管道或精简终端抛出 `NoConsoleScreenBufferError`）时，自动平滑降级为 `run_fallback()` 标准控制台输入。
2. **命令自动扫描**：
   - `cli/commands/__init__.py` 会自动扫描 `commands/` 目录下的所有模块并完成命令注册，无需手动维护命令列表。
3. **中文与宽字符自适应**：
   - `cli/utils.py` 严格基于 East Asian Width 计算中英文字符、全角标点与 Emoji 的真实显示列宽，保证终端边框与对齐无撕裂。

---

## 配置文件说明 (config.json)

`cli/config.json` 用于定制 CLI 的交互行为与外观：

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Todo Agent CLI Configuration",
  "welcome": {
    "enabled": true,
    "message": "🎉 欢迎使用 Todo Agent CLI！\n💡 输入 /help 查看命令列表，直接输入内容即可与 AI 助理交互。\n🚪 输入 exit、quit 或按两次 Ctrl+C 退出程序。"
  },
  "default_mode": "agent",
  "prompt_text": "❯ ",
  "max_history_turns": 30,
  "slash_menu": {
    "max_visible": 10
  },
  "status_bar": {
    "enabled": true,
    "items": [
      "status",
      "mode",
      "model",
      "think",
      "key",
      "todo",
      "help"
    ]
  },
  "theme": {
    "prompt": "#ansicyan bold",
    "input": "#ffffff",
    "rprompt": "#ansigreen italic",
    "border": "#ansibrightblack",
    "bottom-toolbar": "noreverse bg:default",
    "statusbar": "#7f848e"
  }
}
```

- **welcome**：欢迎语配置，支持开关及自定义欢迎文本。
- **prompt_text**：主输入提示符（默认 `❯ `）。
- **max_history_turns**：对话历史轮数限制，超过将自动修剪历史。
- **slash_menu.max_visible**：斜线指令补全弹窗最大可见项数量。
- **status_bar.items**：底部状态栏显示项过滤与顺序。
- **theme**：终端色彩样式映射（支持 prompt_toolkit 样式定义）。

---

## 代码目录结构

```text
cli/
├── __init__.py           # 包导出入口，导出主要 API 与函数
├── __main__.py           # python -m cli 直接启动入口
├── app.py                # CLI 应用主循环、CliAgentApp 类、main 启动入口
├── config.py             # 配置读写 (load/save_cli_config) 与欢迎信息渲染
├── config.json           # CLI 运行时基础配置文件（供应商、主题、状态栏等）
├── utils.py              # 宽字符列宽计算、文本对齐、ANSI 过滤与终端工具
├── commands/             # 斜线命令注册与派发模块
│   ├── __init__.py       # 自动发现并注册所有命令模块
│   ├── base.py           # CommandContext、LlmConfig 与 @register_command 装饰器
│   ├── help.py           # /help 命令实现（格式化命令速查表格）
│   ├── clear.py          # /clear 及 /cls 命令实现
│   ├── provider.py       # /provider 及 /model 命令实现（本地供应商管理与脱敏）
│   └── quit.py           # /quit 及 /exit 命令实现
└── components/           # 终端交互组件
    ├── __init__.py       # 组件统一导出
    ├── input.py          # 自适应带边框输入框组件 (BoxedInputSession)
    ├── completer.py      # 斜线命令自动补全器 (SlashCommandCompleter)
    ├── slash_menu.py     # 弹出菜单状态管理
    ├── status_bar.py     # 底部状态栏构造与渲染器
    ├── number_menu.py    # 数字列表单选菜单组件 (NumberMenu)
    ├── checkbox.py       # 多选菜单组件 (CheckboxMenu)
    └── style.py          # UI 配色风格定义
```
