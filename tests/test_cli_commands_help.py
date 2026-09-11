"""Unit tests for backend.cli.commands.help module."""

import pytest
from unittest.mock import AsyncMock, patch
from backend.cli.commands.help import (
    show_help,
    show_command_detail,
    handle_help_command,
    COMMAND_DETAILS,
)
from backend.cli.commands.base import console


@pytest.mark.asyncio
async def test_show_help_calls_runner():
    mock_runner = AsyncMock(return_value=("cancel", None))
    await show_help(menu_runner=mock_runner)
    assert mock_runner.called
    kwargs = mock_runner.call_args.kwargs
    assert kwargs.get("title") == "📌 常用 Slash 命令帮助"
    assert len(kwargs.get("items")) > 0


@pytest.mark.asyncio
async def test_handle_help_command_triggers_show_fn():
    mock_show = AsyncMock()
    for trigger in ["/help", "help", "?", "/?"]:
        res = await handle_help_command(trigger, show_fn=mock_show)
        assert res is True
    assert mock_show.call_count == 4


@pytest.mark.asyncio
async def test_handle_help_command_with_detail():
    outputs = []

    def _capture(*args, **kwargs):
        for a in args:
            outputs.append(str(getattr(a, "renderable", a)))

    with patch.object(console, "print", _capture):
        res = await handle_help_command("/help add")
        assert res is True
        assert any("add" in out.lower() for out in outputs)

        outputs.clear()
        res = await handle_help_command("help unknown_cmd")
        assert res is True
        assert any("未找到命令" in out for out in outputs)


@pytest.mark.asyncio
async def test_handle_help_command_ignores_other_inputs():
    res = await handle_help_command("/add buy milk")
    assert res is False
    res = await handle_help_command("hello world")
    assert res is False
