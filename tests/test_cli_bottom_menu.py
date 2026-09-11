"""Tests for bottom-anchored CLI selection menu."""

import asyncio
import unittest

from backend.cli.components import (
    BottomMenuHost,
    compute_completion_menu_max_height,
    compute_menu_panel_height,
    render_selection_menu_tokens,
)


class TestMenuSizing(unittest.TestCase):
    def test_panel_height_adapts_to_small_terminal(self):
        h = compute_menu_panel_height(20, max_visible_items=12, terminal_rows=12, reserved_rows=5)
        self.assertLessEqual(h, 7)  # 12 - 5
        self.assertGreaterEqual(h, 3)

    def test_panel_height_caps_by_visible_items(self):
        h = compute_menu_panel_height(3, max_visible_items=12, terminal_rows=40)
        # 3 items + title (+ no scroll extras) => small
        self.assertLessEqual(h, 6)

    def test_completion_max_height_adapts(self):
        h = compute_completion_menu_max_height(terminal_rows=10)
        self.assertGreaterEqual(h, 3)
        self.assertLessEqual(h, 12)


class TestRenderSelectionMenu(unittest.TestCase):
    def test_borderless_indented_and_title_at_bottom(self):
        items = [
            {"id": "opt1", "name": "Option 1"},
            {"id": "opt2", "name": "Option 2"},
        ]
        tokens = render_selection_menu_tokens(
            title="测试菜单",
            items=items,
            selected_index=0,
            current_id="opt1",
            help_hint="↑/↓",
            terminal_rows=40,
        )
        full_text = "".join(t[1] for t in tokens)
        self.assertNotIn("╭", full_text)
        lines = full_text.split("\n")
        self.assertTrue(lines[0].startswith("  ❯ Option 1"))
        self.assertTrue(lines[1].startswith("    Option 2"))
        self.assertTrue(lines[2].startswith("测试菜单"))

    def test_scroll_indicator_when_truncated(self):
        items = [{"id": f"id_{i}", "name": f"Option {i}"} for i in range(15)]
        tokens = render_selection_menu_tokens(
            title="多项菜单",
            items=items,
            selected_index=0,
            current_id="id_0",
            max_visible_items=5,
            terminal_rows=40,
        )
        full_text = "".join(t[1] for t in tokens)
        self.assertIn("    ▼ 更多项目...", full_text)

    def test_narrow_terminal_still_renders(self):
        items = [{"id": f"i{i}", "name": f"Item {i}"} for i in range(10)]
        tokens = render_selection_menu_tokens(
            title="窄屏",
            items=items,
            selected_index=3,
            max_visible_items=12,
            terminal_rows=10,
        )
        full_text = "".join(t[1] for t in tokens)
        self.assertIn("窄屏", full_text)
        self.assertIn("❯", full_text)


class TestBottomMenuHost(unittest.TestCase):
    def test_show_confirm_and_cancel(self):
        host = BottomMenuHost()
        items = [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}]

        async def run_confirm():
            task = asyncio.create_task(
                host.show(title="t", items=items, current_id="a")
            )
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            self.assertTrue(host.is_active())
            self.assertGreater(host.preferred_height(), 0)
            self.assertEqual(host.height_dimension().min, host.preferred_height())
            # Bypass enter-grace window used to absorb the submitting Enter key.
            host._ignore_confirm_until = 0.0
            host.move(1)
            host.confirm()
            return await task

        action, selected = asyncio.run(run_confirm())
        self.assertEqual(action, "confirm")
        self.assertEqual(selected["id"], "b")
        self.assertFalse(host.is_active())
        self.assertEqual(host.preferred_height(), 0)

        async def run_cancel():
            task = asyncio.create_task(host.show(title="t", items=items))
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            host.cancel()
            return await task

        action, selected = asyncio.run(run_cancel())
        self.assertEqual(action, "cancel")
        self.assertIsNone(selected)

    def test_confirm_ignored_during_grace_period(self):
        host = BottomMenuHost()
        items = [{"id": "a", "name": "A"}]

        async def run():
            task = asyncio.create_task(host.show(title="t", items=items))
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            host.confirm()  # should be ignored (grace)
            self.assertTrue(host.is_active())
            self.assertFalse(host._future.done())
            host._ignore_confirm_until = 0.0
            host.cancel()
            return await task

        action, selected = asyncio.run(run())
        self.assertEqual(action, "cancel")
        self.assertIsNone(selected)

    def test_height_dimension_exact_zero_when_hidden(self):
        host = BottomMenuHost()
        dim = host.height_dimension()
        self.assertEqual(dim.min, 0)
        self.assertEqual(dim.max, 0)


if __name__ == "__main__":
    unittest.main()
