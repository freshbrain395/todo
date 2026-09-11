"""CLI status toolbar component."""

from typing import Any, Dict
from ..layout import get_terminal_width, truncate_to_width
from backend.repository.db import DbState
from backend.service.todo import TodoService
from backend.service.ai import LlmConfig


def format_status_text(db: DbState, llm_cfg: LlmConfig, current_mode: Dict[str, Any]) -> str:
    """生成统一的状态栏纯文本（灰色、无背景，支持窄屏 Compact 模式）"""
    try:
        todo_svc = TodoService(db)
        all_todos = todo_svc.get_todos("all", "")
        total_cnt = len(all_todos)
        pending_cnt = sum(1 for t in all_todos if not t["completed"])
        todo_badge = f"{pending_cnt}/{total_cnt}"
    except Exception:
        todo_badge = "-/-"

    mode_label = current_mode.get("display_name", "聊天模式")
    prov = llm_cfg.provider or "默认"
    model_name = llm_cfg.model or "未选择"
    status_label = current_mode.get("status_text", "就绪")

    is_ollama = (llm_cfg.provider or "").lower() == "ollama" or "11434" in (llm_cfg.base_url or "")
    if is_ollama:
        key_badge = "已配CloudKey" if (llm_cfg.api_key and llm_cfg.api_key.strip()) else "免Key(可选)"
    else:
        key_badge = "已配置" if (llm_cfg.api_key and llm_cfg.api_key.strip()) else "未设置"

    think_badge = "开" if llm_cfg.enable_thinking else "关"
    term_w = get_terminal_width()

    # 紧凑窄屏模式
    if term_w < 85:
        short_model = truncate_to_width(model_name, 10)
        return f"[{status_label}] | {mode_label} | {short_model} | 思考:{think_badge} | {todo_badge} | /help"
    elif term_w < 115:
        short_model = truncate_to_width(model_name, 16)
        return (
            f" [{status_label}] "
            f"| [{mode_label}] "
            f"| [{prov}:{short_model}] "
            f"| [思考:{think_badge}] "
            f"| [Key:{key_badge}] "
            f"| [待办:{todo_badge}]"
        )
    else:
        # 宽屏模式
        short_model = truncate_to_width(model_name, 26)
        return (
            f" [状态: {status_label}] "
            f"| [模式: {mode_label}] "
            f"| [模型: {prov}:{short_model}] "
            f"| [思考: {think_badge}] "
            f"| [Key: {key_badge}] "
            f"| [待办: {todo_badge}] "
            f"| /help 帮助"
        )


def create_bottom_toolbar_getter(
    db: DbState,
    llm_cfg: LlmConfig,
    current_mode: Dict[str, Any],
):
    """动态生成 prompt_toolkit CLI 底部状态栏"""
    def get_toolbar():
        return [("class:toolbar-gray", format_status_text(db, llm_cfg, current_mode))]

    return get_toolbar
