import json
from typing import List, Dict, Any
from backend.repository.db import DbState


# ============ AI Providers ============

def load_providers(db: DbState) -> List[Dict[str, Any]]:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, base_url, api_key, model, is_custom FROM ai_providers ORDER BY rowid"
    )
    rows = cursor.fetchall()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "base_url": r["base_url"] or "",
            "api_key": r["api_key"] or "",
            "model": r["model"] or "",
            "is_custom": bool(r["is_custom"]),
        }
        for r in rows
    ]


def save_providers(db: DbState, providers_json: str) -> None:
    providers = json.loads(providers_json) if isinstance(providers_json, str) else providers_json
    if not isinstance(providers, list):
        providers = []

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ai_providers")
    for p in providers:
        cursor.execute(
            "INSERT INTO ai_providers (id, name, base_url, api_key, model, is_custom) VALUES (?, ?, ?, ?, ?, ?)",
            (
                p.get("id", ""),
                p.get("name", ""),
                p.get("base_url", ""),
                p.get("api_key", ""),
                p.get("model", ""),
                1 if p.get("is_custom") else 0,
            ),
        )
    conn.commit()


# ============ AI Prompts ============

def load_prompts(db: DbState) -> List[Dict[str, Any]]:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, category, title, text, json_format, enabled, is_active FROM ai_prompts ORDER BY rowid"
    )
    rows = cursor.fetchall()
    return [
        {
            "id": r["id"],
            "category": r["category"] or "自定义",
            "title": r["title"] or "未命名提示词",
            "text": r["text"] or "",
            "jsonFormat": r["json_format"] or "",
            "enabled": bool(r["enabled"]),
            "isActive": bool(r["is_active"]),
        }
        for r in rows
    ]


def save_prompts(db: DbState, prompts_json: str) -> None:
    prompts = json.loads(prompts_json) if isinstance(prompts_json, str) else prompts_json
    if not isinstance(prompts, list):
        prompts = []

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ai_prompts")
    for p in prompts:
        cursor.execute(
            "INSERT INTO ai_prompts (id, category, title, text, json_format, enabled, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                p.get("id", ""),
                p.get("category", "自定义"),
                p.get("title", "未命名提示词"),
                p.get("text", ""),
                p.get("jsonFormat", "") or p.get("json_format", ""),
                1 if p.get("enabled", True) else 0,
                1 if p.get("isActive", False) or p.get("is_active", False) else 0,
            ),
        )
    conn.commit()


# ============ AI Skills ============

def load_skills(db: DbState) -> List[Dict[str, Any]]:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, category, title, description, system_prompt, enabled FROM ai_skills ORDER BY rowid"
    )
    rows = cursor.fetchall()
    return [
        {
            "id": r["id"],
            "category": r["category"] or "自定义",
            "title": r["title"] or "未命名 Skill",
            "description": r["description"] or "",
            "systemPrompt": r["system_prompt"] or "",
            "enabled": bool(r["enabled"]),
        }
        for r in rows
    ]


def save_skills(db: DbState, skills_json: str) -> None:
    skills = json.loads(skills_json) if isinstance(skills_json, str) else skills_json
    if not isinstance(skills, list):
        skills = []

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ai_skills")
    for s in skills:
        cursor.execute(
            "INSERT INTO ai_skills (id, category, title, description, system_prompt, enabled) VALUES (?, ?, ?, ?, ?, ?)",
            (
                s.get("id", ""),
                s.get("category", "自定义"),
                s.get("title", "未命名 Skill"),
                s.get("description", ""),
                s.get("systemPrompt", "") or s.get("system_prompt", ""),
                1 if s.get("enabled", True) else 0,
            ),
        )
    conn.commit()


# ============ AI Sessions ============

def load_sessions(db: DbState) -> List[Dict[str, Any]]:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, created_at, updated_at FROM ai_sessions ORDER BY updated_at DESC"
    )
    session_rows = cursor.fetchall()

    cursor.execute(
        "SELECT id, session_id, sender, text, timestamp, action_result FROM ai_messages ORDER BY rowid"
    )
    msg_rows = cursor.fetchall()

    messages_by_session: Dict[str, List[Dict[str, Any]]] = {}
    for mr in msg_rows:
        sid = mr["session_id"]
        act_res_raw = mr["action_result"]
        act_res = None
        if act_res_raw and act_res_raw.strip():
            try:
                act_res = json.loads(act_res_raw)
            except Exception:
                act_res = None

        msg_item = {
            "id": mr["id"],
            "sender": mr["sender"],
            "text": mr["text"] or "",
            "timestamp": mr["timestamp"] or "",
            "actionResult": act_res,
        }
        messages_by_session.setdefault(sid, []).append(msg_item)

    results = []
    for sr in session_rows:
        sid = sr["id"]
        results.append(
            {
                "id": sid,
                "title": sr["title"] or "新对话",
                "createdAt": sr["created_at"] or 0,
                "updatedAt": sr["updated_at"] or 0,
                "messages": messages_by_session.get(sid, []),
            }
        )
    return results


def save_sessions(db: DbState, sessions_json: str) -> None:
    sessions = json.loads(sessions_json) if isinstance(sessions_json, str) else sessions_json
    if not isinstance(sessions, list):
        sessions = []

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ai_messages")
    cursor.execute("DELETE FROM ai_sessions")

    for s in sessions:
        sid = s.get("id", "")
        cursor.execute(
            "INSERT INTO ai_sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (
                sid,
                s.get("title", "新对话"),
                s.get("createdAt") or s.get("created_at") or 0,
                s.get("updatedAt") or s.get("updated_at") or 0,
            ),
        )
        msgs = s.get("messages", [])
        if isinstance(msgs, list):
            for m in msgs:
                act_res = m.get("actionResult") or m.get("action_result")
                act_res_str = json.dumps(act_res, ensure_ascii=False) if act_res else ""
                cursor.execute(
                    "INSERT INTO ai_messages (id, session_id, sender, text, timestamp, action_result) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        m.get("id", ""),
                        sid,
                        m.get("sender", "user"),
                        m.get("text", ""),
                        m.get("timestamp", ""),
                        act_res_str,
                    ),
                )
    conn.commit()
