"""Fixed bottom input shell: scrollable log pane + pinned input + status bar."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, List, Optional, Tuple

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import Completer
from prompt_toolkit.filters import Condition, has_completions
from prompt_toolkit.formatted_text import ANSI, HTML, StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_bindings import merge_key_bindings
from prompt_toolkit.layout.containers import ConditionalContainer, Float, FloatContainer, HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.processors import BeforeInput
from prompt_toolkit.styles import Style

from .menu import BottomMenuHost, compute_completion_menu_max_height
from ..app import strip_ansi


class CliLogBuffer:
    """In-memory line buffer that receives Rich/ANSI stdout and feeds the log pane."""

    def __init__(self, max_lines: int = 5000):
        self.max_lines = max(100, max_lines)
        self.lines: List[str] = []
        self.scroll_offset: int = 0
        self._on_change: Optional[Callable[[], None]] = None
        self._pending: str = ""

    def set_on_change(self, callback: Optional[Callable[[], None]]) -> None:
        self._on_change = callback

    def _notify(self) -> None:
        if self._on_change:
            try:
                self._on_change()
            except Exception:
                pass

    def clear(self) -> None:
        self.lines.clear()
        self._pending = ""
        self.scroll_offset = 0
        self._notify()

    def append_line(self, line: str) -> None:
        self.lines.append(line.rstrip("\r"))
        if len(self.lines) > self.max_lines:
            overflow = len(self.lines) - self.max_lines
            del self.lines[:overflow]
        self._notify()

    def write(self, data: str) -> int:
        """File-like write for Rich Console(file=...)."""
        if not data:
            return 0
        self._pending += data.replace("\r\n", "\n").replace("\r", "\n")
        while "\n" in self._pending:
            line, self._pending = self._pending.split("\n", 1)
            self.append_line(line)
        return len(data)

    def flush(self) -> None:
        if self._pending:
            self.append_line(self._pending)
            self._pending = ""

    def writable(self) -> bool:
        return True

    def isatty(self) -> bool:
        return True

    def scroll_up(self, n: int = 5) -> None:
        max_off = max(0, len(self.lines) - 1)
        self.scroll_offset = min(max_off, self.scroll_offset + max(1, n))
        self._notify()

    def scroll_down(self, n: int = 5) -> None:
        self.scroll_offset = max(0, self.scroll_offset - max(1, n))
        self._notify()

    def scroll_to_bottom(self) -> None:
        self.scroll_offset = 0
        self._notify()

    def visible_slice(self, height: int) -> List[str]:
        """Return lines that should appear in a pane of the given height."""
        if height <= 0:
            return []
        total = len(self.lines)
        if total == 0:
            return []
        end = total - self.scroll_offset
        if end < 1:
            end = 1
            self.scroll_offset = max(0, total - 1)
        start = max(0, end - height)
        return self.lines[start:end]

    def plain_text(self) -> str:
        return "\n".join(strip_ansi(line) for line in self.lines)


class LogStream:
    """Thin file-like wrapper so Rich Console can write into CliLogBuffer."""

    def __init__(self, buffer: CliLogBuffer):
        self.buffer = buffer

    def write(self, data: str) -> int:
        return self.buffer.write(data)

    def flush(self) -> None:
        self.buffer.flush()

    def writable(self) -> bool:
        return True

    def isatty(self) -> bool:
        return True


def build_log_fragments(buffer: CliLogBuffer, height: int) -> StyleAndTextTuples:
    lines = buffer.visible_slice(height)
    if not lines:
        return [("", "")]
    return ANSI("\n".join(lines))


def create_fixed_input_app(
    *,
    log_buffer: CliLogBuffer,
    completer: Completer,
    style: Style,
    toolbar_getter: Callable[[], Any],
    key_bindings: KeyBindings,
    on_submit: Callable[[str], Awaitable[bool]],
    menu_host: Optional[BottomMenuHost] = None,
    input_prefix: str = "<b><ansicyan>You</ansicyan></b> › ",
) -> Tuple[Application, BottomMenuHost]:
    """
    Build a full-screen Application with:
      - scrollable log pane (top)
      - bottom selection / help menu panel (collapsible)
      - fixed single-line input
      - status toolbar (bottom)
      - slash completions floated above the input row
    """
    busy = {"value": False}
    log_height_ref = {"h": 20}
    host = menu_host or BottomMenuHost()
    menu_inactive = Condition(lambda: not host.is_active())

    input_buffer = Buffer(
        completer=completer,
        complete_while_typing=True,
        multiline=False,
        enable_history_search=True,
    )

    def accept_handler(buff: Buffer) -> bool:
        if host.is_active():
            return True
        text = buff.text
        buff.complete_state = None
        buff.reset(append_to_history=bool(text.strip()))

        async def _run() -> None:
            if busy["value"]:
                return
            busy["value"] = True
            try:
                should_continue = await on_submit(text)
                if not should_continue:
                    app.exit()
            finally:
                busy["value"] = False
                try:
                    app.invalidate()
                except Exception:
                    pass

        app.create_background_task(_run())
        return True

    input_buffer.accept_handler = accept_handler

    def get_log_text() -> Any:
        return build_log_fragments(log_buffer, max(1, log_height_ref["h"]))

    class SizedLogWindow(Window):
        def write_to_screen(self, screen, mouse_handlers, write_position, parent_style, erase_bg, z_index):
            try:
                log_height_ref["h"] = max(1, int(write_position.height))
            except Exception:
                pass
            return super().write_to_screen(
                screen, mouse_handlers, write_position, parent_style, erase_bg, z_index
            )

    log_window = SizedLogWindow(
        content=FormattedTextControl(get_log_text, focusable=False),
        wrap_lines=False,
    )

    menu_window = host.create_window()

    input_window = Window(
        BufferControl(
            buffer=input_buffer,
            input_processors=[BeforeInput(HTML(input_prefix))],
            focus_on_click=True,
        ),
        height=1,
        dont_extend_height=True,
    )

    toolbar_window = Window(
        content=FormattedTextControl(toolbar_getter),
        height=1,
        dont_extend_height=True,
        style="class:bottom-toolbar",
    )

    completion_max_h = compute_completion_menu_max_height()
    root = FloatContainer(
        content=HSplit([log_window, input_window, menu_window, toolbar_window]),
        floats=[
            Float(
                xcursor=False,
                ycursor=False,
                left=0,
                bottom=2,
                content=ConditionalContainer(
                    content=CompletionsMenu(max_height=completion_max_h, scroll_offset=1),
                    filter=menu_inactive,
                ),
            ),
        ],
    )

    extra = KeyBindings()

    @extra.add("c-c", filter=menu_inactive)
    def _(event):
        event.app.exit()

    @extra.add("c-d", filter=menu_inactive)
    def _(event):
        event.app.exit()

    @extra.add("pageup", filter=menu_inactive & ~has_completions)
    def _(event):
        log_buffer.scroll_up(8)
        event.app.invalidate()

    @extra.add("pagedown", filter=menu_inactive & ~has_completions)
    def _(event):
        log_buffer.scroll_down(8)
        event.app.invalidate()

    @extra.add("c-home", filter=menu_inactive)
    def _(event):
        log_buffer.scroll_offset = max(0, len(log_buffer.lines) - 1)
        event.app.invalidate()

    @extra.add("c-end", filter=menu_inactive)
    def _(event):
        log_buffer.scroll_to_bottom()
        event.app.invalidate()

    merged = merge_key_bindings([key_bindings, host.create_key_bindings(), extra])

    try:
        app = Application(
            layout=Layout(root, focused_element=input_window),
            key_bindings=merged,
            style=style,
            full_screen=True,
            mouse_support=True,
        )
    except Exception:
        from prompt_toolkit.output import DummyOutput
        app = Application(
            layout=Layout(root, focused_element=input_window),
            key_bindings=merged,
            style=style,
            full_screen=True,
            mouse_support=False,
            output=DummyOutput(),
        )

    def _invalidate() -> None:
        try:
            app.invalidate()
        except Exception:
            pass

    log_buffer.set_on_change(_invalidate)
    host.bind_app(app, menu_window, input_window, _invalidate, input_buffer=input_buffer)
    return app, host


class NestedPromptAdapter:
    """Adapter exposing prompt_async for secondary prompts inside handle_command."""

    def __init__(self):
        from ..app import PromptSession
        self._session = PromptSession()

    async def prompt_async(self, *args, **kwargs):
        return await self._session.prompt_async(*args, **kwargs)


from .completer import PromptSession as _BasePromptSession
from prompt_toolkit.formatted_text import AnyFormattedText, HTML


class BoxedPromptSession(_BasePromptSession):
    """带边框的现代终端输入框组件，只包住主输入区域，不包裹底部工具栏。"""

    def __init__(
        self,
        title: Any = "",
        placeholder: str = "输入命令 (如 /help) 或直接与 AI 对话...",
        placeholder_once: bool = True,
        prompt_text: str = "❯ ",
        *args,
        **kwargs,
    ):
        self.box_title = title
        self.box_placeholder = placeholder
        self.placeholder_once = placeholder_once
        self._placeholder_consumed = False
        self.prompt_text = prompt_text
        self._frame_widget: Optional[Any] = None
        # prompt_toolkit 原生 show_frame 会把 Frame 精确放在 main input
        # 外层，不会把 validation/system/bottom toolbar 一起包进去。
        kwargs["show_frame"] = True
        kwargs.setdefault("multiline", False)
        super().__init__(*args, **kwargs)
        self._fix_menu_floats()

    def _get_default_buffer_control_height(self):
        """当斜线补全菜单不需要显示时，不额外撑开屏幕；仅在有补全项待显示时按需预留高度。"""
        from prompt_toolkit.shortcuts.prompt import CompleteStyle
        from prompt_toolkit.layout.dimension import Dimension

        if (
            self.completer is not None
            and self.complete_style != CompleteStyle.READLINE_LIKE
        ):
            space = self.reserve_space_for_menu
        else:
            space = 0

        if space:
            try:
                from prompt_toolkit.application.current import get_app
                if get_app().is_done:
                    return Dimension()
            except Exception:
                pass

            buff = self.default_buffer
            if buff.complete_state is not None and buff.complete_state.completions:
                needed = min(space, max(1, len(buff.complete_state.completions)))
                return Dimension(min=needed)

        return Dimension()

    def _create_layout(self):
        layout = super()._create_layout()

        # PromptSession 的原生布局已经把 Frame 限定在 main_input_container (children[0])。
        # 这里用自定义 Frame 替换并保存引用，保持只框住主输入区并支持动态标题。
        from prompt_toolkit.widgets import Frame

        try:
            cond_container = layout.container.children[0]
            main_input = getattr(cond_container, "alternative_content", None)
            if main_input is not None:
                def _get_title():
                    if callable(self.box_title):
                        return self.box_title()
                    return self.box_title or ""

                frame = Frame(body=main_input, title=_get_title)
                self._frame_widget = frame
                cond_container.content = frame.container
        except Exception:
            pass

        return layout

    @property
    def frame(self):
        return self._frame_widget

    def _get_styled_placeholder(self) -> Any:
        """为占位符提示应用 class:placeholder 样式（在 CLI_STYLE 中呈现为淡灰色）"""
        if not self.box_placeholder:
            return ""
        if isinstance(self.box_placeholder, str):
            return [("class:placeholder", self.box_placeholder)]
        return self.box_placeholder

    async def prompt_async(self, message=None, **kwargs):
        if message is None:
            message = HTML(f"<b><green>{self.prompt_text}</green></b> ")
        if "placeholder" not in kwargs:
            if self.box_placeholder:
                styled_ph = self._get_styled_placeholder()
                if self.placeholder_once:
                    if not self._placeholder_consumed:
                        kwargs["placeholder"] = styled_ph
                        self._placeholder_consumed = True
                    else:
                        kwargs["placeholder"] = ""
                else:
                    kwargs["placeholder"] = styled_ph
            else:
                kwargs["placeholder"] = ""
        return await super().prompt_async(message=message, **kwargs)


def create_boxed_input_session(
    title: Any = "",
    placeholder: str = "输入命令 (如 /help) 或直接与 AI 对话...",
    placeholder_once: bool = True,
    prompt_text: str = "❯ ",
    **kwargs,
) -> BoxedPromptSession:
    """创建并返回配置完成的终端输入框会话组件"""
    return BoxedPromptSession(
        title=title,
        placeholder=placeholder,
        placeholder_once=placeholder_once,
        prompt_text=prompt_text,
        **kwargs,
    )
