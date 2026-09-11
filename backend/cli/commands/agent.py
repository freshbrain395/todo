"""Switch to agent mode command: /agent."""

from typing import Dict, Any
from .mode import apply_mode_switch


def handle_agent_command(line: str, current_mode: Dict[str, Any]) -> bool:
    """Handle /agent command."""
    trimmed = line.strip()
    if trimmed == "/agent" or trimmed.startswith("/agent "):
        apply_mode_switch("agent", current_mode)
        return True
    return False
