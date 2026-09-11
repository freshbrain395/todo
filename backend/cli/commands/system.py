"""System commands aggregator: delegates to quit, cls, clear, help."""

from typing import List, Dict, Any, Optional
from .quit import handle_quit_command
from .cls import handle_cls_command
from .clear import handle_clear_command
from .help import show_help, handle_help_command

__all__ = [
    "handle_quit_command",
    "handle_cls_command",
    "handle_clear_command",
    "show_help",
    "handle_help_command",
    "handle_system_command",
]


def handle_system_command(
    line: str,
    history: List[Dict[str, str]],
    log_buffer: Any = None,
    display_cfg: Any = None,
    current_mode: Optional[Dict[str, Any]] = None,
    llm_cfg: Any = None,
) -> Optional[bool]:
    """处理系统级命令，如果是系统命令则返回布尔值（False表示退出，True表示继续），否则返回None"""
    quit_ret = handle_quit_command(line)
    if quit_ret is not None:
        return quit_ret

    if handle_cls_command(
        line,
        log_buffer=log_buffer,
        display_cfg=display_cfg,
        current_mode=current_mode,
        llm_cfg=llm_cfg,
    ):
        return True

    if handle_clear_command(line, history=history):
        return True

    return None
