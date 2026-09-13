"""CLI status bar component (底部状态栏组件)."""

import json
from typing import Any, Dict, List, Optional
from ..app import get_terminal_width, truncate_to_width, pad_to_width, display_width
from backend.repository.db import DbState
from backend.service.config import ConfigService
from backend.service.todo import TodoService
from backend.service.ai import LlmConfig

STATUS_BAR_CONFIG_KEY = "cli_statusbar_items"

STATUS_BAR_OPTIONS: List[Dict[str, str]] = [
    {"id": "status", "title": "运行状态", "desc": "显示系统状态，如 [就绪]"},
    {"id": "mode", "title": "工作模式", "desc": "显示当前工作模式，如 [模式: 聊天模式]"},
    {"id": "model", "title": "AI模型", "desc": "显示当前供应商与模型，如 [模型: siliconflow:deepseek]"},
    {"id": "think", "title": "思考模式", "desc": "显示思考推理状态，如 [思考: 关]"},
    {"id": "key", "title": "API Key", "desc": "显示 Key 配置状态，如 [Key: 已配置]"},
    {"id": "todo", "title": "待办统计", "desc": "显示未完成/总待办数，如 [待办: 2/5]"},
    {"id": "help", "title": "帮助提示", "desc": "显示快捷提示，如 /help 帮助"},
]

DEFAULT_STATUS_BAR_ITEMS: List[str] = [opt["id"] for opt in STATUS_BAR_OPTIONS]


def load_status_bar_items(db: DbState) -> List[str]:
    """从数据库加载已启用的状态栏项列表"""
    try:
        cfg = ConfigService(db).get_config(STATUS_BAR_CONFIG_KEY)
        if cfg:
            data = json.loads(cfg)
            if isinstance(data, list):
                valid_ids = {opt["id"] for opt in STATUS_BAR_OPTIONS}
                items = [item for item in data if item in valid_ids]
                if items:
                    return items
    except Exception:
        pass
    return list(DEFAULT_STATUS_BAR_ITEMS)


def save_status_bar_items(db: DbState, items: List[str]) -> None:
    """保存已启用的状态栏项列表到数据库"""
    valid_ids = {opt["id"] for opt in STATUS_BAR_OPTIONS}
    filtered = [item for item in items if item in valid_ids]
    ConfigService(db).save_config(STATUS_BAR_CONFIG_KEY, json.dumps(filtered, ensure_ascii=False))


def format_status_text(
    db: DbState,
    llm_cfg: LlmConfig,
    current_mode: Dict[str, Any],
    enabled_items: Optional[List[str]] = None,
) -> str:
    """
    生成统一的状态栏纯文本（灰色、无背景）。
    对齐排版规则：
    1. 若未启用任何项：返回空字符串。
    2. 若仅显示 1 项：显示在左侧。
    3. 若显示 2 项或更多：
       - 若总宽度未超出终端列宽：中心对齐。
       - 若超出终端列宽（放不下）：从左往右显示，并在终端边缘截断。
    """
    if enabled_items is None:
        enabled_items = DEFAULT_STATUS_BAR_ITEMS
    enabled_set = set(enabled_items)

    term_w = get_terminal_width()
    is_compact = term_w < 90

    # 准备各状态数据
    # 1. 待办统计
    todo_badge = "-/-"
    if "todo" in enabled_set:
        try:
            todo_svc = TodoService(db)
            all_todos = todo_svc.get_todos("all", "")
            total_cnt = len(all_todos)
            pending_cnt = sum(1 for t in all_todos if not t["completed"])
            todo_badge = f"{pending_cnt}/{total_cnt}"
        except Exception:
            todo_badge = "-/-"

    # 2. 状态与模式
    mode_label = current_mode.get("display_name", "聊天模式")
    status_label = current_mode.get("status_text", "就绪")

    # 3. 模型
    prov = llm_cfg.provider or "默认"
    model_name = llm_cfg.model or "未选择"
    model_max_len = 12 if is_compact else 22
    short_model = truncate_to_width(model_name, model_max_len)

    # 4. Key 状态
    is_ollama = (llm_cfg.provider or "").lower() == "ollama" or "11434" in (llm_cfg.base_url or "")
    if is_ollama:
        key_badge = "已配CloudKey" if (llm_cfg.api_key and llm_cfg.api_key.strip()) else "免Key(可选)"
    else:
        key_badge = "已配置" if (llm_cfg.api_key and llm_cfg.api_key.strip()) else "未设置"

    # 5. 思考开关
    think_badge = "开" if llm_cfg.enable_thinking else "关"

    # 构建各个状态块
    blocks: List[str] = []
    for item_id in enabled_items:
        if item_id == "status":
            blocks.append(f"[{status_label}]" if is_compact else f"[状态: {status_label}]")
        elif item_id == "mode":
            blocks.append(f"[{mode_label}]" if is_compact else f"[模式: {mode_label}]")
        elif item_id == "model":
            blocks.append(f"[{prov}:{short_model}]" if is_compact else f"[模型: {prov}:{short_model}]")
        elif item_id == "think":
            blocks.append(f"[思考:{think_badge}]" if is_compact else f"[思考: {think_badge}]")
        elif item_id == "key":
            blocks.append(f"[Key:{key_badge}]" if is_compact else f"[Key: {key_badge}]")
        elif item_id == "todo":
            blocks.append(f"[待办:{todo_badge}]" if is_compact else f"[待办: {todo_badge}]")
        elif item_id == "help":
            blocks.append("/help" if is_compact else "/help 帮助")

    if not blocks:
        return ""

    # 单项：显示在左侧
    if len(blocks) == 1:
        text = f" {blocks[0]}"
        if display_width(text) > term_w:
            return truncate_to_width(text, term_w)
        return text

    # 两项或更多
    raw_content = " | ".join(blocks)
    content_with_padding = f" {raw_content} "
    text_w = display_width(content_with_padding)

    if text_w <= term_w:
        # 放得下：中心对齐
        return pad_to_width(content_with_padding, term_w, align="center")
    else:
        # 放不下：从左往右显示，并按终端宽度截断
        return truncate_to_width(content_with_padding, term_w)


def create_status_bar_getter(
    db: DbState,
    llm_cfg: LlmConfig,
    current_mode: Dict[str, Any],
    status_bar_state: Optional[Dict[str, Any]] = None,
):
    """动态生成 prompt_toolkit CLI 底部状态栏 getter"""
    def get_status_bar():
        items = status_bar_state.get("items") if status_bar_state else None
        return [("class:toolbar-gray", format_status_text(db, llm_cfg, current_mode, enabled_items=items))]

    return get_status_bar


# 保持兼容别名
create_bottom_toolbar_getter = create_status_bar_getter
