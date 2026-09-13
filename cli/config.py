"""CLI configuration loader and welcome display utility."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from rich.console import Console

_cli_console = Console(force_terminal=True, legacy_windows=False)
_welcome_shown = False


def get_cli_config_path() -> Path:
    """获取 CLI 专用配置文件路径 (cli/config.json)"""
    cli_dir = Path(__file__).resolve().parent
    cfg_file = cli_dir / "config.json"
    if cfg_file.exists():
        return cfg_file

    # 备选：从项目根目录定位
    root_cfg = cli_dir.parent / "cli" / "config.json"
    if root_cfg.exists():
        return root_cfg

    return cfg_file


def load_cli_config() -> Dict[str, Any]:
    """读取 cli/config.json 配置文件"""
    path = get_cli_config_path()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}


def save_cli_config(data: Dict[str, Any]) -> bool:
    """持久化保存 cli/config.json 配置文件"""
    path = get_cli_config_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def get_welcome_message(config: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """从 CLI 配置获取欢迎内容（委托至 components.welcome 统一管理）。"""
    from .components.welcome import WelcomeComponent
    if config is None:
        config = load_cli_config()
    return WelcomeComponent.get_welcome_text(config)


def show_welcome(
    config: Optional[Dict[str, Any]] = None,
    console: Optional[Any] = None,
    force: bool = False,
) -> bool:
    """在终端显示欢迎信息（委托至 components.welcome 组件）。

    如果已经显示过且 force 为 False，则跳过以防重复输出。
    返回 True 表示成功显示，False 表示未显示（已禁用或无内容）。
    """
    from .components.welcome import show_welcome as _comp_show_welcome
    if config is None:
        config = load_cli_config()
    return _comp_show_welcome(config=config, console=console or _cli_console, force=force)


def reset_welcome_state() -> None:
    """重置欢迎信息显示状态（用于测试或重新启动）"""
    from .components.welcome import reset_welcome_state as _comp_reset
    _comp_reset()
