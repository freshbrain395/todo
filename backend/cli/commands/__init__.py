"""CLI Slash commands package. Each command is implemented in its own module."""

from .base import console

# Todo commands
from .list import list_todos, handle_list_command
from .add import handle_add_command
from .done import handle_done_command
from .undone import handle_undone_command
from .delete import handle_delete_command
from .todo import handle_todo_command

# Mode commands
from .mode import (
    MODE_OPTIONS,
    select_mode_interactive,
    apply_mode_switch,
    handle_mode_command,
)
from .chat import handle_chat_command
from .agent import handle_agent_command

# AI Configuration commands
from .ai_config import (
    load_current_llm_config,
    save_current_llm_config,
)
from .provider import select_provider_interactive, handle_provider_command
from .model import FALLBACK_MODELS, select_model_interactive, handle_model_command
from .think import select_think_interactive, handle_think_command
from .prompt import select_prompt_interactive, handle_prompt_command
from .skill import select_skill_interactive, handle_skill_command

# System commands
from .help import show_help, handle_help_command, show_command_detail
from .statusbar import select_status_bar_items_interactive, handle_statusbar_command
from .clear import handle_clear_command
from .cls import handle_cls_command
from .quit import handle_quit_command
from .system import handle_system_command

__all__ = [
    "console",
    # Todo
    "list_todos",
    "handle_list_command",
    "handle_add_command",
    "handle_done_command",
    "handle_undone_command",
    "handle_delete_command",
    "handle_todo_command",
    # Mode
    "MODE_OPTIONS",
    "select_mode_interactive",
    "apply_mode_switch",
    "handle_mode_command",
    "handle_chat_command",
    "handle_agent_command",
    # AI Config
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
    # System
    "show_help",
    "handle_help_command",
    "show_command_detail",
    "select_status_bar_items_interactive",
    "handle_statusbar_command",
    "handle_clear_command",
    "handle_cls_command",
    "handle_quit_command",
    "handle_system_command",
]
