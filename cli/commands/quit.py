"""Quit CLI command: /quit, /exit."""

from typing import Optional
from .base import console


def handle_quit_command(line: str) -> Optional[bool]:
    """Handle /quit and /exit commands. Returns False to exit CLI, or None if not matched."""
    trimmed = line.strip()
    if trimmed in ["/quit", "/exit"]:
        console.print("[dim]再见！感谢使用 Todo Agent。[/dim]")
        return False
    return None
