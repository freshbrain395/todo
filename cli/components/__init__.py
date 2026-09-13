"""CLI UI components (completer, style, radio, checkbox, slash_menu, status_bar, input)."""

from .checkbox import (
    CheckboxItem,
    CheckboxMenu,
    run_checkbox_menu,
)
from .completer import (
    SLASH_COMMANDS,
    PromptSession,
    SlashCommandCompleter,
    get_current_slash_commands,
    match_slash_commands,
)
from .input import (
    BoxedInputSession,
)
from .slash import (
    NumberItem,
    NumberMenu,
    RadioItem,
    RadioMenu,
    SlashCommandItem,
    SlashCommandsComponent,
    SlashCommandsContainer,
    SlashMenuState,
    SlashResultContainer,
    get_slash_commands_component,
    get_slash_commands_container,
    render_slash_commands,
    run_number_menu,
    run_radio_menu,
    run_slash_commands_menu,
    show_help_result,
    show_slash_commands,
    show_slash_container,
    show_slash_result,
)
from .status_bar import (
    DEFAULT_STATUS_BAR_ITEMS,
    STATUS_BAR_OPTIONS,
    create_bottom_toolbar_getter,
    create_status_bar_getter,
    format_status_text,
    load_status_bar_items,
    save_status_bar_items,
)
from .style import (
    CHECKBOX_STYLE,
    CLI_STYLE,
    MENU_STYLE,
    RADIO_STYLE,
)
from .welcome import (
    DEFAULT_LOGO,
    DEFAULT_WELCOME_MESSAGE,
    DEFAULT_WELCOME_TEXT,
    WelcomeComponent,
    get_welcome_renderable,
    reset_welcome_state,
    show_welcome,
)

__all__ = [
    # Style
    "CLI_STYLE",
    "RADIO_STYLE",
    "CHECKBOX_STYLE",
    "MENU_STYLE",
    # Number List Single-select
    "NumberItem",
    "NumberMenu",
    "run_number_menu",
    # Radio Single-select (backward-compatible)
    "RadioItem",
    "RadioMenu",
    "run_radio_menu",
    # Checkbox Multi-select
    "CheckboxItem",
    "CheckboxMenu",
    "run_checkbox_menu",
    # Boxed Input Component
    "BoxedInputSession",
    # Slash Commands Component
    "SlashCommandItem",
    "SlashCommandsComponent",
    "get_slash_commands_component",
    "show_slash_commands",
    "render_slash_commands",
    "run_slash_commands_menu",
    # Slash Container Component
    "SlashCommandsContainer",
    "SlashResultContainer",
    "get_slash_commands_container",
    "show_slash_container",
    "show_slash_result",
    "show_help_result",
    # Slash Menu & Completer
    "SlashMenuState",
    "SlashCommandCompleter",
    "SLASH_COMMANDS",
    "PromptSession",
    "get_current_slash_commands",
    "match_slash_commands",
    # Status bar
    "format_status_text",
    "create_status_bar_getter",
    "create_bottom_toolbar_getter",
    "STATUS_BAR_OPTIONS",
    "DEFAULT_STATUS_BAR_ITEMS",
    "load_status_bar_items",
    "save_status_bar_items",
    # Welcome Component
    "DEFAULT_LOGO",
    "DEFAULT_WELCOME_TEXT",
    "DEFAULT_WELCOME_MESSAGE",
    "WelcomeComponent",
    "show_welcome",
    "get_welcome_renderable",
    "reset_welcome_state",
]
