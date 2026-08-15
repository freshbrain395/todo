use rusqlite::{params, Result};
use serde::{Deserialize, Serialize};
use crate::repository::db::DbState;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Todo {
    pub id: i64,
    pub title: String,
    pub priority: String,
    pub category: String,
    pub completed: bool,
    pub remind_at: Option<String>,
    pub created_at: String,
    pub updated_at: String,
    pub user_id: i64,
}

pub fn get_todos(db: &DbState, filter: &str, search: &str, user_id: Option<i64>) -> Result<Vec<Todo>> {
    let uid = user_id.unwrap_or(0);
    let conn = db.conn.lock().unwrap();

    let mut query = String::from("SELECT id, title, priority, category, completed, remind_at, created_at, updated_at, user_id FROM todos WHERE 1=1");
    let mut params_vec: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();

    if uid > 0 {
        query.push_str(" AND user_id = ?");
        params_vec.push(Box::new(uid));
    } else {
        query.push_str(" AND (user_id IS NULL OR user_id = 0)");
    }

    if filter == "pending" {
        query.push_str(" AND completed = 0");
    } else if filter == "completed" {
        query.push_str(" AND completed = 1");
    }

    if !search.trim().is_empty() {
        query.push_str(" AND title LIKE ?");
        params_vec.push(Box::new(format!("%{}%", search.trim())));
    }

    query.push_str(" ORDER BY completed ASC, CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 ELSE 4 END, id DESC");

    let mut stmt = conn.prepare(&query)?;
    let params_refs: Vec<&dyn rusqlite::ToSql> = params_vec.iter().map(|b| b.as_ref()).collect();
    let todo_iter = stmt.query_map(params_refs.as_slice(), |row| {
        let completed_int: i32 = row.get(4)?;
        let created_at: Option<String> = row.get(6).ok();
        let updated_at: Option<String> = row.get(7).ok();
        let u_id: i64 = row.get(8).unwrap_or(0);
        Ok(Todo {
            id: row.get(0)?,
            title: row.get(1)?,
            priority: row.get(2)?,
            category: row.get(3)?,
            completed: completed_int == 1,
            remind_at: row.get(5)?,
            created_at: created_at.unwrap_or_default(),
            updated_at: updated_at.unwrap_or_default(),
            user_id: u_id,
        })
    })?;

    let mut todos = Vec::new();
    for todo in todo_iter {
        todos.push(todo?);
    }
    Ok(todos)
}

pub fn add_todo(
    db: &DbState,
    title: &str,
    priority: &str,
    category: &str,
    remind_at: Option<&str>,
    user_id: Option<i64>,
) -> Result<i64> {
    let uid = user_id.unwrap_or(0);
    let conn = db.conn.lock().unwrap();
    conn.execute(
        "INSERT INTO todos (title, priority, category, remind_at, user_id) VALUES (?1, ?2, ?3, ?4, ?5)",
        params![title, priority, category, remind_at, uid],
    )?;
    Ok(conn.last_insert_rowid())
}

pub fn update_todo_status(db: &DbState, id: i64, completed: bool, user_id: Option<i64>) -> Result<bool> {
    let uid = user_id.unwrap_or(0);
    let conn = db.conn.lock().unwrap();
    let completed_int = if completed { 1 } else { 0 };

    let count = if uid > 0 {
        conn.execute(
            "UPDATE todos SET completed = ?1, updated_at = CURRENT_TIMESTAMP WHERE id = ?2 AND user_id = ?3",
            params![completed_int, id, uid],
        )?
    } else {
        conn.execute(
            "UPDATE todos SET completed = ?1, updated_at = CURRENT_TIMESTAMP WHERE id = ?2 AND (user_id IS NULL OR user_id = 0)",
            params![completed_int, id],
        )?
    };
    Ok(count > 0)
}

pub fn update_todo(
    db: &DbState,
    id: i64,
    title: &str,
    priority: &str,
    category: &str,
    remind_at: Option<&str>,
    user_id: Option<i64>,
) -> Result<bool> {
    let uid = user_id.unwrap_or(0);
    let conn = db.conn.lock().unwrap();

    let count = if uid > 0 {
        conn.execute(
            "UPDATE todos SET title = ?1, priority = ?2, category = ?3, remind_at = ?4, updated_at = CURRENT_TIMESTAMP WHERE id = ?5 AND user_id = ?6",
            params![title, priority, category, remind_at, id, uid],
        )?
    } else {
        conn.execute(
            "UPDATE todos SET title = ?1, priority = ?2, category = ?3, remind_at = ?4, updated_at = CURRENT_TIMESTAMP WHERE id = ?5 AND (user_id IS NULL OR user_id = 0)",
            params![title, priority, category, remind_at, id],
        )?
    };
    Ok(count > 0)
}

pub fn delete_todo(db: &DbState, id: i64, user_id: Option<i64>) -> Result<bool> {
    let uid = user_id.unwrap_or(0);
    let conn = db.conn.lock().unwrap();

    let count = if uid > 0 {
        conn.execute("DELETE FROM todos WHERE id = ?1 AND user_id = ?2", params![id, uid])?
    } else {
        conn.execute("DELETE FROM todos WHERE id = ?1 AND (user_id IS NULL OR user_id = 0)", params![id])?
    };
    Ok(count > 0)
}
