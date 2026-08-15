import json
from typing import Dict, Any
from backend.repository.db import DbState


def get_local_users(db: DbState) -> str:
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, username, password, avatar_color, last_login_time, is_admin FROM local_users"
    )
    user_rows = cursor.fetchall()
    users = [
        {
            "id": r["id"],
            "username": r["username"],
            "password": r["password"],
            "avatarColor": r["avatar_color"] or "#10B981",
            "lastLoginTime": r["last_login_time"],
            "isAdmin": bool(r["is_admin"]),
        }
        for r in user_rows
    ]

    cursor.execute("SELECT user_id, config_json FROM local_user_configs")
    cfg_rows = cursor.fetchall()
    configs: Dict[str, Any] = {}
    for r in cfg_rows:
        uid = r["user_id"]
        cfg_str = r["config_json"]
        try:
            configs[uid] = json.loads(cfg_str)
        except Exception:
            configs[uid] = {}

    result: Dict[str, Any] = {}
    for u in users:
        uid = u["id"]
        result[uid] = {
            "user": u,
            "config": configs.get(uid, {}),
        }

    return json.dumps(result, ensure_ascii=False)


def save_local_users(db: DbState, accounts_json: str) -> None:
    accounts = json.loads(accounts_json) if isinstance(accounts_json, str) else accounts_json
    if not isinstance(accounts, dict):
        accounts = {}

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM local_user_configs")
    cursor.execute("DELETE FROM local_users")

    for uid, data in accounts.items():
        user = data.get("user", {})
        config = data.get("config", {})
        cursor.execute(
            "INSERT INTO local_users (id, username, password, avatar_color, last_login_time, is_admin) VALUES (?, ?, ?, ?, ?, ?)",
            (
                uid,
                user.get("username", ""),
                user.get("password", ""),
                user.get("avatarColor", "#10B981"),
                user.get("lastLoginTime"),
                1 if user.get("isAdmin") else 0,
            ),
        )
        cfg_str = json.dumps(config, ensure_ascii=False)
        cursor.execute(
            "INSERT INTO local_user_configs (user_id, config_json) VALUES (?, ?)",
            (uid, cfg_str),
        )

    conn.commit()
