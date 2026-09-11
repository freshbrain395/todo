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


@pytest.mark.asyncio
async def test_menu_space_not_reserved_when_inactive():
    """验证当斜线菜单不需要显示时，不预留空间，不撑开屏幕。"""
    from prompt_toolkit.document import Document

    with create_pipe_input() as inp:
        session = BoxedPromptSession(
            completer=SlashCommandCompleter(),
            input=inp,
            output=DummyOutput(),
        )
        # 初始未输入斜线，补全菜单不显示，不预留高度
        dim_idle = session._get_default_buffer_control_height()
        assert dim_idle.min is None or dim_idle.min == 0

        # 输入普通文本，不属于斜线菜单，不预留高度
        session.default_buffer.document = Document("普通待办任务")
        dim_text = session._get_default_buffer_control_height()
        assert dim_text.min is None or dim_text.min == 0


@pytest.mark.asyncio
async def test_placeholder_only_appears_once():
    """验证 placeholder_once=True 时，提示仅在第一次 prompt_async 时出现，后续调用置空。"""
    from unittest.mock import AsyncMock, patch

    with create_pipe_input() as inp:
        session = BoxedPromptSession(
            placeholder="输入命令 (如 /help) 或直接与 AI 对话...",
            placeholder_once=True,
            input=inp,
            output=DummyOutput(),
        )
        assert session.placeholder_once is True
        assert session._placeholder_consumed is False

        with patch("prompt_toolkit.PromptSession.prompt_async", new_callable=AsyncMock) as mock_super:
            mock_super.return_value = "cmd1"
            await session.prompt_async()
            assert session._placeholder_consumed is True
            assert mock_super.call_args.kwargs.get("placeholder") == [
                ("class:placeholder", "输入命令 (如 /help) 或直接与 AI 对话...")
            ]

            # 第二次调用时，placeholder 不再传递长提示
            mock_super.return_value = "cmd2"
            await session.prompt_async()
            assert mock_super.call_args.kwargs.get("placeholder") == ""


@pytest.mark.asyncio
async def test_placeholder_styled_as_gray_by_default():
    """验证占位符默认应用 class:placeholder 灰色样式且常驻。"""
    from unittest.mock import AsyncMock, patch

    with create_pipe_input() as inp:
        session = BoxedPromptSession(
            placeholder="输入命令 (如 /help) 或直接与 AI 对话...",
            placeholder_once=False,
            input=inp,
            output=DummyOutput(),
        )
        with patch("prompt_toolkit.PromptSession.prompt_async", new_callable=AsyncMock) as mock_super:
            mock_super.return_value = "cmd"
            await session.prompt_async()
            assert mock_super.call_args.kwargs.get("placeholder") == [
                ("class:placeholder", "输入命令 (如 /help) 或直接与 AI 对话...")
            ]


@pytest.mark.asyncio
async def test_placeholder_empty_when_deleted():
    """验证当 placeholder 为空字符串时，不传递提示内容。"""
    from unittest.mock import AsyncMock, patch

    with create_pipe_input() as inp:
        session = BoxedPromptSession(
            placeholder="",
            input=inp,
            output=DummyOutput(),
        )
        with patch("prompt_toolkit.PromptSession.prompt_async", new_callable=AsyncMock) as mock_super:
            mock_super.return_value = "cmd"
            await session.prompt_async()
            assert mock_super.call_args.kwargs.get("placeholder") == ""

