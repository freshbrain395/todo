use rusqlite::{params, Result};
use crate::repository::db::DbState;

pub fn get_config(db: &DbState, key: &str) -> Result<Option<String>> {
    let conn = db.conn.lock().unwrap();
    let mut stmt = conn.prepare("SELECT value FROM app_config WHERE key = ?1")?;
    let mut rows = stmt.query(params![key])?;
    if let Some(row) = rows.next()? {
        let val: String = row.get(0)?;
        Ok(Some(val))
    } else {
        Ok(None)
    }
}

pub fn save_config(db: &DbState, key: &str, value: &str) -> Result<()> {
    let conn = db.conn.lock().unwrap();
    conn.execute(
        "INSERT INTO app_config (key, value) VALUES (?1, ?2)
         ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
        params![key, value],
    )?;
    Ok(())
}
