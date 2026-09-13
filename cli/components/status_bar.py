from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from ..utils import get_terminal_width, truncate_to_width, pad_to_width, display_width
from ..config import load_cli_config, save_cli_config

if TYPE_CHECKING:
    from .slash import LlmConfig

STATUS_BAR_CONFIG_KEY = "cli_statusbar_items"

STATUS_BAR_OPTIONS: List[Dict[str, str]] = [
    {"id": "status", "title": "运行状态", "desc": "显示系统状态，如 [就绪]"},
    {"id": "mode", "title": "工作模式", "desc": "显示当前工作模式，如 [模式: 助理]"},
    {"id": "model", "title": "AI模型", "desc": "显示当前供应商与模型，如 [模型: deepseek]"},
    {"id": "think", "title": "思考模式", "desc": "显示思考推理状态，如 [思考: 关]"},
    {"id": "key", "title": "API Key", "desc": "显示 Key 配置状态，如 [Key: 已配置]"},
    {"id": "todo", "title": "待办统计", "desc": "显示未完成/总待办数，如 [待办: 2/5]"},
    {"id": "help", "title": "帮助提示", "desc": "显示快捷提示，如 /help"},
]

DEFAULT_STATUS_BAR_ITEMS: List[str] = [opt["id"] for opt in STATUS_BAR_OPTIONS]


def load_status_bar_items(db: Any = None) -> List[str]:
    """加载已启用的状态栏项列表，优先从 cli/config.json 读取"""
    try:
        cfg = load_cli_config()
        status_bar_cfg = cfg.get("status_bar", {})
        items = status_bar_cfg.get("items")
        if isinstance(items, list):
            valid_ids = {opt["id"] for opt in STATUS_BAR_OPTIONS}
            filtered = [item for item in items if item in valid_ids]
            if filtered:
                return filtered
    except Exception:
        pass
    return list(DEFAULT_STATUS_BAR_ITEMS)


def save_status_bar_items(db: Any = None, items: Optional[List[str]] = None) -> None:
    """保存已启用的状态栏项列表到 cli/config.json"""
    if items is None:
        return
    valid_ids = {opt["id"] for opt in STATUS_BAR_OPTIONS}
    filtered = [item for item in items if item in valid_ids]
    try:
        cfg = load_cli_config()
        if "status_bar" not in cfg or not isinstance(cfg["status_bar"], dict):
            cfg["status_bar"] = {}
        cfg["status_bar"]["items"] = filtered
        save_cli_config(cfg)
    except Exception:
        pass


def get_status_blocks(
    db: Any,
    llm_cfg: LlmConfig,
    current_mode: Dict[str, Any],
    enabled_items: Optional[List[str]] = None,
    is_compact: bool = False,
) -> List[str]:
    """获取所有启用的状态简报块"""
    if enabled_items is None:
        enabled_items = DEFAULT_STATUS_BAR_ITEMS
    enabled_set = set(enabled_items)

    blocks: List[str] = []

    # 1. 待办统计
    todo_badge = "0/0"

    # 2. 状态与模式
    mode_label = current_mode.get("display_name", "Agent助理")
    status_label = current_mode.get("status_text", "就绪")

    # 3. 模型
    prov = llm_cfg.provider or "默认"
    model_name = llm_cfg.model or "未选择"
    model_max_len = 10 if is_compact else 18
    short_model = truncate_to_width(model_name, model_max_len)

    # 4. Key 状态
    is_ollama = (llm_cfg.provider or "").lower() == "ollama" or "11434" in (llm_cfg.base_url or "")
    if is_ollama:
        key_badge = "CloudKey" if (llm_cfg.api_key and llm_cfg.api_key.strip()) else "免Key"
    else:
        key_badge = "已配" if (llm_cfg.api_key and llm_cfg.api_key.strip()) else "无Key"

    # 5. 思考开关
    think_badge = "开" if llm_cfg.enable_thinking else "关"

    for item_id in enabled_items:
        if item_id == "status":
            blocks.append(f"[{status_label}]")
        elif item_id == "mode":
            blocks.append(f"[{mode_label}]")
        elif item_id == "model":
            blocks.append(f"[{prov}:{short_model}]")
        elif item_id == "think":
            blocks.append(f"[思考:{think_badge}]")
        elif item_id == "key":
            blocks.append(f"[Key:{key_badge}]")
        elif item_id == "todo":
            blocks.append(f"[待办:{todo_badge}]")
        elif item_id == "help":
            blocks.append("/help")

    return blocks


def format_status_text(
    db: DbState,
    llm_cfg: LlmConfig,
    current_mode: Dict[str, Any],
    enabled_items: Optional[List[str]] = None,
    cols: Optional[int] = None,
) -> str:
    """生成统一的状态栏独立单行文本（自适应宽度，绝不超宽折行）"""
    term_w = max(20, (cols or get_terminal_width()) - 2)
    blocks = get_status_blocks(db, llm_cfg, current_mode, enabled_items, is_compact=(term_w < 90))
    if not blocks:
        return ""
    raw = "  ".join(blocks)
    content = f"  {raw}"
    if display_width(content) > term_w:
        return truncate_to_width(content, term_w)
    return content


def format_status_border(
    db: DbState,
    llm_cfg: LlmConfig,
    current_mode: Dict[str, Any],
    enabled_items: Optional[List[str]] = None,
    cols: Optional[int] = None,
) -> str:
    """
    生成带横线装饰的状态栏边框字符串，浑然一体地作为输入框底部边框：
    例: ── [就绪] ─ [Agent助理] ─ [deepseek] ─ [待办: 0/0] ──────────
    """
    target_cols = max(20, (cols or get_terminal_width()) - 2)
    blocks = get_status_blocks(db, llm_cfg, current_mode, enabled_items, is_compact=(target_cols < 90))
    if not blocks:
        return "─" * target_cols

    # 构造胶囊连接文本
    content = " ─ ".join(blocks)
    wrapped = f"── {content} ──"
    w = display_width(wrapped)

    if w > target_cols:
        # 超宽时逐项精简并截断
        return truncate_to_width(wrapped, target_cols)

    # 剩余空间用横线补齐
    remaining = target_cols - w
    return wrapped + ("─" * remaining)


def create_bottom_toolbar_getter(
    db: DbState,
    llm_cfg: LlmConfig,
    current_mode: Dict[str, Any],
    status_bar_state: Optional[Dict[str, Any]] = None,
):
    """动态生成 prompt_toolkit 输入框底部边框工具栏 getter"""
    def get_bottom_toolbar():
        cols = get_terminal_width()
        items = status_bar_state.get("items") if status_bar_state else None
        border_text = format_status_border(db, llm_cfg, current_mode, enabled_items=items, cols=cols)
        return [("class:border", border_text)]

    return get_bottom_toolbar


# 兼容别名
create_status_bar_getter = create_bottom_toolbar_getter
