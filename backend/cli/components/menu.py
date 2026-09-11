"""Bottom-anchored interactive selection menu for the fixed-input CLI shell."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension

from ..layout import get_terminal_height, get_terminal_width, truncate_to_width


def compute_menu_panel_height(
    item_count: int,
    max_visible_items: int = 12,
    terminal_rows: Optional[int] = None,
    reserved_rows: int = 5,
) -> int:
    """
    Adaptive menu panel height.
    reserved_rows: input(1) + toolbar(1) + min log(2) + safety(1)
    Includes title row and optional scroll indicator rows.
    """
    rows = terminal_rows if terminal_rows is not None else get_terminal_height()
    available = max(3, rows - reserved_rows)
    vis = min(max(1, item_count), max_visible_items, max(1, available - 1))
    scroll_extra = 2 if item_count > vis else 0
    # title (+1) + items/indicators
    return min(available, vis + 1 + scroll_extra)


def compute_completion_menu_max_height(terminal_rows: Optional[int] = None) -> int:
    rows = terminal_rows if terminal_rows is not None else get_terminal_height()
    # leave room for log + input + toolbar
    return max(3, min(12, rows - 5))


def render_selection_menu_tokens(
    *,
    title: str,
    items: List[Dict[str, Any]],
    selected_index: int,
    current_id: Optional[str] = None,
    key_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
    render_item_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
    help_hint: str = "↑/↓ 选择 | Enter 确认 | Esc 取消",
    max_visible_items: int = 12,
    terminal_rows: Optional[int] = None,
) -> StyleAndTextTuples:
    """Render borderless indented menu tokens (title row last)."""
    if not items:
        return [("", "")]

    _key = key_fn or (lambda it: str(it.get("id", "")))
    _render = render_item_fn or (lambda it: str(it.get("title") or it.get("name") or it.get("id") or ""))

    term_w = get_terminal_width(fallback=80)
    max_w = max(20, term_w - 2)
    total = len(items)
    selected_index = max(0, min(selected_index, total - 1))

    panel_h = compute_menu_panel_height(total, max_visible_items, terminal_rows)
    body_rows = max(1, panel_h - 1)  # exclude title row

    # Item window fits into body; reserve 2 rows for ▲/▼ when list is truncated
    if total > min(max_visible_items, body_rows):
        item_window = min(max_visible_items, max(1, body_rows - 2))
    else:
        item_window = min(total, max_visible_items, body_rows)

    if total <= item_window:
        start_i = 0
        end_i = total
    else:
        half = item_window // 2
        if selected_index < half:
            start_i = 0
            end_i = item_window
        elif selected_index >= total - (item_window - half):
            start_i = total - item_window
            end_i = total
        else:
            start_i = selected_index - half
            end_i = start_i + item_window

    all_lines: List[Tuple[str, str]] = []

    if start_i > 0:
        all_lines.append(("class:menu-dim", truncate_to_width("    ▲ 更多项目...", max_w)))

    for idx in range(start_i, end_i):
        it = items[idx]
        it_key = str(_key(it)).strip().lower()
        is_cur = bool(current_id and it_key == str(current_id).strip().lower())
        is_sel = idx == selected_index
        pointer = "❯ " if is_sel else "  "
        cur_tag = " [当前]" if is_cur else ""
        raw_line = f"  {pointer}{_render(it)}{cur_tag}"
        style = "class:menu-selected" if is_sel else "class:menu-item"
        all_lines.append((style, truncate_to_width(raw_line, max_w)))

    if end_i < total:
        all_lines.append(("class:menu-dim", truncate_to_width("    ▼ 更多项目...", max_w)))

    all_lines.append(("class:menu-title", truncate_to_width(f"{title} [{help_hint}]", max_w)))

    tokens: StyleAndTextTuples = []
    for i, (style, text) in enumerate(all_lines):
        tokens.append((style, text + ("\n" if i < len(all_lines) - 1 else "")))
    return tokens


class BottomMenuHost:
    """
    In-app bottom menu panel hosted by the fixed-input Application.
    Avoids nested full_screen=False apps that tear the parent UI.
    """

    def __init__(self) -> None:
        self.active: bool = False
        self.title: str = ""
        self.items: List[Dict[str, Any]] = []
        self.selected_index: int = 0
        self.current_id: Optional[str] = None
        self.help_hint: str = ""
        self.max_visible_items: int = 12
        self.extra_bindings: Dict[str, str] = {}
        self._key_fn: Callable[[Dict[str, Any]], str] = lambda it: str(it.get("id", ""))
        self._render_fn: Callable[[Dict[str, Any]], str] = (
            lambda it: str(it.get("title") or it.get("name") or it.get("id") or "")
        )
        self._future: Optional[asyncio.Future] = None
        self._app = None
        self._menu_window: Optional[Window] = None
        self._input_window = None
        self._input_buffer = None
        self._on_invalidate: Optional[Callable[[], None]] = None
        # Ignore confirm keys briefly after open to avoid the same Enter that
        # submitted "/help" also closing the menu immediately.
        self._ignore_confirm_until: float = 0.0

    def bind_app(
        self,
        app,
        menu_window: Window,
        input_window,
        on_invalidate: Callable[[], None],
        input_buffer=None,
    ) -> None:
        self._app = app
        self._menu_window = menu_window
        self._input_window = input_window
        self._on_invalidate = on_invalidate
        self._input_buffer = input_buffer

    def is_active(self) -> bool:
        return self.active

    def preferred_height(self) -> int:
        if not self.active or not self.items:
            return 0
        tokens = self.get_tokens()
        text = "".join(fragment[1] for fragment in tokens)
        if not text:
            return 0
        return text.count("\n") + 1

    def height_dimension(self) -> Dimension:
        """Stable exact height for layout (0 when hidden)."""
        return Dimension.exact(self.preferred_height())

    def get_tokens(self) -> StyleAndTextTuples:
        if not self.active or not self.items:
            return [("", "")]
        return render_selection_menu_tokens(
            title=self.title,
            items=self.items,
            selected_index=self.selected_index,
            current_id=self.current_id,
            key_fn=self._key_fn,
            render_item_fn=self._render_fn,
            help_hint=self.help_hint,
            max_visible_items=self.max_visible_items,
        )

    def _invalidate(self) -> None:
        if self._on_invalidate:
            try:
                self._on_invalidate()
            except Exception:
                pass
        elif self._app is not None:
            try:
                self._app.invalidate()
            except Exception:
                pass

    def _clear_completions(self) -> None:
        buf = self._input_buffer
        if buf is None:
            return
        try:
            buf.complete_state = None
        except Exception:
            pass

    def _focus_menu(self) -> None:
        if self._app is not None and self._menu_window is not None:
            try:
                self._app.layout.focus(self._menu_window)
            except Exception:
                pass

    def _focus_input(self) -> None:
        if self._app is not None and self._input_window is not None:
            try:
                self._app.layout.focus(self._input_window)
            except Exception:
                pass

    def move(self, delta: int) -> None:
        if not self.items:
            return
        self.selected_index = (self.selected_index + delta) % len(self.items)
        self._invalidate()

    def _resolve(self, action: Optional[str], selected: Optional[Dict[str, Any]] = None) -> None:
        if self._future is not None and not self._future.done():
            self._future.set_result((action, selected))

    def _confirm_allowed(self) -> bool:
        return time.monotonic() >= self._ignore_confirm_until

    def confirm(self) -> None:
        if not self._confirm_allowed():
            return
        selected = self.items[self.selected_index] if self.items else None
        self._resolve("confirm", selected)

    def cancel(self) -> None:
        self._resolve("cancel", None)

    def trigger_extra(self, act_name: str) -> None:
        if act_name != "cancel" and not self._confirm_allowed():
            return
        selected = self.items[self.selected_index] if self.items else None
        self._resolve(act_name, selected)

    async def show(
        self,
        *,
        title: str,
        items: List[Dict[str, Any]],
        current_id: Optional[str] = None,
        key_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
        render_item_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
        extra_bindings: Optional[Dict[str, str]] = None,
        help_hint: str = "↑/↓ 选择 | Enter 确认 | Esc 取消",
        max_visible_items: int = 12,
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        if not items:
            return (None, None)

        if self._future is not None and not self._future.done():
            self._future.set_result(("cancel", None))
            # Let the previous show()'s finally settle before reopening.
            await asyncio.sleep(0)

        self.title = title
        self.items = list(items)
        self.current_id = current_id
        self.help_hint = help_hint
        self.max_visible_items = max_visible_items
        self.extra_bindings = dict(extra_bindings or {})
        self._key_fn = key_fn or (lambda it: str(it.get("id", "")))
        self._render_fn = render_item_fn or (
            lambda it: str(it.get("title") or it.get("name") or it.get("id") or "")
        )

        self.selected_index = 0
        if current_id:
            target = str(current_id).strip().lower()
            for idx, it in enumerate(self.items):
                if str(self._key_fn(it)).strip().lower() == target:
                    self.selected_index = idx
                    break

        loop = asyncio.get_running_loop()
        self._future = loop.create_future()

        # 1) Clear slash completions so the bottom float cannot cover this panel.
        self._clear_completions()

        # 2) Expand panel first (height > 0), redraw, THEN focus.
        self.active = True
        # Ignore Enter briefly so the key that submitted the slash command
        # cannot immediately confirm/close this menu.
        self._ignore_confirm_until = time.monotonic() + 0.35
        self._invalidate()
        await asyncio.sleep(0)
        self._invalidate()
        await asyncio.sleep(0)
        self._focus_menu()
        self._invalidate()

        try:
            return await self._future
        finally:
            self.active = False
            self.items = []
            self.extra_bindings = {}
            self._ignore_confirm_until = 0.0
            self._focus_input()
            self._invalidate()
            self._future = None

    def create_window(self) -> Window:
        control = FormattedTextControl(self.get_tokens, focusable=True, show_cursor=False)
        return Window(
            content=control,
            height=self.height_dimension,
            dont_extend_height=True,
        )

    def create_key_bindings(self) -> KeyBindings:
        kb = KeyBindings()
        active = Condition(lambda: self.active)

        @kb.add("up", filter=active)
        def _(event):
            self.move(-1)

        @kb.add("down", filter=active)
        def _(event):
            self.move(1)

        @kb.add("pageup", filter=active)
        def _(event):
            self.move(-max(1, self.preferred_height() - 2))

        @kb.add("pagedown", filter=active)
        def _(event):
            self.move(max(1, self.preferred_height() - 2))

        @kb.add("enter", filter=active)
        def _(event):
            self.confirm()

        @kb.add("escape", filter=active)
        def _(event):
            self.cancel()

        @kb.add("c-c", filter=active)
        def _(event):
            self.cancel()

        @kb.add("q", filter=active)
        @kb.add("Q", filter=active)
        def _(event):
            act = self.extra_bindings.get("q") or self.extra_bindings.get("Q")
            if act:
                self.trigger_extra(act)
            else:
                self.cancel()

        @kb.add("e", filter=active)
        def _(event):
            act = self.extra_bindings.get("e")
            if act:
                self.trigger_extra(act)

        @kb.add("d", filter=active)
        def _(event):
            act = self.extra_bindings.get("d")
            if act:
                self.trigger_extra(act)

        return kb
