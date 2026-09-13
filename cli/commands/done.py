"""Mark todo as completed command: /done."""

from backend.repository.db import DbState
from backend.service.todo import TodoService
from .base import console


def handle_done_command(line: str, db: DbState) -> bool:
    """Handle /done <id> command."""
    if not (line == "/done" or line.startswith("/done ")):
        return False

    parts = line.split(maxsplit=1)
    if len(parts) == 1:
        console.print("[red]错误: 请输入有效的任务 ID，例如: /done 1[/red]")
        return True

    id_str = parts[1].strip().lstrip("#")
    if id_str.isdigit():
        todo_service = TodoService(db)
        ok = todo_service.update_todo_status(int(id_str), True)
        if ok:
            console.print(f"[green]✓ 任务 #{id_str} 已标记为完成！[/green]")
        else:
            console.print(f"[yellow]未找到任务 #{id_str}[/yellow]")
    else:
        console.print("[red]错误: 请输入有效的任务 ID，例如: /done 1[/red]")
    return True
