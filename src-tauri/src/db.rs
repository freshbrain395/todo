use serde::{Deserialize, Serialize};
use rusqlite::{params, Connection, Result};
use std::path::PathBuf;
use std::sync::Mutex;
use sha2::{Sha256, Digest};

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

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct User {
    pub id: i64,
    pub username: String,
    pub created_at: String,
}

pub struct DbState {
    pub conn: Mutex<Connection>,
}

fn hash_password(password: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(password.as_bytes());
    hasher.update(b"_todo_agent_salt_2026");
    format!("{:x}", hasher.finalize())
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER DEFAULT 0
            )",
            [],
        )?;

        // Ensure user_id column exists if table existed previously without it
        let _ = conn.execute("ALTER TABLE todos ADD COLUMN user_id INTEGER DEFAULT 0", []);

        conn.execute(
            "CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )",
            [],
        )?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS app_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )",
            [],
        )?;
        Ok(())
    }

    pub fn register_user(&self, username: &str, password: &str) -> Result<User, String> {
        let clean_name = username.trim();
        if clean_name.is_empty() {
            return Err("用户名不能为空".to_string());
        }
        if password.trim().len() < 3 {
            return Err("密码长度不能小于 3 位".to_string());
        }

        let pwd_hash = hash_password(password);
        let conn = self.conn.lock().map_err(|e| e.to_string())?;

        let res = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?1, ?2)",
            params![clean_name, pwd_hash],
        );

        match res {
            Ok(_) => {
                let user_id = conn.last_insert_rowid();
                let created_at: String = conn
                    .query_row(
                        "SELECT created_at FROM users WHERE id = ?1",
                        params![user_id],
                        |row| row.get(0),
                    )
                    .unwrap_or_default();

                Ok(User {
                    id: user_id,
                    username: clean_name.to_string(),
                    created_at,
                })
            }
            Err(e) => {
                if e.to_string().contains("UNIQUE") {
                    Err("该用户名已被注册，请尝试直接登录".to_string())
                } else {
                    Err(format!("注册失败: {}", e))
                }
            }
        }
    }

    pub fn login_user(&self, username: &str, password: &str) -> Result<User, String> {
        let clean_name = username.trim();
        let pwd_hash = hash_password(password);
        let conn = self.conn.lock().map_err(|e| e.to_string())?;

        let mut stmt = conn
            .prepare("SELECT id, username, password_hash, created_at FROM users WHERE username = ?1")
            .map_err(|e| e.to_string())?;

        let user_opt = stmt
            .query_row(params![clean_name], |row| {
                let id: i64 = row.get(0)?;
                let uname: String = row.get(1)?;
                let stored_hash: String = row.get(2)?;
                let created_at: String = row.get(3)?;
                Ok((id, uname, stored_hash, created_at))
            })
            .ok();

        if let Some((id, uname, stored_hash, created_at)) = user_opt {
            if stored_hash == pwd_hash {
                Ok(User {
                    id,
                    username: uname,
                    created_at,
                })
            } else {
                Err("密码不正确，请重新输入".to_string())
            }
        } else {
            Err("用户不存在，请先注册账号".to_string())
        }
    }

    pub fn get_todos(&self, filter: &str, search: &str, user_id: Option<i64>) -> Result<Vec<Todo>> {
        let uid = user_id.unwrap_or(0);
        let conn = self.conn.lock().unwrap();

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
        &self,
        title: &str,
        priority: &str,
        category: &str,
        remind_at: Option<&str>,
        user_id: Option<i64>,
    ) -> Result<i64> {
        let uid = user_id.unwrap_or(0);
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO todos (title, priority, category, remind_at, user_id) VALUES (?1, ?2, ?3, ?4, ?5)",
            params![title, priority, category, remind_at, uid],
        )?;
        Ok(conn.last_insert_rowid())
    }

    pub fn update_todo_status(&self, id: i64, completed: bool, user_id: Option<i64>) -> Result<bool> {
        let uid = user_id.unwrap_or(0);
        let conn = self.conn.lock().unwrap();
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
        &self,
        id: i64,
        title: &str,
        priority: &str,
        category: &str,
        remind_at: Option<&str>,
        user_id: Option<i64>,
    ) -> Result<bool> {
        let uid = user_id.unwrap_or(0);
        let conn = self.conn.lock().unwrap();

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

    pub fn delete_todo(&self, id: i64, user_id: Option<i64>) -> Result<bool> {
        let uid = user_id.unwrap_or(0);
        let conn = self.conn.lock().unwrap();

        let count = if uid > 0 {
            conn.execute("DELETE FROM todos WHERE id = ?1 AND user_id = ?2", params![id, uid])?
        } else {
            conn.execute("DELETE FROM todos WHERE id = ?1 AND (user_id IS NULL OR user_id = 0)", params![id])?
        };
        Ok(count > 0)
    }

    pub fn get_config(&self, key: &str) -> Result<Option<String>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare("SELECT value FROM app_config WHERE key = ?1")?;
        let mut rows = stmt.query(params![key])?;
        if let Some(row) = rows.next()? {
            let val: String = row.get(0)?;
            Ok(Some(val))
        } else {
            Ok(None)
        }
    }

    pub fn save_config(&self, key: &str, value: &str) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO app_config (key, value) VALUES (?1, ?2)
             ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
            params![key, value],
        )?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sqlite_crud_and_user_auth() {
        let db_state = DbState::new(PathBuf::from(":memory:")).expect("Failed to create in-memory db");
        
        // 1. Register & Login User
        let user = db_state.register_user("testuser", "123456").expect("Register failed");
        assert_eq!(user.username, "testuser");

        let logged_user = db_state.login_user("testuser", "123456").expect("Login failed");
        assert_eq!(logged_user.id, user.id);

        // 2. Add local todo & user todo
        let local_id = db_state.add_todo("本地任务", "high", "工作", None, None).expect("Add local failed");
        let user_id_todo = db_state.add_todo("用户专属任务", "high", "学习", None, Some(user.id)).expect("Add user todo failed");

        // 3. Verify Isolation
        let local_todos = db_state.get_todos("all", "", None).expect("Get local failed");
        assert_eq!(local_todos.len(), 1);
        assert_eq!(local_todos[0].id, local_id);

        let user_todos = db_state.get_todos("all", "", Some(user.id)).expect("Get user failed");
        assert_eq!(user_todos.len(), 1);
        assert_eq!(user_todos[0].id, user_id_todo);
    }
}

