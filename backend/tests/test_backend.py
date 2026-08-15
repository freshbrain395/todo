import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.repository.db import DbState
from backend.service.user import UserService
from backend.service.todo import TodoService
from backend.service.config import ConfigService
from backend.service.ai import fallback_intent_parse
from backend.api.app import app


@pytest.fixture
def temp_db(tmp_path: Path):
    db_file = tmp_path / "test_todos.db"
    db = DbState(db_file)
    return db


def test_user_service(temp_db):
    service = UserService(temp_db)
    user = service.register("testuser", "password123")
    assert user["username"] == "testuser"
    assert user["id"] > 0

    login_res = service.login("testuser", "password123")
    assert login_res["id"] == user["id"]

    with pytest.raises(ValueError):
        service.login("testuser", "wrongpassword")

    with pytest.raises(ValueError):
        service.register("testuser", "password123")


def test_todo_service(temp_db):
    service = TodoService(temp_db)
    todo_id = service.add_todo("测试任务1", "high", "工作")
    assert todo_id > 0

    todos = service.get_todos()
    assert len(todos) == 1
    assert todos[0]["title"] == "测试任务1"
    assert todos[0]["priority"] == "high"
    assert not todos[0]["completed"]

    service.update_todo_status(todo_id, True)
    todos = service.get_todos()
    assert todos[0]["completed"] is True

    service.update_todo(todo_id, "修改后的标题", "low", "生活")
    todos = service.get_todos()
    assert todos[0]["title"] == "修改后的标题"
    assert todos[0]["priority"] == "low"

    deleted = service.delete_todo(todo_id)
    assert deleted is True
    todos = service.get_todos()
    assert len(todos) == 0


def test_config_service(temp_db):
    service = ConfigService(temp_db)
    service.save_config("theme", "dark")
    val = service.get_config("theme")
    assert val == "dark"


def test_fallback_intent_parse():
    res = fallback_intent_parse("帮我新建一个紧急任务：写年终总结", "test")
    assert res["action"] == "add"
    assert "年终总结" in res["data"]["title"]
    assert res["data"]["priority"] == "high"

    res_done = fallback_intent_parse("完成任务 #12", "test")
    assert res_done["action"] == "complete"
    assert res_done["data"]["id"] == 12


def test_api_client():
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    # 测试 invoke 统一 RPC 端点
    resp_invoke = client.post(
        "/api/invoke",
        json={"cmd": "get_todos", "args": {"filter": "all"}},
    )
    assert resp_invoke.status_code == 200
    assert isinstance(resp_invoke.json(), list)
