from typing import List, Optional, Dict, Any
from backend.repository.db import DbState


def get_todos(
    db: DbState,
    filter_type: str = "all",
    search: str = "",
    user_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    uid = user_id or 0
    conn = db.get_connection()
    cursor = conn.cursor()

    query = (
        "SELECT id, title, priority, category, completed, remind_at, created_at, updated_at, user_id "
        "FROM todos WHERE 1=1"
    )
    params = []

    if uid > 0:
        query += " AND user_id = ?"
        params.append(uid)
    else:
        query += " AND (user_id IS NULL OR user_id = 0)"

    if filter_type == "pending":
        query += " AND completed = 0"
    elif filter_type == "completed":
        query += " AND completed = 1"

    if search and search.strip():
        query += " AND title LIKE ?"
        params.append(f"%{search.strip()}%")

    query += (
        " ORDER BY completed ASC, "
        "CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 ELSE 4 END, "
        "id DESC"
    )

    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = []
    for r in rows:
        results.append(
            {
                "id": r["id"],
                "title": r["title"],
                "priority": r["priority"] or "medium",
                "category": r["category"] or "工作",
                "completed": bool(r["completed"]),
                "remind_at": r["remind_at"],
                "created_at": str(r["created_at"] or ""),
                "updated_at": str(r["updated_at"] or ""),
                "user_id": r["user_id"] or 0,
            }
        )
    return results


def add_todo(
    db: DbState,
    title: str,
    priority: str = "medium",
    category: str = "工作",
    remind_at: Optional[str] = None,
    user_id: Optional[int] = None,
) -> int:
    uid = user_id or 0
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO todos (title, priority, category, remind_at, user_id) VALUES (?, ?, ?, ?, ?)",
        (title, priority, category, remind_at, uid),
    )
    conn.commit()
    return cursor.lastrowid or 0


def update_todo_status(
    db: DbState,
    todo_id: int,
    completed: bool,
    user_id: Optional[int] = None,
) -> bool:
    uid = user_id or 0
    conn = db.get_connection()
    cursor = conn.cursor()
    completed_int = 1 if completed else 0

    if uid > 0:
        cursor.execute(
            "UPDATE todos SET completed = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (completed_int, todo_id, uid),
        )
    else:
        cursor.execute(
            "UPDATE todos SET completed = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND (user_id IS NULL OR user_id = 0)",
            (completed_int, todo_id),
        )
    conn.commit()
    return cursor.rowcount > 0


def update_todo(
    db: DbState,
    todo_id: int,
    title: str,
    priority: str,
    category: str,
    remind_at: Optional[str] = None,
    user_id: Optional[int] = None,
) -> bool:
    uid = user_id or 0
    conn = db.get_connection()
    cursor = conn.cursor()

    if uid > 0:
        cursor.execute(
            "UPDATE todos SET title = ?, priority = ?, category = ?, remind_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (title, priority, category, remind_at, todo_id, uid),
        )
    else:
        cursor.execute(
            "UPDATE todos SET title = ?, priority = ?, category = ?, remind_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND (user_id IS NULL OR user_id = 0)",
            (title, priority, category, remind_at, todo_id),
        )
    conn.commit()
    return cursor.rowcount > 0


def delete_todo(
    db: DbState,
    todo_id: int,
    user_id: Optional[int] = None,
) -> bool:
    uid = user_id or 0
    conn = db.get_connection()
    cursor = conn.cursor()

    if uid > 0:
        cursor.execute(
            "DELETE FROM todos WHERE id = ? AND user_id = ?",
            (todo_id, uid),
        )
    else:
        cursor.execute(
            "DELETE FROM todos WHERE id = ? AND (user_id IS NULL OR user_id = 0)",
            (todo_id,),
        )
    conn.commit()
    return cursor.rowcount > 0
