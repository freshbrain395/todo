use rusqlite::params;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use crate::repository::db::DbState;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct User {
    pub id: i64,
    pub username: String,
    pub created_at: String,
}

pub fn hash_password(password: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(password.as_bytes());
    hasher.update(b"_todo_agent_salt_2026");
    format!("{:x}", hasher.finalize())
}

pub fn register_user(db: &DbState, username: &str, password: &str) -> Result<User, String> {
    let clean_name = username.trim();
    if clean_name.is_empty() {
        return Err("用户名不能为空".to_string());
    }
    if password.trim().len() < 3 {
        return Err("密码长度不能小于 3 位".to_string());
    }

    let pwd_hash = hash_password(password);
    let conn = db.conn.lock().map_err(|e| e.to_string())?;

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

pub fn login_user(db: &DbState, username: &str, password: &str) -> Result<User, String> {
    let clean_name = username.trim();
    let pwd_hash = hash_password(password);
    let conn = db.conn.lock().map_err(|e| e.to_string())?;

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
