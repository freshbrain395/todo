"""AI Configuration storage and command delegates."""

import json
from backend.repository.db import DbState
from backend.service.config import ConfigService
from backend.service.ai import LlmConfig


def load_current_llm_config(db: DbState) -> LlmConfig:
    cfg_service = ConfigService(db)
    raw = cfg_service.get_config("llm_config_v2")
    if raw:
        try:
            d = json.loads(raw)
            return LlmConfig(
                provider=d.get("provider", "siliconflow"),
                base_url=d.get("base_url", "https://api.siliconflow.cn/v1"),
                api_key=d.get("api_key", ""),
                model=d.get("model", "deepseek-ai/DeepSeek-V4-Flash"),
                enable_thinking=d.get("enable_thinking", False),
            )
        except Exception:
            pass
    return LlmConfig()


def save_current_llm_config(db: DbState, config: LlmConfig):
    cfg_service = ConfigService(db)
    cfg_service.save_config(
        "llm_config_v2",
        json.dumps(
            {
                "provider": config.provider,
                "base_url": config.base_url,
                "api_key": config.api_key,
                "model": config.model,
                "enable_thinking": config.enable_thinking,
            },
            ensure_ascii=False,
        ),
    )


# Re-export command handlers and interactive pickers for compatibility
from .provider import select_provider_interactive, handle_provider_command
from .model import FALLBACK_MODELS, select_model_interactive, handle_model_command
from .think import select_think_interactive, handle_think_command
from .prompt import select_prompt_interactive, handle_prompt_command
from .skill import select_skill_interactive, handle_skill_command

__all__ = [
    "load_current_llm_config",
    "save_current_llm_config",
    "select_provider_interactive",
    "handle_provider_command",
    "FALLBACK_MODELS",
    "select_model_interactive",
    "handle_model_command",
    "select_think_interactive",
    "handle_think_command",
    "select_prompt_interactive",
    "handle_prompt_command",
    "select_skill_interactive",
    "handle_skill_command",
]
