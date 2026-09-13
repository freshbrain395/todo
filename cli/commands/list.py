"""List todos command: /list."""

from rich.table import Table
from ..app import get_terminal_width
from backend.repository.db import DbState
from backend.service.todo import TodoService
from .base import console


def list_todos(db: DbState, filter_type: str = "all", search: str = "") -> None:
    service = TodoService(db)
    todos = service.get_todos(filter_type, search)
    if not todos:
        if filter_type != "all" or search:
            console.print("[yellow]未找到符合条件的待办任务。[/yellow]")
        else:
            console.print("[yellow]当前待办列表为空，使用 /add <标题> 新建一个吧！[/yellow]")
        return

    term_w = get_terminal_width()
    table = Table(title="📋 待办事项列表", title_style="bold blue")

    if term_w < 90:
        table.add_column("ID", style="dim", width=4)
        table.add_column("状态", width=6)
        table.add_column("优先", width=6)
        table.add_column("标题", style="bold")

        for t in todos:
            status = "[green]✓完[/green]" if t["completed"] else "[yellow]○待[/yellow]"
            pri = t["priority"]
            pri_style = (
                "[red]🔴高[/red]"
                if pri == "high"
                else ("[yellow]🟡中[/yellow]" if pri == "medium" else "[green]🟢低[/green]")
            )
            table.add_row(
                str(t["id"]),
                status,
                pri_style,
                t["title"],
            )
    elif term_w < 120:
        table.add_column("ID", style="dim", width=5)
        table.add_column("状态", width=7)
        table.add_column("优先级", width=8)
        table.add_column("分类", width=8)
        table.add_column("标题", style="bold")
        table.add_column("提醒", style="dim", width=12)

        for t in todos:
            status = "[green]✓ 完成[/green]" if t["completed"] else "[yellow]○ 待办[/yellow]"
            pri = t["priority"]
            pri_style = (
                "[red]🔴 高[/red]"
                if pri == "high"
                else ("[yellow]🟡 中[/yellow]" if pri == "medium" else "[green]🟢 低[/green]")
            )
            remind = (t["remind_at"] or "-")
            if len(remind) > 12:
                remind = remind[:10] + ".."
            table.add_row(
                str(t["id"]),
                status,
                pri_style,
                t["category"],
                t["title"],
                remind,
            )
    else:
        table.add_column("ID", style="dim", width=6)
        table.add_column("状态", width=8)
        table.add_column("优先级", width=10)
        table.add_column("分类", width=12)
        table.add_column("标题", style="bold")
        table.add_column("提醒时间", style="dim", width=20)

        for t in todos:
            status = "[green]✓ 完成[/green]" if t["completed"] else "[yellow]○ 待办[/yellow]"
            pri = t["priority"]
            pri_style = (
                "[red]🔴 高[/red]"
                if pri == "high"
                else ("[yellow]🟡 中[/yellow]" if pri == "medium" else "[green]🟢 低[/green]")
            )
            remind = t["remind_at"] or "-"
            table.add_row(
                str(t["id"]),
                status,
                pri_style,
                t["category"],
                t["title"],
                remind,
            )

    console.print(table)


def handle_list_command(line: str, db: DbState) -> bool:
    """Handle /list [all | pending | completed] [search] command."""
    if not (line == "/list" or line.startswith("/list ")):
        return False

    parts = line.split(maxsplit=2)
    filter_type = "all"
    search = ""
    if len(parts) == 2:
        arg = parts[1].strip()
        if arg.lower() in ["all", "pending", "completed"]:
            filter_type = arg.lower()
        else:
            search = arg
    elif len(parts) >= 3:
        first_arg = parts[1].strip().lower()
        if first_arg in ["all", "pending", "completed"]:
            filter_type = first_arg
            search = parts[2].strip()
        else:
            console.print(f"[red]错误: 非法的过滤类型 '{parts[1]}'. 可选类型: all, pending, completed (例如: /list pending 会议)[/red]")
            return True

    list_todos(db, filter_type=filter_type, search=search)
    return True
