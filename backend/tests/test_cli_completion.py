from prompt_toolkit.document import Document

from backend.cli import PromptSession, SlashCommandCompleter


def _completion_texts(text: str):
    document = Document(text=text, cursor_position=len(text))
    return list(SlashCommandCompleter().get_completions(document, None))


def test_mode_completion_is_available_at_command_boundary():
    completions = _completion_texts("/mode")

    assert [item.text for item in completions] == [
        "/mode chat",
        "/mode agent",
        "/mode json",
    ]


def test_mode_completion_filters_partial_argument():
    completions = _completion_texts("/mode a")

    assert [item.text for item in completions] == ["/mode agent"]
    assert completions[0].start_position == -7


def test_prompt_session_enables_completion_while_typing():
    session = PromptSession()

    assert session.complete_while_typing is True


def test_prompt_session_fixes_menu_position_at_left():
    from prompt_toolkit.layout.containers import FloatContainer

    session = PromptSession()

    def find_floats(container):
        if isinstance(container, FloatContainer):
            return container.floats
        for child in getattr(container, "get_children", lambda: [])():
            res = find_floats(child)
            if res:
                return res
        return []

    floats = find_floats(session.layout.container)
    # 验证补全浮动菜单的 xcursor 为 False 且固定在左侧 left=0
    menu_floats = [f for f in floats if f.ycursor]
    assert len(menu_floats) >= 2
    for f in menu_floats:
        assert f.xcursor is False
        assert f.left == 0
