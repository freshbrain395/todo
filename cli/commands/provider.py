"""Provider management command: /provider, /providers."""

from typing import List, Dict, Any, Optional, Tuple
from prompt_toolkit.formatted_text import HTML
from backend.repository.db import DbState
from backend.service.ai import LlmConfig
from backend.service.ai_config import AiConfigService
from .base import console
from .ai_config import save_current_llm_config


async def select_provider_interactive(
    providers: List[Dict[str, Any]],
    current_id: Optional[str],
    menu_runner=None,
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """二级菜单：选择 AI 供应商"""
    from ..app import run_interactive_selection_menu
    runner = menu_runner or run_interactive_selection_menu

    if not providers:
        return (None, None)

    custom_option = {
        "id": "__custom__",
        "name": "[🛠 自定义 AI 供应商管理...]",
        "model": "",
        "api_key": "",
    }
    all_items = list(providers) + [custom_option]

    def render_provider(p: Dict[str, Any]) -> str:
        if p.get("id") == "__custom__":
            return p.get("name", "")
        if p.get("id") == "ollama" or "11434" in (p.get("base_url") or ""):
            key_tag = "✓ 已配Key" if p.get("api_key") else "本地免Key"
        else:
            key_tag = "✓ 已配Key" if p.get("api_key") else "✗ 无Key"
        custom_tag = " [自定义]" if p.get("is_custom") else ""
        name = p.get("name", p.get("id"))
        model = p.get("model", "")
        return f"{name:<16} ({model}) [{key_tag}]{custom_tag}"

    action, selected = await runner(
        title="🤖 选择 AI 供应商",
        items=all_items,
        current_id=current_id,
        key_fn=lambda it: str(it.get("id", "")),
        render_item_fn=render_provider,
        extra_bindings={
            "e": "edit", "E": "edit",
            "d": "delete", "D": "delete",
            "c": "custom", "C": "custom",
            "a": "custom", "A": "custom",
        },
        help_hint="↑/↓ 选择 | Enter 切换 | e 编辑 | d 删除(自定义) | c 自定义管理 | Esc 取消",
        max_visible_items=10,
    )
    if action in ("custom", "add"):
        return ("custom", None)
    elif action == "confirm":
        if selected and selected.get("id") == "__custom__":
            return ("custom", None)
        return ("switch", selected)
    elif action == "edit":
        if selected and selected.get("id") == "__custom__":
            return ("custom", None)
        return ("edit", selected)
    elif action == "delete":
        if selected and selected.get("id") == "__custom__":
            return ("custom", None)
        return ("delete", selected)
    return (None, None)


async def handle_provider_command(
    line: str,
    db: DbState,
    llm_cfg: LlmConfig,
    session=None,
    menu_runner=None,
) -> bool:
    """Handle /provider and /providers commands."""
    trimmed = line.strip()
    if not (trimmed == "/provider" or trimmed == "/providers" or trimmed.startswith("/provider ")):
        return False

    ai_cfg_service = AiConfigService(db)
    providers = ai_cfg_service.get_providers()
    parts = trimmed.split(maxsplit=2)

    from ..app import run_interactive_selection_menu
    runner = menu_runner or run_interactive_selection_menu

    async def _prompt_input(msg: str, default_val: str = "") -> str:
        if session:
            val = await session.prompt_async(HTML(msg), default=default_val)
            return val.strip()
        return ""

    async def _handle_add_provider():
        console.print("[bold cyan]➕ 添加新的自定义 AI 供应商[/bold cyan]")
        p_id = await _prompt_input("<b>供应商唯一标识 (ID, 如 my-llm): </b>")
        if not p_id:
            console.print("[dim]已取消添加供应商。[/dim]")
            return
        existing = next((p for p in providers if p.get("id", "").lower() == p_id.lower()), None)
        if existing:
            console.print(f"[yellow]供应商 ID '{p_id}' 已存在，请使用编辑功能或更换 ID。[/yellow]")
            return
        p_name = await _prompt_input(f"<b>供应商显示名称 (默认: {p_id}): </b>", default_val=p_id)
        p_base_url = await _prompt_input("<b>Base URL (例如: https://api.example.com/v1): </b>")
        p_api_key = await _prompt_input("<b>API Key (可选): </b>")
        p_model = await _prompt_input("<b>默认模型名称 (如 gpt-4o, deepseek-chat): </b>")

        new_provider = {
            "id": p_id,
            "name": p_name or p_id,
            "base_url": p_base_url,
            "api_key": p_api_key,
            "model": p_model,
            "is_custom": True,
        }
        providers.append(new_provider)
        ai_cfg_service.save_providers(providers)
        console.print(f"[green]✓ 成功添加自定义供应商 [bold]{new_provider['name']}[/bold] 并保存至 config.json！[/green]")

        llm_cfg.provider = p_id
        llm_cfg.base_url = p_base_url
        if p_model:
            llm_cfg.model = p_model
        llm_cfg.api_key = p_api_key
        save_current_llm_config(db, llm_cfg)
        console.print(f"[green]✓ 已自动切换为新供应商: [bold]{new_provider['name']}[/bold] (模型: {llm_cfg.model})[/green]")

    async def _handle_edit_provider(target_p: Dict[str, Any]):
        is_custom = bool(target_p.get("is_custom", False))
        p_name = target_p.get("name", target_p.get("id"))
        console.print(f"[bold cyan]⚙ 编辑供应商: {p_name} ({target_p.get('id')}){' [自定义]' if is_custom else ' [内置]'}[/bold cyan]")
        
        cur_key = target_p.get("api_key") or ""
        if is_custom:
            cur_base_url = target_p.get("base_url") or ""
            cur_model = target_p.get("model") or ""
            new_base_url = await _prompt_input(f"<b>Base URL: </b>", default_val=cur_base_url)
            new_key = await _prompt_input(f"<b>API Key: </b>", default_val=cur_key)
            new_model = await _prompt_input(f"<b>默认模型: </b>", default_val=cur_model)
            target_p["base_url"] = new_base_url
            target_p["api_key"] = new_key
            if new_model:
                target_p["model"] = new_model
        else:
            console.print(f"[dim]提示: 内置官方供应商仅需配置 API Key (Base URL 固定为 {target_p.get('base_url')})。[/dim]")
            new_key = await _prompt_input(f"<b>API Key: </b>", default_val=cur_key)
            target_p["api_key"] = new_key

        ai_cfg_service.save_providers(providers)

        if (llm_cfg.provider or "").lower() == target_p.get("id", "").lower():
            if is_custom:
                llm_cfg.base_url = target_p["base_url"]
                if target_p.get("model"):
                    llm_cfg.model = target_p["model"]
            llm_cfg.api_key = target_p["api_key"]
            save_current_llm_config(db, llm_cfg)
        console.print(f"[green]✓ 已成功更新 [{p_name}] 的配置并持久化！[/green]")

    async def _handle_delete_provider(target_p: Dict[str, Any]):
        if not target_p.get("is_custom"):
            console.print(f"[yellow]⚠️ 供应商 [{target_p.get('name')}] 为系统内置官方供应商，不可删除！[/yellow]")
            return
        p_id = target_p.get("id")
        p_name = target_p.get("name", p_id)
        confirm_del = await _prompt_input(f"<b>确认删除自定义供应商 [{p_name}] 吗？(y/N): </b>", default_val="n")
        if confirm_del.lower() in ("y", "yes"):
            providers[:] = [p for p in providers if p.get("id") != p_id]
            ai_cfg_service.save_providers(providers)
            console.print(f"[green]✓ 已删除自定义供应商 [{p_name}]。[/green]")
            if (llm_cfg.provider or "").lower() == p_id.lower():
                fallback = providers[0] if providers else None
                if fallback:
                    llm_cfg.provider = fallback.get("id", "")
                    llm_cfg.base_url = fallback.get("base_url", "")
                    if fallback.get("model"):
                        llm_cfg.model = fallback.get("model")
                    llm_cfg.api_key = fallback.get("api_key", "")
                    save_current_llm_config(db, llm_cfg)
                    console.print(f"[yellow]当前供应商已被重置回: [bold]{fallback.get('name')}[/bold][/yellow]")
        else:
            console.print("[dim]已取消删除。[/dim]")

    async def _handle_custom_management():
        custom_items = [
            {"id": "add", "name": "➕ 添加新自定义供应商", "desc": "录入新 Base URL, API Key 与模型"},
        ]
        for p in providers:
            if p.get("is_custom"):
                custom_items.append({
                    "id": f"manage_{p.get('id')}",
                    "name": f"⚙ {p.get('name', p.get('id'))}",
                    "desc": f"Base URL: {p.get('base_url')} | Model: {p.get('model')}",
                    "provider": p,
                })

        act, sel = await runner(
            title="🛠 自定义 AI 供应商管理",
            items=custom_items,
            current_id="add",
            key_fn=lambda it: it["id"],
            render_item_fn=lambda it: f"{it['name']:<24} {it.get('desc', '')}",
            extra_bindings={"d": "delete", "D": "delete"},
            help_hint="↑/↓ 选择 | Enter 编辑/进入 | d 删除(自定义) | Esc 返回",
            max_visible_items=10,
        )
        if act == "confirm" and sel:
            if sel["id"] == "add":
                await _handle_add_provider()
            else:
                await _handle_edit_provider(sel["provider"])
        elif act == "delete" and sel:
            if sel.get("provider"):
                await _handle_delete_provider(sel["provider"])
            else:
                console.print("[yellow]无法删除该选项。[/yellow]")

    if len(parts) == 1:
        action, target_p = await select_provider_interactive(providers, llm_cfg.provider, menu_runner=runner)
        if action == "switch" and target_p:
            llm_cfg.provider = target_p.get("id", "")
            llm_cfg.base_url = target_p.get("base_url", "")
            if target_p.get("model"):
                llm_cfg.model = target_p.get("model")
            llm_cfg.api_key = target_p.get("api_key", "")
            save_current_llm_config(db, llm_cfg)
            console.print(
                f"[green]✓ 已成功切换供应商为: [bold]{target_p.get('name')}[/bold] (模型: {llm_cfg.model})[/green]"
            )
        elif action == "edit" and target_p:
            await _handle_edit_provider(target_p)
        elif action == "delete" and target_p:
            await _handle_delete_provider(target_p)
        elif action == "custom":
            await _handle_custom_management()
        else:
            console.print("[dim]已取消操作。[/dim]")
        return True
    else:
        sub = parts[1].strip()
        if sub.lower() in ("custom", "add"):
            await _handle_custom_management()
            return True

        if sub.lower() == "delete":
            target_id = parts[2].strip() if len(parts) > 2 else ""
            target_p = next((p for p in providers if p.get("id", "").lower() == target_id.lower()), None)
            if target_p:
                await _handle_delete_provider(target_p)
            else:
                console.print(f"[red]未找到供应商 '{target_id}' 进行删除。[/red]")
            return True

        if sub.lower() == "edit":
            target_id = parts[2].strip() if len(parts) > 2 else llm_cfg.provider
            target_p = next((p for p in providers if p.get("id", "").lower() == (target_id or "").lower()), None)
            if target_p:
                await _handle_edit_provider(target_p)
            else:
                console.print(f"[red]未找到供应商 '{target_id}' 进行编辑。[/red]")
            return True

        target_p = next((p for p in providers if p.get("id", "").lower() == sub.lower()), None)
        if target_p:
            llm_cfg.provider = target_p.get("id", sub)
            llm_cfg.base_url = target_p.get("base_url", "")
            if target_p.get("model"):
                llm_cfg.model = target_p.get("model")
            llm_cfg.api_key = target_p.get("api_key", "")
            save_current_llm_config(db, llm_cfg)
            console.print(
                f"[green]✓ 已成功切换供应商为: [bold]{target_p.get('name')}[/bold] (模型: {llm_cfg.model})[/green]"
            )
        else:
            available_ids = ", ".join([p.get("id", "") for p in providers])
            console.print(f"[red]未找到供应商 '{sub}'。可用 ID: {available_ids}[/red]")
        return True
