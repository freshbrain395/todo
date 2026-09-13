"""Thinking mode command: /think, /thinking."""

from typing import Optional, List, Dict, Any
from backend.repository.db import DbState
from backend.service.ai import LlmConfig
from .base import console
from .ai_config import save_current_llm_config


async def select_think_interactive(
    current_thinking: bool = False,
    menu_runner=None,
) -> Optional[str]:
    """二级菜单：选择 AI 思考模式状态"""
    from ..app import run_interactive_selection_menu
    runner = menu_runner or run_interactive_selection_menu

    items = [
        {"id": "toggle", "title": "快速切换开关", "desc": "在当前开/关状态之间快速反转"},
        {"id": "on", "title": "开启思考模式", "desc": "展示深度思考与推理过程 (Thinking)"},
        {"id": "off", "title": "关闭思考模式", "desc": "直接输出最终回答，加快响应速度"},
    ]
    cur_id = "on" if current_thinking else "off"
    action, selected = await runner(
        title="💭 选择思考模式 (Thinking)",
        items=items,
        current_id=cur_id,
        render_item_fn=lambda it: f"{it['id']:<8} {it['title']:<16} {it['desc']}",
        help_hint="↑/↓ 选择 | Enter 确认 | Esc 取消",
        max_visible_items=10,
    )
    if action == "confirm" and selected:
        return selected["id"]
    return None


async def handle_think_command(
    line: str,
    db: DbState,
    llm_cfg: LlmConfig,
    session=None,
    menu_runner=None,
) -> bool:
    """Handle /think and /thinking commands."""
    trimmed = line.strip()
    if not (trimmed == "/think" or trimmed.startswith("/think ") or trimmed in ["/thinking"]):
        return False

    parts = trimmed.split(maxsplit=1)
    if len(parts) == 1:
        if session is not None:
            selected_th = await select_think_interactive(llm_cfg.enable_thinking, menu_runner=menu_runner)
            if selected_th == "toggle":
                llm_cfg.enable_thinking = not llm_cfg.enable_thinking
            elif selected_th == "on":
                llm_cfg.enable_thinking = True
            elif selected_th == "off":
                llm_cfg.enable_thinking = False
            elif selected_th is None:
                console.print("[dim]已取消选择思考模式。[/dim]")
                return True
        else:
            llm_cfg.enable_thinking = not llm_cfg.enable_thinking
    else:
        sub = parts[1].strip().lower()
        if sub == "toggle":
            llm_cfg.enable_thinking = not llm_cfg.enable_thinking
        elif sub in ["on", "true", "1", "open", "enable"]:
            llm_cfg.enable_thinking = True
        elif sub in ["off", "false", "0", "close", "disable"]:
            llm_cfg.enable_thinking = False
        elif sub in ["status", "state"]:
            status_text = "开启" if llm_cfg.enable_thinking else "关闭"
            console.print(f"[dim]当前思考模式状态: [bold]{status_text}[/bold][/dim]")
            return True
        else:
            console.print("[yellow]用法: /think [on | off | toggle | status][/yellow]")
            return True

    save_current_llm_config(db, llm_cfg)
    status_text = "[bold green]已开启[/bold green]" if llm_cfg.enable_thinking else "[bold yellow]已关闭[/bold yellow]"
    console.print(f"[green]✓ AI 思考模式 (Thinking): {status_text}[/green]")
    return True
