import os
import sys
import json
import asyncio
from typing import List, Optional, Dict, Any, Tuple, Callable
from prompt_toolkit import PromptSession as _PromptSession
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from prompt_toolkit.filters import has_completions
from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout.menus import CompletionsMenuControl, _get_menu_item_fragments
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from .layout import (
    get_terminal_width,
    is_compact_terminal,
    display_width,
    truncate_to_width,
    pad_to_width,
)

from .commands.base import console

# Fixed-input shell log buffer (set while run_cli is active)
_log_buffer = None  # type: ignore
_active_app = None  # type: ignore
_menu_host = None  # type: ignore

from backend.repository.db import DbState
from backend.service.todo import TodoService
from backend.service.config import ConfigService
from backend.service.ai_config import AiConfigService
from backend.service.display_config import DisplayConfigService
from backend.service.ai import (
    LlmConfig,
    fetch_models,
    parse_intent_and_execute,
    DEFAULT_AGENT_PROMPT,
    DEFAULT_CHAT_PROMPT,
    DEFAULT_JSON_PROMPT,
)
from .components import (
    SLASH_COMMANDS,
    SlashCommandCompleter,
    PromptSession,
    BoxedPromptSession,
    create_boxed_input_session,
    format_status_text,
    create_bottom_toolbar_getter,
    print_banner,
    print_welcome,
    build_welcome_panel,
    CLI_STYLE,
)
from .commands import (
    list_todos,
    handle_list_command,
    handle_add_command,
    handle_done_command,
    handle_undone_command,
    handle_delete_command,
    handle_todo_command,
    MODE_OPTIONS,
    select_mode_interactive,
    apply_mode_switch,
    handle_mode_command,
    handle_chat_command,
    handle_agent_command,
    FALLBACK_MODELS,
    load_current_llm_config,
    save_current_llm_config,
    select_provider_interactive,
    handle_provider_command,
    select_model_interactive,
    handle_model_command,
    select_think_interactive,
    handle_think_command,
    select_prompt_interactive,
    handle_prompt_command,
    select_skill_interactive,
    handle_skill_command,
    show_help,
    handle_help_command,
    show_command_detail,
    handle_clear_command,
    handle_cls_command,
    handle_quit_command,
    handle_system_command,
)


def create_cli_key_bindings() -> KeyBindings:
    """创建 CLI 专属按键绑定：补全弹出时 ↑/↓ 平滑循环切换，Enter 选中当前/首项并直接执行"""
    kb = KeyBindings()

    @kb.add("down", filter=has_completions)
    def _(event):
        b = event.current_buffer
        if b.complete_state and b.complete_state.completions:
            total = len(b.complete_state.completions)
            cur = 0 if b.complete_state.complete_index is None else b.complete_state.complete_index
            next_idx = (cur + 1) % total
            b.go_to_completion(next_idx)

    @kb.add("up", filter=has_completions)
    def _(event):
        b = event.current_buffer
        if b.complete_state and b.complete_state.completions:
            total = len(b.complete_state.completions)
            cur = 0 if b.complete_state.complete_index is None else b.complete_state.complete_index
            prev_idx = (cur - 1) % total
            b.go_to_completion(prev_idx)

    @kb.add("enter", filter=has_completions)
    def _(event):
        b = event.current_buffer
        if b.complete_state and b.complete_state.completions:
            idx = 0 if b.complete_state.complete_index is None else b.complete_state.complete_index
            exact_match = any(c.lower() == b.text.strip().lower() for c, _ in SLASH_COMMANDS)
            if b.complete_state.complete_index is None and exact_match:
                b.complete_state = None
            else:
                b.apply_completion(b.complete_state.completions[idx])
                b.complete_state = None
        b.validate_and_handle()

    return kb










async def run_interactive_selection_menu(
    title: str,
    items: List[Dict[str, Any]],
    current_id: Optional[str] = None,
    key_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
    render_item_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
    extra_bindings: Optional[Dict[str, str]] = None,
    help_hint: str = "↑/↓ 选择 | Enter 确认 | Esc 取消",
    max_visible_items: int = 12,
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    通用二级交互选择菜单组件：
    - 固定输入模式下：在主界面底部面板展示（可滚动、自适应终端高度）
    - 无宿主时回退：独立 Application（供测试与非全屏场景）
    """
    if not items:
        return (None, None)

    # Prefer in-app bottom panel to avoid nested-app screen tearing
    if _menu_host is not None and _active_app is not None:
        return await _menu_host.show(
            title=title,
            items=items,
            current_id=current_id,
            key_fn=key_fn,
            render_item_fn=render_item_fn,
            extra_bindings=extra_bindings,
            help_hint=help_hint,
            max_visible_items=max_visible_items,
        )

    _key = key_fn or (lambda it: str(it.get("id", "")))
    _render = render_item_fn or (lambda it: str(it.get("title") or it.get("name") or it.get("id") or ""))

    selected_index = [0]
    if current_id:
        target_cur = str(current_id).strip().lower()
        for idx, it in enumerate(items):
            if str(_key(it)).strip().lower() == target_cur:
                selected_index[0] = idx
                break

    action_holder: List[Optional[str]] = [None]
    result_holder: List[Optional[Dict[str, Any]]] = [None]

    kb = KeyBindings()

    @kb.add("up")
    def _(event):
        selected_index[0] = (selected_index[0] - 1) % len(items)
        event.app.invalidate()

    @kb.add("down")
    def _(event):
        selected_index[0] = (selected_index[0] + 1) % len(items)
        event.app.invalidate()

    @kb.add("enter")
    def _(event):
        action_holder[0] = "confirm"
        result_holder[0] = items[selected_index[0]]
        event.app.exit()

    @kb.add("escape")
    @kb.add("c-c")
    def _(event):
        action_holder[0] = "cancel"
        event.app.exit()

    if extra_bindings:
        for key_str, act_name in extra_bindings.items():
            @kb.add(key_str)
            def _(event, act=act_name):
                action_holder[0] = act
                result_holder[0] = items[selected_index[0]]
                event.app.exit()

    from .components import compute_menu_panel_height, render_selection_menu_tokens

    def get_text():
        return render_selection_menu_tokens(
            title=title,
            items=items,
            selected_index=selected_index[0],
            current_id=current_id,
            key_fn=_key,
            render_item_fn=_render,
            help_hint=help_hint,
            max_visible_items=max_visible_items,
        )

    window_h = compute_menu_panel_height(len(items), max_visible_items)
    control = FormattedTextControl(get_text)
    window = Window(content=control, height=window_h)
    try:
        app = Application(
            layout=Layout(HSplit([window])),
            key_bindings=kb,
            style=CLI_STYLE,
            full_screen=False,
            erase_when_done=True,
        )
    except Exception:
        from prompt_toolkit.output import DummyOutput
        app = Application(
            layout=Layout(HSplit([window])),
            key_bindings=kb,
            style=CLI_STYLE,
            full_screen=False,
            erase_when_done=True,
            output=DummyOutput(),
        )

    try:
        await app.run_async()
    except Exception:
        pass
    return (action_holder[0], result_holder[0])





async def handle_command(
    cmd_line: str,
    db: DbState,
    llm_cfg: LlmConfig,
    history: List[Dict[str, str]],
    current_mode: Dict[str, Any],
    session: Optional[PromptSession] = None,
) -> bool:
    """返回 False 表示退出"""
    line = cmd_line.strip()
    if not line:
        return True

    todo_service = TodoService(db)
    ai_cfg_service = AiConfigService(db)
    display_cfg = DisplayConfigService.load()

    sys_ret = handle_system_command(
        line,
        history,
        _log_buffer,
        display_cfg,
        current_mode=current_mode,
        llm_cfg=llm_cfg,
    )
    if sys_ret is not None:
        return sys_ret

    show_fn = getattr(sys.modules.get("backend.cli"), "show_help", getattr(sys.modules.get("backend.cli.app"), "show_help", show_help))
    if await handle_help_command(line, show_fn=show_fn):
        return True

    if handle_todo_command(line, db):
        return True

    select_fn = getattr(sys.modules.get("backend.cli"), "select_mode_interactive", getattr(sys.modules.get("backend.cli.app"), "select_mode_interactive", select_mode_interactive))
    if await handle_mode_command(line, current_mode, select_fn=select_fn):
        return True

    if handle_chat_command(line, current_mode):
        return True

    if handle_agent_command(line, current_mode):
        return True

    if await handle_model_command(line, db, llm_cfg, session=session):
        return True

    if await handle_think_command(line, db, llm_cfg, session=session):
        return True

    if await handle_provider_command(line, db, llm_cfg, session=session):
        return True

    prompt_handled, prompt_text = await handle_prompt_command(line, db)
    if prompt_handled:
        if prompt_text:
            line = prompt_text
        else:
            return True

    if await handle_skill_command(line, db, current_mode):
        return True

    # 其它自然语言或意图指令，调用 AI 执行
    current_mode["status_text"] = "思考中..."
    if _active_app is not None:
        try:
            _active_app.invalidate()
        except Exception:
            pass
    console.print(f"[dim]{display_cfg.ai_name} 正在思考处理中...[/dim]")

    try:
        result = await parse_intent_and_execute(
            user_input=line,
            config=llm_cfg,
            db=db,
            user_id=None,
            system_prompt=current_mode.get("system_prompt"),
            history=history,
        )
        history.append({"role": "user", "content": line})
        history.append({"role": "assistant", "content": result.message})

        if current_mode.get("output_format") == "json":
            out_payload = {
                "action": result.action,
                "data": result.data,
                "raw_response": result.message,
            }
            console.print_json(data=out_payload)
            console.print()
        else:
            console.print(f"[bold green]AI[/bold green] › {result.message}\n")
    except Exception as e:
        console.print(f"[red]执行出错: {e}[/red]")
    finally:
        current_mode["status_text"] = "就绪"
        if _active_app is not None:
            try:
                _active_app.invalidate()
            except Exception:
                pass

    return True


def _attach_console_to_log_buffer(log_buffer) -> None:
    """Redirect module-level Rich console output into the fixed log pane."""
    global console
    from .components import LogStream

    console = Console(
        file=LogStream(log_buffer),
        force_terminal=True,
        legacy_windows=False,
        color_system="truecolor",
        width=get_terminal_width(fallback=80),
        no_color=False,
    )


async def main_loop():
    global _log_buffer, _active_app, _menu_host

    db = DbState.get_instance()
    llm_cfg = load_current_llm_config(db)
    display_cfg = DisplayConfigService.load()

    current_mode: Dict[str, Any] = {
        "name": "agent",
        "role": "agent",
        "display_name": "Agent助理",
        "status_text": "就绪",
        "system_prompt": DEFAULT_AGENT_PROMPT,
        "output_format": "text",
    }
    history: List[Dict[str, str]] = []

    # 1. 启动后正常在终端显示欢迎组件
    print_welcome(display_cfg, current_mode, llm_cfg, console=console)

    toolbar_getter = create_bottom_toolbar_getter(db, llm_cfg, current_mode)

    # 2. 现代带框输入组件 (Boxed Input component)
    box_title = lambda: f" 💬 输入指令或与 AI 对话 [{current_mode.get('display_name', 'Agent助理')}] "
    session = BoxedPromptSession(
        title=box_title,
        placeholder="输入命令 (如 /help, /list) 或直接输入任务与 AI 对话...",
        prompt_text="❯ ",
        completer=SlashCommandCompleter(),
        style=CLI_STYLE,
        key_bindings=create_cli_key_bindings(),
    )

    while True:
        try:
            user_input = await session.prompt_async(
                bottom_toolbar=toolbar_getter,
            )
            line = user_input.strip()
            if not line:
                continue

            should_continue = await handle_command(
                user_input, db, llm_cfg, history, current_mode, session
            )
            if not should_continue:
                break
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]程序已退出。[/dim]")
            break
        except Exception as e:
            console.print(f"[red]执行出错: {e}[/red]")


def run_cli():
    asyncio.run(main_loop())


if __name__ == "__main__":
    run_cli()
