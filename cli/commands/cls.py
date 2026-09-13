"""Clear screen command: /cls, /clear_screen."""

import os
from typing import Any, Optional, Dict


def handle_cls_command(
    line: str,
    log_buffer: Any = None,
    display_cfg: Any = None,
    current_mode: Optional[Dict[str, Any]] = None,
    llm_cfg: Any = None,
) -> bool:
    """Handle /cls and /clear_screen commands."""
    trimmed = line.strip()
    if trimmed in ["/cls", "/clear_screen"]:
        if log_buffer is not None:
            log_buffer.clear()
        else:
            os.system("cls" if os.name == "nt" else "clear")
        return True
    return False
