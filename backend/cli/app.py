import os
import sys
import json
import asyncio
from typing import List, Optional, Dict, Any, Tuple, Callable
from prompt_toolkit import PromptSession as _PromptSession
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from prompt_toolkit.filters import has_completions
from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout.menus import CompletionsMenuControl, _get_menu_item_fragments
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from .layout import (
    get_terminal_width,
    is_compact_terminal,
    display_width,
    truncate_to_width,
    pad_to_width,
)

console = Console(force_terminal=True, legacy_windows=False)

from backend.repository.db import DbState
from backend.service.todo import TodoService
from backend.service.config import ConfigService
from backend.service.ai_config import AiConfigService
from backend.service.display_config import DisplayConfigService
from backend.service.ai import (
    LlmConfig,
    fetch_models,
    parse_intent_and_execute,
    DEFAULT_AGENT_PROMPT,
    DEFAULT_CHAT_PROMPT,
    DEFAULT_JSON_PROMPT,
)

SLASH_COMMANDS = [
    ("/help", "显示可用命令帮助"),
    ("/mode", "切换工作模式 (chat / agent / json)"),
    ("/todo", "创建待办任务 (/todo <标题>)"),
    ("/add", "新建待办任务 (/add <标题>)"),
    ("/list", "查看待办任务 (/list [all|pending|completed] [关键词])"),
    ("/done", "完成待办任务 (/done <ID>)"),
    ("/undone", "撤销完成状态 (/undone <ID>)"),
    ("/delete", "删除待办任务 (/delete <ID>)"),
    ("/chat", "切换到常规 AI 聊天模式 (alias: /mode chat)"),
    ("/agent", "切换并进入 Agent 角色模式 (alias: /mode agent)"),
    ("/prompt", "选择并执行 Prompt 模板"),
    ("/skill", "切换并启用 Skill 技能模式"),
    ("/provider", "管理/切换供应商与配置 API Key (上下箭头选择)"),
    ("/model", "查看/切换当前 LLM 模型 (上下箭头选择)"),
    ("/think", "开关或切换 AI 思考模式 (/think [on|off|toggle])"),
    ("/clear", "清空当前对话上下文历史"),
    ("/cls", "清空控制台屏幕"),
    ("/quit", "退出命令行程序"),
    ("/exit", "退出命令行程序"),
]

# 纯无背景色、全灰色字体样式，补全菜单完全融入终端背景，选中项仅改变前景色
CLI_STYLE = Style.from_dict({
    "bottom-toolbar": "noreverse noinherit bg:default fg:#7f848e",
    "toolbar-gray": "noreverse noinherit bg:default fg:#7f848e",
    "menu-title": "#61afef bold",
    "menu-selected": "#98c379 bold",
    "menu-item": "#abb2bf",
    "menu-dim": "#5c6370",
    # prompt_toolkit 补全菜单样式：纯透明无背景，普通项灰色，当前选中项绿色加粗
    "completion-menu": "bg:default fg:default",
    "completion-menu.completion": "noinherit bg:default fg:#7f848e",
    "completion-menu.completion.current": "noinherit noreverse bg:default fg:#98c379 bold",
    "completion-menu.meta.completion": "noinherit bg:default fg:#5c6370",
    "completion-menu.meta.completion.current": "noinherit noreverse bg:default fg:#98c379",
    "scrollbar": "noinherit bg:default",
    "scrollbar.background": "noinherit bg:default",
    "scrollbar.button": "noinherit bg:default",
    "scrollbar.arrow": "noinherit bg:default",
    "scrollbar.start": "noinherit bg:default nounderline",
    "scrollbar.end": "noinherit bg:default nounderline",
})

# 各供应商常用推荐模型备选表
FALLBACK_MODELS = {
    "deepseek": ["deepseek-chat", "deepseek-reasoner"],
    "siliconflow": [
        "deepseek-ai/DeepSeek-V3",
        "deepseek-ai/DeepSeek-R1",
        "Qwen/Qwen2.5-7B-Instruct",
        "Qwen/Qwen2.5-14B-Instruct",
        "Pro/deepseek-ai/DeepSeek-V3",
    ],
    "openai": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "o1-mini"],
    "ollama": ["llama3:latest", "qwen2.5:latest", "deepseek-r1:latest", "mistral:latest"],
}


class PromptSession(_PromptSession):
    """Enable completion menus to appear automatically while typing and keep menu position fixed."""

    def __init__(self, *args: Any, **kwargs: Any):
        kwargs.setdefault("complete_while_typing", True)
        try:
            super().__init__(*args, **kwargs)
        except Exception:
            if "output" not in kwargs:
                try:
                    from prompt_toolkit.output import DummyOutput
                    kwargs["output"] = DummyOutput()
                    super().__init__(*args, **kwargs)
                except Exception:
                    raise
            else:
                raise
        self._fix_menu_floats()

    def _fix_menu_floats(self) -> None:
        """保持补全菜单水平位置固定在左侧，不随光标向右位移。"""
        def _walk(container: Any) -> None:
            from prompt_toolkit.layout.containers import FloatContainer
            if isinstance(container, FloatContainer):
                for f in container.floats:
                    if f.xcursor:
                        f.xcursor = False
                        f.left = 0
            for child in getattr(container, "get_children", lambda: [])():
                _walk(child)

        try:
            _walk(self.layout.container)
        except Exception:
            pass


class SlashCommandCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # /mode 二级补全
        if text == "/mode" or text.startswith("/mode "):
            sub = "" if text == "/mode" else text[len("/mode "):].lower()
            options = [
                ("chat", "普通聊天模式"),
                ("agent", "Todo Agent 助理模式"),
                ("json", "严格 JSON 输出模式"),
            ]
            for opt, desc in options:
                if opt.startswith(sub):
                    replacement = f"/mode {opt}"
                    if text == replacement:
                        replacement = f"/mode {opt} "
                    yield Completion(
                        replacement,
                        start_position=-len(text),
                        display=f"{opt:<12} {desc}",
                    )
            return

        # /think 二级补全
        if text == "/think" or text.startswith("/think "):
            sub = "" if text == "/think" else text[len("/think "):].lower()
            options = [
                ("toggle", "切换思考模式开关"),
                ("on", "开启思考模式 (Thinking)"),
                ("off", "关闭思考模式"),
            ]
            for opt, desc in options:
                if opt.startswith(sub):
                    replacement = f"/think {opt}"
                    if text == replacement:
                        replacement = f"/think {opt} "
                    yield Completion(
                        replacement,
                        start_position=-len(text),
                        display=f"{opt:<12} {desc}",
                    )
            return

        # /list 二级补全
        if text == "/list" or text.startswith("/list "):
            sub = "" if text == "/list" else text[len("/list "):].lower()
            options = [
                ("all", "查看全部待办任务"),
                ("pending", "查看未完成待办任务"),
                ("completed", "查看已完成待办任务"),
            ]
            for opt, desc in options:
                if opt.startswith(sub):
                    replacement = f"/list {opt}"
                    if text == replacement:
                        replacement = f"/list {opt} "
                    yield Completion(
                        replacement,
                        start_position=-len(text),
                        display=f"{opt:<12} {desc}",
                    )
            return

        # /provider 二级补全
        if text == "/provider" or text.startswith("/provider "):
            sub = "" if text == "/provider" else text[len("/provider "):].lower()
            options = [
                ("custom", "自定义 AI 供应商管理 (添加/修改/删除)"),
                ("ollama", "切换至 Ollama 本地供应商"),
                ("deepseek", "切换至 DeepSeek 官方供应商"),
                ("openai", "切换至 OpenAI 官方供应商"),
            ]
            for opt, desc in options:
                if opt.startswith(sub):
                    replacement = f"/provider {opt}"
                    if text == replacement:
                        replacement = f"/provider {opt} "
                    yield Completion(
                        replacement,
                        start_position=-len(text),
                        display=f"{opt:<12} {desc}",
                    )
            return

        # /model 二级补全
        if text == "/model" or text.startswith("/model "):
            sub = "" if text == "/model" else text[len("/model "):].lower()
            options = [
                ("deepseek-chat", "DeepSeek 通用模型"),
                ("gpt-4o-mini", "OpenAI 轻量快速模型"),
                ("gpt-4o", "OpenAI 旗舰推理模型"),
                ("llama3:latest", "Ollama 开源本地模型"),
            ]
            for opt, desc in options:
                if opt.startswith(sub):
                    replacement = f"/model {opt}"
                    if text == replacement:
                        replacement = f"/model {opt} "
                    yield Completion(
                        replacement,
                        start_position=-len(text),
                        display=f"{opt:<16} {desc}",
                    )
            return

        # /prompt 二级补全
        if text == "/prompt" or text.startswith("/prompt "):
            sub = "" if text == "/prompt" else text[len("/prompt "):].lower()
            options = [
                ("p1", "任务拆解助手 (多步目标细化)"),
                ("p2", "GTD 每日复盘 (任务检视与反思)"),
                ("p3", "四象限优先级评估 (重要紧急度梳理)"),
            ]
            for opt, desc in options:
                if opt.startswith(sub):
                    replacement = f"/prompt {opt}"
                    if text == replacement:
                        replacement = f"/prompt {opt} "
                    yield Completion(
                        replacement,
                        start_position=-len(text),
                        display=f"{opt:<12} {desc}",
                    )
            return

        # /skill 二级补全
        if text == "/skill" or text.startswith("/skill "):
            sub = "" if text == "/skill" else text[len("/skill "):].lower()
            options = [
                ("skill-gtd", "GTD 时间管理与任务梳理导师"),
                ("skill-pomodoro", "番茄工作法与专注节奏教练"),
                ("skill-review", "待办进度与周度复盘专家"),
            ]
            for opt, desc in options:
                if opt.startswith(sub):
                    replacement = f"/skill {opt}"
                    if text == replacement:
                        replacement = f"/skill {opt} "
                    yield Completion(
                        replacement,
                        start_position=-len(text),
                        display=f"{opt:<16} {desc}",
                    )
            return

        # 一级 Slash 命令补全
        if text.startswith("/"):
            query = text.lower().strip()
            term_w = get_terminal_width()
            has_exact = any(c.lower() == query for c, _ in SLASH_COMMANDS)
            has_prefix = any(
                c.lower().startswith(query) and c.lower() != query
                for c, _ in SLASH_COMMANDS
            )
            for cmd, desc in SLASH_COMMANDS:
                exact = cmd.lower() == query
                prefix = cmd.lower().startswith(query)
                desc_match = query.lstrip("/") in desc.lower()
                if has_exact:
                    matched = exact
                elif has_prefix:
                    matched = prefix
                else:
                    matched = prefix or desc_match

                if matched:
                    if term_w < 80:
                        max_desc_w = max(10, term_w - 20)
                        disp_desc = truncate_to_width(desc, max_desc_w)
                        display_text = f"{cmd:<10} {disp_desc}"
                    else:
                        display_text = f"{cmd:<12} {desc}"

                    if exact:
                        rep = f"{cmd} " if text == cmd else cmd
                    else:
                        rep = cmd

                    yield Completion(rep, start_position=-len(text), display=display_text, display_meta="")


# 增强 CompletionsMenuControl：当用户刚弹出补全列表（complete_index 为 None）时，首项默认以高亮选中样式显示
_orig_create_content = CompletionsMenuControl.create_content


def _custom_completions_menu_create_content(self, width: int, height: int):
    content = _orig_create_content(self, width, height)
    complete_state = get_app().current_buffer.complete_state
    if complete_state and complete_state.completions:
        effective_index = (
            0 if complete_state.complete_index is None else complete_state.complete_index
        )
        completions = complete_state.completions
        menu_width = self._get_menu_width(width, complete_state)
        menu_meta_width = self._get_menu_meta_width(width - menu_width, complete_state)
        show_meta = self._show_meta(complete_state)

        def get_line(i: int):
            c = completions[i]
            is_current = i == effective_index
            res = _get_menu_item_fragments(c, is_current, menu_width, space_after=True)
            if show_meta:
                res += self._get_menu_item_meta_fragments(c, is_current, menu_meta_width)
            return res

        content.get_line = get_line
    return content


CompletionsMenuControl.create_content = _custom_completions_menu_create_content


def create_cli_key_bindings() -> KeyBindings:
    """创建 CLI 专属按键绑定：补全弹出时 ↑/↓ 平滑循环切换，Enter 选中当前/首项并直接执行"""
    kb = KeyBindings()

    @kb.add("down", filter=has_completions)
    def _(event):
        b = event.current_buffer
        if b.complete_state and b.complete_state.completions:
            total = len(b.complete_state.completions)
            cur = 0 if b.complete_state.complete_index is None else b.complete_state.complete_index
            next_idx = (cur + 1) % total
            b.go_to_completion(next_idx)

    @kb.add("up", filter=has_completions)
    def _(event):
        b = event.current_buffer
        if b.complete_state and b.complete_state.completions:
            total = len(b.complete_state.completions)
            cur = 0 if b.complete_state.complete_index is None else b.complete_state.complete_index
            prev_idx = (cur - 1) % total
            b.go_to_completion(prev_idx)

    @kb.add("enter", filter=has_completions)
    def _(event):
        b = event.current_buffer
        if b.complete_state and b.complete_state.completions:
            idx = 0 if b.complete_state.complete_index is None else b.complete_state.complete_index
            b.apply_completion(b.complete_state.completions[idx])
            b.complete_state = None
        b.validate_and_handle()

    return kb


def print_banner(display_cfg, current_mode_name: str = "agent"):
    banner_text = "[bold cyan]Todo Agent CLI[/bold cyan]\n"
    banner_text += f"[dim]当前模式：[bold green]{current_mode_name}[/bold green] | 输入 [green]/mode[/green] 查看或切换模式\n直接输入自然语言对话或管理待办，输入 [green]/help[/green] 查看全部命令[/dim]"
    console.print(Panel(banner_text, border_style="cyan", padding=(0, 2)))


async def show_help():
    """交互式显示可用 Slash 命令帮助，支持上下箭头浏览，Esc/q 返回"""
    items = [
        {"id": cmd, "cmd": cmd, "desc": desc}
        for cmd, desc in SLASH_COMMANDS
    ]
    term_w = get_terminal_width(fallback=80)
    cmd_w = 12 if term_w >= 80 else 10

    def render_cmd(it: Dict[str, Any]) -> str:
        c = it["cmd"]
        d = it["desc"]
        if term_w < 80:
            max_d_w = max(10, term_w - cmd_w - 6)
            d = truncate_to_width(d, max_d_w)
        return f"{c:<{cmd_w}} {d}"

    await run_interactive_selection_menu(
        title="📌 常用 Slash 命令帮助",
        items=items,
        key_fn=lambda it: it["id"],
        render_item_fn=render_cmd,
        extra_bindings={"q": "cancel", "Q": "cancel"},
        help_hint="↑/↓ 浏览 | Esc/q 返回",
        max_visible_items=12,
    )


def list_todos(db: DbState, filter_type: str = "all", search: str = ""):
    service = TodoService(db)
    todos = service.get_todos(filter_type, search)
    if not todos:
        if filter_type != "all" or search:
            console.print("[yellow]未找到符合条件的待办任务。[/yellow]")
        else:
            console.print("[yellow]当前待办列表为空，使用 /add <标题> 新建一个吧！[/yellow]")
        return

    term_w = get_terminal_width()
    table = Table(title="📋 待办事项列表", title_style="bold blue")

    if term_w < 90:
        # 窄终端模式：精简列，主要空间留给标题
        table.add_column("ID", style="dim", width=4)
        table.add_column("状态", width=6)
        table.add_column("优先", width=6)
        table.add_column("标题", style="bold")

        for t in todos:
            status = "[green]✓完[/green]" if t["completed"] else "[yellow]○待[/yellow]"
            pri = t["priority"]
            pri_style = (
                "[red]🔴高[/red]"
                if pri == "high"
                else ("[yellow]🟡中[/yellow]" if pri == "medium" else "[green]🟢低[/green]")
            )
            table.add_row(
                str(t["id"]),
                status,
                pri_style,
                t["title"],
            )
    elif term_w < 120:
        # 中等宽度模式：显示分类与提醒，适度控制列宽
        table.add_column("ID", style="dim", width=5)
        table.add_column("状态", width=7)
        table.add_column("优先级", width=8)
        table.add_column("分类", width=8)
        table.add_column("标题", style="bold")
        table.add_column("提醒", style="dim", width=12)

        for t in todos:
            status = "[green]✓ 完成[/green]" if t["completed"] else "[yellow]○ 待办[/yellow]"
            pri = t["priority"]
            pri_style = (
                "[red]🔴 高[/red]"
                if pri == "high"
                else ("[yellow]🟡 中[/yellow]" if pri == "medium" else "[green]🟢 低[/green]")
            )
            remind = (t["remind_at"] or "-")
            if len(remind) > 12:
                remind = remind[:10] + ".."
            table.add_row(
                str(t["id"]),
                status,
                pri_style,
                t["category"],
                t["title"],
                remind,
            )
    else:
        # 宽终端模式：全列展开，标题弹性延伸
        table.add_column("ID", style="dim", width=6)
        table.add_column("状态", width=8)
        table.add_column("优先级", width=10)
        table.add_column("分类", width=12)
        table.add_column("标题", style="bold")
        table.add_column("提醒时间", style="dim", width=20)

        for t in todos:
            status = "[green]✓ 完成[/green]" if t["completed"] else "[yellow]○ 待办[/yellow]"
            pri = t["priority"]
            pri_style = (
                "[red]🔴 高[/red]"
                if pri == "high"
                else ("[yellow]🟡 中[/yellow]" if pri == "medium" else "[green]🟢 低[/green]")
            )
            remind = t["remind_at"] or "-"
            table.add_row(
                str(t["id"]),
                status,
                pri_style,
                t["category"],
                t["title"],
                remind,
            )

    console.print(table)


def load_current_llm_config(db: DbState) -> LlmConfig:
    cfg_service = ConfigService(db)
    raw = cfg_service.get_config("llm_config_v2")
    if raw:
        try:
            d = json.loads(raw)
            return LlmConfig(
                provider=d.get("provider", "siliconflow"),
                base_url=d.get("base_url", "https://api.siliconflow.cn/v1"),
                api_key=d.get("api_key", ""),
                model=d.get("model", "deepseek-ai/DeepSeek-V4-Flash"),
                enable_thinking=d.get("enable_thinking", False),
            )
        except Exception:
            pass
    return LlmConfig()


def save_current_llm_config(db: DbState, config: LlmConfig):
    cfg_service = ConfigService(db)
    cfg_service.save_config(
        "llm_config_v2",
        json.dumps(
            {
                "provider": config.provider,
                "base_url": config.base_url,
                "api_key": config.api_key,
                "model": config.model,
                "enable_thinking": config.enable_thinking,
            },
            ensure_ascii=False,
        ),
    )


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


async def run_interactive_selection_menu(
    title: str,
    items: List[Dict[str, Any]],
    current_id: Optional[str] = None,
    key_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
    render_item_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
    extra_bindings: Optional[Dict[str, str]] = None,
    help_hint: str = "↑/↓ 选择 | Enter 确认 | Esc 取消",
    max_visible_items: int = 12,
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    通用二级交互选择菜单组件：
    - 无边框纯净排版，选项统一新增缩进
    - 统一键盘交互 (↑/↓ 循环切换、Enter 确认、Esc 取消、支持扩展热键)
    - 统一选中与前景色高亮 (❯ 标记、[当前] 指示、全终端融入透明样式)
    - 支持长列表安全高度截断与平滑窗口滚动指示
    """
    if not items:
        return (None, None)

    _key = key_fn or (lambda it: str(it.get("id", "")))
    _render = render_item_fn or (lambda it: str(it.get("title") or it.get("name") or it.get("id") or ""))

    selected_index = [0]
    if current_id:
        target_cur = str(current_id).strip().lower()
        for idx, it in enumerate(items):
            if str(_key(it)).strip().lower() == target_cur:
                selected_index[0] = idx
                break

    action_holder: List[Optional[str]] = [None]
    result_holder: List[Optional[Dict[str, Any]]] = [None]

    kb = KeyBindings()

    @kb.add("up")
    def _(event):
        selected_index[0] = (selected_index[0] - 1) % len(items)
        event.app.invalidate()

    @kb.add("down")
    def _(event):
        selected_index[0] = (selected_index[0] + 1) % len(items)
        event.app.invalidate()

    @kb.add("enter")
    def _(event):
        action_holder[0] = "confirm"
        result_holder[0] = items[selected_index[0]]
        event.app.exit()

    @kb.add("escape")
    @kb.add("c-c")
    def _(event):
        action_holder[0] = "cancel"
        event.app.exit()

    if extra_bindings:
        for key_str, act_name in extra_bindings.items():
            @kb.add(key_str)
            def _(event, act=act_name):
                action_holder[0] = act
                result_holder[0] = items[selected_index[0]]
                event.app.exit()

    def get_text():
        term_w = get_terminal_width(fallback=80)
        max_w = max(20, term_w - 2)

        total = len(items)
        vis_count = min(total, max_visible_items)

        if total <= vis_count:
            start_i = 0
            end_i = total
        else:
            half = vis_count // 2
            if selected_index[0] < half:
                start_i = 0
                end_i = vis_count
            elif selected_index[0] >= total - (vis_count - half):
                start_i = total - vis_count
                end_i = total
            else:
                start_i = selected_index[0] - half
                end_i = start_i + vis_count

        all_lines: List[Tuple[str, str]] = []

        if start_i > 0:
            more_up = truncate_to_width("    ▲ 更多项目...", max_w)
            all_lines.append(("class:menu-dim", more_up))

        for idx in range(start_i, end_i):
            it = items[idx]
            it_key = str(_key(it)).strip().lower()
            is_cur = bool(current_id and it_key == str(current_id).strip().lower())
            is_sel = idx == selected_index[0]
            pointer = "❯ " if is_sel else "  "
            cur_tag = " [当前]" if is_cur else ""

            item_text = _render(it)
            raw_line = f"  {pointer}{item_text}{cur_tag}"
            line_str = truncate_to_width(raw_line, max_w)
            style = "class:menu-selected" if is_sel else "class:menu-item"
            all_lines.append((style, line_str))

        if end_i < total:
            more_down = truncate_to_width("    ▼ 更多项目...", max_w)
            all_lines.append(("class:menu-dim", more_down))

        hint_text = truncate_to_width(f"{title} [{help_hint}]", max_w)
        all_lines.append(("class:menu-title", hint_text))

        tokens = []
        for i, (style, text) in enumerate(all_lines):
            tokens.append((style, text + ("\n" if i < len(all_lines) - 1 else "")))
        return tokens

    total_vis = min(len(items), max_visible_items)
    scroll_extra = (1 if len(items) > max_visible_items else 0) * 2
    window_h = min(total_vis + 1 + scroll_extra, 16)

    control = FormattedTextControl(get_text)
    window = Window(content=control, height=window_h)
    try:
        app = Application(
            layout=Layout(HSplit([window])),
            key_bindings=kb,
            style=CLI_STYLE,
            full_screen=False,
            erase_when_done=True,
        )
    except Exception:
        from prompt_toolkit.output import DummyOutput
        app = Application(
            layout=Layout(HSplit([window])),
            key_bindings=kb,
            style=CLI_STYLE,
            full_screen=False,
            erase_when_done=True,
            output=DummyOutput(),
        )

    try:
        await app.run_async()
    except Exception:
        pass
    return (action_holder[0], result_holder[0])


async def select_provider_interactive(
    providers: List[Dict[str, Any]],
    current_id: str,
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """二级菜单：使用上下箭头选择 AI 供应商，支持 Enter 切换、e 编辑、d 删除(自定义)、或选择自定义供应商管理"""
    if not providers:
        return (None, None)

    custom_option = {
        "id": "__custom__",
        "name": "[⚙ 自定义供应商管理 (添加/管理)...]",
        "model": "",
        "base_url": "",
        "api_key": "",
    }
    all_items = list(providers) + [custom_option]

    def render_provider(p: Dict[str, Any]) -> str:
        if p.get("id") == "__custom__":
            return p.get("name", "")
        if p.get("id") == "ollama" or "11434" in (p.get("base_url") or ""):
            key_tag = "✓ 已配Key" if p.get("api_key") else "本地免Key"
        else:
            key_tag = "✓ 已配Key" if p.get("api_key") else "✗ 无Key"
        custom_tag = " [自定义]" if p.get("is_custom") else ""
        name = p.get("name", p.get("id"))
        model = p.get("model", "")
        return f"{name:<16} ({model}) [{key_tag}]{custom_tag}"

    action, selected = await run_interactive_selection_menu(
        title="🤖 选择 AI 供应商",
        items=all_items,
        current_id=current_id,
        key_fn=lambda it: str(it.get("id", "")),
        render_item_fn=render_provider,
        extra_bindings={
            "e": "edit", "E": "edit",
            "d": "delete", "D": "delete",
            "c": "custom", "C": "custom",
            "a": "custom", "A": "custom",
        },
        help_hint="↑/↓ 选择 | Enter 切换 | e 编辑 | d 删除(自定义) | c 自定义管理 | Esc 取消",
        max_visible_items=10,
    )
    if action in ("custom", "add"):
        return ("custom", None)
    elif action == "confirm":
        if selected and selected.get("id") == "__custom__":
            return ("custom", None)
        return ("switch", selected)
    elif action == "edit":
        if selected and selected.get("id") == "__custom__":
            return ("custom", None)
        return ("edit", selected)
    elif action == "delete":
        if selected and selected.get("id") == "__custom__":
            return ("custom", None)
        return ("delete", selected)
    return (None, None)


async def select_model_interactive(
    models: List[str],
    current_model: str,
) -> Optional[str]:
    """二级菜单：使用上下箭头选择 LLM 模型"""
    if not models:
        return None

    custom_option = "[➕ 输入自定义模型名称...]"
    all_models = list(models)
    if custom_option not in all_models:
        all_models.append(custom_option)

    items = [{"id": m, "name": m} for m in all_models]
    action, selected = await run_interactive_selection_menu(
        title="🧠 选择 LLM 模型",
        items=items,
        current_id=current_model,
        render_item_fn=lambda it: it["name"],
        help_hint="↑/↓ 选择 | Enter 确认 | Esc 取消",
        max_visible_items=12,
    )
    if action == "confirm" and selected:
        return selected["id"]
    return None


# 交互式模式选择菜单选项定义
MODE_OPTIONS = [
    ("chat", "普通聊天模式"),
    ("agent", "Todo Agent 助理模式"),
    ("json", "严格 JSON 输出模式"),
]


async def select_mode_interactive(current_mode_name: str = "chat") -> Optional[str]:
    """二级菜单：使用上下箭头选择工作模式"""
    items = [
        {"id": opt_name, "name": opt_name, "desc": opt_desc}
        for opt_name, opt_desc in MODE_OPTIONS
    ]
    action, selected = await run_interactive_selection_menu(
        title="🔄 选择工作模式",
        items=items,
        current_id=current_mode_name or "chat",
        render_item_fn=lambda it: f"{it['id']:<8} {it['desc']}",
        help_hint="↑/↓ 选择 | Enter 确认 | Esc 取消",
        max_visible_items=10,
    )
    if action == "confirm" and selected:
        return selected["id"]
    return None


async def select_think_interactive(current_thinking: bool = False) -> Optional[str]:
    """二级菜单：使用上下箭头选择 AI 思考模式状态"""
    items = [
        {"id": "toggle", "title": "快速切换开关", "desc": "在当前开/关状态之间快速反转"},
        {"id": "on", "title": "开启思考模式", "desc": "展示深度思考与推理过程 (Thinking)"},
        {"id": "off", "title": "关闭思考模式", "desc": "直接输出最终回答，加快响应速度"},
    ]
    cur_id = "on" if current_thinking else "off"
    action, selected = await run_interactive_selection_menu(
        title="💭 选择思考模式 (Thinking)",
        items=items,
        current_id=cur_id,
        render_item_fn=lambda it: f"{it['id']:<8} {it['title']:<16} {it['desc']}",
        help_hint="↑/↓ 选择 | Enter 确认 | Esc 取消",
        max_visible_items=10,
    )
    if action == "confirm" and selected:
        return selected["id"]
    return None


async def select_prompt_interactive(prompts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """二级菜单：使用上下箭头选择预设 Prompt 模板"""
    if not prompts:
        return None

    def render_pr(pr: Dict[str, Any]) -> str:
        pid = pr.get("id", "")
        title = pr.get("title", "")
        category = pr.get("category", "")
        return f"{pid:<8} {title:<18} [{category}]"

    action, selected = await run_interactive_selection_menu(
        title="📝 选择 Prompt 提示词模板",
        items=prompts,
        key_fn=lambda it: str(it.get("id", "")),
        render_item_fn=render_pr,
        help_hint="↑/↓ 选择 | Enter 执行 | Esc 取消",
        max_visible_items=10,
    )
    if action == "confirm":
        return selected
    return None


async def select_skill_interactive(skills: List[Dict[str, Any]], current_role: str = "") -> Optional[Dict[str, Any]]:
    """二级菜单：使用上下箭头选择 AI 技能角色"""
    if not skills:
        return None

    def render_sk(sk: Dict[str, Any]) -> str:
        sid = sk.get("id", "")
        title = sk.get("title", sid)
        desc = sk.get("description", "")
        return f"{sid:<14} {title:<16} {desc}"

    action, selected = await run_interactive_selection_menu(
        title="⚡ 选择 AI 技能角色 (Skills)",
        items=skills,
        current_id=current_role,
        key_fn=lambda it: str(it.get("id", "")),
        render_item_fn=render_sk,
        help_hint="↑/↓ 选择 | Enter 启用 | Esc 取消",
        max_visible_items=10,
    )
    if action == "confirm":
        return selected
    return None


def apply_mode_switch(target_mode: str, current_mode: Dict[str, Any]) -> bool:
    """统一应用模式切换逻辑"""
    m = target_mode.lower().strip()
    if m == "chat":
        current_mode["name"] = "chat"
        current_mode["role"] = "chat"
        current_mode["display_name"] = "聊天模式"
        current_mode["system_prompt"] = DEFAULT_CHAT_PROMPT
        current_mode["output_format"] = "text"
        console.print("[green]✓ 已切换到常规聊天模式。[/green]")
        return True
    elif m == "agent":
        current_mode["name"] = "agent"
        current_mode["role"] = "agent"
        current_mode["display_name"] = "Agent助理"
        current_mode["system_prompt"] = DEFAULT_AGENT_PROMPT
        current_mode["output_format"] = "text"
        console.print("[green]✓ 已切换到 Todo Agent 智能助理模式。[/green]")
        return True
    elif m == "json":
        current_mode["name"] = "json"
        current_mode["role"] = "json"
        current_mode["display_name"] = "JSON模式"
        current_mode["system_prompt"] = DEFAULT_JSON_PROMPT
        current_mode["output_format"] = "json"
        console.print("[green]✓ 已切换到结构化 JSON 模式。[/green]")
        return True
    return False



async def handle_command(
    cmd_line: str,
    db: DbState,
    llm_cfg: LlmConfig,
    history: List[Dict[str, str]],
    current_mode: Dict[str, Any],
    session: Optional[PromptSession] = None,
) -> bool:
    """返回 False 表示退出"""
    line = cmd_line.strip()
    if not line:
        return True

    todo_service = TodoService(db)
    ai_cfg_service = AiConfigService(db)
    display_cfg = DisplayConfigService.load()

    if line in ["/quit", "/exit"]:
        console.print("[dim]再见！感谢使用 Todo Agent。[/dim]")
        return False

    elif line in ["/cls", "/clear_screen"]:
        os.system("cls" if os.name == "nt" else "clear")
        print_banner(display_cfg)
        return True

    elif line == "/clear":
        history.clear()
        console.print("[green]已清空当前对话历史。[/green]")
        return True

    elif line == "/help":
        await show_help()
        return True

    elif line == "/list" or line.startswith("/list "):
        parts = line.split(maxsplit=2)
        filter_type = "all"
        search = ""
        if len(parts) == 2:
            arg = parts[1].strip()
            if arg.lower() in ["all", "pending", "completed"]:
                filter_type = arg.lower()
            else:
                search = arg
        elif len(parts) >= 3:
            first_arg = parts[1].strip().lower()
            if first_arg in ["all", "pending", "completed"]:
                filter_type = first_arg
                search = parts[2].strip()
            else:
                console.print(f"[red]错误: 非法的过滤类型 '{parts[1]}'. 可选类型: all, pending, completed (例如: /list pending 会议)[/red]")
                return True

        list_todos(db, filter_type=filter_type, search=search)
        return True

    elif line.startswith("/add ") or line.startswith("/todo "):
        title = line.split(" ", 1)[1].strip()
        if not title:
            console.print("[red]错误: 任务标题不能为空，例如: /add 写周报[/red]")
        else:
            new_id = todo_service.add_todo(title)
            console.print(f"[green]✓ 已成功添加任务 #{new_id}: {title}[/green]")
        return True

    elif line.startswith("/done "):
        id_str = line.split(" ", 1)[1].strip().lstrip("#")
        if id_str.isdigit():
            ok = todo_service.update_todo_status(int(id_str), True)
            if ok:
                console.print(f"[green]✓ 任务 #{id_str} 已标记为完成！[/green]")
            else:
                console.print(f"[yellow]未找到任务 #{id_str}[/yellow]")
        else:
            console.print("[red]错误: 请输入有效的任务 ID，例如: /done 1[/red]")
        return True

    elif line.startswith("/undone "):
        id_str = line.split(" ", 1)[1].strip().lstrip("#")
        if id_str.isdigit():
            ok = todo_service.update_todo_status(int(id_str), False)
            if ok:
                console.print(f"[green]✓ 任务 #{id_str} 已标记为未完成[/green]")
            else:
                console.print(f"[yellow]未找到任务 #{id_str}[/yellow]")
        else:
            console.print("[red]错误: 请输入有效的任务 ID，例如: /undone 1[/red]")
        return True

    elif line.startswith("/delete "):
        id_str = line.split(" ", 1)[1].strip().lstrip("#")
        if id_str.isdigit():
            ok = todo_service.delete_todo(int(id_str))
            if ok:
                console.print(f"[green]✓ 任务 #{id_str} 已删除[/green]")
            else:
                console.print(f"[yellow]未找到任务 #{id_str}[/yellow]")
        else:
            console.print("[red]错误: 请输入有效的任务 ID，例如: /delete 1[/red]")
        return True

    elif line == "/mode" or line.startswith("/mode "):
        parts = line.split(maxsplit=1)
        if len(parts) == 1:
            cur_name = current_mode.get("name", "chat")
            select_fn = getattr(sys.modules.get("backend.cli"), "select_mode_interactive", select_mode_interactive)
            selected = await select_fn(cur_name)
            if selected:
                apply_mode_switch(selected, current_mode)
            else:
                console.print("[dim]已取消模式选择。[/dim]")
            return True
        else:
            target_mode = parts[1].strip().lower()
            ok = apply_mode_switch(target_mode, current_mode)
            if not ok:
                console.print(f"[red]未知模式 '{target_mode}'。可选模式：chat, agent, json[/red]")
            return True

    elif line == "/chat":
        apply_mode_switch("chat", current_mode)
        return True

    elif line == "/agent" or line.startswith("/agent "):
        apply_mode_switch("agent", current_mode)
        return True

    elif line == "/model" or line.startswith("/model "):
        parts = line.split(maxsplit=1)
        if len(parts) == 1:
            # 尝试从当前 BaseUrl 拉取可用模型，失败则使用预置推荐
            models: List[str] = []
            try:
                models = await fetch_models(llm_cfg.base_url, llm_cfg.api_key, llm_cfg.provider)
            except Exception:
                pass

            if not models:
                prov_key = (llm_cfg.provider or "").lower()
                models = FALLBACK_MODELS.get(prov_key, ["deepseek-chat", "gpt-4o-mini", "llama3:latest"])

            # 确保当前模型在列表中
            if llm_cfg.model and llm_cfg.model not in models:
                models.insert(0, llm_cfg.model)

            selected_m = await select_model_interactive(models, llm_cfg.model)
            if selected_m:
                if selected_m == "[➕ 输入自定义模型名称...]":
                    if session:
                        custom_name = await session.prompt_async(HTML("<b>输入自定义模型名称: </b>"))
                        if custom_name.strip():
                            llm_cfg.model = custom_name.strip()
                            save_current_llm_config(db, llm_cfg)
                            console.print(f"[green]✓ 已将当前模型切换为: [bold]{llm_cfg.model}[/bold][/green]")
                else:
                    llm_cfg.model = selected_m
                    save_current_llm_config(db, llm_cfg)
                    console.print(f"[green]✓ 已将当前模型切换为: [bold]{selected_m}[/bold][/green]")
            else:
                console.print("[dim]已取消选择模型。[/dim]")
            return True
        else:
            new_model = parts[1].strip()
            llm_cfg.model = new_model
            save_current_llm_config(db, llm_cfg)
            console.print(f"[green]✓ 已将当前模型切换为: [bold]{new_model}[/bold][/green]")
        return True

    elif line == "/think" or line.startswith("/think ") or line in ["/thinking"]:
        parts = line.split(maxsplit=1)
        if len(parts) == 1:
            if session is not None:
                selected_th = await select_think_interactive(llm_cfg.enable_thinking)
                if selected_th == "toggle":
                    llm_cfg.enable_thinking = not llm_cfg.enable_thinking
                elif selected_th == "on":
                    llm_cfg.enable_thinking = True
                elif selected_th == "off":
                    llm_cfg.enable_thinking = False
                elif selected_th is None:
                    console.print("[dim]已取消选择思考模式。[/dim]")
                    return True
            else:
                llm_cfg.enable_thinking = not llm_cfg.enable_thinking
        else:
            sub = parts[1].strip().lower()
            if sub == "toggle":
                llm_cfg.enable_thinking = not llm_cfg.enable_thinking
            elif sub in ["on", "true", "1", "open", "enable"]:
                llm_cfg.enable_thinking = True
            elif sub in ["off", "false", "0", "close", "disable"]:
                llm_cfg.enable_thinking = False
            elif sub in ["status", "state"]:
                status_text = "开启" if llm_cfg.enable_thinking else "关闭"
                console.print(f"[dim]当前思考模式状态: [bold]{status_text}[/bold][/dim]")
                return True
            else:
                console.print("[yellow]用法: /think [on | off | toggle | status][/yellow]")
                return True

        save_current_llm_config(db, llm_cfg)
        status_text = "[bold green]已开启[/bold green]" if llm_cfg.enable_thinking else "[bold yellow]已关闭[/bold yellow]"
        console.print(f"[green]✓ AI 思考模式 (Thinking): {status_text}[/green]")
        return True

    elif line == "/provider" or line == "/providers" or line.startswith("/provider "):
        providers = ai_cfg_service.get_providers()
        parts = line.split(maxsplit=2)

        async def _prompt_input(msg: str, default_val: str = "") -> str:
            if session:
                val = await session.prompt_async(HTML(msg), default=default_val)
                return val.strip()
            return ""

        async def _handle_add_provider():
            console.print("[bold cyan]➕ 添加新的自定义 AI 供应商[/bold cyan]")
            p_id = await _prompt_input("<b>供应商唯一标识 (ID, 如 my-llm): </b>")
            if not p_id:
                console.print("[dim]已取消添加供应商。[/dim]")
                return
            # 检查是否已存在
            existing = next((p for p in providers if p.get("id", "").lower() == p_id.lower()), None)
            if existing:
                console.print(f"[yellow]供应商 ID '{p_id}' 已存在，请使用编辑功能或更换 ID。[/yellow]")
                return
            p_name = await _prompt_input(f"<b>供应商显示名称 (默认: {p_id}): </b>", default_val=p_id)
            p_base_url = await _prompt_input("<b>Base URL (例如: https://api.example.com/v1): </b>")
            p_api_key = await _prompt_input("<b>API Key (可选): </b>")
            p_model = await _prompt_input("<b>默认模型名称 (如 gpt-4o, deepseek-chat): </b>")

            new_provider = {
                "id": p_id,
                "name": p_name or p_id,
                "base_url": p_base_url,
                "api_key": p_api_key,
                "model": p_model,
                "is_custom": True,
            }
            providers.append(new_provider)
            ai_cfg_service.save_providers(providers)
            console.print(f"[green]✓ 成功添加自定义供应商 [bold]{new_provider['name']}[/bold] 并保存至 config.json！[/green]")

            # 自动切换至新建供应商
            llm_cfg.provider = p_id
            llm_cfg.base_url = p_base_url
            if p_model:
                llm_cfg.model = p_model
            llm_cfg.api_key = p_api_key
            save_current_llm_config(db, llm_cfg)
            console.print(f"[green]✓ 已自动切换为新供应商: [bold]{new_provider['name']}[/bold] (模型: {llm_cfg.model})[/green]")

        async def _handle_edit_provider(target_p: Dict[str, Any]):
            is_custom = bool(target_p.get("is_custom", False))
            p_name = target_p.get("name", target_p.get("id"))
            console.print(f"[bold cyan]⚙ 编辑供应商: {p_name} ({target_p.get('id')}){' [自定义]' if is_custom else ' [内置]'}[/bold cyan]")
            
            cur_key = target_p.get("api_key") or ""
            if is_custom:
                cur_base_url = target_p.get("base_url") or ""
                cur_model = target_p.get("model") or ""
                new_base_url = await _prompt_input(f"<b>Base URL: </b>", default_val=cur_base_url)
                new_key = await _prompt_input(f"<b>API Key: </b>", default_val=cur_key)
                new_model = await _prompt_input(f"<b>默认模型: </b>", default_val=cur_model)
                target_p["base_url"] = new_base_url
                target_p["api_key"] = new_key
                if new_model:
                    target_p["model"] = new_model
            else:
                console.print(f"[dim]提示: 内置官方供应商仅需配置 API Key (Base URL 固定为 {target_p.get('base_url')})。[/dim]")
                new_key = await _prompt_input(f"<b>API Key: </b>", default_val=cur_key)
                target_p["api_key"] = new_key

            ai_cfg_service.save_providers(providers)

            # 如果当前正在使用该供应商，同步更新当前活跃配置
            if (llm_cfg.provider or "").lower() == target_p.get("id", "").lower():
                if is_custom:
                    llm_cfg.base_url = target_p["base_url"]
                    if target_p.get("model"):
                        llm_cfg.model = target_p["model"]
                llm_cfg.api_key = target_p["api_key"]
                save_current_llm_config(db, llm_cfg)
            console.print(f"[green]✓ 已成功更新 [{p_name}] 的配置并持久化！[/green]")

        async def _handle_delete_provider(target_p: Dict[str, Any]):
            if not target_p.get("is_custom"):
                console.print(f"[yellow]⚠️ 供应商 [{target_p.get('name')}] 为系统内置官方供应商，不可删除！[/yellow]")
                return
            p_id = target_p.get("id")
            p_name = target_p.get("name", p_id)
            confirm_del = await _prompt_input(f"<b>确认删除自定义供应商 [{p_name}] 吗？(y/N): </b>", default_val="n")
            if confirm_del.lower() in ("y", "yes"):
                providers[:] = [p for p in providers if p.get("id") != p_id]
                ai_cfg_service.save_providers(providers)
                console.print(f"[green]✓ 已删除自定义供应商 [{p_name}]。[/green]")
                # 如果当前正在使用的就是被删除的供应商，重置为第一个可用供应商
                if (llm_cfg.provider or "").lower() == p_id.lower():
                    fallback = providers[0] if providers else None
                    if fallback:
                        llm_cfg.provider = fallback.get("id", "")
                        llm_cfg.base_url = fallback.get("base_url", "")
                        if fallback.get("model"):
                            llm_cfg.model = fallback.get("model")
                        llm_cfg.api_key = fallback.get("api_key", "")
                        save_current_llm_config(db, llm_cfg)
                        console.print(f"[yellow]当前供应商已被重置回: [bold]{fallback.get('name')}[/bold][/yellow]")
            else:
                console.print("[dim]已取消删除。[/dim]")

        async def _handle_custom_management():
            # 自定义管理交互选项列表
            custom_items = [
                {"id": "add", "name": "➕ 添加新自定义供应商", "desc": "录入新 Base URL, API Key 与模型"},
            ]
            for p in providers:
                if p.get("is_custom"):
                    custom_items.append({
                        "id": f"manage_{p.get('id')}",
                        "name": f"⚙ {p.get('name', p.get('id'))}",
                        "desc": f"Base URL: {p.get('base_url')} | Model: {p.get('model')}",
                        "provider": p,
                    })

            act, sel = await run_interactive_selection_menu(
                title="🛠 自定义 AI 供应商管理",
                items=custom_items,
                current_id="add",
                key_fn=lambda it: it["id"],
                render_item_fn=lambda it: f"{it['name']:<24} {it.get('desc', '')}",
                extra_bindings={"d": "delete", "D": "delete"},
                help_hint="↑/↓ 选择 | Enter 编辑/进入 | d 删除(自定义) | Esc 返回",
                max_visible_items=10,
            )
            if act == "confirm" and sel:
                if sel["id"] == "add":
                    await _handle_add_provider()
                else:
                    await _handle_edit_provider(sel["provider"])
            elif act == "delete" and sel:
                if sel.get("provider"):
                    await _handle_delete_provider(sel["provider"])
                else:
                    console.print("[yellow]无法删除该选项。[/yellow]")

        if len(parts) == 1:
            # 二级菜单：上下箭头交互式选择，支持 Enter 切换、e 编辑、d 删除(自定义)、c 自定义管理
            action, target_p = await select_provider_interactive(providers, llm_cfg.provider)
            if action == "switch" and target_p:
                llm_cfg.provider = target_p.get("id", "")
                llm_cfg.base_url = target_p.get("base_url", "")
                if target_p.get("model"):
                    llm_cfg.model = target_p.get("model")
                llm_cfg.api_key = target_p.get("api_key", "")
                save_current_llm_config(db, llm_cfg)
                console.print(
                    f"[green]✓ 已成功切换供应商为: [bold]{target_p.get('name')}[/bold] (模型: {llm_cfg.model})[/green]"
                )
            elif action == "edit" and target_p:
                await _handle_edit_provider(target_p)
            elif action == "delete" and target_p:
                await _handle_delete_provider(target_p)
            elif action == "custom":
                await _handle_custom_management()
            else:
                console.print("[dim]已取消操作。[/dim]")
            return True
        else:
            sub = parts[1].strip()
            if sub.lower() in ("custom", "add"):
                await _handle_custom_management()
                return True

            if sub.lower() == "delete":
                target_id = parts[2].strip() if len(parts) > 2 else ""
                target_p = next((p for p in providers if p.get("id", "").lower() == target_id.lower()), None)
                if target_p:
                    await _handle_delete_provider(target_p)
                else:
                    console.print(f"[red]未找到供应商 '{target_id}' 进行删除。[/red]")
                return True

            if sub.lower() == "edit":
                target_id = parts[2].strip() if len(parts) > 2 else llm_cfg.provider
                target_p = next((p for p in providers if p.get("id", "").lower() == (target_id or "").lower()), None)
                if target_p:
                    await _handle_edit_provider(target_p)
                else:
                    console.print(f"[red]未找到供应商 '{target_id}' 进行编辑。[/red]")
                return True

            target_p = next((p for p in providers if p.get("id", "").lower() == sub.lower()), None)
            if target_p:
                llm_cfg.provider = target_p.get("id", sub)
                llm_cfg.base_url = target_p.get("base_url", "")
                if target_p.get("model"):
                    llm_cfg.model = target_p.get("model")
                llm_cfg.api_key = target_p.get("api_key", "")
                save_current_llm_config(db, llm_cfg)
                console.print(
                    f"[green]✓ 已成功切换供应商为: [bold]{target_p.get('name')}[/bold] (模型: {llm_cfg.model})[/green]"
                )
            else:
                available_ids = ", ".join([p.get("id", "") for p in providers])
                console.print(f"[red]未找到供应商 '{sub}'。可用 ID: {available_ids}[/red]")
            return True

    elif line == "/prompt" or line.startswith("/prompt "):
        prompts = ai_cfg_service.get_prompts()
        parts = line.split(maxsplit=1)
        if len(parts) == 1:
            target_pr = await select_prompt_interactive(prompts)
            if target_pr:
                prompt_text = target_pr.get("text", "")
                console.print(f"[dim]📌 正在执行 Prompt [{target_pr.get('title')}]: {prompt_text}[/dim]")
                line = prompt_text
            else:
                console.print("[dim]已取消选择 Prompt。[/dim]")
                return True
        else:
            pid = parts[1].strip()
            target_pr = next((pr for pr in prompts if pr.get("id", "").lower() == pid.lower()), None)
            if target_pr:
                prompt_text = target_pr.get("text", "")
                console.print(f"[dim]📌 正在执行 Prompt [{target_pr.get('title')}]: {prompt_text}[/dim]")
                line = prompt_text
            else:
                available_pids = ", ".join([pr.get("id", "") for pr in prompts])
                console.print(f"[red]未找到 Prompt '{pid}'。可用 ID: {available_pids}[/red]")
                return True

    elif line == "/skill" or line.startswith("/skill "):
        skills = ai_cfg_service.get_skills()
        parts = line.split(maxsplit=1)
        if len(parts) == 1:
            target_sk = await select_skill_interactive(skills, current_mode.get("role", ""))
            if target_sk:
                current_mode["name"] = f"skill:{target_sk.get('id')}"
                current_mode["role"] = target_sk.get("id")
                current_mode["display_name"] = f"技能:{target_sk.get('title', target_sk.get('id'))}"
                current_mode["system_prompt"] = target_sk.get("systemPrompt") or target_sk.get("system_prompt", "")
                current_mode["output_format"] = "text"
                console.print(f"[green]✓ 已切换到技能模式: [bold]{target_sk.get('title')}[/bold][/green]")
            else:
                console.print("[dim]已取消选择技能。[/dim]")
            return True
        else:
            sid = parts[1].strip()
            target_sk = next((sk for sk in skills if sk.get("id", "").lower() == sid.lower()), None)
            if target_sk:
                current_mode["name"] = f"skill:{target_sk.get('id')}"
                current_mode["role"] = target_sk.get("id")
                current_mode["display_name"] = f"技能:{target_sk.get('title', sid)}"
                current_mode["system_prompt"] = target_sk.get("systemPrompt") or target_sk.get("system_prompt", "")
                current_mode["output_format"] = "text"
                console.print(f"[green]✓ 已切换到技能模式: [bold]{target_sk.get('title')}[/bold][/green]")
            else:
                available_sids = ", ".join([sk.get("id", "") for sk in skills])
            return True

    # 其它自然语言或意图指令，调用 AI 执行
    current_mode["status_text"] = "思考中..."
    from rich.live import Live
    from rich.spinner import Spinner
    from rich.console import Group

    status_str = format_status_text(db, llm_cfg, current_mode)
    thinking_view = Group(
        Spinner("dots", text=Text(f" {display_cfg.ai_name} 正在思考处理中...", style="dim")),
        Text(status_str, style="#7f848e"),
    )

    with Live(thinking_view, refresh_per_second=10, transient=True, console=console):
        try:
            result = await parse_intent_and_execute(
                user_input=line,
                config=llm_cfg,
                db=db,
                user_id=None,
                system_prompt=current_mode.get("system_prompt"),
                history=history,
            )
            history.append({"role": "user", "content": line})
            history.append({"role": "assistant", "content": result.message})

            if current_mode.get("output_format") == "json":
                out_payload = {
                    "action": result.action,
                    "data": result.data,
                    "raw_response": result.message,
                }
                console.print_json(data=out_payload)
                console.print()
            else:
                console.print(f"[bold green]AI[/bold green] › {result.message}\n")
        except Exception as e:
            console.print(f"[red]执行出错: {e}[/red]")
        finally:
            current_mode["status_text"] = "就绪"

    return True


async def main_loop():
    db = DbState.get_instance()
    llm_cfg = load_current_llm_config(db)
    display_cfg = DisplayConfigService.load()

    current_mode: Dict[str, Any] = {
        "name": "agent",
        "role": "agent",
        "display_name": "Agent助理",
        "status_text": "就绪",
        "system_prompt": DEFAULT_AGENT_PROMPT,
        "output_format": "text",
    }
    print_banner(display_cfg, current_mode.get("display_name", "Agent助理"))
    history: List[Dict[str, str]] = []

    toolbar_getter = create_bottom_toolbar_getter(db, llm_cfg, current_mode)
    session = PromptSession(
        completer=SlashCommandCompleter(),
        bottom_toolbar=toolbar_getter,
        style=CLI_STYLE,
        key_bindings=create_cli_key_bindings(),
    )

    while True:
        try:
            prompt_str = "<b><ansicyan>You</ansicyan></b> › "
            user_input = await session.prompt_async(HTML(prompt_str))
            should_continue = await handle_command(
                user_input, db, llm_cfg, history, current_mode, session
            )
            if not should_continue:
                break
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]程序已退出。[/dim]")
            break
        except Exception as e:
            console.print(f"[red]异常: {e}[/red]")


def run_cli():
    asyncio.run(main_loop())


if __name__ == "__main__":
    run_cli()
