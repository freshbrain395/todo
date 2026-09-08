import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Any, Dict
import platformdirs

APP_NAME = "Todo Agent"
APP_AUTHOR = "Todo Agent"


def get_app_dir() -> Path:
    """获取应用数据根目录: %APPDATA%\\Todo Agent"""
    data_dir = Path(platformdirs.user_data_dir(APP_NAME, appauthor=False, roaming=True))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_logs_dir() -> Path:
    """获取日志存储目录: %APPDATA%\\Todo Agent\\logs"""
    logs_dir = get_app_dir() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_db_path() -> Path:
    """数据库统一保存在用户数据目录下: %APPDATA%\\Todo Agent\\todos.db"""
    return get_app_dir() / "todos.db"


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_backend_dir() -> Path:
    return Path(__file__).resolve().parent


def get_config_path() -> Path:
    """获取全局统一 JSON 配置文件路径 (存储在 %APPDATA%\\Todo Agent\\config.json)"""
    app_cfg = get_app_dir() / "config.json"
    if not app_cfg.exists():
        # 如果用户目录中尚无配置文件，尝试从项目目录或模板初始化
        for candidate in [
            get_backend_dir() / "config.json",
            get_backend_dir() / "config.example.json",
            get_project_root() / "config.json",
        ]:
            if candidate.exists():
                try:
                    import shutil
                    shutil.copy2(candidate, app_cfg)
                    return app_cfg
                except Exception:
                    pass
    return app_cfg


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
