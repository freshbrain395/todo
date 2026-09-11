"""Skill selection command: /skill."""

from typing import List, Dict, Any, Optional
from backend.repository.db import DbState
from backend.service.ai_config import AiConfigService
from .base import console


async def select_skill_interactive(
    skills: List[Dict[str, Any]],
    current_role: str = "",
    menu_runner=None,
) -> Optional[Dict[str, Any]]:
    """二级菜单：选择 AI 技能角色"""
    from ..app import run_interactive_selection_menu
    runner = menu_runner or run_interactive_selection_menu

    if not skills:
        return None

    def render_sk(sk: Dict[str, Any]) -> str:
        sid = sk.get("id", "")
        title = sk.get("title", sid)
        desc = sk.get("description", "")
        return f"{sid:<14} {title:<16} {desc}"

    action, selected = await runner(
        title="⚡ 选择 AI 技能角色 (Skills)",
        items=skills,
        current_id=current_role,
        key_fn=lambda it: str(it.get("id", "")),
        render_item_fn=render_sk,
        help_hint="↑/↓ 选择 | Enter 启用 | Esc 取消",
        max_visible_items=10,
    )
    if action == "confirm":
        return selected
    return None


async def handle_skill_command(
    line: str,
    db: DbState,
    current_mode: Dict[str, Any],
    menu_runner=None,
) -> bool:
    """Handle /skill command."""
    trimmed = line.strip()
    if not (trimmed == "/skill" or trimmed.startswith("/skill ")):
        return False

    ai_cfg_service = AiConfigService(db)
    skills = ai_cfg_service.get_skills()
    parts = trimmed.split(maxsplit=1)

    if len(parts) == 1:
        target_sk = await select_skill_interactive(skills, current_mode.get("role", ""), menu_runner=menu_runner)
        if target_sk:
            current_mode["name"] = f"skill:{target_sk.get('id')}"
            current_mode["role"] = target_sk.get("id")
            current_mode["display_name"] = f"技能:{target_sk.get('title', target_sk.get('id'))}"
            current_mode["system_prompt"] = target_sk.get("systemPrompt") or target_sk.get("system_prompt", "")
            current_mode["output_format"] = "text"
            console.print(f"[green]✓ 已切换到技能模式: [bold]{target_sk.get('title')}[/bold][/green]")
        else:
            console.print("[dim]已取消选择技能。[/dim]")
        return True
    else:
        sid = parts[1].strip()
        target_sk = next((sk for sk in skills if sk.get("id", "").lower() == sid.lower()), None)
        if target_sk:
            current_mode["name"] = f"skill:{target_sk.get('id')}"
            current_mode["role"] = target_sk.get("id")
            current_mode["display_name"] = f"技能:{target_sk.get('title', sid)}"
            current_mode["system_prompt"] = target_sk.get("systemPrompt") or target_sk.get("system_prompt", "")
            current_mode["output_format"] = "text"
            console.print(f"[green]✓ 已切换到技能模式: [bold]{target_sk.get('title')}[/bold][/green]")
        else:
            available_sids = ", ".join([sk.get("id", "") for sk in skills])
            console.print(f"[red]未找到技能 '{sid}'。可用 ID: {available_sids}[/red]")
        return True
