import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.repository.db import DbState
from backend.service.todo import TodoService
from backend.service.config import ConfigService
from backend.service.ai import fallback_intent_parse
from backend.api.app import app


@pytest.fixture
def temp_db(tmp_path: Path):
    db_file = tmp_path / "test_todos.db"
    db = DbState(db_file)
    return db


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


def test_todo_filtering(temp_db):
    service = TodoService(temp_db)
    # 准备测试数据
    t1 = service.add_todo("参加周会会议", "high", "工作")
    t2 = service.add_todo("准备周会材料", "medium", "工作")
    t3 = service.add_todo("购买日用品", "low", "生活")

    # 1. 默认查询全部
    all_todos = service.get_todos("all", "")
    assert len(all_todos) == 3

    # 2. 状态过滤: pending (全为未完成)
    pending_todos = service.get_todos("pending", "")
    assert len(pending_todos) == 3

    # 完成 t1
    service.update_todo_status(t1, True)

    # 3. 状态过滤: completed
    completed_todos = service.get_todos("completed", "")
    assert len(completed_todos) == 1
    assert completed_todos[0]["id"] == t1

    # pending 剩 2 个
    pending_todos = service.get_todos("pending", "")
    assert len(pending_todos) == 2

    # 4. 关键词搜索
    search_todos = service.get_todos("all", "周会")
    assert len(search_todos) == 2

    # 5. completed + search 组合过滤
    comb_todos = service.get_todos("completed", "周会")
    assert len(comb_todos) == 1
    assert comb_todos[0]["id"] == t1

    comb_none = service.get_todos("completed", "日用品")
    assert len(comb_none) == 0

    # 6. 无结果查询
    no_res = service.get_todos("all", "不存在的搜索词XYZ")
    assert len(no_res) == 0


@pytest.mark.asyncio
async def test_ai_query_filter(temp_db, monkeypatch):
    import httpx
    from backend.service.ai import parse_intent_and_execute, LlmConfig

    service = TodoService(temp_db)
    t1 = service.add_todo("部门周会", "high", "工作")
    t2 = service.add_todo("项目会议", "medium", "工作")
    t3 = service.add_todo("购买咖啡", "low", "生活")
    service.update_todo_status(t1, True)

    llm_cfg = LlmConfig(provider="openai", base_url="http://test-llm.local", api_key="sk-test")

    # Mock 1: AI 返回 query 动作，指定 completed 和搜索词 会议
    ai_json_1 = {
        "action": "query",
        "data": {
            "filter_type": "completed",
            "search": "会议",
        },
        "raw_response": "为您找到 1 个已完成的会议任务",
    }

    import json

    class MockResponse:
        def __init__(self, json_data):
            self._json = json_data
            self.status_code = 200
            self.is_success = True

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(self._json, ensure_ascii=False),
                        }
                    }
                ]
            }

    async def mock_post(self, url, json_body=None, headers=None, **kwargs):
        return MockResponse(ai_json_1)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    res1 = await parse_intent_and_execute("查看已完成的会议任务", llm_cfg, temp_db)
    assert res1.action == "query"
    assert res1.data["filter_type"] == "completed"
    assert res1.data["search"] == "会议"
    assert res1.message == "为您找到 1 个已完成的会议任务"

    # Mock 2: AI 返回 query 动作但无 raw_response，需自动格式化列表
    ai_json_2 = {
        "action": "query",
        "data": {
            "filter_type": "pending",
            "search": "会议",
        },
        "raw_response": "",
    }

    async def mock_post_2(self, url, json_body=None, headers=None, **kwargs):
        return MockResponse(ai_json_2)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post_2)

    res2 = await parse_intent_and_execute("查一下未完成的会议", llm_cfg, temp_db)
    assert res2.action == "query"
    assert res2.data["filter_type"] == "pending"
    assert res2.data["search"] == "会议"
    assert len(res2.data["todos"]) == 1
    assert res2.data["todos"][0]["id"] == t2
    assert "项目会议" in res2.message

    # Mock 3: AI 返回 query 无匹配结果时的提示
    ai_json_3 = {
        "action": "query",
        "data": {
            "filter_type": "completed",
            "search": "游泳",
        },
        "raw_response": "",
    }

    async def mock_post_3(self, url, json_body=None, headers=None, **kwargs):
        return MockResponse(ai_json_3)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post_3)

    res3 = await parse_intent_and_execute("查一下已完成的游泳任务", llm_cfg, temp_db)
    assert res3.action == "query"
    assert res3.data["todos"] == []
    assert "未找到符合条件的待办任务" in res3.message


@pytest.mark.asyncio
async def test_cli_list_command(temp_db, monkeypatch):
    from backend.cli.app import handle_command, LlmConfig
    service = TodoService(temp_db)
    t1 = service.add_todo("团队周会", "high", "工作")
    t2 = service.add_todo("代码评审", "medium", "工作")
    service.update_todo_status(t1, True)

    llm_cfg = LlmConfig()
    history = []
    mode = {"name": "agent", "display_name": "Agent助理"}

    captured_outputs = []
    from backend.cli import app as cli_app
    monkeypatch.setattr(cli_app.console, "print", lambda *args, **kwargs: captured_outputs.append(str(args[0])))

    # 测试 /list 默认显示全部
    captured_outputs.clear()
    await handle_command("/list", temp_db, llm_cfg, history, mode)
    assert len(captured_outputs) > 0

    # 测试 /list pending
    captured_outputs.clear()
    await handle_command("/list pending", temp_db, llm_cfg, history, mode)
    assert len(captured_outputs) > 0

    # 测试 /list completed
    captured_outputs.clear()
    await handle_command("/list completed", temp_db, llm_cfg, history, mode)
    assert len(captured_outputs) > 0

    # 测试 /list pending 评审
    captured_outputs.clear()
    await handle_command("/list pending 评审", temp_db, llm_cfg, history, mode)
    assert len(captured_outputs) > 0

    # 测试 /list 非法参数
    captured_outputs.clear()
    await handle_command("/list invalid_filter 某关键词", temp_db, llm_cfg, history, mode)
    assert any("非法的过滤类型" in out for out in captured_outputs)

    # 测试 /list 无结果空提示
    captured_outputs.clear()
    await handle_command("/list completed 评审", temp_db, llm_cfg, history, mode)
    assert any("未找到符合条件的待办任务" in out for out in captured_outputs)

