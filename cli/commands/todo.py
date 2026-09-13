"""Todo CRUD commands aggregator: delegates to list, add, done, undone, delete."""

from backend.repository.db import DbState
from .list import list_todos, handle_list_command
from .add import handle_add_command
from .done import handle_done_command
from .undone import handle_undone_command
from .delete import handle_delete_command

__all__ = [
    "list_todos",
    "handle_list_command",
    "handle_add_command",
    "handle_done_command",
    "handle_undone_command",
    "handle_delete_command",
    "handle_todo_command",
]


def handle_todo_command(line: str, db: DbState) -> bool:
    """Handle /list, /add, /todo, /done, /undone, /delete commands. Returns True if handled."""
    if handle_list_command(line, db):
        return True
    if handle_add_command(line, db):
        return True
    if handle_done_command(line, db):
        return True
    if handle_undone_command(line, db):
        return True
    if handle_delete_command(line, db):
        return True
    return False
