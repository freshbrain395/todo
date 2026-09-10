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
