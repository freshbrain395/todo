"""Mode switching commands: /mode."""

import sys
from typing import Dict, Any, Optional, List
from backend.service.ai import (
    DEFAULT_AGENT_PROMPT,
    DEFAULT_CHAT_PROMPT,
    DEFAULT_JSON_PROMPT,
)
from .base import console

MODE_OPTIONS = [
    ("chat", "普通聊天模式"),
    ("agent", "Todo Agent 助理模式"),
    ("json", "严格 JSON 输出模式"),
]


async def select_mode_interactive(current_mode_name: str = "chat", menu_runner=None) -> Optional[str]:
    """二级菜单：使用上下箭头选择工作模式"""
    from ..app import run_interactive_selection_menu
    runner = menu_runner or run_interactive_selection_menu

    items = [
        {"id": opt_name, "name": opt_name, "desc": opt_desc}
        for opt_name, opt_desc in MODE_OPTIONS
    ]
    action, selected = await runner(
        title="🔄 选择工作模式",
        items=items,
        current_id=current_mode_name or "chat",
        render_item_fn=lambda it: f"{it['id']:<8} {it['desc']}",
        help_hint="↑/↓ 选择 | Enter 确认 | Esc 取消",
        max_visible_items=10,
    )
    if action == "confirm" and selected:
        return selected["id"]
    return None


def apply_mode_switch(target_mode: str, current_mode: Dict[str, Any]) -> bool:
    """统一应用模式切换逻辑"""
    m = target_mode.lower().strip()
    if m == "chat":
        current_mode["name"] = "chat"
        current_mode["role"] = "chat"
        current_mode["display_name"] = "聊天模式"
        current_mode["system_prompt"] = DEFAULT_CHAT_PROMPT
        current_mode["output_format"] = "text"
        console.print("[green]✓ 已切换到常规聊天模式。[/green]")
        return True
    elif m == "agent":
        current_mode["name"] = "agent"
        current_mode["role"] = "agent"
        current_mode["display_name"] = "Agent助理"
        current_mode["system_prompt"] = DEFAULT_AGENT_PROMPT
        current_mode["output_format"] = "text"
        console.print("[green]✓ 已切换到 Todo Agent 智能助理模式。[/green]")
        return True
    elif m == "json":
        current_mode["name"] = "json"
        current_mode["role"] = "json"
        current_mode["display_name"] = "JSON模式"
        current_mode["system_prompt"] = DEFAULT_JSON_PROMPT
        current_mode["output_format"] = "json"
        console.print("[green]✓ 已切换到结构化 JSON 模式。[/green]")
        return True
    return False


async def handle_mode_command(line: str, current_mode: Dict[str, Any], menu_runner=None, select_fn=None) -> bool:
    """Handle /mode [chat | agent | json] command."""
    trimmed = line.strip()
    if not (trimmed == "/mode" or trimmed.startswith("/mode ")):
        return False

    parts = trimmed.split(maxsplit=1)
    if len(parts) == 1:
        cur_name = current_mode.get("name", "chat")
        fn = select_fn
        if fn is None:
            fn = getattr(sys.modules.get("backend.cli"), "select_mode_interactive", select_mode_interactive)
        selected = await fn(cur_name, menu_runner=menu_runner) if "menu_runner" in fn.__code__.co_varnames else await fn(cur_name)
        if selected:
            apply_mode_switch(selected, current_mode)
        else:
            console.print("[dim]已取消模式选择。[/dim]")
        return True
    else:
        target_mode = parts[1].strip().lower()
        ok = apply_mode_switch(target_mode, current_mode)
        if not ok:
            console.print(f"[red]未知模式 '{target_mode}'。可选模式：chat, agent, json[/red]")
        return True
