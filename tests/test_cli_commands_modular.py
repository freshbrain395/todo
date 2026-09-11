"""Tests for each modular CLI command file."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.repository.db import DbState
from backend.service.todo import TodoService
from backend.service.ai import LlmConfig
from backend.cli.commands import (
    handle_list_command,
    handle_add_command,
    handle_done_command,
    handle_undone_command,
    handle_delete_command,
    handle_chat_command,
    handle_agent_command,
    handle_mode_command,
    handle_think_command,
    handle_clear_command,
    handle_cls_command,
    handle_quit_command,
    console,
)


@pytest.fixture
def mock_db(tmp_path):
    import sqlite3
    db_file = str(tmp_path / "test_modular.db")
    state = DbState(db_file)
    with sqlite3.connect(db_file) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                category TEXT DEFAULT '默认',
                completed BOOLEAN DEFAULT 0,
                remind_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
    return state


def test_modular_add_done_undone_delete_list(mock_db):
    # 1. /add
    assert handle_add_command("/add 测试任务", mock_db) is True
    todos = TodoService(mock_db).get_todos()
    assert len(todos) == 1
    t_id = todos[0]["id"]
    assert todos[0]["title"] == "测试任务"
    assert todos[0]["completed"] is False

    # 2. /done
    assert handle_done_command(f"/done {t_id}", mock_db) is True
    todos = TodoService(mock_db).get_todos()
    assert todos[0]["completed"] is True

    # 3. /undone
    assert handle_undone_command(f"/undone {t_id}", mock_db) is True
    todos = TodoService(mock_db).get_todos()
    assert todos[0]["completed"] is False

    # 4. /list
    outputs = []
    with patch.object(console, "print", lambda *args, **kwargs: outputs.append(str(args[0]))):
        assert handle_list_command("/list", mock_db) is True
    assert len(outputs) > 0

    # 5. /delete
    assert handle_delete_command(f"/delete {t_id}", mock_db) is True
    todos = TodoService(mock_db).get_todos()
    assert len(todos) == 0


def test_modular_mode_chat_agent():
    mode = {"name": "chat", "display_name": "聊天模式"}
    # /agent
    assert handle_agent_command("/agent", mode) is True
    assert mode["name"] == "agent"

    # /chat
    assert handle_chat_command("/chat", mode) is True
    assert mode["name"] == "chat"


@pytest.mark.asyncio
async def test_modular_mode_command():
    mode = {"name": "chat", "display_name": "聊天模式"}
    # direct switch
    res = await handle_mode_command("/mode agent", mode)
    assert res is True
    assert mode["name"] == "agent"

    # interactive switch with mock runner
    mock_runner = AsyncMock(return_value=("confirm", {"id": "json"}))
    res = await handle_mode_command("/mode", mode, menu_runner=mock_runner)
    assert res is True
    assert mode["name"] == "json"


@pytest.mark.asyncio
async def test_modular_think_command(mock_db):
    cfg = LlmConfig(enable_thinking=False)
    # direct toggle
    assert await handle_think_command("/think on", mock_db, cfg) is True
    assert cfg.enable_thinking is True

    assert await handle_think_command("/think off", mock_db, cfg) is True
    assert cfg.enable_thinking is False


def test_modular_system_commands():
    # /clear
    history = [{"role": "user", "content": "hello"}]
    assert handle_clear_command("/clear", history) is True
    assert len(history) == 0

    # /cls
    mock_buf = MagicMock()
    assert handle_cls_command("/cls", log_buffer=mock_buf) is True
    assert mock_buf.clear.called

    # /quit
    assert handle_quit_command("/quit") is False
    assert handle_quit_command("/exit") is False
    assert handle_quit_command("/other") is None
