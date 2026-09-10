import os
import sys
import json
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from prompt_toolkit import PromptSession
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
    build_box_header,
    build_box_footer,
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


class SlashCommandCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # /think 二级补全
        if text.startswith("/think "):
            sub = text[len("/think "):].lower()
            options = [("on", "开启思考模式"), ("off", "关闭思考模式"), ("toggle", "切换思考模式开关")]
            for opt, desc in options:
                if opt.startswith(sub):
                    yield Completion(opt, start_position=-len(sub), display=f"{opt:<8} {desc}")
        # /list 二级补全
        if text.startswith("/list "):
            sub = text[len("/list "):].lower()
            options = [("all", "查看全部待办"), ("pending", "查看未完成待办"), ("completed", "查看已完成待办")]
            for opt, desc in options:
                if opt.startswith(sub):
                    yield Completion(opt, start_position=-len(sub), display=f"{opt:<10} {desc}")
            return
        # 一级 Slash 命令补全
        if text.startswith("/"):
            query = text.lower()
            # 如果包含空格且命令已结束（如 '/mode '），不应把其他命令的描述当成命令匹配
            if " " in query:
                return
            term_w = get_terminal_width()
            # 三级过滤策略：
            # 1. 精确匹配优先：输入完整命令（如 /mode）时只显示该命令
            # 2. 前缀匹配合并：有前缀匹配结果时，只展示前缀匹配项，避免描述匹配引入无关项
            # 3. 兜底描述匹配：仅当前缀无匹配时，才回退到描述关键词搜索
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
                    yield Completion(cmd, start_position=-len(text), display=display_text, display_meta="")


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


def show_help():
    table = Table(title="📌 常用 Slash 命令帮助", title_style="bold green")
    table.add_column("命令", style="cyan", no_wrap=True)
    table.add_column("说明", style="white")

    for cmd, desc in SLASH_COMMANDS:
        table.add_row(cmd, desc)

    console.print(table)


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


async def select_provider_interactive(
    providers: List[Dict[str, Any]],
    current_id: str,
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """二级菜单：使用上下箭头选择 AI 供应商，支持 Enter 切换 或 k 配置 Key（自适应终端宽度）"""
    if not providers:
        return (None, None)

    selected_index = 0
    for idx, p in enumerate(providers):
        if p.get("id", "").lower() == (current_id or "").lower():
            selected_index = idx
            break

    action_holder: List[Optional[str]] = [None]
    result_holder: List[Optional[Dict[str, Any]]] = [None]

    kb = KeyBindings()

    @kb.add("up")
    def _(event):
        nonlocal selected_index
        selected_index = (selected_index - 1) % len(providers)

    @kb.add("down")
    def _(event):
        nonlocal selected_index
        selected_index = (selected_index + 1) % len(providers)

    @kb.add("enter")
    def _(event):
        action_holder[0] = "switch"
        result_holder[0] = providers[selected_index]
        event.app.exit()

    @kb.add("k")
    @kb.add("K")
    def _(event):
        action_holder[0] = "set_key"
        result_holder[0] = providers[selected_index]
        event.app.exit()

    @kb.add("escape")
    @kb.add("c-c")
    def _(event):
        action_holder[0] = "cancel"
        event.app.exit()

    def get_text():
        term_w = get_terminal_width(fallback=80)
        menu_w = max(50, term_w - 4)

        header = build_box_header("🤖 选择 AI 供应商 [Enter 切换 | k 设置Key | Esc 取消]", menu_w)
        tokens = [("class:menu-title", header)]

        inner_w = max(20, menu_w - 4)
        for idx, p in enumerate(providers):
            is_cur = p.get("id", "").lower() == (current_id or "").lower()
            is_sel = idx == selected_index
            pointer = "❯ " if is_sel else "  "
            cur_tag = " [当前]" if is_cur else ""

            if p.get("id") == "ollama" or "11434" in (p.get("base_url") or ""):
                key_tag = "✓ 已配Key" if p.get("api_key") else "本地免Key"
            else:
                key_tag = "✓ 已配Key" if p.get("api_key") else "✗ 无Key"

            # 组合行内容并自适应截断
            name = p.get("name", p.get("id"))
            model = p.get("model", "")
            raw_line = f"{pointer}{name} ({model}) [{key_tag}]{cur_tag}"
            line_str = truncate_to_width(raw_line, inner_w) + "\n"

            if is_sel:
                tokens.append(("class:menu-selected", line_str))
            else:
                tokens.append(("class:menu-item", line_str))

        footer = build_box_footer(menu_w)
        tokens.append(("class:menu-dim", footer))
        return tokens

    control = FormattedTextControl(get_text)
    window = Window(content=control, height=len(providers) + 3)
    app = Application(
        layout=Layout(HSplit([window])),
        key_bindings=kb,
        style=CLI_STYLE,
        full_screen=False,
    )

    await app.run_async()
    return (action_holder[0], result_holder[0])


async def select_model_interactive(
    models: List[str],
    current_model: str,
) -> Optional[str]:
    """二级菜单：使用上下箭头选择模型（自适应终端宽度）"""
    if not models:
        return None

    # 加入自定义选项
    options = list(models)
    custom_option = "[➕ 输入自定义模型名称...]"
    options.append(custom_option)

    selected_index = 0
    for idx, m in enumerate(options):
        if m.lower() == (current_model or "").lower():
            selected_index = idx
            break

    result_holder: List[Optional[str]] = [None]
    cancelled_holder = [False]

    kb = KeyBindings()

    @kb.add("up")
    def _(event):
        nonlocal selected_index
        selected_index = (selected_index - 1) % len(options)

    @kb.add("down")
    def _(event):
        nonlocal selected_index
        selected_index = (selected_index + 1) % len(options)

    @kb.add("enter")
    def _(event):
        result_holder[0] = options[selected_index]
        event.app.exit()

    @kb.add("escape")
    @kb.add("c-c")
    def _(event):
        cancelled_holder[0] = True
        event.app.exit()

    def get_text():
        term_w = get_terminal_width(fallback=80)
        menu_w = max(50, term_w - 4)

        header = build_box_header("🧠 选择 LLM 模型 [↑/↓ 选择 | Enter 确认 | Esc 取消]", menu_w)
        tokens = [("class:menu-title", header)]

        inner_w = max(20, menu_w - 4)
        for idx, m in enumerate(options):
            is_cur = m.lower() == (current_model or "").lower()
            is_sel = idx == selected_index
            pointer = "❯ " if is_sel else "  "
            cur_tag = " [当前]" if is_cur else ""

            raw_line = f"{pointer}{m}{cur_tag}"
            line_str = truncate_to_width(raw_line, inner_w) + "\n"

            if is_sel:
                tokens.append(("class:menu-selected", line_str))
            else:
                tokens.append(("class:menu-item", line_str))

        footer = build_box_footer(menu_w)
        tokens.append(("class:menu-dim", footer))
        return tokens

    control = FormattedTextControl(get_text)
    window = Window(content=control, height=min(len(options) + 3, 16))
    app = Application(
        layout=Layout(HSplit([window])),
        key_bindings=kb,
        style=CLI_STYLE,
        full_screen=False,
    )

    await app.run_async()
    if cancelled_holder[0]:
        return None
    return result_holder[0]


# 交互式模式选择菜单选项定义
MODE_OPTIONS = [
    ("chat", "普通聊天模式"),
    ("agent", "Todo Agent 助理模式"),
    ("json", "严格 JSON 输出模式"),
]


async def select_mode_interactive(current_mode_name: str = "chat") -> Optional[str]:
    """二级菜单：使用上下箭头选择模式（无背景、默认选中第一项、高亮前景色、Enter确认、Esc取消）"""
    # 使用列表存储 selected_index，避免 nonlocal 在 prompt_toolkit 回调中的闭包问题
    selected_index = [0]
    # 按照需求：第一项 chat 默认获得焦点
    for idx, (m_name, _) in enumerate(MODE_OPTIONS):
        if m_name.lower() == (current_mode_name or "chat").lower():
            # 若已有当前模式可对应，否则默认 0 (chat)
            selected_index[0] = idx
            break

    result_holder: List[Optional[str]] = [None]
    cancelled_holder = [False]

    kb = KeyBindings()

    @kb.add("up")
    def _(event):
        selected_index[0] = (selected_index[0] - 1) % len(MODE_OPTIONS)
        event.app.invalidate()

    @kb.add("down")
    def _(event):
        selected_index[0] = (selected_index[0] + 1) % len(MODE_OPTIONS)
        event.app.invalidate()

    @kb.add("enter")
    def _(event):
        result_holder[0] = MODE_OPTIONS[selected_index[0]][0]
        event.app.exit()

    @kb.add("escape")
    @kb.add("c-c")
    def _(event):
        cancelled_holder[0] = True
        event.app.exit()

    def get_text():
        term_w = get_terminal_width(fallback=80)
        menu_w = max(50, term_w - 4)

        header = build_box_header("🔄 选择工作模式 [↑/↓ 选择 | Enter 确认 | Esc 取消]", menu_w)
        tokens = [("class:menu-title", header)]

        inner_w = max(20, menu_w - 4)
        for idx, (opt_name, opt_desc) in enumerate(MODE_OPTIONS):
            is_cur = opt_name.lower() == (current_mode_name or "chat").lower()
            is_sel = idx == selected_index[0]
            pointer = "❯ " if is_sel else "  "
            cur_tag = " [当前]" if is_cur else ""

            raw_line = f"{pointer}{opt_name:<8} {opt_desc}{cur_tag}"
            line_str = truncate_to_width(raw_line, inner_w) + "\n"

            if is_sel:
                tokens.append(("class:menu-selected", line_str))
            else:
                tokens.append(("class:menu-item", line_str))

        footer = build_box_footer(menu_w)
        tokens.append(("class:menu-dim", footer))
        return tokens

    control = FormattedTextControl(get_text)
    window = Window(content=control, height=len(MODE_OPTIONS) + 3)
    app = Application(
        layout=Layout(HSplit([window])),
        key_bindings=kb,
        style=CLI_STYLE,
        full_screen=False,
    )

    await app.run_async()
    if cancelled_holder[0]:
        return None
    return result_holder[0]


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
        show_help()
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
        if len(parts) == 1 or parts[1].strip().lower() == "toggle":
            llm_cfg.enable_thinking = not llm_cfg.enable_thinking
        else:
            sub = parts[1].strip().lower()
            if sub in ["on", "true", "1", "open", "enable"]:
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
        if len(parts) == 1:
            # 二级菜单：上下箭头交互式选择，支持 Enter 切换与 k 设置 Key
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
            elif action == "set_key" and target_p:
                if session:
                    new_key = await session.prompt_async(HTML(f"<b>为 [{target_p.get('name')}] 输入新 API Key: </b>"))
                    new_key = new_key.strip()
                    target_p["api_key"] = new_key
                    ai_cfg_service.save_providers(providers)
                    if (llm_cfg.provider or "").lower() == target_p.get("id", "").lower():
                        llm_cfg.api_key = new_key
                        save_current_llm_config(db, llm_cfg)
                    console.print(f"[green]✓ 已成功更新 [{target_p.get('name')}] 的 API Key 并保存至 config.json！[/green]")
            else:
                console.print("[dim]已取消操作。[/dim]")
            return True
        else:
            sub = parts[1].strip()
            if sub.lower() == "key" and len(parts) > 2:
                new_key = parts[2].strip()
                llm_cfg.api_key = new_key
                # 同步更新 providers 列表中当前提供商的 key
                for p in providers:
                    if p.get("id", "").lower() == (llm_cfg.provider or "").lower():
                        p["api_key"] = new_key
                ai_cfg_service.save_providers(providers)
                save_current_llm_config(db, llm_cfg)
                console.print(f"[green]✓ 已为当前供应商 ({llm_cfg.provider}) 更新 API Key 并持久化至 config.json！[/green]")
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
            term_w = get_terminal_width()
            table = Table(title="📝 预设 Prompt 提示词模板", title_style="bold blue")
            if term_w < 90:
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("标题", style="bold white")
                table.add_column("内容", style="white")
                for pr in prompts:
                    text_snippet = truncate_to_width(pr.get("text", ""), max(15, term_w - 30))
                    table.add_row(pr.get("id", ""), pr.get("title", ""), text_snippet)
            else:
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("分类", style="dim", width=10)
                table.add_column("标题", style="bold white", width=16)
                table.add_column("内容", style="white")
                content_limit = max(40, term_w - 50)
                for pr in prompts:
                    text_snippet = truncate_to_width(pr.get("text", ""), content_limit)
                    table.add_row(pr.get("id", ""), pr.get("category", ""), pr.get("title", ""), text_snippet)
            console.print(table)
            console.print("[dim]💡 执行指定 Prompt: /prompt <ID> (例如: /prompt p1)[/dim]")
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
            term_w = get_terminal_width()
            table = Table(title="⚡ AI 技能与角色模式 (Skills)", title_style="bold magenta")
            if term_w < 90:
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("技能名称", style="bold white")
                table.add_column("描述", style="white")
                for sk in skills:
                    desc = truncate_to_width(sk.get("description", ""), max(15, term_w - 30))
                    table.add_row(sk.get("id", ""), sk.get("title", ""), desc)
            else:
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("分类", style="dim", width=10)
                table.add_column("技能名称", style="bold white", width=18)
                table.add_column("描述", style="white")
                desc_limit = max(35, term_w - 55)
                for sk in skills:
                    desc = truncate_to_width(sk.get("description", ""), desc_limit)
                    table.add_row(sk.get("id", ""), sk.get("category", ""), sk.get("title", ""), desc)
            console.print(table)
            console.print("[dim]💡 切换技能角色模式: /skill <ID> (例如: /skill skill-gtd)[/dim]")
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
                console.print(f"[dim]已切换到技能模式: {target_sk.get('title')}[/dim]")
            else:
                available_sids = ", ".join([sk.get("id", "") for sk in skills])
                console.print(f"[red]未找到技能 '{sid}'。可用 ID: {available_sids}[/red]")
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
