import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Any, Dict
import platformdirs

APP_NAME = "todo_agent"
APP_AUTHOR = "todo_agent"


def get_app_dir() -> Path:
    data_dir = Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_db_path() -> Path:
    return get_app_dir() / "todos.db"


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_backend_dir() -> Path:
    return Path(__file__).resolve().parent


def get_config_path() -> Path:
    """获取全局统一 JSON 配置文件路径 (优先 backend/config.json，兼容根目录)"""
    backend_cfg = get_backend_dir() / "config.json"
    if backend_cfg.exists():
        return backend_cfg
    root_cfg = get_project_root() / "config.json"
    if root_cfg.exists():
        return root_cfg
    return backend_cfg


# 兼容别名
def get_ai_config_path() -> Path:
    return get_config_path()


def get_display_config_path() -> Path:
    return get_config_path()


def read_raw_config() -> Dict[str, Any]:
    """读取全局统一 JSON 配置文件"""
    path = get_config_path()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}


def write_raw_config(data: Dict[str, Any]) -> None:
    """写入全局统一 JSON 配置文件"""
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@dataclass
class DisplayConfig:
    user_name: str = "用户"
    user_prefix: str = "todo-agent"
    ai_name: str = "Todo Agent"
    ai_prefix: str = "🤖"

    @classmethod
    def load(cls) -> "DisplayConfig":
        data = read_raw_config()
        sys_cfg = data.get("system", {})
        if isinstance(sys_cfg, dict) and sys_cfg:
            try:
                return cls(**{k: v for k, v in sys_cfg.items() if k in cls.__dataclass_fields__})
            except Exception:
                pass
        return cls()

    def save(self) -> None:
        data = read_raw_config()
        data["system"] = asdict(self)
        write_raw_config(data)
