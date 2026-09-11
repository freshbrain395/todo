"""Clear screen command: /cls, /clear_screen."""

import os
from typing import Any, Optional, Dict
from ..components import print_welcome, print_banner


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
        print_welcome(display_cfg, current_mode, llm_cfg)
        return True
    return False
