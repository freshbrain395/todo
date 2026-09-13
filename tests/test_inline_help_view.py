from types import SimpleNamespace

from cli.components.input import BoxedInputSession
from cli.components.slash import SlashHelpMenu


def test_help_view_is_rendered_between_input_border_and_status_bar(monkeypatch):
    app = SimpleNamespace(
        db=None,
        llm_cfg=None,
        current_mode={},
        status_bar_state={"items": []},
    )
    session = BoxedInputSession.__new__(BoxedInputSession)
    session.app = app
    session.slash_menu = SimpleNamespace(render_menu_tokens=lambda *args, **kwargs: [])
    session.help_menu = SlashHelpMenu(max_visible=8)
    session.help_menu.open()

    monkeypatch.setattr("cli.components.input.get_terminal_width", lambda _: 80)
    monkeypatch.setattr("cli.components.input.get_border", lambda _: "-" * 78)
    monkeypatch.setattr("cli.components.input.format_status_text", lambda **_: "STATUS")

    tokens = session.get_bottom_toolbar()
    rendered = "".join(text for _, text in tokens)

    assert "📖 可用命令帮助与指南" in rendered
    assert rendered.index("📖 可用命令帮助与指南") < rendered.index("STATUS")


def test_open_help_activates_help_menu_and_closes_slash_menu():
    session = BoxedInputSession.__new__(BoxedInputSession)
    session.help_menu = SlashHelpMenu(max_visible=8)
    session.slash_menu = SimpleNamespace(is_open=True, close=lambda: setattr(session.slash_menu, "is_open", False))

    session.open_help("provider")

    assert session.help_menu.is_active is True
    assert session.help_menu.query == "provider"
    assert session.slash_menu.is_open is False
