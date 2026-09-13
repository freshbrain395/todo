"""CLI slash commands auto-completer component and matching logic."""

from typing import Any, List, Optional, Tuple
from prompt_toolkit import PromptSession as _PromptSession
from prompt_toolkit.completion import Completer, Completion
from ..utils import get_terminal_width, truncate_to_width


def get_current_slash_commands() -> List[Tuple[str, str]]:
    """动态获取当前已注册的所有斜线命令列表"""
    try:
        from .slash import get_registered_commands
        return get_registered_commands()
    except Exception:
        return []


def match_slash_commands(
    text: str,
    commands: Optional[List[Tuple[str, str]]] = None,
) -> List[Tuple[str, str]]:
    """
    统一的斜线命令匹配与过滤逻辑，供 SlashCommandCompleter 与 SlashMenuState 共享。
    匹配规则：
    1. 输入以 '/' 开头且不含空格；
    2. 匹配命令名自身（如 '/help'）；
    3. 匹配注册表中该命令的别名（如 '/cls' -> '/clear'）；
    4. 匹配命令描述中的关键字。
    """
    if not text.startswith("/") or " " in text:
        return []

    available = commands if commands is not None else get_current_slash_commands()
    if not available:
        return []

    query = text.lower().strip()
    if query == "/":
        return available

    q = query.lstrip("/")
    matched: List[Tuple[str, str]] = []
    try:
        from .slash import COMMAND_REGISTRY
    except Exception:
        COMMAND_REGISTRY = {}

    for cmd, desc in available:
        cmd_lower = cmd.lower()
        spec = COMMAND_REGISTRY.get(cmd)
        aliases = [a.lower() for a in getattr(spec, "aliases", [])]
        alias_match = any(q and (q in a.lstrip("/") or a.lstrip("/").startswith(q)) for a in aliases)

        if cmd_lower.startswith(query) or q in desc.lower() or alias_match:
            matched.append((cmd, desc))

    return matched


# 向后兼容常量与别名
SLASH_COMMANDS: List[Tuple[str, str]] = []
PromptSession = _PromptSession


class SlashCommandCompleter(Completer):
    """Slash command auto-completion provider for prompt_toolkit."""

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if not text.startswith("/") or " " in text:
            return

        term_w = get_terminal_width()
        matched = match_slash_commands(text)
        query = text.lower().strip()

        for cmd, desc in matched:
            if term_w < 80:
                max_desc_w = max(10, term_w - 20)
                disp_desc = truncate_to_width(desc, max_desc_w)
                display_text = f"{cmd:<10} {disp_desc}"
            else:
                display_text = f"{cmd:<12} {desc}"

            rep = f"{cmd} " if query != cmd.lower() else cmd
            yield Completion(
                rep,
                start_position=-len(text),
                display=display_text,
            )
