"""Unit tests for BoxedPromptSession component."""

import pytest
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.input import create_pipe_input
from backend.cli.components import BoxedPromptSession, create_boxed_input_session, SlashCommandCompleter


def test_boxed_prompt_session_creates_frame():
    with create_pipe_input() as inp:
        session = BoxedPromptSession(
            title="测试输入框",
            placeholder="请输入...",
            prompt_text="❯ ",
            input=inp,
            output=DummyOutput(),
        )
        assert session.show_frame is True
        assert session.box_title == "测试输入框"
        assert session.box_placeholder == "请输入..."
        
        # 验证 Frame 对象存在
        frame = session.frame
        assert frame is not None
        title_val = frame.title() if callable(frame.title) else frame.title
        assert title_val == "测试输入框"


def test_create_boxed_input_session_factory():
    with create_pipe_input() as inp:
        session = create_boxed_input_session(
            title=lambda: "动态模式",
            completer=SlashCommandCompleter(),
            input=inp,
            output=DummyOutput(),
        )
        assert isinstance(session, BoxedPromptSession)
        frame = session.frame
        assert frame.title() == "动态模式"

