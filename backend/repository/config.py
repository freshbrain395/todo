from typing import Optional
from backend.repository.db import DbState


def get_config(db: DbState, key: str) -> Optional[str]:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_config WHERE key = ?", (key,))
    row = cursor.fetchone()
    if row:
        return str(row["value"])
    return None


def save_config(db: DbState, key: str, value: str) -> None:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO app_config (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
        """,
        (key, value),
    )
    conn.commit()
