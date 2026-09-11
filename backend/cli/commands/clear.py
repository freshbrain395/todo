"""Clear history command: /clear."""

from typing import List, Dict
from .base import console


def handle_clear_command(line: str, history: List[Dict[str, str]]) -> bool:
    """Handle /clear command."""
    if line.strip() == "/clear":
        history.clear()
        console.print("[green]已清空当前对话历史。[/green]")
        return True
    return False
