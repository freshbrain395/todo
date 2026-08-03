use serde::{Deserialize, Serialize};
use rusqlite::{params, Connection, Result};
use std::path::PathBuf;
use std::sync::Mutex;

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
}

pub struct DbState {
    pub conn: Mutex<Connection>,
}

impl DbState {
    pub fn new(db_path: PathBuf) -> Result<Self> {
        let conn = Connection::open(db_path)?;
        let state = DbState {
            conn: Mutex::new(conn),
        };
        state.init_tables()?;
        Ok(state)
    }

    pub fn init_tables(&self) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                category TEXT DEFAULT '工作',
                completed INTEGER DEFAULT 0,
                remind_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )",
            [],
        )?;
        Ok(())
    }

    pub fn get_todos(&self, filter: &str, search: &str) -> Result<Vec<Todo>> {
        let conn = self.conn.lock().unwrap();
        let mut query = String::from("SELECT id, title, priority, category, completed, remind_at, created_at, updated_at FROM todos WHERE 1=1");
        let mut params_vec: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();

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
            Ok(Todo {
                id: row.get(0)?,
                title: row.get(1)?,
                priority: row.get(2)?,
                category: row.get(3)?,
                completed: completed_int == 1,
                remind_at: row.get(5)?,
                created_at: created_at.unwrap_or_default(),
                updated_at: updated_at.unwrap_or_default(),
            })
        })?;

        let mut todos = Vec::new();
        for todo in todo_iter {
            todos.push(todo?);
        }
        Ok(todos)
    }

    pub fn add_todo(&self, title: &str, priority: &str, category: &str, remind_at: Option<&str>) -> Result<i64> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO todos (title, priority, category, remind_at) VALUES (?1, ?2, ?3, ?4)",
            params![title, priority, category, remind_at],
        )?;
        Ok(conn.last_insert_rowid())
    }

    pub fn update_todo_status(&self, id: i64, completed: bool) -> Result<bool> {
        let conn = self.conn.lock().unwrap();
        let completed_int = if completed { 1 } else { 0 };
        let count = conn.execute(
            "UPDATE todos SET completed = ?1, updated_at = CURRENT_TIMESTAMP WHERE id = ?2",
            params![completed_int, id],
        )?;
        Ok(count > 0)
    }

    pub fn update_todo(&self, id: i64, title: &str, priority: &str, category: &str, remind_at: Option<&str>) -> Result<bool> {
        let conn = self.conn.lock().unwrap();
        let count = conn.execute(
            "UPDATE todos SET title = ?1, priority = ?2, category = ?3, remind_at = ?4, updated_at = CURRENT_TIMESTAMP WHERE id = ?5",
            params![title, priority, category, remind_at, id],
        )?;
        Ok(count > 0)
    }

    pub fn delete_todo(&self, id: i64) -> Result<bool> {
        let conn = self.conn.lock().unwrap();
        let count = conn.execute("DELETE FROM todos WHERE id = ?1", params![id])?;
        Ok(count > 0)
    }
}
