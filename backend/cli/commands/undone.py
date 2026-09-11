"""Mark todo as pending command: /undone."""

from backend.repository.db import DbState
from backend.service.todo import TodoService
from .base import console


def handle_undone_command(line: str, db: DbState) -> bool:
    """Handle /undone <id> command."""
    if not (line == "/undone" or line.startswith("/undone ")):
        return False

    parts = line.split(maxsplit=1)
    if len(parts) == 1:
        console.print("[red]错误: 请输入有效的任务 ID，例如: /undone 1[/red]")
        return True

    id_str = parts[1].strip().lstrip("#")
    if id_str.isdigit():
        todo_service = TodoService(db)
        ok = todo_service.update_todo_status(int(id_str), False)
        if ok:
            console.print(f"[green]✓ 任务 #{id_str} 已标记为未完成[/green]")
        else:
            console.print(f"[yellow]未找到任务 #{id_str}[/yellow]")
    else:
        console.print("[red]错误: 请输入有效的任务 ID，例如: /undone 1[/red]")
    return True
