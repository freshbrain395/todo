import unittest
from backend.cli.layout import (
    get_terminal_width,
    get_terminal_height,
    display_width,
    truncate_to_width,
    pad_to_width,
    build_box_header,
    build_box_footer,
    is_compact_terminal,
)


class TestCliLayout(unittest.TestCase):
    def test_display_width_ascii(self):
        self.assertEqual(display_width("hello"), 5)
        self.assertEqual(display_width("1234567890"), 10)

    def test_display_width_cjk_and_emoji(self):
        self.assertEqual(display_width("中文"), 4)
        self.assertEqual(display_width("待办事项"), 8)
        self.assertGreaterEqual(display_width("🤖"), 1)

    def test_truncate_to_width(self):
        text = "这是一个很长的待办事项标题测试"
        truncated = truncate_to_width(text, 10, ellipsis="...")
        self.assertLessEqual(display_width(truncated), 10)
        self.assertTrue(truncated.endswith("..."))

        en_text = "SiliconFlow (deepseek-ai/DeepSeek-V4-Flash)"
        tr_en = truncate_to_width(en_text, 20, ellipsis="...")
        self.assertLessEqual(display_width(tr_en), 20)
        self.assertTrue(tr_en.endswith("..."))

    def test_pad_to_width(self):
        text = "待办"
        padded = pad_to_width(text, 10, align="left")
        self.assertEqual(display_width(padded), 10)

        padded_right = pad_to_width(text, 10, align="right")
        self.assertEqual(display_width(padded_right), 10)
        self.assertTrue(padded_right.endswith("待办"))

    def test_box_header_and_footer(self):
        for width in [60, 80, 120, 160]:
            header = build_box_header("🤖 选择 AI 供应商", width)
            footer = build_box_footer(width)
            self.assertIn("🤖", header)
            self.assertTrue(footer.startswith("╰"))
            self.assertTrue(footer.endswith("╯"))
            self.assertEqual(display_width(footer), width)

    def test_responsive_layout_modes(self):
        self.assertTrue(is_compact_terminal(threshold=9999))
        self.assertFalse(is_compact_terminal(threshold=1))

    def test_terminal_height_bounds(self):
        h = get_terminal_height(fallback=24, min_height=8)
        self.assertGreaterEqual(h, 8)


if __name__ == "__main__":
    unittest.main()
