"""CLI UI components (menu, fixed input, log buffer, toolbar, completer, banner)."""

from .menu import (
    BottomMenuHost,
    compute_menu_panel_height,
    compute_completion_menu_max_height,
    render_selection_menu_tokens,
)
from .input import (
    CliLogBuffer,
    LogStream,
    build_log_fragments,
    create_fixed_input_app,
    NestedPromptAdapter,
    BoxedPromptSession,
    create_boxed_input_session,
)
from .toolbar import (
    format_status_text,
    create_bottom_toolbar_getter,
)
from .completer import (
    SLASH_COMMANDS,
    SlashCommandCompleter,
    PromptSession,
)
from .banner import (
    print_banner,
)
from .welcome import (
    build_welcome_panel,
    print_welcome,
)
from .help_view import (
    build_help_panel,
    build_command_detail_panel,
    print_help_view,
    COMMAND_DETAILS,
    COMMAND_CATEGORIES,
)
from .style import (
    CLI_STYLE,
)

__all__ = [
    "BottomMenuHost",
    "compute_menu_panel_height",
    "compute_completion_menu_max_height",
    "render_selection_menu_tokens",
    "CliLogBuffer",
    "LogStream",
    "build_log_fragments",
    "create_fixed_input_app",
    "NestedPromptAdapter",
    "BoxedPromptSession",
    "create_boxed_input_session",
    "format_status_text",
    "create_bottom_toolbar_getter",
    "SLASH_COMMANDS",
    "SlashCommandCompleter",
    "PromptSession",
    "print_banner",
    "build_welcome_panel",
    "print_welcome",
    "build_help_panel",
    "build_command_detail_panel",
    "print_help_view",
    "COMMAND_DETAILS",
    "COMMAND_CATEGORIES",
    "CLI_STYLE",
]
