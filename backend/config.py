import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict
import platformdirs

APP_NAME = "todo_agent"
APP_AUTHOR = "todo_agent"


def get_app_dir() -> Path:
    data_dir = Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_db_path() -> Path:
    return get_app_dir() / "todos.db"


def get_display_config_path() -> Path:
    return get_app_dir() / "cli_config.json"


@dataclass
class DisplayConfig:
    user_name: str = "用户"
    user_prefix: str = "todo-agent"
    ai_name: str = "Todo Agent"
    ai_prefix: str = "🤖"

    @classmethod
    def load(cls) -> "DisplayConfig":
        path = get_display_config_path()
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return cls(**data)
            except Exception:
                pass
        cfg = cls()
        cfg.save()
        return cfg

    def save(self) -> None:
        path = get_display_config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)
