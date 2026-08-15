import hashlib
from typing import Optional, Dict, Any
from backend.repository.db import DbState


def hash_password(password: str) -> str:
    hasher = hashlib.sha256()
    hasher.update(password.encode("utf-8"))
    hasher.update(b"_todo_agent_salt_2026")
    return hasher.hexdigest()


def register_user(db: DbState, username: str, password: str) -> Dict[str, Any]:
    clean_name = username.strip()
    if not clean_name:
        raise ValueError("用户名不能为空")
    if len(password.strip()) < 3:
        raise ValueError("密码长度不能小于 3 位")

    pwd_hash = hash_password(password)
    conn = db.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (clean_name, pwd_hash),
        )
        conn.commit()
        user_id = cursor.lastrowid

        cursor.execute("SELECT created_at FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        created_at = row["created_at"] if row else ""

        return {
            "id": user_id,
            "username": clean_name,
            "created_at": str(created_at),
        }
    except Exception as e:
        if "UNIQUE" in str(e).upper():
            raise ValueError("该用户名已被注册，请尝试直接登录")
        raise RuntimeError(f"注册失败: {e}")


def login_user(db: DbState, username: str, password: str) -> Dict[str, Any]:
    clean_name = username.strip()
    pwd_hash = hash_password(password)
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
        (clean_name,),
    )
    row = cursor.fetchone()
    if not row:
        raise ValueError("用户不存在，请先注册账号")

    if row["password_hash"] != pwd_hash:
        raise ValueError("密码不正确，请重新输入")

    return {
        "id": row["id"],
        "username": row["username"],
        "created_at": str(row["created_at"]),
    }
