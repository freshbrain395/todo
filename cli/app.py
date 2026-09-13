"""CLI application entrypoint, interactive menus, layout helpers, and command loop."""

from __future__ import annotations

import asyncio
import os
import re
import shutil
import sys
import unicodedata
from typing import Any, Callable, Dict, List, Optional, Tuple

from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout

# ============================================================================
# 1. 终端布局与字符宽度度量基础工具 (需最先定义以消除循环导入)
# ============================================================================

ANSI_ESCAPE_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from string."""
    if not text:
        return ""
    return ANSI_ESCAPE_RE.sub("", text)


def display_width(text: str) -> int:
    """Compute visual terminal display width for ASCII, CJK and emoji."""
    if not text:
        return 0
    clean = strip_ansi(text)
    w = 0
    for ch in clean:
        cat = unicodedata.category(ch)
        if cat.startswith("M"):
            continue
        ea = unicodedata.east_asian_width(ch)
        if ea in ("F", "W"):
            w += 2
        elif ord(ch) >= 0x1F000:
            w += 2
        else:
            w += 1
    return w


def truncate_to_width(text: str, width: int, ellipsis: str = "...") -> str:
    """Truncate text to fit terminal column width, appending ellipsis if truncated."""
    if display_width(text) <= width:
        return text

    el_w = display_width(ellipsis)
    target = max(0, width - el_w)

    cur_w = 0
    chars: List[str] = []
    for ch in text:
        ch_w = display_width(ch)
        if cur_w + ch_w > target:
            break
        chars.append(ch)
        cur_w += ch_w

    return "".join(chars) + ellipsis


def pad_to_width(text: str, width: int, align: str = "left") -> str:
    """Pad string to exact visual display width."""
    cur_w = display_width(text)
    pad_len = max(0, width - cur_w)
    if align == "right":
        return (" " * pad_len) + text
    elif align == "center":
        left = pad_len // 2
        right = pad_len - left
        return (" " * left) + text + (" " * right)
    return text + (" " * pad_len)


def build_box_header(title: str, width: int) -> str:
    """Construct a box top border with title."""
    prefix = f"╭─ {title} "
    p_w = display_width(prefix)
    suffix = "╮"
    s_w = display_width(suffix)
    rem = max(0, width - p_w - s_w)
    return prefix + ("─" * rem) + suffix


def build_box_footer(width: int) -> str:
    """Construct a box bottom border."""
    prefix = "╰"
    suffix = "╯"
    rem = max(0, width - 2)
    return prefix + ("─" * rem) + suffix


def is_compact_terminal(threshold: int = 80) -> bool:
    """Check if current terminal width is narrower than threshold."""
    return get_terminal_width() < threshold


def get_terminal_width(fallback: int = 80, min_width: int = 20) -> int:
    """Get terminal columns safely."""
    try:
        cols = shutil.get_terminal_size((fallback, 24)).columns
        return max(min_width, cols)
    except Exception:
        return fallback


def get_terminal_height(fallback: int = 24, min_height: int = 8) -> int:
    """Get terminal rows safely."""
    try:
        rows = shutil.get_terminal_size((80, fallback)).lines
        return max(min_height, rows)
    except Exception:
        return fallback


def fit_box_line(text: str, width: int) -> str:
    """Format a line inside a box border (│ content │\n)."""
    inner_w = max(0, width - 4)
    truncated = truncate_to_width(text, inner_w)
    padded = pad_to_width(truncated, inner_w, align="left")
    return f"│ {padded} │\n"


# ============================================================================
# 2. 交互式菜单运行器 (定义在前，避免 commands 模块引用时未就绪)
# ============================================================================

async def run_interactive_selection_menu(
    title: str,
    items: List[Dict[str, Any]],
    current_id: Optional[str] = None,
    key_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
    render_item_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
    help_hint: str = "↑/↓ 选择 | Enter 确认 | Esc 取消",
    max_visible_items: int = 12,
    extra_bindings: Optional[Dict[str, str]] = None,
    terminal_rows: Optional[int] = None,
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Interactive bottom menu using prompt_toolkit Application."""
    from .components.menu import render_selection_menu_tokens

    if not items:
        return ("cancel", None)

    _key = key_fn or (lambda it: str(it.get("id", "")))
    selected_idx = 0
    if current_id:
        for i, it in enumerate(items):
            if str(_key(it)).strip().lower() == str(current_id).strip().lower():
                selected_idx = i
                break

    kb = KeyBindings()
    result: Tuple[str, Optional[Dict[str, Any]]] = ("cancel", None)

    @kb.add("up")
    def _(event):
        nonlocal selected_idx
        selected_idx = (selected_idx - 1) % len(items)

    @kb.add("down")
    def _(event):
        nonlocal selected_idx
        selected_idx = (selected_idx + 1) % len(items)

    @kb.add("enter")
    def _(event):
        nonlocal result
        result = ("confirm", items[selected_idx])
        event.app.exit(result=result)

    @kb.add("escape")
    @kb.add("c-c")
    def _(event):
        nonlocal result
        result = ("cancel", None)
        event.app.exit(result=result)

    if extra_bindings:
        for k, action in extra_bindings.items():
            def _make_handler(act):
                def _handler(event):
                    nonlocal result
                    result = (act, items[selected_idx])
                    event.app.exit(result=result)
                return _handler
            kb.add(k)(_make_handler(action))

    def get_tokens() -> StyleAndTextTuples:
        return render_selection_menu_tokens(
            title=title,
            items=items,
            selected_index=selected_idx,
            current_id=current_id,
            key_fn=key_fn,
            render_item_fn=render_item_fn,
            help_hint=help_hint,
            max_visible_items=max_visible_items,
            terminal_rows=terminal_rows,
        )

    control = FormattedTextControl(get_tokens, focusable=True, show_cursor=False)
    window = Window(content=control, dont_extend_height=True)
    layout = Layout(container=HSplit([window]))

    app = Application(
        layout=layout,
        key_bindings=kb,
        full_screen=False,
        erase_when_done=True,
    )
    res = await app.run_async()
    return res or result


async def run_interactive_checkbox_menu(
    title: str,
    items: List[Dict[str, Any]],
    checked_ids: Optional[List[str]] = None,
    key_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
    render_item_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
    help_hint: str = "↑/↓ 移动 | Space 勾选/反选 | a 全选 | Enter 保存 | Esc 取消",
    max_visible_items: int = 12,
    terminal_rows: Optional[int] = None,
) -> Tuple[str, Optional[List[Dict[str, Any]]]]:
    """Interactive multi-select checkbox menu using prompt_toolkit Application."""
    from .components.menu import render_checkbox_menu_tokens

    if not items:
        return ("cancel", None)

    _key = key_fn or (lambda it: str(it.get("id", "")))
    checked_set = {str(x).strip().lower() for x in (checked_ids or [])}
    selected_idx = 0

    kb = KeyBindings()
    result: Tuple[str, Optional[List[Dict[str, Any]]]] = ("cancel", None)

    @kb.add("up")
    def _(event):
        nonlocal selected_idx
        selected_idx = (selected_idx - 1) % len(items)

    @kb.add("down")
    def _(event):
        nonlocal selected_idx
        selected_idx = (selected_idx + 1) % len(items)

    @kb.add("space")
    def _(event):
        it_key = str(_key(items[selected_idx])).strip().lower()
        if it_key in checked_set:
            checked_set.remove(it_key)
        else:
            checked_set.add(it_key)

    @kb.add("a")
    @kb.add("A")
    def _(event):
        all_keys = {str(_key(it)).strip().lower() for it in items}
        if checked_set >= all_keys:
            checked_set.clear()
        else:
            checked_set.update(all_keys)

    @kb.add("enter")
    def _(event):
        nonlocal result
        selected_items = [it for it in items if str(_key(it)).strip().lower() in checked_set]
        result = ("confirm", selected_items)
        event.app.exit(result=result)

    @kb.add("escape")
    @kb.add("c-c")
    def _(event):
        nonlocal result
        result = ("cancel", None)
        event.app.exit(result=result)

    def get_tokens() -> StyleAndTextTuples:
        return render_checkbox_menu_tokens(
            title=title,
            items=items,
            selected_index=selected_idx,
            checked_ids=checked_set,
            key_fn=key_fn,
            render_item_fn=render_item_fn,
            help_hint=help_hint,
            max_visible_items=max_visible_items,
            terminal_rows=terminal_rows,
        )

    control = FormattedTextControl(get_tokens, focusable=True, show_cursor=False)
    window = Window(content=control, dont_extend_height=True)
    layout = Layout(container=HSplit([window]))

    app = Application(
        layout=layout,
        key_bindings=kb,
        full_screen=False,
        erase_when_done=True,
    )
    res = await app.run_async()
    return res or result


# ============================================================================
# 3. 业务服务、命令与组件导入 (此时基础布局和菜单 runner 已就绪)
# ============================================================================

from backend.repository.db import DbState
from backend.service.ai import (
    DEFAULT_AGENT_PROMPT,
    LlmConfig,
    parse_intent_and_execute,
)
from backend.service.display_config import DisplayConfigService

from .commands.base import console
from .commands.ai_config import load_current_llm_config
from .commands.agent import handle_agent_command
from .commands.chat import handle_chat_command
from .commands.help import handle_help_command, show_command_detail, show_help
from .commands.mode import (
    MODE_OPTIONS,
    apply_mode_switch,
    handle_mode_command,
    select_mode_interactive,
)
from .commands.model import handle_model_command, select_model_interactive
from .commands.prompt import handle_prompt_command, select_prompt_interactive
from .commands.provider import handle_provider_command, select_provider_interactive
from .commands.skill import handle_skill_command, select_skill_interactive
from .commands.statusbar import handle_statusbar_command, select_status_bar_items_interactive
from .commands.system import handle_system_command
from .commands.think import handle_think_command, select_think_interactive
from .commands.todo import handle_todo_command
from .components import (
    CLI_STYLE,
    SlashCommandCompleter,
    create_bottom_toolbar_getter,
    create_boxed_input_session,
    load_status_bar_items,
    print_welcome,
)


# ============================================================================
# 4. 命令统一分发处理器
# ============================================================================

async def handle_command(
    line: str,
    db: Any,
    llm_cfg: Any,
    history: List[Dict[str, str]],
    current_mode: Dict[str, Any],
    session: Any = None,
    menu_runner: Any = None,
    status_bar_state: Optional[Dict[str, Any]] = None,
    log_buffer: Any = None,
    display_cfg: Any = None,
) -> Any:
    """Dispatch and handle slash commands. Returns True/False/tuple."""
    trimmed = line.strip()
    if not trimmed:
        return False

    # 1. 帮助命令 (/help, help, ?, /?)
    if await handle_help_command(trimmed, menu_runner=menu_runner):
        return True

    # 2. 系统级命令 (/quit, /exit, /cls, /clear)
    sys_ret = handle_system_command(
        trimmed,
        history=history,
        log_buffer=log_buffer,
        display_cfg=display_cfg,
        current_mode=current_mode,
        llm_cfg=llm_cfg,
    )
    if sys_ret is not None:
        return sys_ret

    # 3. 模式快捷命令
    if handle_chat_command(trimmed, current_mode):
        return True
    if handle_agent_command(trimmed, current_mode):
        return True
    if await handle_mode_command(trimmed, current_mode, menu_runner=menu_runner):
        return True

    # 4. Todo CRUD 命令
    if handle_todo_command(trimmed, db):
        return True

    # 5. 供应商与模型配置
    if await handle_provider_command(trimmed, db, llm_cfg, session=session, menu_runner=menu_runner):
        return True
    if await handle_model_command(trimmed, db, llm_cfg, session=session, menu_runner=menu_runner):
        return True
    if await handle_think_command(trimmed, db, llm_cfg, session=session, menu_runner=menu_runner):
        return True

    # 6. Prompt 模板与 Skill
    p_handled, p_text = await handle_prompt_command(trimmed, db, menu_runner=menu_runner)
    if p_handled:
        if p_text:
            return ("prompt", p_text)
        return True

    if await handle_skill_command(trimmed, db, current_mode, menu_runner=menu_runner):
        return True

    # 7. 状态栏配置
    if status_bar_state is None:
        status_bar_state = {}
    if await handle_statusbar_command(trimmed, db, llm_cfg, status_bar_state, session=session, menu_runner=menu_runner):
        return True

    # 8. 其他斜线命令提示未识别
    if trimmed.startswith("/"):
        console.print(f"[red]未知命令: {trimmed}[/red] 输入 [green]/help[/green] 查看可用命令。")
        return True

    return False


# ============================================================================
# 5. CLI 主启动函数
# ============================================================================

async def run_cli_async(db_path: Optional[str] = None) -> None:
    """CLI 主交互事件循环"""
    db = DbState.get_instance(db_path) if db_path else DbState.get_instance()
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
    status_bar_state: Dict[str, Any] = {"items": load_status_bar_items(db)}

    # 打印欢迎面板
    print_welcome(display_cfg, current_mode, llm_cfg, console=console)

    # 创建状态栏与输入框 Session
    toolbar_getter = create_bottom_toolbar_getter(
        db=db,
        llm_cfg=llm_cfg,
        current_mode=current_mode,
        status_bar_state=status_bar_state,
    )

    session = create_boxed_input_session(
        title=lambda: f" {current_mode.get('display_name', 'Agent助理')} ",
        completer=SlashCommandCompleter(),
        bottom_toolbar=toolbar_getter,
        style=CLI_STYLE,
    )

    while True:
        try:
            user_input = await session.prompt_async()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]退出 CLI。[/dim]")
            break

        line = user_input.strip()
        if not line:
            continue

        res = await handle_command(
            line=line,
            db=db,
            llm_cfg=llm_cfg,
            history=history,
            current_mode=current_mode,
            session=session,
            status_bar_state=status_bar_state,
            display_cfg=display_cfg,
        )

        if res is False:
            break
        elif res is True:
            continue
        elif isinstance(res, tuple) and res[0] == "prompt":
            ai_input = res[1]
        else:
            ai_input = line

        # 触发 AI 交互
        history.append({"role": "user", "content": ai_input})
        console.print(f"[dim]🤖 {current_mode.get('display_name', 'Agent')} 思考中...[/dim]")
        try:
            action_result = await parse_intent_and_execute(
                user_input=ai_input,
                config=llm_cfg,
                db=db,
                system_prompt=current_mode.get("system_prompt"),
                history=history[:-1],
            )
            reply = action_result.message
            console.print(f"[bold cyan]🤖 {current_mode.get('display_name', 'Agent')}:[/bold cyan] {reply}\n")
            history.append({"role": "assistant", "content": reply})
        except Exception as e:
            console.print(f"[red]请求异常: {e}[/red]\n")


def run_cli(db_path: Optional[str] = None) -> None:
    """CLI 入口点"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        loop.create_task(run_cli_async(db_path))
    else:
        asyncio.run(run_cli_async(db_path))
