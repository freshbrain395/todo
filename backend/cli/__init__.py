"""CLI public API and interactive completion compatibility hooks."""

from .app import (
    run_cli,
    SlashCommandCompleter,
    PromptSession,
    MODE_OPTIONS,
    select_mode_interactive,
    select_model_interactive,
    select_provider_interactive,
    select_think_interactive,
    select_prompt_interactive,
    select_skill_interactive,
    apply_mode_switch,
    handle_command,
    show_help,
)

__all__ = [
    "run_cli",
    "SlashCommandCompleter",
    "PromptSession",
    "MODE_OPTIONS",
    "select_mode_interactive",
    "select_model_interactive",
    "select_provider_interactive",
    "select_think_interactive",
    "select_prompt_interactive",
    "select_skill_interactive",
    "apply_mode_switch",
    "handle_command",
    "show_help",
]
