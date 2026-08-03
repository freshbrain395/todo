import pytest
import os
import sqlite3
from db_manager import TodoDatabase


@pytest.fixture
def temp_db(tmp_path):
    db_file = os.path.join(tmp_path, "test_todos.db")
    db = TodoDatabase(db_file, auto_migrate_json=False)
    yield db


def test_add_and_query_todo(temp_db):
    todo_id = temp_db.add_todo(title="测试任务1", priority="high", category="学习")
    assert todo_id > 0

    todos = temp_db.query_sql("SELECT * FROM todos WHERE id = ?", (todo_id,))
    assert len(todos) == 1
    assert todos[0]["title"] == "测试任务1"
    assert todos[0]["priority"] == "high"
    assert todos[0]["category"] == "学习"
    assert todos[0]["completed"] == 0


def test_complete_and_uncomplete_todo(temp_db):
    todo_id = temp_db.add_todo(title="测试完成任务", priority="medium", category="工作")
    
    # 完成任务
    res = temp_db.complete_todo(todo_id)
    assert res is True
    todos = temp_db.query_sql("SELECT completed FROM todos WHERE id = ?", (todo_id,))
    assert todos[0]["completed"] == 1

    # 恢复未完成
    res_un = temp_db.uncomplete_todo(todo_id)
    assert res_un is True
    todos = temp_db.query_sql("SELECT completed FROM todos WHERE id = ?", (todo_id,))
    assert todos[0]["completed"] == 0


def test_update_todo(temp_db):
    todo_id = temp_db.add_todo(title="原始标题", priority="low", category="生活")
    res = temp_db.update_todo(todo_id, title="更新后标题", priority="high")
    assert res is True

    todos = temp_db.query_sql("SELECT title, priority, category FROM todos WHERE id = ?", (todo_id,))
    assert todos[0]["title"] == "更新后标题"
    assert todos[0]["priority"] == "high"
    assert todos[0]["category"] == "生活"


def test_batch_complete_and_clear(temp_db):
    id1 = temp_db.add_todo(title="任务1")
    id2 = temp_db.add_todo(title="任务2")
    id3 = temp_db.add_todo(title="任务3")

    # 批量完成 1 和 2
    affected = temp_db.batch_complete([id1, id2])
    assert affected == 2

    # 清理已完成任务
    cleared = temp_db.clear_completed()
    assert cleared == 2

    remaining = temp_db.query_sql("SELECT id FROM todos")
    assert len(remaining) == 1
    assert remaining[0]["id"] == id3
