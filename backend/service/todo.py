from typing import List, Optional, Dict, Any
from backend.repository.db import DbState
from backend.repository import todo as todo_repo


class TodoService:
    def __init__(self, db: DbState):
        self.db = db

    def get_todos(
        self,
        filter_type: str = "all",
        search: str = "",
        user_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        return todo_repo.get_todos(self.db, filter_type, search, user_id)

    def add_todo(
        self,
        title: str,
        priority: str = "medium",
        category: str = "工作",
        remind_at: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> int:
        return todo_repo.add_todo(self.db, title, priority, category, remind_at, user_id)

    def update_todo_status(
        self,
        todo_id: int,
        completed: bool,
        user_id: Optional[int] = None,
    ) -> bool:
        return todo_repo.update_todo_status(self.db, todo_id, completed, user_id)

    def update_todo(
        self,
        todo_id: int,
        title: str,
        priority: str,
        category: str,
        remind_at: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> bool:
        return todo_repo.update_todo(self.db, todo_id, title, priority, category, remind_at, user_id)

    def delete_todo(
        self,
        todo_id: int,
        user_id: Optional[int] = None,
    ) -> bool:
        return todo_repo.delete_todo(self.db, todo_id, user_id)
