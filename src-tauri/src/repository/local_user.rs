use rusqlite::params;
use serde_json::{json, Map, Value};
use crate::repository::DbState;

fn conn_err(e: rusqlite::Error) -> String {
    e.to_string()
}

pub fn get_local_users(db: &DbState) -> Result<String, String> {
    let conn = db.conn.lock().unwrap();

    let mut user_stmt = conn
        .prepare("SELECT id, username, password, avatar_color, last_login_time, is_admin FROM local_users")
        .map_err(conn_err)?;
    let user_rows = user_stmt
        .query_map([], |row| {
            Ok(json!({
                "id": row.get::<_, String>(0)?,
                "username": row.get::<_, String>(1)?,
                "password": row.get::<_, String>(2)?,
                "avatarColor": row.get::<_, String>(3)?,
                "lastLoginTime": row.get::<_, String>(4)?,
                "isAdmin": int_to_bool(row.get::<_, i64>(5)?),
            }))
        })
        .map_err(conn_err)?;

    let mut users: Vec<Value> = Vec::new();
    for r in user_rows {
        users.push(r.map_err(conn_err)?);
    }

    let mut cfg_stmt = conn
        .prepare("SELECT user_id, config_json FROM local_user_configs")
        .map_err(conn_err)?;
    let cfg_rows = cfg_stmt
        .query_map([], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?))
        })
        .map_err(conn_err)?;
    let mut configs: Map<String, Value> = Map::new();
    for r in cfg_rows {
        let (uid, cfg) = r.map_err(conn_err)?;
        let parsed = serde_json::from_str::<Value>(&cfg).unwrap_or(Value::Null);
        configs.insert(uid, parsed);
    }

    let mut result: Map<String, Value> = Map::new();
    for u in users {
        let uid = u["id"].as_str().unwrap_or("").to_string();
        let mut account = Map::new();
        account.insert("user".to_string(), u.clone());
        account.insert(
            "config".to_string(),
            configs
                .get(&uid)
                .cloned()
                .unwrap_or(Value::Null),
        );
        result.insert(uid, Value::Object(account));
    }

    Ok(Value::Object(result).to_string())
}

pub fn save_local_users(db: &DbState, accounts_json: &str) -> Result<(), String> {
    let accounts: Value = serde_json::from_str(accounts_json).map_err(|e| e.to_string())?;
    let map = accounts
        .as_object()
        .cloned()
        .unwrap_or_default();

    let conn = db.conn.lock().unwrap();
    let tx = conn.unchecked_transaction().map_err(conn_err)?;
    tx.execute("DELETE FROM local_user_configs", []).map_err(conn_err)?;
    tx.execute("DELETE FROM local_users", []).map_err(conn_err)?;

    for (uid, data) in map {
        let user = &data["user"];
        let config = &data["config"];
        tx.execute(
            "INSERT INTO local_users (id, username, password, avatar_color, last_login_time, is_admin) VALUES (?1,?2,?3,?4,?5,?6)",
            params![
                uid,
                user["username"].as_str().unwrap_or(""),
                user["password"].as_str().unwrap_or(""),
                user["avatarColor"].as_str().unwrap_or("#10B981"),
                user["lastLoginTime"].as_str().unwrap_or(""),
                bool_to_int(user["isAdmin"].as_bool().unwrap_or(false)),
            ],
        )
        .map_err(conn_err)?;
        let cfg_json = if config.is_null() {
            "{}".to_string()
        } else {
            config.to_string()
        };
        tx.execute(
            "INSERT INTO local_user_configs (user_id, config_json) VALUES (?1,?2)",
            params![uid, cfg_json],
        )
        .map_err(conn_err)?;
    }
    tx.commit().map_err(conn_err)?;
    Ok(())
}

fn bool_to_int(b: bool) -> i64 {
    if b { 1 } else { 0 }
}

fn int_to_bool(v: i64) -> bool {
    v != 0
}
