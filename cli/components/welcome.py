"""CLI 欢迎信息与 Banner 组件。

将欢迎 Logo 与默认欢迎文本集中在此组件中统一管理，
支持左侧 Logo、富文本 Panel 边框、快捷指令提示、自定义欢迎语以及优雅降级。
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional
from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

_default_console = Console(force_terminal=True, legacy_windows=False)
_welcome_shown = False

# 默认立体的 TODO ASCII 标识
DEFAULT_LOGO = (
    r"[bold cyan]   ______ ____  ____   ____ [/bold cyan]" + "\n"
    r"[bold cyan]  /_  __/ __ \/ __ \ / __ \ [/bold cyan]" + "\n"
    r"[bold cyan]   / / / / / / / / // / / / [/bold cyan]" + "\n"
    r"[bold cyan]  / / / /_/ / /_/ // /_/ /  [/bold cyan]" + "\n"
    r"[bold cyan] /_/  \____/_____/ \____/   [/bold cyan]"
)

# 默认欢迎提示文本
DEFAULT_WELCOME_TEXT = (
    "🎉 欢迎使用 Todo Agent CLI！\n"
    "💡 输入 /help 查看命令列表，直接输入内容即可与 AI 助理交互。\n"
    "🚪 输入 exit、quit 或按两次 Ctrl+C 退出程序。"
)
DEFAULT_WELCOME_MESSAGE = DEFAULT_WELCOME_TEXT


def _load_default_config() -> Dict[str, Any]:
    try:
        from ..config import load_cli_config
        return load_cli_config()
    except Exception:
        return {}


class WelcomeComponent:
    """CLI 欢迎界面组件，负责渲染并展示欢迎标语、快捷提示与左侧 Logo。"""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        console: Optional[Console] = None,
    ) -> None:
        self.config = _load_default_config() if config is None else config
        self.console = console or _default_console

    @classmethod
    def get_welcome_text(cls, config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """从配置中提取欢迎文本字符串；未配置或未提供 message 时使用组件内置的默认欢迎语。"""
        cfg = _load_default_config() if config is None else config
        val = cfg.get("welcome")
        if val is None:
            val = cfg.get("welcome_message")

        # 未在配置中指定时，使用组件内置的默认文本
        if val is None:
            return DEFAULT_WELCOME_TEXT

        if isinstance(val, bool):
            return DEFAULT_WELCOME_TEXT if val else None

        if isinstance(val, dict):
            if not val.get("enabled", True):
                return None
            text = val.get("message") or val.get("text") or val.get("content") or ""
            return str(text).strip() if text else DEFAULT_WELCOME_TEXT
        elif isinstance(val, list):
            return "\n".join(str(item) for item in val).strip() or DEFAULT_WELCOME_TEXT
        elif isinstance(val, str):
            return val.strip() or DEFAULT_WELCOME_TEXT
        else:
            return str(val).strip() or DEFAULT_WELCOME_TEXT

    @classmethod
    def get_logo(cls, config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """获取用于展示在左侧的 Logo 标识。"""
        cfg = _load_default_config() if config is None else config
        welcome_cfg = cfg.get("welcome")

        if isinstance(welcome_cfg, dict):
            # 允许通过配置显式禁用 logo
            if not welcome_cfg.get("show_logo", True):
                return None
            custom_logo = welcome_cfg.get("logo")
            if custom_logo:
                return str(custom_logo).strip()

        return DEFAULT_LOGO

    def build_renderable(self) -> Optional[RenderableType]:
        """构建 Rich 可渲染对象（含左侧 Logo 与右侧欢迎说明）。"""
        text = self.get_welcome_text(self.config)
        if not text:
            return None

        logo = self.get_logo(self.config)

        # 组织左右布局或单一文本
        if logo:
            grid = Table.grid(padding=(0, 2))
            grid.add_column(justify="left", vertical="middle")
            grid.add_column(justify="left", vertical="middle")
            grid.add_row(logo, text)
            content: RenderableType = grid
        else:
            content = Text.from_markup(text)

        # 检查是否要求以 Panel 容器包装
        welcome_cfg = self.config.get("welcome")
        use_panel = False
        title = "Todo Agent CLI"
        border_style = "bright_blue"

        if isinstance(welcome_cfg, dict):
            use_panel = welcome_cfg.get("panel", False)
            title = welcome_cfg.get("title", title)
            border_style = welcome_cfg.get("border_style", border_style)

        if use_panel:
            return Panel(
                content,
                title=f"[bold cyan]{title}[/bold cyan]",
                border_style=border_style,
                padding=(1, 2),
                expand=False,
            )

        return content

    def show(self, force: bool = False) -> bool:
        """显示欢迎内容。

        Args:
            force: 为 True 时强制重新输出，即使之前已输出过。

        Returns:
            bool: 是否成功打印。
        """
        global _welcome_shown
        if _welcome_shown and not force:
            return False

        renderable = self.build_renderable()
        if renderable is None:
            return False

        try:
            self.console.print(renderable)
            self.console.print()
        except Exception:
            text = self.get_welcome_text(self.config)
            if text:
                print(text)
                print()

        _welcome_shown = True
        return True


def show_welcome(
    config: Optional[Dict[str, Any]] = None,
    console: Optional[Any] = None,
    force: bool = False,
) -> bool:
    """显示欢迎组件的便捷入口函数。"""
    comp = WelcomeComponent(config=config, console=console)
    return comp.show(force=force)


def get_welcome_renderable(
    config: Optional[Dict[str, Any]] = None,
    console: Optional[Any] = None,
) -> Optional[RenderableType]:
    """获取欢迎组件的可渲染对象。"""
    comp = WelcomeComponent(config=config, console=console)
    return comp.build_renderable()


def reset_welcome_state() -> None:
    """重置欢迎组件的显示状态标记。"""
    global _welcome_shown
    _welcome_shown = False
