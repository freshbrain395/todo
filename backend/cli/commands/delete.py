"""Delete todo command: /delete."""

from backend.repository.db import DbState
from backend.service.todo import TodoService
from .base import console


def handle_delete_command(line: str, db: DbState) -> bool:
    """Handle /delete <id> command."""
    if not (line == "/delete" or line.startswith("/delete ")):
        return False

    parts = line.split(maxsplit=1)
    if len(parts) == 1:
        console.print("[red]错误: 请输入有效的任务 ID，例如: /delete 1[/red]")
        return True

    id_str = parts[1].strip().lstrip("#")
    if id_str.isdigit():
        todo_service = TodoService(db)
        ok = todo_service.delete_todo(int(id_str))
        if ok:
            console.print(f"[green]✓ 任务 #{id_str} 已删除[/green]")
        else:
            console.print(f"[yellow]未找到任务 #{id_str}[/yellow]")
    else:
        console.print("[red]错误: 请输入有效的任务 ID，例如: /delete 1[/red]")
    return True
