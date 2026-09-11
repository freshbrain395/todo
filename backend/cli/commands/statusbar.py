"""Status bar configuration command: /statusbar, /status."""

from typing import Optional, List, Dict, Any
from backend.repository.db import DbState
from backend.service.ai import LlmConfig
from ..components.status_bar import (
    STATUS_BAR_OPTIONS,
    DEFAULT_STATUS_BAR_ITEMS,
    load_status_bar_items,
    save_status_bar_items,
)
from .base import console


async def select_status_bar_items_interactive(
    current_items: List[str],
    menu_runner=None,
) -> Optional[List[str]]:
    """二级 Checkbox 多选菜单：配置状态栏显示项"""
    from ..app import run_interactive_checkbox_menu
    runner = menu_runner or run_interactive_checkbox_menu

    action, selected = await runner(
        title="📊 配置状态栏显示项 (Checkbox 多选)",
        items=STATUS_BAR_OPTIONS,
        checked_ids=current_items,
        render_item_fn=lambda it: f"{it['title']:<10} {it['desc']}",
        help_hint="↑/↓ 移动 | Space 勾选/反选 | a 全选 | Enter 保存 | Esc 取消",
        max_visible_items=10,
    )
    if action == "confirm" and selected is not None:
        return [it["id"] for it in selected]
    return None


async def handle_statusbar_command(
    line: str,
    db: DbState,
    llm_cfg: LlmConfig,
    status_bar_state: Dict[str, Any],
    session=None,
    menu_runner=None,
) -> bool:
    """Handle /statusbar and /status commands."""
    trimmed = line.strip()
    if not (trimmed in ["/statusbar", "/status"] or trimmed.startswith("/statusbar ") or trimmed.startswith("/status ")):
        return False

    parts = trimmed.split(maxsplit=1)
    sub = parts[1].strip().lower() if len(parts) > 1 else ""

    if sub == "reset":
        new_items = list(DEFAULT_STATUS_BAR_ITEMS)
        save_status_bar_items(db, new_items)
        status_bar_state["items"] = new_items
        console.print("[green]✓ 状态栏显示配置已重置为默认（全部显示）。[/green]")
        return True

    if sub == "list":
        cur_items = status_bar_state.get("items") or load_status_bar_items(db)
        cur_set = set(cur_items)
        console.print("[bold cyan]当前状态栏显示配置：[/bold cyan]")
        for opt in STATUS_BAR_OPTIONS:
            mark = "[bold green][x][/bold green]" if opt["id"] in cur_set else "[dim][ ][/dim]"
            console.print(f"  {mark} {opt['title']} - {opt['desc']}")
        return True

    # 交互式 Checkbox 菜单配置
    cur_items = status_bar_state.get("items") or load_status_bar_items(db)
    selected_ids = await select_status_bar_items_interactive(cur_items, menu_runner=menu_runner)

    if selected_ids is None:
        console.print("[dim]已取消状态栏配置。[/dim]")
        return True

    save_status_bar_items(db, selected_ids)
    status_bar_state["items"] = selected_ids

    # 打印成功提示
    cur_set = set(selected_ids)
    enabled_titles = [opt["title"] for opt in STATUS_BAR_OPTIONS if opt["id"] in cur_set]
    display_str = "、".join(enabled_titles) if enabled_titles else "无（全部隐藏）"
    console.print(f"[green]✓ 状态栏配置已保存！当前显示项 ({len(selected_ids)} 项): [bold]{display_str}[/bold][/green]")
    return True
