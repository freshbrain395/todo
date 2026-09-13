"""Model selection command: /model."""

from typing import List, Optional
from prompt_toolkit.formatted_text import HTML
from backend.repository.db import DbState
from backend.service.ai import LlmConfig, fetch_models
from .base import console
from .ai_config import save_current_llm_config

FALLBACK_MODELS = {
    "deepseek": ["deepseek-chat", "deepseek-reasoner"],
    "siliconflow": [
        "deepseek-ai/DeepSeek-V3",
        "deepseek-ai/DeepSeek-R1",
        "Qwen/Qwen2.5-7B-Instruct",
        "Qwen/Qwen2.5-14B-Instruct",
        "Pro/deepseek-ai/DeepSeek-V3",
    ],
    "openai": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "o1-mini"],
    "ollama": ["llama3:latest", "qwen2.5:latest", "deepseek-r1:latest", "mistral:latest"],
}


async def select_model_interactive(
    models: List[str],
    current_model: str,
    menu_runner=None,
) -> Optional[str]:
    """二级菜单：选择 LLM 模型"""
    from ..app import run_interactive_selection_menu
    runner = menu_runner or run_interactive_selection_menu

    if not models:
        return None

    custom_option = "[➕ 输入自定义模型名称...]"
    all_models = list(models)
    if custom_option not in all_models:
        all_models.append(custom_option)

    items = [{"id": m, "name": m} for m in all_models]
    action, selected = await runner(
        title="🧠 选择 LLM 模型",
        items=items,
        current_id=current_model,
        render_item_fn=lambda it: it["name"],
        help_hint="↑/↓ 选择 | Enter 确认 | Esc 取消",
        max_visible_items=12,
    )
    if action == "confirm" and selected:
        return selected["id"]
    return None


async def handle_model_command(
    line: str,
    db: DbState,
    llm_cfg: LlmConfig,
    session=None,
    menu_runner=None,
) -> bool:
    """Handle /model command."""
    trimmed = line.strip()
    if not (trimmed == "/model" or trimmed.startswith("/model ")):
        return False

    parts = trimmed.split(maxsplit=1)
    if len(parts) == 1:
        models: List[str] = []
        try:
            models = await fetch_models(llm_cfg.base_url, llm_cfg.api_key, llm_cfg.provider)
        except Exception:
            pass

        if not models:
            prov_key = (llm_cfg.provider or "").lower()
            models = FALLBACK_MODELS.get(prov_key, ["deepseek-chat", "gpt-4o-mini", "llama3:latest"])

        if llm_cfg.model and llm_cfg.model not in models:
            models.insert(0, llm_cfg.model)

        selected_m = await select_model_interactive(models, llm_cfg.model, menu_runner=menu_runner)
        if selected_m:
            if selected_m == "[➕ 输入自定义模型名称...]":
                if session:
                    custom_name = await session.prompt_async(HTML("<b>输入自定义模型名称: </b>"))
                    if custom_name.strip():
                        llm_cfg.model = custom_name.strip()
                        save_current_llm_config(db, llm_cfg)
                        console.print(f"[green]✓ 已将当前模型切换为: [bold]{llm_cfg.model}[/bold][/green]")
            else:
                llm_cfg.model = selected_m
                save_current_llm_config(db, llm_cfg)
                console.print(f"[green]✓ 已将当前模型切换为: [bold]{selected_m}[/bold][/green]")
        else:
            console.print("[dim]已取消选择模型。[/dim]")
        return True
    else:
        new_model = parts[1].strip()
        llm_cfg.model = new_model
        save_current_llm_config(db, llm_cfg)
        console.print(f"[green]✓ 已将当前模型切换为: [bold]{new_model}[/bold][/green]")
        return True
