import sqlite3
import os
import json
import datetime
from typing import List, Dict, Any, Tuple, Optional


class TodoDatabase:
    """SQLite 数据库底层引擎，统一管理 CRUD 操作与数据迁移"""

    def __init__(self, db_path: str = "todos.db", auto_migrate_json: bool = True):
        self.db_path = db_path
        self.init_db(auto_migrate_json=auto_migrate_json)

    def init_db(self, auto_migrate_json: bool = True) -> None:
        """初始化 SQLite 数据库表结构并可选自动迁移已有 json 数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    completed INTEGER DEFAULT 0,
                    priority TEXT DEFAULT 'medium',
                    category TEXT DEFAULT '工作',
                    remind_at TEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

        # 数据迁移逻辑 (todos.json -> todos.db)
        if auto_migrate_json and os.path.exists("todos.json"):
            try:
                with open("todos.json", "r", encoding="utf-8") as f:
                    todos = json.load(f)
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM todos")
                    count = cursor.fetchone()[0]
                    if count == 0 and todos:
                        for t in todos:
                            cursor.execute("""
                                INSERT INTO todos (id, title, completed, priority, category, remind_at)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                t.get("id"),
                                t.get("title"),
                                1 if t.get("completed") else 0,
                                t.get("priority", "medium"),
                                t.get("category", "工作"),
                                t.get("remind_at")
                            ))
                        conn.commit()
            except Exception:
                pass

    def query_sql(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行 SELECT 查询并返回字典列表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def execute_sql(self, sql: str, params: tuple = ()) -> Tuple[int, int]:
        """执行 INSERT/UPDATE/DELETE，返回 (lastrowid, affected_rows)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid, cursor.rowcount

    def add_todo(self, title: str, priority: str = "medium", category: str = "工作", remind_at: Optional[str] = None) -> int:
        """添加待办事项"""
        last_id, _ = self.execute_sql("""
            INSERT INTO todos (title, completed, priority, category, remind_at)
            VALUES (?, 0, ?, ?, ?)
        """, (title, priority, category, remind_at))
        return last_id

    def complete_todo(self, todo_id: int) -> bool:
        """完成待办事项"""
        _, affected = self.execute_sql("UPDATE todos SET completed = 1 WHERE id = ?", (todo_id,))
        return affected > 0

    def uncomplete_todo(self, todo_id: int) -> bool:
        """恢复待办事项为未完成"""
        _, affected = self.execute_sql("UPDATE todos SET completed = 0 WHERE id = ?", (todo_id,))
        return affected > 0

    def delete_todo(self, todo_id: int) -> bool:
        """删除待办事项"""
        _, affected = self.execute_sql("DELETE FROM todos WHERE id = ?", (todo_id,))
        return affected > 0

    def update_todo(self, todo_id: int, title: Optional[str] = None, priority: Optional[str] = None, category: Optional[str] = None, remind_at: Optional[str] = None) -> bool:
        """修改已有待办事项"""
        updates = []
        params = []
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        if remind_at is not None:
            updates.append("remind_at = ?")
            params.append(remind_at)

        if not updates:
            return False

        params.append(todo_id)
        sql = f"UPDATE todos SET {', '.join(updates)} WHERE id = ?"
        _, affected = self.execute_sql(sql, tuple(params))
        return affected > 0

    def batch_complete(self, todo_ids: List[int]) -> int:
        """批量完成待办事项"""
        if not todo_ids:
            return 0
        placeholders = ",".join(["?"] * len(todo_ids))
        _, affected = self.execute_sql(f"UPDATE todos SET completed = 1 WHERE id IN ({placeholders})", tuple(todo_ids))
        return affected

    def clear_completed(self) -> int:
        """清理所有已完成的待办事项"""
        _, affected = self.execute_sql("DELETE FROM todos WHERE completed = 1")
        return affected

    def get_pending_reminders(self) -> List[Dict[str, Any]]:
        """获取所有未完成且带有提醒时间的任务"""
        return self.query_sql("SELECT id, title, remind_at FROM todos WHERE completed = 0 AND remind_at IS NOT NULL")
