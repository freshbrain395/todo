use rusqlite::{Connection, Result};
use std::path::PathBuf;
use std::sync::Mutex;

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

        conn.execute(
            "CREATE TABLE IF NOT EXISTS local_users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL DEFAULT '123456',
                avatar_color TEXT DEFAULT '#10B981',
                last_login_time TEXT,
                is_admin INTEGER DEFAULT 0
            )",
            [],
        )?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS local_user_configs (
                user_id TEXT PRIMARY KEY,
                config_json TEXT NOT NULL DEFAULT '{}'
            )",
            [],
        )?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS ai_providers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                base_url TEXT DEFAULT '',
                api_key TEXT DEFAULT '',
                model TEXT DEFAULT '',
                is_custom INTEGER DEFAULT 0
            )",
            [],
        )?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS ai_prompts (
                id TEXT PRIMARY KEY,
                category TEXT DEFAULT '自定义',
                title TEXT DEFAULT '未命名提示词',
                text TEXT DEFAULT '',
                json_format TEXT,
                enabled INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 0
            )",
            [],
        )?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS ai_skills (
                id TEXT PRIMARY KEY,
                category TEXT DEFAULT '自定义',
                title TEXT DEFAULT '未命名 Skill',
                description TEXT DEFAULT '',
                system_prompt TEXT DEFAULT '',
                enabled INTEGER DEFAULT 1
            )",
            [],
        )?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS ai_sessions (
                id TEXT PRIMARY KEY,
                title TEXT DEFAULT '新对话',
                created_at INTEGER,
                updated_at INTEGER
            )",
            [],
        )?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS ai_messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                sender TEXT NOT NULL,
                text TEXT DEFAULT '',
                timestamp TEXT DEFAULT '',
                action_result TEXT
            )",
            [],
        )?;
        Ok(())
    }
}
