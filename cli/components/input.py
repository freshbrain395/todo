"""Boxed Input Component for Todo Agent CLI.

Encapsulates the terminal boxed input box with adaptive borders, floating slash command
completion menu, dynamic status bar, and real-time renderer position synchronization.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from prompt_toolkit import PromptSession
from prompt_toolkit.application.current import get_app
from prompt_toolkit.filters import Condition, is_done
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import ConditionalContainer, Window
from prompt_toolkit.layout.controls import FormattedTextControl

from ..utils import get_border, get_terminal_height, get_terminal_width
from .slash import SlashHelpMenu, SlashMenuState
from .status_bar import format_status_text
from .style import CLI_STYLE


class _CompactPromptSession(PromptSession):
    """紧凑盒式会话：将底部边框、浮动菜单与状态栏作为输入行紧随挂载窗口，杜绝沉底到终端最底端"""

    def __init__(self, *args, get_compact_bottom: Optional[Callable] = None, **kwargs):
        self.get_compact_bottom = get_compact_bottom
        super().__init__(*args, **kwargs)

    def _create_layout(self):
        layout = super()._create_layout()
        if hasattr(layout, "current_window") and layout.current_window:
            layout.current_window.dont_extend_height = lambda: True

        if self.get_compact_bottom:
            root_hsplit = layout.container
            old_children = list(root_hsplit.children)
            compact_bottom = ConditionalContainer(
                Window(
                    FormattedTextControl(self.get_compact_bottom),
                    dont_extend_height=True,
                ),
                filter=~is_done,
            )
            old_children[-1] = compact_bottom
            root_hsplit.children = old_children
        return layout


class BoxedInputSession:
    """
    自适应边框终端输入框组件会话：
    - 上边框与 ❯ 提示符一体化
    - 智能斜线命令补全菜单浮层与快捷键联动
    - /help 与斜线菜单共用输入框下方交互区域
    - 下边框与自适应状态栏一体化
    - 原生支持清屏与长输出后的光标与边框位置精准复位
    """

    def __init__(
        self,
        app: Any,
        *,
        max_menu_visible: int = 10,
        history: Optional[Any] = None,
    ):
        self.app = app
        self.slash_menu = SlashMenuState(max_visible=max_menu_visible)
        self.help_menu = SlashHelpMenu(max_visible=max_menu_visible)

        @Condition
        def is_help_active() -> bool:
            return self.help_menu.is_active

        self.is_help_active = is_help_active

        @Condition
        def is_slash_menu_active() -> bool:
            if self.help_menu.is_active:
                return False
            try:
                current_app = get_app()
                if current_app and current_app.current_buffer:
                    txt = current_app.current_buffer.text
                    self.slash_menu.update(txt)
                    return bool(self.slash_menu.get_matched(txt))
            except Exception:
                pass
            return False

        self.is_slash_menu_active = is_slash_menu_active
        kb = KeyBindings()

        # /help 视图：与斜线菜单一样使用输入框下方区域，并接管导航键。
        @kb.add("down", filter=is_help_active)
        def _(event):
            self.help_menu.move(1)
            event.app.invalidate()

        @kb.add("up", filter=is_help_active)
        def _(event):
            self.help_menu.move(-1)
            event.app.invalidate()

        @kb.add("tab", filter=is_help_active)
        def _(event):
            self.help_menu.move(1)
            event.app.invalidate()

        @kb.add("s-tab", filter=is_help_active)
        def _(event):
            self.help_menu.move(-1)
            event.app.invalidate()

        @kb.add("escape", filter=is_help_active)
        def _(event):
            self.close_help(event.app)

        @kb.add("enter", filter=is_help_active)
        def _(event):
            b = event.current_buffer
            spec = self.help_menu.get_selected_command()
            if spec is None:
                self.close_help(event.app)
                return

            self.help_menu.close()
            b.text = spec.name
            b.cursor_position = len(b.text)
            try:
                event.app.renderer.erase()
            except Exception:
                pass

            try:
                from ..commands import command_needs_args
                needs_args = command_needs_args(spec.name)
            except Exception:
                needs_args = spec.needs_args

            if needs_args:
                b.text = spec.name + " "
                b.cursor_position = len(b.text)
                event.app.invalidate()
            else:
                b.validate_and_handle()

        # 斜线菜单导航。
        @kb.add("down", filter=is_slash_menu_active)
        def _(event):
            matched = self.slash_menu.get_matched(event.current_buffer.text)
            self.slash_menu.move(1, len(matched))
            event.app.invalidate()

        @kb.add("up", filter=is_slash_menu_active)
        def _(event):
            matched = self.slash_menu.get_matched(event.current_buffer.text)
            self.slash_menu.move(-1, len(matched))
            event.app.invalidate()

        @kb.add("tab", filter=is_slash_menu_active)
        def _(event):
            matched = self.slash_menu.get_matched(event.current_buffer.text)
            self.slash_menu.move(1, len(matched))
            event.app.invalidate()

        @kb.add("s-tab", filter=is_slash_menu_active)
        def _(event):
            matched = self.slash_menu.get_matched(event.current_buffer.text)
            self.slash_menu.move(-1, len(matched))
            event.app.invalidate()

        @kb.add("escape", filter=is_slash_menu_active)
        def _(event):
            event.current_buffer.text = ""
            self.slash_menu.close()
            try:
                event.app.renderer.erase()
            except Exception:
                pass
            event.app.invalidate()

        @kb.add("enter", filter=is_slash_menu_active)
        def _(event):
            b = event.current_buffer
            matched = self.slash_menu.get_matched(b.text)
            if not matched:
                self.slash_menu.close()
                b.validate_and_handle()
                return

            idx = self.slash_menu.selected_index
            if idx >= len(matched):
                idx = 0
            cmd, _ = matched[idx]
            self.slash_menu.close()

            try:
                from ..commands import command_needs_args
                needs_args = command_needs_args(cmd)
            except Exception:
                needs_args = False
            if needs_args:
                b.text = cmd + " "
                b.cursor_position = len(b.text)
                try:
                    event.app.renderer.erase()
                except Exception:
                    pass
                event.app.invalidate()
            else:
                b.text = cmd
                b.cursor_position = len(b.text)
                try:
                    event.app.renderer.erase()
                except Exception:
                    pass
                b.validate_and_handle()

        self.key_bindings = kb

        self.session: PromptSession = _CompactPromptSession(
            history=history or InMemoryHistory(),
            style=CLI_STYLE,
            erase_when_done=True,
            multiline=False,
            wrap_lines=False,
            key_bindings=self.key_bindings,
            get_compact_bottom=self.get_bottom_toolbar,
        )

        def on_buffer_text_changed(buf):
            txt = buf.text
            if self.help_menu.is_active:
                return
            matched = self.slash_menu.get_matched(txt)
            current_lines = (1 + min(len(matched), self.slash_menu.max_visible)) if matched else 0
            active_lines = getattr(self.slash_menu, "active_menu_lines", 0)
            if active_lines > current_lines:
                try:
                    current_app = get_app()
                    if current_app and current_app.renderer:
                        current_app.renderer.erase()
                except Exception:
                    pass
            self.slash_menu.active_menu_lines = current_lines

        self.session.default_buffer.on_text_changed += on_buffer_text_changed
        self._apply_compact_patch()

    def open_help(self, query: str = "") -> None:
        """打开与斜线菜单同位置的 Help 视图。"""
        self.slash_menu.close()
        self.help_menu.open(query=query)
        try:
            current_app = get_app()
            if current_app and current_app.renderer:
                current_app.renderer.erase()
                current_app.invalidate()
        except Exception:
            pass

    def close_help(self, app: Any = None) -> None:
        """关闭 Help 视图并恢复普通输入/斜线菜单。"""
        self.help_menu.close()
        current_app = app
        if current_app is None:
            try:
                current_app = get_app()
            except Exception:
                current_app = None
        try:
            if current_app and current_app.renderer:
                current_app.renderer.erase()
            if current_app:
                current_app.invalidate()
        except Exception:
            pass

    def _apply_compact_patch(self) -> None:
        """彻底解除 prompt_toolkit 与终端物理屏幕底部的绑定"""
        if not hasattr(self.session, "app") or not self.session.app:
            return
        app = self.session.app

        if hasattr(app, "output") and hasattr(app.output, "get_rows_below_cursor_position"):
            app.output.get_rows_below_cursor_position = lambda: 0

        app._request_absolute_cursor_position = lambda: None

        if hasattr(app, "renderer") and app.renderer:
            r = app.renderer
            r.request_absolute_cursor_position = lambda: None
            r.report_absolute_cursor_row = lambda row: None
            r._min_available_height = 0

    def get_prompt_message(self) -> StyleAndTextTuples:
        """生成输入框顶部边框与提示符 ❯"""
        cols = get_terminal_width(80)
        return self.slash_menu.build_prompt_fragments("", cols=cols)

    def get_bottom_toolbar(self) -> StyleAndTextTuples:
        """生成输入框下边框、Help/斜线菜单与底部状态栏"""
        cols = get_terminal_width(80)
        border_line = get_border(cols)

        current_text = ""
        try:
            current_app = get_app()
            if current_app and current_app.current_buffer:
                current_text = current_app.current_buffer.text
        except Exception:
            pass

        tokens: StyleAndTextTuples = [
            ("class:border", border_line + "\n"),
        ]

        # Help 与斜线菜单互斥，共享同一个输入框下方区域。
        if self.help_menu.is_active:
            help_tokens = self.help_menu.render_help_tokens(cols=cols)
            if help_tokens:
                tokens.extend(help_tokens)
        else:
            menu_tokens = self.slash_menu.render_menu_tokens(current_text, cols=cols)
            if menu_tokens:
                tokens.extend(menu_tokens)

        status_text = format_status_text(
            db=self.app.db,
            llm_cfg=self.app.llm_cfg,
            current_mode=self.app.current_mode,
            enabled_items=self.app.status_bar_state.get("items"),
            cols=cols,
        )

        if status_text:
            tokens.append(("class:statusbar", status_text))

        if tokens and tokens[-1][1].endswith("\n"):
            last_style, last_text = tokens[-1]
            tokens[-1] = (last_style, last_text[:-1])

        return tokens

    def reset_renderer(self) -> None:
        """重置渲染器状态，保证新一轮绘制紧随当前终端物理光标行"""
        self.slash_menu.reset()
        if hasattr(self.session, "app") and self.session.app and self.session.app.renderer:
            try:
                r = self.session.app.renderer
                r.reset()
                r._min_available_height = 0
            except Exception:
                pass
        self._apply_compact_patch()

    async def prompt_async(self, rprompt_text: Optional[str] = None) -> str:
        """弹出输入框并等待用户输入。"""
        self.reset_renderer()

        rprompt_tokens = [("class:rprompt", f"[{rprompt_text}]")] if rprompt_text else None

        def pre_run_hook():
            self.reset_renderer()
            self._apply_compact_patch()

        user_input = await self.session.prompt_async(
            self.get_prompt_message,
            rprompt=rprompt_tokens,
            pre_run=pre_run_hook,
        )

        self.slash_menu.reset()
        return user_input.strip()
