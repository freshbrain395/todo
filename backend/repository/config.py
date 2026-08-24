from typing import Optional, Any
from backend.config import read_raw_config, write_raw_config
from backend.repository.db import DbState


def get_config(db: Optional[DbState], key: str) -> Optional[str]:
    """从 config.json 的 app_config 中获取配置"""
    data = read_raw_config()
    app_cfg = data.get("app_config", {})
    if isinstance(app_cfg, dict) and key in app_cfg:
        val = app_cfg[key]
        return str(val) if val is not None else None
    return None


def save_config(db: Optional[DbState], key: str, value: str) -> None:
    """保存配置到 config.json 的 app_config 中"""
    data = read_raw_config()
    if "app_config" not in data or not isinstance(data["app_config"], dict):
        data["app_config"] = {}
    data["app_config"][key] = value
    write_raw_config(data)
