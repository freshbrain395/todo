"""CLI 统一斜线命令与菜单交互核心组件 (Unified Slash Commands & Menu System).
"""

from __future__ import annotations

import asyncio
import inspect
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.shortcuts import clear as pt_clear
from rich.box import DOUBLE_EDGE, ROUNDED
from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from ..config import load_cli_config, save_cli_config, show_welcome
from ..utils import get_border, get_terminal_height, get_terminal_width, truncate_to_width
from .style import CLI_STYLE

_default_console = Console(force_terminal=True, legacy_windows=False)
console = _default_console


# ============================================================================
# 1. LLM 配置与命令注册表基础设施 (Command Infrastructure)
# ============================================================================

@dataclass
class LlmConfig:
    """LLM 模型配置"""

    provider: str = "siliconflow"
    base_url: str = "https://api.siliconflow.cn/v1"
    api_key: str = ""
    model: str = "deepseek-ai/DeepSeek-V4-Flash"
    enable_thinking: bool = False


def load_current_llm_config(db: Any = None) -> LlmConfig:
    """加载当前生效的 LLM 模型配置，优先从 cli/config.json 读取"""
    try:
        cli_cfg = load_cli_config()
        providers = cli_cfg.get("providers", [])
        if providers:
            p = providers[0]
            models = p.get("models") or []
            return LlmConfig(
                provider=p.get("provider") or p.get("id", "siliconflow"),
                base_url=p.get("base_url") or p.get("baseurl", "https://api.siliconflow.cn/v1"),
                api_key=p.get("api_key") or p.get("apikey", ""),
                model=p.get("model") or (models[0] if models else "deepseek-ai/DeepSeek-V4-Flash"),
                enable_thinking=p.get("enable_thinking", False),
            )
    except Exception:
        pass
    return LlmConfig()


@dataclass
class CommandContext:
    """CLI 命令执行上下文环境"""

    app: Any = None
    db: Any = None
    llm_cfg: Any = None
    current_mode: Any = None
    display_cfg: Any = None
    status_bar_state: Any = None
    menu_runner: Any = None
    current_cmd: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def show_result(
        self,
        content: Any,
        status: str = "success",
        hint: Optional[str] = None,
        subtitle: Optional[str] = None,
    ) -> None:
        """使用斜线命令结果容器统一展示当前命令的执行结果"""
        cmd_title = self.current_cmd or "斜线命令"
        SlashResultContainer.display(
            command=cmd_title,
            content=content,
            status=status,
            hint=hint,
            subtitle=subtitle,
            console=console,
        )


@dataclass
class CommandSpec:
    """斜线命令规格定义"""

    name: str
    handler: Callable
    description: str = ""
    usage: str = ""
    aliases: List[str] = field(default_factory=list)
    category: str = "通用命令"
    needs_args: bool = False


# 全局命令注册表
COMMAND_REGISTRY: Dict[str, CommandSpec] = {}


def register_command(
    name: str,
    description: str = "",
    usage: str = "",
    aliases: Optional[List[str]] = None,
    category: str = "通用命令",
    needs_args: bool = False,
):
    """
    命令注册装饰器。
    """

    def decorator(func: Callable):
        spec = CommandSpec(
            name=name,
            handler=func,
            description=description,
            usage=usage or name,
            aliases=aliases or [],
            category=category,
            needs_args=needs_args,
        )
        COMMAND_REGISTRY[name] = spec
        for alias in spec.aliases:
            COMMAND_REGISTRY[alias] = spec
        return func

    return decorator


def command_needs_args(cmd_name: str) -> bool:
    """查询指定命令是否需要后续追加参数（补全选中时不立即提交）"""
    spec = COMMAND_REGISTRY.get(cmd_name.lower())
    if spec:
        return spec.needs_args
    return False


def get_registered_commands() -> List[Tuple[str, str]]:
    """获取所有已注册的唯一主命令及其说明，用于菜单展示和自动补全"""
    seen = set()
    commands = []
    for spec in COMMAND_REGISTRY.values():
        if spec.name not in seen:
            seen.add(spec.name)
            commands.append((spec.name, spec.description))
    return sorted(commands, key=lambda x: x[0])


async def dispatch_command(raw_input: str, ctx: CommandContext) -> Optional[Any]:
    """
    根据用户输入的命令字符串分发执行对应命令。
    """
    trimmed = raw_input.strip()
    if not trimmed:
        return None

    parts = trimmed.split(maxsplit=1)
    cmd_name = parts[0].lower()
    args_str = parts[1] if len(parts) > 1 else ""

    spec = COMMAND_REGISTRY.get(cmd_name)
    if not spec:
        return None

    ctx.current_cmd = f"{spec.name} {args_str}".strip() if args_str else spec.name

    handler = spec.handler
    if inspect.iscoroutinefunction(handler):
        result = await handler(args_str, ctx)
    else:
        result = handler(args_str, ctx)

    if result is not None and not isinstance(result, bool):
        ctx.show_result(result, status="success")
        return True

    return True if result is None else result


# ============================================================================
# 2. 内置斜线命令处理器 (Builtin Command Handlers: /help, /clear, /quit, /exit)
# ============================================================================

@register_command(
    name="/help",
    description="查看所有可用命令及帮助指南",
    usage="/help [关键词]",
    aliases=["help", "/?", "?", "/commands", "commands"],
    category="系统命令",
)
async def handle_help(args: str, ctx: CommandContext) -> bool:
    """展示斜线命令帮助指南"""
    query = args.strip()
    # 优先在交互式输入框与状态栏之间展开帮助视图
    if ctx.app and hasattr(ctx.app, "input_session") and hasattr(ctx.app.input_session, "open_help"):
        ctx.app.input_session.open_help(query=query)
        return True

    # 降级：控制台面板输出
    show_help_result(
        query=query,
        console=console,
        command=ctx.current_cmd or "/help",
    )
    return True


@register_command(
    name="/clear",
    description="清空控制台屏幕与对话上下文历史",
    usage="/clear [screen|history|all]",
    aliases=["/cls", "clear", "cls", "/clear_screen"],
    category="系统命令",
)
async def handle_clear(args: str, ctx: CommandContext) -> bool:
    """清屏或清空上下文并强制同步重绘底部状态栏与边框"""
    target = (args or "all").strip().lower()
    cfg = getattr(ctx.app, "cli_cfg", None) if ctx.app else None

    def do_screen_clear():
        try:
            pt_clear()
        except Exception:
            pass
        console.clear()

    if target in ("screen", "s"):
        do_screen_clear()
        show_welcome(cfg, console=console, force=True)
        ctx.show_result("✓ 控制台屏幕已清空。", status="success")
    elif target in ("history", "h"):
        if ctx.app and hasattr(ctx.app, "history"):
            ctx.app.history.clear()
        ctx.show_result("✓ 当前对话上下文历史已重置。", status="success")
    else:  # all 或默认
        do_screen_clear()
        if ctx.app and hasattr(ctx.app, "history"):
            ctx.app.history.clear()
        show_welcome(cfg, console=console, force=True)
        ctx.show_result("✓ 控制台已清空，对话上下文历史已重置。", status="success")

    session = ctx.extra.get("session") if ctx.extra else None
    if session and hasattr(session, "app") and session.app and session.app.renderer:
        try:
            r = session.app.renderer
            r.reset()
            r._min_available_height = 20
        except Exception:
            pass

    return True


@register_command(
    name="/quit",
    description="退出命令行程序 (同 /exit)",
    usage="/quit",
    aliases=["exit", "/exit", "quit", "quit()", "exit()", ":q"],
    category="系统命令",
)
async def handle_quit(args: str, ctx: CommandContext) -> bool:
    """退出 CLI 事件循环"""
    ctx.show_result("👋 退出 Todo Agent，再见！感谢您的使用。", status="info")
    return False


@register_command(
    name="/exit",
    description="退出命令行程序 (同 /quit)",
    usage="/exit",
    aliases=["quit", "/quit", "exit", "exit()", "quit()", ":q"],
    category="系统命令",
)
async def handle_exit(args: str, ctx: CommandContext) -> bool:
    """退出 CLI 事件循环"""
    ctx.show_result("👋 退出 Todo Agent，再见！感谢您的使用。", status="info")
    return False


@register_command(
    name="/provider",
    description="查看或切换当前 AI 模型供应商",
    usage="/provider [id|list]",
    aliases=["/providers", "provider", "providers"],
    category="配置命令",
)
async def handle_provider(args: str, ctx: CommandContext) -> bool:
    """查看或切换当前 AI 供应商"""
    cfg = load_cli_config()
    providers = cfg.get("providers", [])
    if not providers:
        ctx.show_result("⚠️ 配置文件中未配置任何 AI 供应商。", status="warning")
        return True

    cur_llm = getattr(ctx, "llm_cfg", None) or load_current_llm_config()
    cur_provider_id = (cur_llm.provider or "").lower()

    sub = (args or "").strip()
    if not sub or sub.lower() in ("list", "ls"):
        table = Table(title="AI 模型供应商列表", box=ROUNDED, border_style="cyan")
        table.add_column("当前", justify="center", style="bold green", width=4)
        table.add_column("ID", style="bold cyan")
        table.add_column("名称", style="white")
        table.add_column("模型", style="yellow")
        table.add_column("API Key 状态", style="magenta")
        table.add_column("Base URL", style="dim")

        for p in providers:
            p_id = p.get("id") or p.get("provider", "")
            is_cur = "●" if p_id.lower() == cur_provider_id else ""
            key_val = p.get("api_key") or ""
            if p_id == "ollama" or "11434" in (p.get("base_url") or ""):
                key_tag = "本地免Key"
            else:
                key_tag = "✓ 已配置" if key_val else "✗ 未配置"
            table.add_row(
                is_cur,
                p_id,
                p.get("name", p_id),
                str(p.get("model", "")),
                key_tag,
                str(p.get("base_url", "")),
            )

        ctx.show_result(
            table,
            status="info",
            hint="切换命令: /provider <id>，如: /provider deepseek",
        )
        return True

    # 切换供应商
    target = None
    target_idx = -1
    for idx, p in enumerate(providers):
        p_id = (p.get("id") or p.get("provider", "")).lower()
        if p_id == sub.lower():
            target = p
            target_idx = idx
            break

    if not target:
        available = ", ".join(p.get("id") or p.get("provider", "") for p in providers)
        ctx.show_result(
            f"❌ 未找到供应商 '{sub}'。\n可用供应商 ID: {available}",
            status="error",
        )
        return True

    # 将目标供应商置于列表首位
    providers.pop(target_idx)
    providers.insert(0, target)
    cfg["providers"] = providers
    save_cli_config(cfg)

    # 同步更新当前环境配置
    if ctx.llm_cfg:
        ctx.llm_cfg.provider = target.get("provider") or target.get("id", "")
        ctx.llm_cfg.base_url = target.get("base_url", "")
        ctx.llm_cfg.api_key = target.get("api_key", "")
        if target.get("model"):
            ctx.llm_cfg.model = target.get("model")
        if "enable_thinking" in target:
            ctx.llm_cfg.enable_thinking = target.get("enable_thinking", False)

    ctx.show_result(
        f"✓ 已成功切换 AI 供应商为: [bold cyan]{target.get('name', target.get('id'))}[/bold cyan]\n"
        f"  - 模型: [yellow]{target.get('model', '')}[/yellow]\n"
        f"  - 接口: [dim]{target.get('base_url', '')}[/dim]",
        status="success",
    )
    return True


# ============================================================================
# 3. 数字列表交互单选组件 (NumberMenu & RadioMenu)
# ============================================================================

@dataclass
class NumberItem:
    """数字列表菜单项数据结构"""

    id: str
    label: str
    desc: str = ""
    disabled: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_any(cls, item: Union[NumberItem, Dict[str, Any], Tuple[str, str], str]) -> NumberItem:
        """从各种常见数据类型转换为 NumberItem"""
        if isinstance(item, NumberItem):
            return item
        if isinstance(item, dict):
            return cls(
                id=str(item.get("id", item.get("name", item.get("value", "")))),
                label=str(item.get("label", item.get("title", item.get("name", item.get("id", ""))))),
                desc=str(item.get("desc", item.get("description", ""))),
                disabled=bool(item.get("disabled", False)),
                extra=item,
            )
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            return cls(id=str(item[0]), label=str(item[1]), desc=str(item[2]) if len(item) > 2 else "")
        if isinstance(item, (list, tuple)) and len(item) == 1:
            return cls(id=str(item[0]), label=str(item[0]))
        return cls(id=str(item), label=str(item))


RadioItem = NumberItem


class NumberMenu:
    """数字列表组件控制器与状态管理"""

    def __init__(
        self,
        items: List[Union[NumberItem, Dict[str, Any], Tuple[str, str], str]],
        *,
        title: str = "请选择一个选项",
        current_id: Optional[str] = None,
        max_visible: int = 8,
        help_hint: str = "↑/↓ 移动 | 1-9 数字跳转 | Enter 确认 | Esc 取消",
    ):
        self.items: List[NumberItem] = [NumberItem.from_any(it) for it in items]
        self.title = title
        self.current_id = str(current_id) if current_id is not None else None
        self.max_visible = max_visible
        self.help_hint = help_hint

        self.selected_index = 0
        if self.current_id:
            for idx, item in enumerate(self.items):
                if item.id.lower() == self.current_id.lower() and not item.disabled:
                    self.selected_index = idx
                    break

        self.visible_start = 0
        self._ensure_visible()

    def move(self, delta: int) -> None:
        """移动高亮光标，跳过 disabled 选项"""
        if not self.items:
            return
        total = len(self.items)
        idx = self.selected_index
        for _ in range(total):
            idx = (idx + delta) % total
            if not self.items[idx].disabled:
                self.selected_index = idx
                self._ensure_visible()
                return

    def select_number(self, num: int) -> bool:
        """通过序号(1-based)直接高亮选择对应选项"""
        if not self.items:
            return False
        idx = num - 1
        if 0 <= idx < len(self.items) and not self.items[idx].disabled:
            self.selected_index = idx
            self._ensure_visible()
            return True
        return False

    def _ensure_visible(self) -> None:
        """自适应滚动视口计算"""
        total = len(self.items)
        if total <= self.max_visible:
            self.visible_start = 0
            return
        if self.selected_index < self.visible_start:
            self.visible_start = self.selected_index
        elif self.selected_index >= self.visible_start + self.max_visible:
            self.visible_start = self.selected_index - self.max_visible + 1

    def get_selected(self) -> Optional[NumberItem]:
        """获取当前高亮选中的 NumberItem"""
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None

    def render_tokens(self, width: Optional[int] = None) -> StyleAndTextTuples:
        """渲染数字列表菜单的 prompt_toolkit 格式化 tokens"""
        term_w = width or get_terminal_width(80)
        max_w = max(24, term_w - 2)
        total = len(self.items)

        tokens: StyleAndTextTuples = []

        header = f"● {self.title} [{self.selected_index + 1}/{total}]"
        tokens.append(("class:title", f"{truncate_to_width(header, max_w)}\n"))

        if total == 0:
            tokens.append(("class:hint", "  (暂无可选项目)\n"))
            return tokens

        if self.visible_start > 0:
            tokens.append(("class:scroll-indicator", "  ▲ 更多项目...\n"))

        end = min(total, self.visible_start + self.max_visible)
        for idx in range(self.visible_start, end):
            item = self.items[idx]
            is_cursor = idx == self.selected_index
            is_current = self.current_id is not None and item.id.lower() == self.current_id.lower()

            pointer = "❯ " if is_cursor else "  "
            num_str = f"{idx + 1}. "

            item_style = "class:item-selected" if is_cursor else "class:item"
            num_style = "class:item-selected" if is_cursor else "class:hint"

            tokens.append((item_style, f"  {pointer}"))
            tokens.append((num_style, num_str))

            label_text = item.label
            tokens.append((item_style, label_text))

            if is_current:
                tokens.append(("class:current-tag", " [当前]"))

            if item.desc:
                used_len = len(pointer) + len(num_str) + len(label_text) + (7 if is_current else 0) + 4
                avail_desc_len = max(8, max_w - used_len)
                short_desc = truncate_to_width(item.desc, avail_desc_len)
                tokens.append(("class:desc", f" - {short_desc}"))

            tokens.append(("", "\n"))

        if end < total:
            tokens.append(("class:scroll-indicator", "  ▼ 更多项目...\n"))

        tokens.append(("class:hint", f"  └─ {self.help_hint}\n"))

        return tokens


RadioMenu = NumberMenu


async def run_number_menu(
    items: List[Union[NumberItem, Dict[str, Any], Tuple[str, str], str]],
    *,
    title: str = "请选择一个选项",
    current_id: Optional[str] = None,
    max_visible: int = 8,
    help_hint: str = "↑/↓ 移动 | 1-9 数字跳转 | Enter 确认 | Esc 取消",
) -> Optional[NumberItem]:
    """交互式数字列表菜单入口函数"""
    if not items:
        return None

    menu = NumberMenu(
        items,
        title=title,
        current_id=current_id,
        max_visible=max_visible,
        help_hint=help_hint,
    )

    result_holder: List[Optional[NumberItem]] = [None]
    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def _(event):
        menu.move(-1)

    @kb.add("down")
    @kb.add("j")
    def _(event):
        menu.move(1)

    for digit in range(1, 10):
        def _make_handler(d: int):
            def _handler(event):
                if menu.select_number(d):
                    event.app.invalidate()
            return _handler
        kb.add(str(digit))(_make_handler(digit))

    @kb.add("enter")
    @kb.add("space")
    def _(event):
        result_holder[0] = menu.get_selected()
        event.app.exit(result=result_holder[0])

    @kb.add("escape")
    @kb.add("q")
    @kb.add("c-c")
    def _(event):
        result_holder[0] = None
        event.app.exit(result=None)

    layout = Layout(
        HSplit([
            Window(
                content=FormattedTextControl(lambda: menu.render_tokens()),
                dont_extend_height=True,
            )
        ])
    )

    app: Application[Optional[NumberItem]] = Application(
        layout=layout,
        key_bindings=kb,
        style=CLI_STYLE,
        full_screen=False,
    )

    return await app.run_async()


run_radio_menu = run_number_menu


# ============================================================================
# 4. 输入框悬浮斜线菜单组件 (SlashMenuState)
# ============================================================================

class SlashMenuState:
    """管理在输入框下边框和底部栏中间展示的斜线命令状态"""

    def __init__(self, commands: Optional[Any] = None, max_visible: int = 10):
        self._commands_source = commands
        self.max_visible = max_visible
        self.selected_index = 0
        self.visible_start = 0
        self.is_open = False
        self.just_closed = False
        self.active_menu_lines = 0
        self.last_rendered_lines = 0

    @property
    def commands(self) -> List[Tuple[str, str]]:
        """动态获取当前可用命令列表"""
        if callable(self._commands_source):
            return self._commands_source()
        if self._commands_source is not None:
            return self._commands_source
        return get_registered_commands()

    def open(self) -> None:
        """打开菜单"""
        self.is_open = True
        self.just_closed = False

    def close(self) -> None:
        """关闭菜单并重置"""
        self.is_open = False
        self.just_closed = True
        self.selected_index = 0
        self.visible_start = 0
        self.active_menu_lines = 0

    def reset(self) -> None:
        """完全重置状态"""
        self.is_open = False
        self.just_closed = False
        self.selected_index = 0
        self.visible_start = 0
        self.active_menu_lines = 0

    def update(self, text: str) -> bool:
        """根据当前文本更新菜单开关状态"""
        was_open = self.is_open
        if text.startswith("/") and " " not in text and len(text) >= 1:
            if not self.just_closed:
                self.is_open = True
        else:
            self.is_open = False
            self.just_closed = False
        return was_open and not self.is_open

    def get_matched(self, text: str) -> List[Tuple[str, str]]:
        """根据当前输入前缀匹配可用斜线命令"""
        if not text.startswith("/") or " " in text:
            self.is_open = False
            self.just_closed = False
            return []
        if self.just_closed:
            return []

        from .completer import match_slash_commands
        matched = match_slash_commands(text, self.commands)
        self.is_open = bool(matched)
        return matched

    def move(self, delta: int, count: int) -> None:
        """上下切换选中项并同步滚动可视视口"""
        if count <= 0:
            return
        self.selected_index = (self.selected_index + delta) % count
        if self.selected_index < self.visible_start:
            self.visible_start = self.selected_index
        elif self.selected_index >= self.visible_start + self.max_visible:
            self.visible_start = self.selected_index - self.max_visible + 1

    def render_menu_tokens(self, current_text: str, cols: Optional[int] = None) -> StyleAndTextTuples:
        """渲染斜线命令菜单 tokens"""
        width = cols or get_terminal_width(80)
        matched = self.get_matched(current_text)
        if not matched:
            self.last_rendered_lines = 0
            self.active_menu_lines = 0
            return []

        if self.selected_index >= len(matched):
            self.selected_index = 0
            self.visible_start = 0

        start = self.visible_start
        end = min(len(matched), start + self.max_visible)
        visible = matched[start:end]
        self.last_rendered_lines = 1 + len(visible)
        self.active_menu_lines = self.last_rendered_lines

        tokens: StyleAndTextTuples = []
        hint_text = f"💡 可用斜线命令 (↑/↓ 选择, Enter 确认) [{self.selected_index + 1}/{len(matched)}]"
        tokens.append(("class:menu-dim", f"  {hint_text}\n"))

        for idx, (cmd, desc) in enumerate(visible):
            actual_idx = start + idx
            is_current = actual_idx == self.selected_index
            max_desc_len = max(10, width - 24)
            short_desc = truncate_to_width(desc, max_desc_len)

            if is_current:
                tokens.append(("class:menu-selected", f"  ❯ {cmd:<14} {short_desc}\n"))
            else:
                tokens.append(("class:menu-item", f"    {cmd:<14} {short_desc}\n"))

        return tokens

    def render_float_tokens(self, current_text: str, cols: Optional[int] = None) -> StyleAndTextTuples:
        """向后兼容保留"""
        return self.render_menu_tokens(current_text, cols=cols)

    def build_prompt_fragments(self, current_text: str = "", cols: Optional[int] = None) -> StyleAndTextTuples:
        """构建输入框顶部提示 tokens"""
        width = cols or get_terminal_width(80)
        border_line = get_border(width)
        return [
            ("class:border", border_line + "\n"),
            ("class:prompt", "❯ "),
        ]


class SlashHelpMenu:
    """管理在输入框下边框和状态栏之间展示的 Help 命令帮助交互组件"""

    def __init__(
        self,
        registry: Optional[Dict[str, CommandSpec]] = None,
        max_visible: int = 8,
    ):
        self._registry = registry if registry is not None else COMMAND_REGISTRY
        self.max_visible = max_visible
        self.selected_index = 0
        self.visible_start = 0
        self.is_active = False
        self.query = ""
        self.active_lines = 0

    def open(self, query: str = "") -> None:
        """激活并打开 Help 视图"""
        self.is_active = True
        self.query = query.strip()
        self.selected_index = 0
        self.visible_start = 0

    def close(self) -> None:
        """关闭 Help 视图"""
        self.is_active = False
        self.selected_index = 0
        self.visible_start = 0
        self.active_lines = 0

    def get_commands(self) -> List[CommandSpec]:
        """根据当前搜索关键字过滤可用命令规格列表"""
        q = self.query.lower().lstrip("/")
        seen = set()
        specs: List[CommandSpec] = []
        for spec in self._registry.values():
            if spec.name not in seen:
                seen.add(spec.name)
                specs.append(spec)
        specs.sort(key=lambda s: (s.category, s.name))
        if not q:
            return specs
        return [
            s for s in specs
            if q in s.name.lower()
            or any(q in alias.lower() for alias in s.aliases)
            or q in s.description.lower()
            or q in s.category.lower()
        ]

    def move(self, delta: int) -> None:
        """上下移动高亮光标并滚动可视视口"""
        cmds = self.get_commands()
        if not cmds:
            return
        total = len(cmds)
        self.selected_index = (self.selected_index + delta) % total
        if self.selected_index < self.visible_start:
            self.visible_start = self.selected_index
        elif self.selected_index >= self.visible_start + self.max_visible:
            self.visible_start = self.selected_index - self.max_visible + 1

    def select_number(self, num: int) -> bool:
        """通过 1-9 序号直接选择对应命令"""
        cmds = self.get_commands()
        idx = num - 1
        if 0 <= idx < len(cmds):
            self.selected_index = idx
            if self.selected_index < self.visible_start:
                self.visible_start = self.selected_index
            elif self.selected_index >= self.visible_start + self.max_visible:
                self.visible_start = self.selected_index - self.max_visible + 1
            return True
        return False

    def get_selected_command(self) -> Optional[CommandSpec]:
        """获取当前高亮光标选中的命令规格"""
        cmds = self.get_commands()
        if 0 <= self.selected_index < len(cmds):
            return cmds[self.selected_index]
        return None

    def render_help_tokens(self, cols: Optional[int] = None) -> StyleAndTextTuples:
        """渲染在输入框下边框和状态栏中间的 help tokens"""
        width = cols or get_terminal_width(80)
        max_w = max(24, width - 2)
        cmds = self.get_commands()
        total = len(cmds)

        tokens: StyleAndTextTuples = []
        if total == 0:
            header = f"💡 没有找到匹配 '{self.query}' 的斜线命令 (Esc 退出帮助)"
            tokens.append(("class:menu-dim", f"  {truncate_to_width(header, max_w)}\n"))
            self.active_lines = 1
            return tokens

        if self.selected_index >= total:
            self.selected_index = 0
            self.visible_start = 0

        header = f"📖 可用命令帮助与指南 (↑/↓ 移动光标 | 1-9 跳转 | Enter 选用 | Esc 退出) [{self.selected_index + 1}/{total}]"
        tokens.append(("class:title", f"  {truncate_to_width(header, max_w)}\n"))

        start = self.visible_start
        end = min(total, start + self.max_visible)
        line_count = 1

        if start > 0:
            tokens.append(("class:scroll-indicator", "    ▲ 更多命令...\n"))
            line_count += 1

        for idx in range(start, end):
            spec = cmds[idx]
            is_cursor = idx == self.selected_index
            icon = COMMAND_ICONS.get(spec.name, "⚡")
            num_str = f"{idx + 1}. "

            if is_cursor:
                tokens.append(("class:item-selected", f"  ❯ {num_str}{icon} {spec.name:<12} "))
                tokens.append(("class:item-selected", f"{spec.description}\n"))
                line_count += 1

                detail_parts = [f"分类: {spec.category}", f"用法: {spec.usage or spec.name}"]
                if spec.aliases:
                    detail_parts.append(f"别名: {', '.join(spec.aliases)}")
                detail_str = " | ".join(detail_parts)
                short_detail = truncate_to_width(detail_str, max(10, max_w - 6))
                tokens.append(("class:desc", f"      └─ {short_detail}\n"))
                line_count += 1
            else:
                short_desc = truncate_to_width(spec.description, max(10, max_w - 24))
                tokens.append(("class:menu-item", f"    {num_str}{icon} {spec.name:<12} {short_desc}\n"))
                line_count += 1

        if end < total:
            tokens.append(("class:scroll-indicator", "    ▼ 更多命令...\n"))
            line_count += 1

        self.active_lines = line_count
        return tokens


# ============================================================================
# 5. 斜线命令容器与结果卡片 (SlashCommandsContainer & SlashResultContainer)
# ============================================================================

class SlashCommandsContainer:
    """斜线命令容器组件：汇聚并展示命令概览、分类分组与键盘快捷键指引"""

    def __init__(self, registry: Optional[Dict[str, CommandSpec]] = None):
        self._registry = registry if registry is not None else COMMAND_REGISTRY

    def get_all_specs(self) -> List[CommandSpec]:
        """获取去重后的所有唯一命令规格列表"""
        seen = set()
        specs: List[CommandSpec] = []
        for spec in self._registry.values():
            if spec.name not in seen:
                seen.add(spec.name)
                specs.append(spec)
        return sorted(specs, key=lambda s: (s.category, s.name))

    def get_categories(self) -> List[str]:
        """获取所有可用类别"""
        cats = {spec.category for spec in self.get_all_specs()}
        return sorted(list(cats))

    def get_grouped(self) -> Dict[str, List[CommandSpec]]:
        """按类别对命令进行分组"""
        grouped: Dict[str, List[CommandSpec]] = {}
        for spec in self.get_all_specs():
            grouped.setdefault(spec.category, []).append(spec)
        return grouped

    def filter_commands(self, query: str = "") -> List[CommandSpec]:
        """根据关键字筛选命令"""
        q = query.strip().lower().lstrip("/")
        specs = self.get_all_specs()
        if not q:
            return specs
        return [
            s for s in specs
            if q in s.name.lower()
            or any(q in alias.lower() for alias in s.aliases)
            or q in s.description.lower()
            or q in s.category.lower()
        ]

    def build_table(self, specs: Optional[List[CommandSpec]] = None) -> Table:
        """构建命令一览表格"""
        cmd_list = specs if specs is not None else self.get_all_specs()

        table = Table(
            box=ROUNDED,
            header_style="bold cyan",
            show_lines=True,
            expand=True,
        )
        table.add_column("斜线命令", style="bold green", width=14, no_wrap=True)
        table.add_column("分类", style="magenta", width=12, no_wrap=True)
        table.add_column("语法 / 用法", style="yellow", min_width=24)
        table.add_column("参数", style="cyan", width=8, justify="center")
        table.add_column("功能说明与快捷别名", style="white")

        for spec in cmd_list:
            alias_text = f"\n[dim]别名: {', '.join(spec.aliases)}[/dim]" if spec.aliases else ""
            arg_badge = "[bold red]必需[/bold red]" if spec.needs_args else "[dim green]可选[/dim green]"
            usage_str = spec.usage or spec.name
            desc_text = f"{spec.description}{alias_text}"

            table.add_row(
                spec.name,
                spec.category,
                usage_str,
                arg_badge,
                desc_text,
            )

        return table

    def build_help_content(self, query: str = "") -> Any:
        """构建 /help 命令的主体内容"""
        specs = self.filter_commands(query)
        total_unique = len(specs)
        all_aliases_count = sum(len(s.aliases) for s in specs)

        header_text = Text()
        header_text.append("📦 已加载斜线指令: ", style="bold")
        header_text.append(f"{total_unique}", style="bold yellow")
        header_text.append(" 个主命令 / ")
        header_text.append(f"{all_aliases_count}", style="bold cyan")
        header_text.append(" 个快捷别名 | ")
        header_text.append("💡 输入方式: 在输入框输入 ", style="dim")
        header_text.append("/", style="bold green")
        header_text.append(" 唤起自动联想菜单\n", style="dim")

        table = self.build_table(specs)

        footer_text = Text(
            "⌨️ 快捷操作: ↑/↓ 或 Tab 切换补全候选项 | Enter 确认命令 | 直接输入文本可与智能助理对话",
            style="dim italic",
        )

        return Group(header_text, table, Text(""), footer_text)

    def build_container_panel(
        self,
        query: str = "",
        title: str = "⚡ Todo Agent 斜线命令容器 (Slash Commands Container)",
    ) -> Panel:
        """构建完整容器面板 (Rich Panel)"""
        content_group = self.build_help_content(query)
        return Panel(
            content_group,
            title=title,
            title_align="left",
            border_style="bright_blue",
            box=ROUNDED,
            padding=(1, 2),
        )

    def display(
        self,
        console: Optional[Console] = None,
        query: str = "",
        title: Optional[str] = None,
    ) -> None:
        """直接在控制台输出斜线命令容器组件"""
        c = console or _default_console
        panel = self.build_container_panel(
            query=query,
            title=title or "⚡ Todo Agent 斜线命令容器 (Slash Commands Container)",
        )
        c.print(panel)


class SlashResultContainer:
    """斜线命令执行结果容器组件"""

    STATUS_CONFIG = {
        "success": {"border": "green", "badge": "[bold green]✓ 执行成功[/bold green]"},
        "error": {"border": "red", "badge": "[bold red]✗ 执行失败[/bold red]"},
        "warning": {"border": "yellow", "badge": "[bold yellow]! 警告提示[/bold yellow]"},
        "info": {"border": "bright_blue", "badge": "[bold cyan]ℹ 执行完成[/bold cyan]"},
    }

    @classmethod
    def build_panel(
        cls,
        command: str,
        content: Any,
        status: str = "success",
        subtitle: Optional[str] = None,
        hint: Optional[str] = None,
    ) -> Panel:
        """构建包含执行结果的容器面板"""
        cfg = cls.STATUS_CONFIG.get(status, cls.STATUS_CONFIG["info"])
        border_style = cfg["border"]
        badge = cfg["badge"]

        renderables: List[RenderableType] = []

        if isinstance(content, str):
            renderables.append(Text.from_markup(content.strip()) if "[" in content else Text(content.strip()))
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, str):
                    renderables.append(Text.from_markup(item.strip()) if "[" in item else Text(item.strip()))
                else:
                    renderables.append(item)
        else:
            renderables.append(content)

        if hint:
            renderables.append(Text(f"\n💡 {hint}", style="dim"))

        body = Group(*renderables) if len(renderables) > 1 else renderables[0]
        title = f"⚡ [斜线命令] [bold]{command}[/bold]"
        sub = subtitle or badge

        return Panel(
            body,
            title=title,
            title_align="left",
            subtitle=f"[dim]──[/dim] {sub} [dim]──[/dim]",
            subtitle_align="right",
            border_style=border_style,
            box=ROUNDED,
            padding=(0, 2),
        )

    @classmethod
    def display(
        cls,
        command: str,
        content: Any,
        status: str = "success",
        console: Optional[Console] = None,
        subtitle: Optional[str] = None,
        hint: Optional[str] = None,
    ) -> None:
        """直接在控制台展示斜线命令结果容器"""
        c = console or _default_console
        panel = cls.build_panel(
            command=command,
            content=content,
            status=status,
            subtitle=subtitle,
            hint=hint,
        )
        c.print(panel)

    @classmethod
    def display_help(
        cls,
        query: str = "",
        console: Optional[Console] = None,
        command: str = "/help",
    ) -> None:
        """统一在斜线命令执行结果容器中展示 /help 的执行结果"""
        container = get_slash_commands_container()
        content = container.build_help_content(query=query)
        cmd_title = f"/help {query}".strip() if query else command
        cls.display(
            command=cmd_title,
            content=content,
            status="info",
            console=console,
        )


def get_slash_commands_container() -> SlashCommandsContainer:
    """获取斜线命令容器单例/实例"""
    return SlashCommandsContainer()


def show_slash_container(console: Optional[Console] = None, query: str = "") -> None:
    """快速展示斜线命令容器组件"""
    get_slash_commands_container().display(console=console, query=query)


def show_slash_result(
    command: str,
    content: Any,
    status: str = "success",
    console: Optional[Console] = None,
    subtitle: Optional[str] = None,
    hint: Optional[str] = None,
) -> None:
    """快速展示斜线命令执行结果"""
    SlashResultContainer.display(
        command=command,
        content=content,
        status=status,
        console=console,
        subtitle=subtitle,
        hint=hint,
    )


def show_help_result(
    query: str = "",
    console: Optional[Console] = None,
    command: str = "/help",
) -> None:
    """专门展示 /help 命令的执行结果"""
    SlashResultContainer.display_help(
        query=query,
        console=console,
        command=command,
    )


# ============================================================================
# 6. 斜线命令独立展示与选择组件 (SlashCommandsComponent & Helpers)
# ============================================================================

COMMAND_ICONS: Dict[str, str] = {
    "/help": "📖",
    "/clear": "🧹",
    "/cls": "🧹",
    "/exit": "🚪",
    "/quit": "🚪",
    "/todo": "📌",
    "/add": "➕",
    "/done": "✅",
    "/complete": "✅",
    "/delete": "🗑️",
    "/undone": "↩️",
    "/list": "📋",
    "/search": "🔍",
    "/provider": "🔌",
    "/model": "🤖",
    "/mode": "🔀",
    "/prompt": "💬",
    "/statusbar": "📊",
    "/skill": "⚡",
    "/think": "🧠",
}


@dataclass
class SlashCommandItem:
    """斜线命令项统一数据结构"""

    key: str
    label: str = ""
    description: str = ""
    usage: str = ""
    aliases: List[str] = field(default_factory=list)
    category: str = "通用命令"
    needs_args: bool = False
    icon: str = "⚡"
    action: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.label:
            self.label = self.description.split("，")[0].split("。")[0] if self.description else self.key
        if self.icon == "⚡" and self.key in COMMAND_ICONS:
            self.icon = COMMAND_ICONS[self.key]

    @classmethod
    def from_spec(cls, spec: Any) -> SlashCommandItem:
        """从 CommandSpec 对象转换为 SlashCommandItem"""
        key = getattr(spec, "name", "")
        desc = getattr(spec, "description", "")
        usage = getattr(spec, "usage", "") or key
        aliases = list(getattr(spec, "aliases", []))
        category = getattr(spec, "category", "通用命令")
        needs_args = bool(getattr(spec, "needs_args", False))
        icon = COMMAND_ICONS.get(key, "⚡")

        return cls(
            key=key,
            label=desc.split("，")[0].split("。")[0] if desc else key,
            description=desc,
            usage=usage,
            aliases=aliases,
            category=category,
            needs_args=needs_args,
            icon=icon,
            extra={"spec": spec},
        )

    @classmethod
    def from_tuple(cls, item: Tuple[str, str]) -> SlashCommandItem:
        """从 (命令, 描述) 元组转换"""
        key, desc = item
        return cls(
            key=key,
            label=desc.split("，")[0].split("。")[0] if desc else key,
            description=desc,
            usage=key,
            icon=COMMAND_ICONS.get(key, "⚡"),
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SlashCommandItem:
        """从字典转换"""
        key = data.get("key") or data.get("name") or data.get("id", "")
        desc = data.get("description") or data.get("desc", "")
        label = data.get("label") or data.get("title") or desc or key
        return cls(
            key=key,
            label=label,
            description=desc,
            usage=data.get("usage", key),
            aliases=list(data.get("aliases", [])),
            category=data.get("category", "通用命令"),
            needs_args=bool(data.get("needs_args", False)),
            icon=data.get("icon") or COMMAND_ICONS.get(key, "⚡"),
            action=data.get("action"),
            extra=data,
        )


class SlashCommandsComponent:
    """斜线命令展示组件：统一管理、过滤、表格与面板渲染"""

    def __init__(
        self,
        commands: Optional[List[Union[SlashCommandItem, Dict[str, Any], Tuple[str, str]]]] = None,
        console: Optional[Console] = None,
    ):
        self._custom_commands = commands
        self.console = console or _default_console

    def get_all_commands(self) -> List[SlashCommandItem]:
        """获取所有已注册的斜线命令列表"""
        if self._custom_commands is not None:
            results: List[SlashCommandItem] = []
            for item in self._custom_commands:
                if isinstance(item, SlashCommandItem):
                    results.append(item)
                elif isinstance(item, dict):
                    results.append(SlashCommandItem.from_dict(item))
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    results.append(SlashCommandItem.from_tuple((str(item[0]), str(item[1]))))
            return sorted(results, key=lambda c: (c.category, c.key))

        seen = set()
        items: List[SlashCommandItem] = []
        for spec in COMMAND_REGISTRY.values():
            if spec.name not in seen:
                seen.add(spec.name)
                items.append(SlashCommandItem.from_spec(spec))
        if items:
            return sorted(items, key=lambda c: (c.category, c.key))

        try:
            from .completer import get_current_slash_commands
            raw_pairs = get_current_slash_commands()
            return [SlashCommandItem.from_tuple(p) for p in raw_pairs]
        except Exception:
            return []

    def get_categories(self) -> List[str]:
        """获取所有可用类别列表"""
        cats = {cmd.category for cmd in self.get_all_commands()}
        return sorted(list(cats))

    def filter_commands(
        self,
        query: str = "",
        category: Optional[str] = None,
    ) -> List[SlashCommandItem]:
        """根据搜索词或分类筛选命令"""
        commands = self.get_all_commands()
        if category:
            commands = [c for c in commands if c.category == category]

        q = query.strip().lower().lstrip("/")
        if not q:
            return commands

        matched: List[SlashCommandItem] = []
        for cmd in commands:
            cmd_key_clean = cmd.key.lower().lstrip("/")
            alias_match = any(q in a.lower().lstrip("/") for a in cmd.aliases)
            if (
                q in cmd_key_clean
                or q in cmd.label.lower()
                or q in cmd.description.lower()
                or q in cmd.usage.lower()
                or alias_match
            ):
                matched.append(cmd)

        return matched

    def get_grouped(self, query: str = "") -> Dict[str, List[SlashCommandItem]]:
        """按分类对命令进行分组"""
        commands = self.filter_commands(query)
        grouped: Dict[str, List[SlashCommandItem]] = {}
        for cmd in commands:
            grouped.setdefault(cmd.category, []).append(cmd)
        return grouped

    def build_table(
        self,
        commands: Optional[List[SlashCommandItem]] = None,
        show_category: bool = True,
    ) -> Table:
        """构建美观的斜线命令 Rich Table 表格组件"""
        cmd_list = commands if commands is not None else self.get_all_commands()

        table = Table(
            box=ROUNDED,
            header_style="bold cyan",
            show_lines=True,
            expand=True,
        )
        table.add_column("命令", style="bold green", min_width=12, no_wrap=True)
        if show_category:
            table.add_column("分类", style="magenta", width=12, no_wrap=True)
        table.add_column("语法 / 用法", style="yellow", min_width=20)
        table.add_column("参数", style="cyan", width=8, justify="center")
        table.add_column("功能说明与快捷别名", style="white")

        for cmd in cmd_list:
            alias_text = f"\n[dim]别名: {', '.join(cmd.aliases)}[/dim]" if cmd.aliases else ""
            arg_badge = "[bold red]必需[/bold red]" if cmd.needs_args else "[dim green]可选[/dim green]"
            cmd_title = f"{cmd.icon} {cmd.key}"

            row = [
                cmd_title,
                cmd.usage or cmd.key,
                arg_badge,
                f"{cmd.description}{alias_text}",
            ]
            if show_category:
                row.insert(1, cmd.category)

            table.add_row(*row)

        return table

    def build_content(self, query: str = "") -> Group:
        """构建包含头部统计、命令表格与底部操作提示的内容组合"""
        specs = self.filter_commands(query)
        total_unique = len(specs)
        all_aliases = sum(len(s.aliases) for s in specs)

        header = Text()
        header.append("⚡ 斜线指令列表: ", style="bold")
        header.append(f"{total_unique}", style="bold yellow")
        header.append(" 个主命令 / ")
        header.append(f"{all_aliases}", style="bold cyan")
        header.append(" 个快捷别名 | ")
        header.append("💡 输入方式: 在输入框输入 ", style="dim")
        header.append("/", style="bold green")
        header.append(" 可唤起联想候选菜单\n", style="dim")

        table = self.build_table(specs)
        footer = Text(
            "⌨️ 快捷操作: ↑/↓ 选择命令 | Tab 自动补全 | Enter 确认执行 | 支持直接输入自然语言对话",
            style="dim italic",
        )

        return Group(header, table, Text(""), footer)

    def build_panel(
        self,
        query: str = "",
        title: str = "⚡ 可用斜线命令 (Slash Commands)",
    ) -> Panel:
        """构建包含完整边框与说明的斜线命令面板 (Panel)"""
        content = self.build_content(query=query)
        return Panel(
            content,
            title=title,
            title_align="left",
            border_style="bright_blue",
            box=ROUNDED,
            padding=(1, 2),
        )

    def display(
        self,
        console: Optional[Console] = None,
        query: str = "",
        title: Optional[str] = None,
        mode: str = "panel",
    ) -> None:
        """在控制台展示斜线命令组件"""
        c = console or self.console
        if mode == "table":
            table = self.build_table(self.filter_commands(query))
            c.print(table)
        else:
            panel = self.build_panel(
                query=query,
                title=title or "⚡ 可用斜线命令 (Slash Commands)",
            )
            c.print(panel)


def get_slash_commands_component(
    commands: Optional[List[Union[SlashCommandItem, Dict[str, Any], Tuple[str, str]]]] = None,
    console: Optional[Console] = None,
) -> SlashCommandsComponent:
    """获取 SlashCommandsComponent 组件实例"""
    return SlashCommandsComponent(commands=commands, console=console)


def show_slash_commands(
    query: str = "",
    title: Optional[str] = None,
    console: Optional[Console] = None,
    mode: str = "panel",
) -> None:
    """便捷函数：直接在控制台展示斜线命令组件"""
    component = get_slash_commands_component(console=console)
    component.display(console=console, query=query, title=title, mode=mode)


def render_slash_commands(
    query: str = "",
    title: str = "⚡ 可用斜线命令 (Slash Commands)",
) -> Panel:
    """便捷函数：生成斜线命令的 Rich Panel 渲染对象"""
    return get_slash_commands_component().build_panel(query=query, title=title)


async def run_slash_commands_menu(
    title: str = "⚡ 请选择要查看或执行的斜线命令",
    console: Optional[Console] = None,
) -> Optional[SlashCommandItem]:
    """交互式斜线命令选择菜单"""
    component = get_slash_commands_component(console=console)
    commands = component.get_all_commands()
    if not commands:
        return None

    menu_items = [
        NumberItem(
            id=cmd.key,
            label=f"{cmd.icon} {cmd.key:<14} {cmd.label}",
            desc=f"{cmd.description} (用法: {cmd.usage})",
            extra={"command": cmd},
        )
        for cmd in commands
    ]

    selected = await run_number_menu(
        items=menu_items,
        title=title,
    )
    if selected and selected.extra.get("command"):
        return selected.extra["command"]

    return None


__all__ = [
    # Command Infrastructure
    "console",
    "LlmConfig",
    "load_current_llm_config",
    "CommandContext",
    "CommandSpec",
    "COMMAND_REGISTRY",
    "register_command",
    "command_needs_args",
    "get_registered_commands",
    "dispatch_command",
    # Builtin Handlers
    "handle_help",
    "handle_clear",
    "handle_quit",
    "handle_exit",
    "handle_provider",
    # Number & Radio Menu
    "NumberItem",
    "NumberMenu",
    "run_number_menu",
    "RadioItem",
    "RadioMenu",
    "run_radio_menu",
    # Slash Menu Floating State
    "SlashMenuState",
    # Slash Container & Result
    "SlashCommandsContainer",
    "SlashResultContainer",
    "get_slash_commands_container",
    "show_slash_container",
    "show_slash_result",
    "show_help_result",
    # Slash Commands Display Component
    "COMMAND_ICONS",
    "SlashCommandItem",
    "SlashCommandsComponent",
    "get_slash_commands_component",
    "show_slash_commands",
    "render_slash_commands",
    "run_slash_commands_menu",
]

if __name__ == "__main__":
    show_slash_commands()
