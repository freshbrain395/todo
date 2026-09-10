"""CLI public API and interactive completion compatibility hooks."""

from typing import Any

from prompt_toolkit import PromptSession as _PromptSession
from prompt_toolkit.completion import Completion

from . import app as _app


class SlashCommandCompleter(_app.SlashCommandCompleter):
    """Add interactive completion entries for ``/mode`` arguments."""

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text == "/mode" or text.startswith("/mode "):
            sub = "" if text == "/mode" else text[len("/mode "):].lower()
            options = [
                ("chat", "普通聊天模式"),
                ("agent", "Todo Agent 助理模式"),
                ("json", "严格 JSON 输出模式"),
            ]
            for option, description in options:
                if option.startswith(sub):
                    replacement = f"/mode {option}"
                    yield Completion(
                        replacement,
                        start_position=-len(text),
                        display=f"{option:<8} {description}",
                    )
            return

        yield from super().get_completions(document, complete_event)


class PromptSession(_PromptSession):
    """Enable completion menus to appear automatically while typing."""

    def __init__(self, *args: Any, **kwargs: Any):
        kwargs.setdefault("complete_while_typing", True)
        super().__init__(*args, **kwargs)


# app.main_loop resolves these names from its module globals at runtime, so patching
# them here keeps the existing CLI flow unchanged while enabling automatic /mode
# argument completion.
_app.PromptSession = PromptSession
_app.SlashCommandCompleter = SlashCommandCompleter

run_cli = _app.run_cli
MODE_OPTIONS = _app.MODE_OPTIONS
select_mode_interactive = _app.select_mode_interactive
apply_mode_switch = _app.apply_mode_switch
handle_command = _app.handle_command

__all__ = [
    "run_cli",
    "SlashCommandCompleter",
    "PromptSession",
    "MODE_OPTIONS",
    "select_mode_interactive",
    "apply_mode_switch",
    "handle_command",
]
