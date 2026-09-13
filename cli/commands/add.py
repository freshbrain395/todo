"""Add todo command: /add, /todo."""

from backend.repository.db import DbState
from backend.service.todo import TodoService
from .base import console


def handle_add_command(line: str, db: DbState) -> bool:
    """Handle /add <title> and /todo <title> commands."""
    if not (line == "/add" or line.startswith("/add ") or line == "/todo" or line.startswith("/todo ")):
        return False

    parts = line.split(maxsplit=1)
    if len(parts) == 1:
        console.print("[red]错误: 任务标题不能为空，例如: /add 写周报[/red]")
        return True

    title = parts[1].strip()
    if not title:
        console.print("[red]错误: 任务标题不能为空，例如: /add 写周报[/red]")
        return True

    todo_service = TodoService(db)
    new_id = todo_service.add_todo(title)
    console.print(f"[green]✓ 已成功添加任务 #{new_id}: {title}[/green]")
    return True
