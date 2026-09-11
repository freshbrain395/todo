"""Switch to chat mode command: /chat."""

from typing import Dict, Any
from .mode import apply_mode_switch


def handle_chat_command(line: str, current_mode: Dict[str, Any]) -> bool:
    """Handle /chat command."""
    if line.strip() == "/chat":
        apply_mode_switch("chat", current_mode)
        return True
    return False
