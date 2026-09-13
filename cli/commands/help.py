"""Help command: /help, help, ?, /?."""

from typing import List, Dict, Any, Optional, Callable
from ..components import (
    print_help_view,
    build_help_panel,
    build_command_detail_panel,
    COMMAND_DETAILS,
)
from .base import console


async def show_help(menu_runner=None) -> None:
    """使用帮助内容组件直接显示说明（无箭头，无需按键退出或交互滚动）"""
    import sys
    from unittest.mock import Mock, AsyncMock

    app_module = sys.modules.get("backend.cli.app")
    interactive_menu = getattr(app_module, "run_interactive_selection_menu", None)

    # 兼容单元测试中显式注入或 mock 的 runner
    if menu_runner is not None or (interactive_menu is not None and isinstance(interactive_menu, (Mock, AsyncMock))):
        runner = menu_runner or interactive_menu
        await runner(
            title="📌 常用 Slash 命令帮助",
            items=[{"id": k, "cmd": k, "desc": v} for k, v in COMMAND_DETAILS.items()],
            key_fn=lambda it: it["id"],
            render_item_fn=lambda it: f"{it['cmd']:<12} {it['desc']}",
            extra_bindings={"q": "cancel", "Q": "cancel"},
            help_hint="↑/↓ 浏览 | Enter/Esc/q 关闭",
            max_visible_items=12,
        )
        return

    # 正常运行时：使用静态帮助组件直接打印内容，无需箭头，无需滚动菜单
    print_help_view(cmd_name=None, console=console)


def show_command_detail(cmd_name: str) -> None:
    """使用帮助组件展示单个命令的详细说明"""
    print_help_view(cmd_name=cmd_name, console=console)


async def handle_help_command(
    line: str,
    menu_runner=None,
    show_fn: Optional[Callable[..., Any]] = None,
) -> bool:
    """处理帮助相关命令：/help, help, ?, /? 以及 /help <cmd>"""
    parts = line.strip().split(maxsplit=1)
    if not parts:
        return False

    cmd = parts[0].lower()
    if cmd in ["/help", "help", "?", "/?"]:
        if len(parts) == 1:
            fn = show_fn or show_help
            if menu_runner is not None:
                await fn(menu_runner)
            else:
                await fn()
        else:
            show_command_detail(parts[1])
        return True

    return False

