"""Tests for CLI status bar component, configuration, and adaptive alignment."""

import unittest
from unittest.mock import MagicMock
from backend.repository.db import DbState
from backend.service.ai import LlmConfig
from backend.cli.app import display_width
from backend.cli.components.status_bar import (
    STATUS_BAR_OPTIONS,
    DEFAULT_STATUS_BAR_ITEMS,
    load_status_bar_items,
    save_status_bar_items,
    format_status_text,
    create_status_bar_getter,
    create_bottom_toolbar_getter,
)
from backend.cli.components.menu import (
    render_checkbox_menu_tokens,
    BottomMenuHost,
)


class TestStatusBarAlignment(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock(spec=DbState)
        self.llm_cfg = LlmConfig(provider="mock", model="mock-model", enable_thinking=False)
        self.current_mode = {"display_name": "测试模式", "status_text": "就绪"}

    def test_zero_items_returns_empty_string(self):
        text = format_status_text(self.db, self.llm_cfg, self.current_mode, enabled_items=[])
        self.assertEqual(text, "")

    def test_single_item_left_aligned(self):
        # 需求：如果显示一个，显示在左侧
        text = format_status_text(self.db, self.llm_cfg, self.current_mode, enabled_items=["status"])
        self.assertTrue(text.startswith(" ["), f"Expected text to start at the left edge, got: {repr(text)}")
        self.assertIn("就绪", text)

    def test_multiple_items_centered_when_fits(self):
        # 需求：如果显示两个或者更多中心对齐
        items = ["status", "mode"]
        text = format_status_text(self.db, self.llm_cfg, self.current_mode, enabled_items=items)
        self.assertIn("就绪", text)
        self.assertIn("测试模式", text)
        self.assertIn(" | ", text)
        # 居中对齐时，前后均会有空格 padding（假设终端宽度 > 文本总宽度）
        stripped = text.strip()
        leading_spaces = len(text) - len(text.lstrip())
        trailing_spaces = len(text) - len(text.rstrip())
        self.assertGreater(leading_spaces, 1)
        self.assertGreater(trailing_spaces, 1)
        # 左右 padding 相差不超过 1
        self.assertLessEqual(abs(leading_spaces - trailing_spaces), 2)

    def test_multiple_items_left_to_right_when_overflow(self):
        # 需求：如果放不下，从左往右显示
        # 模拟超长项目或窄屏（全部开启），且验证截断宽度不超终端
        items = ["status", "mode", "model", "think", "key", "todo", "help"]
        from unittest.mock import patch
        with patch("backend.cli.components.status_bar.get_terminal_width", return_value=30):
            text = format_status_text(self.db, self.llm_cfg, self.current_mode, enabled_items=items)
            # 放不下时应从左往右显示，起始不应有多余居中大留白
            self.assertTrue(text.startswith(" [") or text.startswith("["), f"Expected left-to-right, got: {repr(text)}")
            self.assertLessEqual(display_width(text), 30)

    def test_backward_compatibility_aliases(self):
        self.assertIs(create_bottom_toolbar_getter, create_status_bar_getter)


class TestCheckboxMenuRendering(unittest.TestCase):
    def test_render_checkbox_marks(self):
        items = [
            {"id": "status", "title": "运行状态"},
            {"id": "mode", "title": "工作模式"},
            {"id": "model", "title": "AI模型"},
        ]
        tokens = render_checkbox_menu_tokens(
            title="状态栏配置",
            items=items,
            selected_index=0,
            checked_ids={"status", "model"},
            render_item_fn=lambda it: it["title"],
        )
        full_text = "".join(t[1] for t in tokens)
        lines = full_text.split("\n")
        # index 0: selected pointer and checked
        self.assertIn("❯", lines[0])
        self.assertIn("[x] 运行状态", lines[0])
        # index 1: unselected and unchecked
        self.assertNotIn("❯", lines[1])
        self.assertIn("[ ] 工作模式", lines[1])
        # index 2: unselected and checked
        self.assertIn("[x] AI模型", lines[2])
        # title line
        self.assertIn("状态栏配置", lines[-1])


if __name__ == "__main__":
    unittest.main()
