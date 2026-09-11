"""Unit tests for CLI fixed-input log buffer and helpers."""

import unittest

from backend.cli.components import CliLogBuffer, LogStream, build_log_fragments


class TestCliLogBuffer(unittest.TestCase):
    def test_append_and_write_splits_lines(self):
        buf = CliLogBuffer(max_lines=100)
        buf.write("hello\nworld")
        self.assertEqual(buf.lines, ["hello"])
        buf.flush()
        self.assertEqual(buf.lines, ["hello", "world"])

    def test_write_crlf_normalized(self):
        buf = CliLogBuffer()
        buf.write("a\r\nb\rc\n")
        self.assertEqual(buf.lines, ["a", "b", "c"])

    def test_max_lines_trims_oldest(self):
        buf = CliLogBuffer(max_lines=100)
        # force a small cap by writing then manually shrinking for assertion clarity
        buf.max_lines = 3
        for i in range(5):
            buf.append_line(f"line-{i}")
        self.assertEqual(buf.lines, ["line-2", "line-3", "line-4"])

    def test_clear_resets_scroll(self):
        buf = CliLogBuffer()
        buf.append_line("one")
        buf.append_line("two")
        buf.scroll_up(1)
        self.assertGreater(buf.scroll_offset, 0)
        buf.clear()
        self.assertEqual(buf.lines, [])
        self.assertEqual(buf.scroll_offset, 0)

    def test_visible_slice_pins_bottom(self):
        buf = CliLogBuffer()
        for i in range(10):
            buf.append_line(str(i))
        visible = buf.visible_slice(3)
        self.assertEqual(visible, ["7", "8", "9"])

    def test_scroll_up_and_down(self):
        buf = CliLogBuffer()
        for i in range(10):
            buf.append_line(str(i))
        buf.scroll_up(2)
        self.assertEqual(buf.visible_slice(3), ["5", "6", "7"])
        buf.scroll_down(2)
        self.assertEqual(buf.visible_slice(3), ["7", "8", "9"])
        buf.scroll_to_bottom()
        self.assertEqual(buf.scroll_offset, 0)

    def test_on_change_callback(self):
        buf = CliLogBuffer()
        calls = []
        buf.set_on_change(lambda: calls.append(1))
        buf.append_line("x")
        self.assertEqual(len(calls), 1)

    def test_log_stream_delegates(self):
        buf = CliLogBuffer()
        stream = LogStream(buf)
        stream.write("hi\n")
        stream.flush()
        self.assertEqual(buf.lines, ["hi"])
        self.assertTrue(stream.writable())
        self.assertTrue(stream.isatty())

    def test_build_log_fragments_empty(self):
        buf = CliLogBuffer()
        frags = build_log_fragments(buf, 5)
        self.assertEqual(frags, [("", "")])

    def test_plain_text_strips_ansi(self):
        buf = CliLogBuffer()
        buf.append_line("\x1b[32mgreen\x1b[0m")
        self.assertIn("green", buf.plain_text())
        self.assertNotIn("\x1b", buf.plain_text())


class TestCreateFixedInputApp(unittest.TestCase):
    def test_app_builds_fullscreen_layout(self):
        from prompt_toolkit.completion import Completer
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.styles import Style

        from backend.cli.components import create_fixed_input_app

        class EmptyCompleter(Completer):
            def get_completions(self, document, complete_event):
                if False:
                    yield None

        async def on_submit(_text: str) -> bool:
            return True

        buf = CliLogBuffer()
        app, host = create_fixed_input_app(
            log_buffer=buf,
            completer=EmptyCompleter(),
            style=Style.from_dict({}),
            toolbar_getter=lambda: [("class:toolbar-gray", " status ")],
            key_bindings=KeyBindings(),
            on_submit=on_submit,
        )
        self.assertTrue(app.full_screen)
        self.assertIsNotNone(app.layout)
        self.assertIsNotNone(host)


if __name__ == "__main__":
    unittest.main()
