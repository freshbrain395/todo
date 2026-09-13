"""Prompt template command: /prompt."""

from typing import List, Dict, Any, Optional, Tuple
from backend.repository.db import DbState
from backend.service.ai_config import AiConfigService
from .base import console


async def select_prompt_interactive(
    prompts: List[Dict[str, Any]],
    menu_runner=None,
) -> Optional[Dict[str, Any]]:
    """二级菜单：选择预设 Prompt 模板"""
    from ..app import run_interactive_selection_menu
    runner = menu_runner or run_interactive_selection_menu

    if not prompts:
        return None

    def render_pr(pr: Dict[str, Any]) -> str:
        pid = pr.get("id", "")
        title = pr.get("title", "")
        category = pr.get("category", "")
        return f"{pid:<8} {title:<18} [{category}]"

    action, selected = await runner(
        title="📝 选择 Prompt 提示词模板",
        items=prompts,
        key_fn=lambda it: str(it.get("id", "")),
        render_item_fn=render_pr,
        help_hint="↑/↓ 选择 | Enter 执行 | Esc 取消",
        max_visible_items=10,
    )
    if action == "confirm":
        return selected
    return None


async def handle_prompt_command(
    line: str,
    db: DbState,
    menu_runner=None,
) -> Tuple[bool, Optional[str]]:
    """Handle /prompt command.
    Returns:
        (handled, execute_prompt_text):
        - If not a prompt command: (False, None)
        - If handled without execution (e.g. cancelled): (True, None)
        - If a prompt was selected for AI execution: (True, prompt_text)
    """
    trimmed = line.strip()
    if not (trimmed == "/prompt" or trimmed.startswith("/prompt ")):
        return (False, None)

    ai_cfg_service = AiConfigService(db)
    prompts = ai_cfg_service.get_prompts()
    parts = trimmed.split(maxsplit=1)

    if len(parts) == 1:
        target_pr = await select_prompt_interactive(prompts, menu_runner=menu_runner)
        if target_pr:
            prompt_text = target_pr.get("text", "")
            console.print(f"[dim]📌 正在执行 Prompt [{target_pr.get('title')}]: {prompt_text}[/dim]")
            return (True, prompt_text)
        else:
            console.print("[dim]已取消选择 Prompt。[/dim]")
            return (True, None)
    else:
        pid = parts[1].strip()
        target_pr = next((pr for pr in prompts if pr.get("id", "").lower() == pid.lower()), None)
        if target_pr:
            prompt_text = target_pr.get("text", "")
            console.print(f"[dim]📌 正在执行 Prompt [{target_pr.get('title')}]: {prompt_text}[/dim]")
            return (True, prompt_text)
        else:
            available_pids = ", ".join([pr.get("id", "") for pr in prompts])
            console.print(f"[red]未找到 Prompt '{pid}'。可用 ID: {available_pids}[/red]")
            return (True, None)
