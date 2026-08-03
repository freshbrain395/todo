# Todo Agent

这是一个基于 Python 的 TODO 智能体项目。

## 开发与管理

本项目使用 [uv](https://github.com/astral-sh/uv) 进行项目和依赖管理。

### 安装依赖

```bash
uv pip install -r requirements.txt
```

或者使用 uv 虚拟环境：

```bash
uv venv
source .venv/Scripts/activate  # Windows (CMD/PowerShell 使用对应的激活脚本)
```

### 运行项目

- **运行 Rich 命令行版 (CLI)**：
  ```bash
  uv run main.py
  ```

- **运行 PyQt6 现代化图形界面 (GUI)**：
  ```bash
  uv run main_gui.py
  ```
