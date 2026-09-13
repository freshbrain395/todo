"""Checkbox / Multi-select component for Todo Agent CLI.

Provides an interactive multi-choice selector with visual checkbox indicators ([✔] / [ ]),
keyboard navigation (↑/↓/Space/a/Enter/Esc), and responsive terminal layout.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout

from ..utils import get_terminal_height, get_terminal_width, truncate_to_width
from .style import CLI_STYLE


@dataclass
class CheckboxItem:
    """多选菜单项数据结构"""
    id: str
    label: str
    desc: str = ""
    checked: bool = False
    disabled: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_any(
        cls,
        item: Union[CheckboxItem, Dict[str, Any], Tuple[str, str], str],
        checked: bool = False,
    ) -> CheckboxItem:
        """从各种常见数据类型转换为 CheckboxItem"""
        if isinstance(item, CheckboxItem):
            return item
        if isinstance(item, dict):
            return cls(
                id=str(item.get("id", item.get("name", item.get("value", "")))),
                label=str(item.get("label", item.get("title", item.get("name", item.get("id", ""))))),
                desc=str(item.get("desc", item.get("description", ""))),
                checked=bool(item.get("checked", checked)),
                disabled=bool(item.get("disabled", False)),
                extra=item,
            )
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            return cls(id=str(item[0]), label=str(item[1]), desc=str(item[2]) if len(item) > 2 else "", checked=checked)
        if isinstance(item, (list, tuple)) and len(item) == 1:
            return cls(id=str(item[0]), label=str(item[0]), checked=checked)
        return cls(id=str(item), label=str(item), checked=checked)


class CheckboxMenu:
    """多选组件控制器与状态管理"""

    def __init__(
        self,
        items: List[Union[CheckboxItem, Dict[str, Any], Tuple[str, str], str]],
        *,
        title: str = "请勾选配置项",
        checked_ids: Optional[Union[List[str], Set[str]]] = None,
        max_visible: int = 8,
        help_hint: str = "↑/↓ 移动 | Space 勾选 | a 全选/反选 | Enter 保存 | Esc 取消",
    ):
        init_checked = {str(x).strip().lower() for x in (checked_ids or [])}
        self.items: List[CheckboxItem] = [
            CheckboxItem.from_any(it, checked=(str(it.get("id", "")).strip().lower() in init_checked if isinstance(it, dict) else False))
            for it in items
        ]
        # 如果显式传入了 checked_ids，统一同步勾选状态
        if init_checked:
            for item in self.items:
                if item.id.strip().lower() in init_checked:
                    item.checked = True

        self.title = title
        self.max_visible = max_visible
        self.help_hint = help_hint
        self.selected_index = 0
        self.visible_start = 0
        self._ensure_visible()

    def move(self, delta: int) -> None:
        """移动高亮光标，跳过 disabled 选项"""
        if not self.items:
            return
        total = len(self.items)
        idx = self.selected_index
        for _ in range(total):
            idx = (idx + delta) % total
            if not self.items[idx].disabled:
                self.selected_index = idx
                self._ensure_visible()
                return

    def toggle_current(self) -> None:
        """切换当前项的勾选状态"""
        if 0 <= self.selected_index < len(self.items):
            item = self.items[self.selected_index]
            if not item.disabled:
                item.checked = not item.checked

    def toggle_all(self) -> None:
        """全选或全不选"""
        enabled_items = [it for it in self.items if not it.disabled]
        all_checked = all(it.checked for it in enabled_items)
        for it in enabled_items:
            it.checked = not all_checked

    def _ensure_visible(self) -> None:
        """自适应滚动视口计算"""
        total = len(self.items)
        if total <= self.max_visible:
            self.visible_start = 0
            return
        if self.selected_index < self.visible_start:
            self.visible_start = self.selected_index
        elif self.selected_index >= self.visible_start + self.max_visible:
            self.visible_start = self.selected_index - self.max_visible + 1

    def get_checked_items(self) -> List[CheckboxItem]:
        """获取所有被勾选的项"""
        return [it for it in self.items if it.checked]

    def get_checked_ids(self) -> List[str]:
        """获取所有被勾选的 ID 列表"""
        return [it.id for it in self.items if it.checked]

    def render_tokens(self, width: Optional[int] = None) -> StyleAndTextTuples:
        """渲染多选菜单的 prompt_toolkit 格式化 tokens"""
        term_w = width or get_terminal_width(80)
        max_w = max(24, term_w - 2)
        total = len(self.items)

        tokens: StyleAndTextTuples = []

        # 1. 标题栏
        checked_count = sum(1 for it in self.items if it.checked)
        header = f"■ {self.title} [已选 {checked_count}/{total}]"
        tokens.append(("class:title", f"{truncate_to_width(header, max_w)}\n"))

        if total == 0:
            tokens.append(("class:hint", "  (暂无可选项目)\n"))
            return tokens

        # 2. 上滚动提示
        if self.visible_start > 0:
            tokens.append(("class:scroll-indicator", "  ▲ 更多项目...\n"))

        # 3. 可视选项列表
        end = min(total, self.visible_start + self.max_visible)
        for idx in range(self.visible_start, end):
            item = self.items[idx]
            is_cursor = (idx == self.selected_index)

            pointer = "❯ " if is_cursor else "  "
            box_icon = "[✔] " if item.checked else "[ ] "
            box_style = "class:checkbox-checked" if item.checked else "class:checkbox-unchecked"
            item_style = "class:item-selected" if is_cursor else "class:item"

            tokens.append((item_style, f"  {pointer}"))
            tokens.append((box_style, box_icon))
            tokens.append((item_style, item.label))

            if item.desc:
                used_len = len(pointer) + len(box_icon) + len(item.label) + 4
                avail_desc_len = max(8, max_w - used_len)
                short_desc = truncate_to_width(item.desc, avail_desc_len)
                tokens.append(("class:desc", f" - {short_desc}"))

            tokens.append(("", "\n"))

        # 4. 下滚动提示
        if end < total:
            tokens.append(("class:scroll-indicator", "  ▼ 更多项目...\n"))

        # 5. 底部快捷键提示
        tokens.append(("class:hint", f"  └─ {self.help_hint}\n"))

        return tokens


async def run_checkbox_menu(
    items: List[Union[CheckboxItem, Dict[str, Any], Tuple[str, str], str]],
    *,
    title: str = "请勾选配置项",
    checked_ids: Optional[Union[List[str], Set[str]]] = None,
    max_visible: int = 8,
    help_hint: str = "↑/↓ 移动 | Space 勾选 | a 全选/反选 | Enter 保存 | Esc 取消",
) -> Optional[List[CheckboxItem]]:
    """
    交互式多选组件入口函数：
    运行一个临时的轻量交互应用，展示多选菜单供用户勾选。
    
    返回:
        用户选中的 CheckboxItem 列表；如果用户按 Esc 取消，则返回 None。
    """
    if not items:
        return None

    menu = CheckboxMenu(
        items,
        title=title,
        checked_ids=checked_ids,
        max_visible=max_visible,
        help_hint=help_hint,
    )

    result_holder: List[Optional[List[CheckboxItem]]] = [None]
    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def _(event):
        menu.move(-1)

    @kb.add("down")
    @kb.add("j")
    def _(event):
        menu.move(1)

    @kb.add("space")
    def _(event):
        menu.toggle_current()

    @kb.add("a")
    @kb.add("A")
    def _(event):
        menu.toggle_all()

    @kb.add("enter")
    def _(event):
        result_holder[0] = menu.get_checked_items()
        event.app.exit(result=result_holder[0])

    @kb.add("escape")
    @kb.add("q")
    @kb.add("c-c")
    def _(event):
        result_holder[0] = None
        event.app.exit(result=None)

    def get_tokens():
        return menu.render_tokens()

    layout = Layout(
        HSplit([
            Window(
                content=FormattedTextControl(get_tokens),
                dont_extend_height=True,
            )
        ])
    )

    app: Application[Optional[List[CheckboxItem]]] = Application(
        layout=layout,
        key_bindings=kb,
        style=CLI_STYLE,
        full_screen=False,
    )

    return await app.run_async()
