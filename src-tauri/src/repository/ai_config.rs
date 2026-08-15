use rusqlite::params;
use serde_json::{json, Value};
use crate::repository::DbState;

fn conn_err(e: rusqlite::Error) -> String {
    e.to_string()
}

fn bool_to_int(b: bool) -> i64 {
    if b { 1 } else { 0 }
}

fn int_to_bool(v: i64) -> bool {
    v != 0
}

// ============ AI Providers ============

pub fn load_providers(db: &DbState) -> Result<Vec<Value>, String> {
    let conn = db.conn.lock().unwrap();
    let mut stmt = conn
        .prepare("SELECT id, name, base_url, api_key, model, is_custom FROM ai_providers ORDER BY rowid")
        .map_err(conn_err)?;
    let rows = stmt
        .query_map([], |row| {
            Ok(json!({
                "id": row.get::<_, String>(0)?,
                "name": row.get::<_, String>(1)?,
                "base_url": row.get::<_, String>(2)?,
                "api_key": row.get::<_, String>(3)?,
                "model": row.get::<_, String>(4)?,
                "is_custom": int_to_bool(row.get::<_, i64>(5)?),
            }))
        })
        .map_err(conn_err)?;
    let mut arr = Vec::new();
    for r in rows {
        arr.push(r.map_err(conn_err)?);
    }
    Ok(arr)
}

pub fn save_providers(db: &DbState, providers_json: &str) -> Result<(), String> {
    let providers: Value = serde_json::from_str(providers_json).map_err(|e| e.to_string())?;
    let arr = providers.as_array().cloned().unwrap_or_default();
    let conn = db.conn.lock().unwrap();
    let tx = conn.unchecked_transaction().map_err(conn_err)?;
    tx.execute("DELETE FROM ai_providers", []).map_err(conn_err)?;
    for p in arr {
        tx.execute(
            "INSERT INTO ai_providers (id, name, base_url, api_key, model, is_custom) VALUES (?1,?2,?3,?4,?5,?6)",
            params![
                p["id"].as_str().unwrap_or(""),
                p["name"].as_str().unwrap_or(""),
                p["base_url"].as_str().unwrap_or(""),
                p["api_key"].as_str().unwrap_or(""),
                p["model"].as_str().unwrap_or(""),
                bool_to_int(p["is_custom"].as_bool().unwrap_or(false)),
            ],
        )
        .map_err(conn_err)?;
    }
    tx.commit().map_err(conn_err)?;
    Ok(())
}

// ============ AI Prompts ============

pub fn load_prompts(db: &DbState) -> Result<Vec<Value>, String> {
    let conn = db.conn.lock().unwrap();
    let mut stmt = conn
        .prepare("SELECT id, category, title, text, json_format, enabled, is_active FROM ai_prompts ORDER BY rowid")
        .map_err(conn_err)?;
    let rows = stmt
        .query_map([], |row| {
            let json_format: Option<String> = row.get(4)?;
            Ok(json!({
                "id": row.get::<_, String>(0)?,
                "category": row.get::<_, String>(1)?,
                "title": row.get::<_, String>(2)?,
                "text": row.get::<_, String>(3)?,
                "jsonFormat": json_format.unwrap_or_default(),
                "enabled": int_to_bool(row.get::<_, i64>(5)?),
                "isActive": int_to_bool(row.get::<_, i64>(6)?),
            }))
        })
        .map_err(conn_err)?;
    let mut arr = Vec::new();
    for r in rows {
        arr.push(r.map_err(conn_err)?);
    }
    Ok(arr)
}

pub fn save_prompts(db: &DbState, prompts_json: &str) -> Result<(), String> {
    let prompts: Value = serde_json::from_str(prompts_json).map_err(|e| e.to_string())?;
    let arr = prompts.as_array().cloned().unwrap_or_default();
    let conn = db.conn.lock().unwrap();
    let tx = conn.unchecked_transaction().map_err(conn_err)?;
    tx.execute("DELETE FROM ai_prompts", []).map_err(conn_err)?;
    for p in arr {
        tx.execute(
            "INSERT INTO ai_prompts (id, category, title, text, json_format, enabled, is_active) VALUES (?1,?2,?3,?4,?5,?6,?7)",
            params![
                p["id"].as_str().unwrap_or(""),
                p["category"].as_str().unwrap_or("自定义"),
                p["title"].as_str().unwrap_or("未命名提示词"),
                p["text"].as_str().unwrap_or(""),
                p.get("jsonFormat").and_then(|v| v.as_str()).unwrap_or(""),
                bool_to_int(p["enabled"].as_bool().unwrap_or(true)),
                bool_to_int(p["isActive"].as_bool().unwrap_or(false)),
            ],
        )
        .map_err(conn_err)?;
    }
    tx.commit().map_err(conn_err)?;
    Ok(())
}

// ============ AI Skills ============

pub fn load_skills(db: &DbState) -> Result<Vec<Value>, String> {
    let conn = db.conn.lock().unwrap();
    let mut stmt = conn
        .prepare("SELECT id, category, title, description, system_prompt, enabled FROM ai_skills ORDER BY rowid")
        .map_err(conn_err)?;
    let rows = stmt
        .query_map([], |row| {
            Ok(json!({
                "id": row.get::<_, String>(0)?,
                "category": row.get::<_, String>(1)?,
                "title": row.get::<_, String>(2)?,
                "description": row.get::<_, String>(3)?,
                "systemPrompt": row.get::<_, String>(4)?,
                "enabled": int_to_bool(row.get::<_, i64>(5)?),
            }))
        })
        .map_err(conn_err)?;
    let mut arr = Vec::new();
    for r in rows {
        arr.push(r.map_err(conn_err)?);
    }
    Ok(arr)
}

pub fn save_skills(db: &DbState, skills_json: &str) -> Result<(), String> {
    let skills: Value = serde_json::from_str(skills_json).map_err(|e| e.to_string())?;
    let arr = skills.as_array().cloned().unwrap_or_default();
    let conn = db.conn.lock().unwrap();
    let tx = conn.unchecked_transaction().map_err(conn_err)?;
    tx.execute("DELETE FROM ai_skills", []).map_err(conn_err)?;
    for s in arr {
        tx.execute(
            "INSERT INTO ai_skills (id, category, title, description, system_prompt, enabled) VALUES (?1,?2,?3,?4,?5,?6)",
            params![
                s["id"].as_str().unwrap_or(""),
                s["category"].as_str().unwrap_or("自定义"),
                s["title"].as_str().unwrap_or("未命名 Skill"),
                s["description"].as_str().unwrap_or(""),
                s["systemPrompt"].as_str().unwrap_or(""),
                bool_to_int(s["enabled"].as_bool().unwrap_or(true)),
            ],
        )
        .map_err(conn_err)?;
    }
    tx.commit().map_err(conn_err)?;
    Ok(())
}

// ============ AI Sessions (with messages) ============

pub fn load_sessions(db: &DbState) -> Result<Vec<Value>, String> {
    let conn = db.conn.lock().unwrap();
    let mut stmt = conn
        .prepare("SELECT id, title, created_at, updated_at FROM ai_sessions ORDER BY updated_at DESC")
        .map_err(conn_err)?;
    let session_rows = stmt
        .query_map([], |row| {
            Ok(json!({
                "id": row.get::<_, String>(0)?,
                "title": row.get::<_, String>(1)?,
                "createdAt": row.get::<_, i64>(2)?,
                "updatedAt": row.get::<_, i64>(3)?,
                "messages": [],
            }))
        })
        .map_err(conn_err)?;

    let mut sessions: Vec<Value> = Vec::new();
    for r in session_rows {
        sessions.push(r.map_err(conn_err)?);
    }

    let mut msg_stmt = conn
        .prepare("SELECT id, session_id, sender, text, timestamp, action_result FROM ai_messages ORDER BY rowid")
        .map_err(conn_err)?;
    let msg_rows = msg_stmt
        .query_map([], |row| {
            let action_result: Option<String> = row.get(5)?;
            let action_result = action_result
                .filter(|s| !s.is_empty())
                .and_then(|s| serde_json::from_str::<Value>(&s).ok());
            Ok(json!({
                "id": row.get::<_, String>(0)?,
                "session_id": row.get::<_, String>(1)?,
                "sender": row.get::<_, String>(2)?,
                "text": row.get::<_, String>(3)?,
                "timestamp": row.get::<_, String>(4)?,
                "actionResult": action_result,
            }))
        })
        .map_err(conn_err)?;

    let mut messages: Vec<Value> = Vec::new();
    for r in msg_rows {
        messages.push(r.map_err(conn_err)?);
    }

    for s in sessions.iter_mut() {
        let sid = s["id"].as_str().unwrap_or("");
        let msgs: Vec<Value> = messages
            .iter()
            .filter(|m| m["session_id"].as_str().unwrap_or("") == sid)
            .map(|m| {
                let mut copy = m.clone();
                copy.as_object_mut().unwrap().remove("session_id");
                copy
            })
            .collect();
        if let Some(obj) = s.as_object_mut() {
            obj.insert("messages".to_string(), Value::Array(msgs));
        }
    }
    Ok(sessions)
}

pub fn save_sessions(db: &DbState, sessions_json: &str) -> Result<(), String> {
    let sessions: Value = serde_json::from_str(sessions_json).map_err(|e| e.to_string())?;
    let arr = sessions.as_array().cloned().unwrap_or_default();
    let conn = db.conn.lock().unwrap();
    let tx = conn.unchecked_transaction().map_err(conn_err)?;
    tx.execute("DELETE FROM ai_messages", []).map_err(conn_err)?;
    tx.execute("DELETE FROM ai_sessions", []).map_err(conn_err)?;
    for s in arr {
        tx.execute(
            "INSERT INTO ai_sessions (id, title, created_at, updated_at) VALUES (?1,?2,?3,?4)",
            params![
                s["id"].as_str().unwrap_or(""),
                s["title"].as_str().unwrap_or("新对话"),
                s["createdAt"].as_i64().unwrap_or(0),
                s["updatedAt"].as_i64().unwrap_or(0),
            ],
        )
        .map_err(conn_err)?;
        let sid = s["id"].as_str().unwrap_or("");
        if let Some(msgs) = s["messages"].as_array() {
            for m in msgs {
                let action_result = m
                    .get("actionResult")
                    .filter(|v| !v.is_null())
                    .map(|v| v.to_string())
                    .unwrap_or_default();
                tx.execute(
                    "INSERT INTO ai_messages (id, session_id, sender, text, timestamp, action_result) VALUES (?1,?2,?3,?4,?5,?6)",
                    params![
                        m["id"].as_str().unwrap_or(""),
                        sid,
                        m["sender"].as_str().unwrap_or("user"),
                        m["text"].as_str().unwrap_or(""),
                        m["timestamp"].as_str().unwrap_or(""),
                        action_result,
                    ],
                )
                .map_err(conn_err)?;
            }
        }
    }
    tx.commit().map_err(conn_err)?;
    Ok(())
}
