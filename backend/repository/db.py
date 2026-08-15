import sqlite3
import threading
from pathlib import Path
from typing import Optional
from backend.config import get_db_path


class DbState:
    _instance: Optional["DbState"] = None
    _lock = threading.Lock()

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_db_path()
        self._local = threading.local()
        self.init_tables()

    @classmethod
    def get_instance(cls, db_path: Optional[Path] = None) -> "DbState":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(db_path)
            return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return self._local.conn

    def init_tables(self) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                category TEXT DEFAULT '工作',
                completed INTEGER DEFAULT 0,
                remind_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER DEFAULT 0
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS app_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS local_users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL DEFAULT '123456',
                avatar_color TEXT DEFAULT '#10B981',
                last_login_time TEXT,
                is_admin INTEGER DEFAULT 0
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS local_user_configs (
                user_id TEXT PRIMARY KEY,
                config_json TEXT NOT NULL DEFAULT '{}'
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_providers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                base_url TEXT DEFAULT '',
                api_key TEXT DEFAULT '',
                model TEXT DEFAULT '',
                is_custom INTEGER DEFAULT 0
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_prompts (
                id TEXT PRIMARY KEY,
                category TEXT DEFAULT '自定义',
                title TEXT DEFAULT '未命名提示词',
                text TEXT DEFAULT '',
                json_format TEXT,
                enabled INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 0
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_skills (
                id TEXT PRIMARY KEY,
                category TEXT DEFAULT '自定义',
                title TEXT DEFAULT '未命名 Skill',
                description TEXT DEFAULT '',
                system_prompt TEXT DEFAULT '',
                enabled INTEGER DEFAULT 1
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_sessions (
                id TEXT PRIMARY KEY,
                title TEXT DEFAULT '新对话',
                created_at INTEGER,
                updated_at INTEGER
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                sender TEXT NOT NULL,
                text TEXT DEFAULT '',
                timestamp TEXT DEFAULT '',
                action_result TEXT
            )
            """
        )

        conn.commit()
