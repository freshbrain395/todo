"""CLI Help content component: renders static, categorized command documentation without arrows or interactive scrolling."""

from typing import Optional, Dict, List
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from ..app import get_terminal_width
from .completer import SLASH_COMMANDS

# 分类组织所有命令
COMMAND_CATEGORIES = [
    {
        "title": "📋 待办事项管理 (Todo)",
        "color": "cyan",
        "commands": [
            ("/list [all|pending|done]", "查看待办事项列表，支持状态过滤与关键词搜索"),
            ("/add <标题> [参数]", "添加新待办任务，支持 priority= 和 category="),
            ("/todo <标题>", "/add 命令的快捷别名"),
            ("/done <ID>", "将指定 ID 的待办标记为已完成"),
            ("/undone <ID>", "将指定 ID 的待办恢复为待完成"),
            ("/delete <ID>", "彻底删除指定 ID 的待办事项"),
        ],
    },
    {
        "title": "🔄 工作模式切换 (Mode)",
        "color": "green",
        "commands": [
            ("/mode [chat|agent|json]", "切换工作模式；无参数时弹出模式选择列表"),
            ("/chat", "快捷切换到常规聊天模式"),
            ("/agent", "快捷切换到 Todo Agent 智能助理模式"),
        ],
    },
    {
        "title": "🤖 AI 模型与配置 (AI Config)",
        "color": "yellow",
        "commands": [
            ("/provider", "管理 AI 供应商 (SiliconFlow, DeepSeek, Ollama 等)"),
            ("/model [模型名]", "切换当前使用的 LLM 模型；无参数时进入模型选择"),
            ("/think [on|off|toggle]", "开启、关闭或反转 AI 深度思考推理模式 (Thinking)"),
            ("/prompt", "交互式选择并载入内置 Prompt 提示词模板"),
            ("/skill", "交互式选择并激活专业 AI 技能角色"),
        ],
    },
    {
        "title": "⚙️ 系统与界面 (System)",
        "color": "magenta",
        "commands": [
            ("/help [命令名]", "显示本命令手册；加命令名可查看其参数详情"),
            ("/statusbar [reset|list]", "配置底部状态栏显示项 (Checkbox 多选，别名: /status)"),
            ("/clear", "清空当前会话历史对话上下文"),
            ("/cls", "清除屏幕内容并重新展示欢迎卡片"),
            ("/quit", "安全退出 Todo Agent 终端 (别名: /exit)"),
        ],
    },
]

COMMAND_DETAILS: Dict[str, str] = {
    "/help": "查看所有可用命令列表。用法：/help 或 /help <命令名>",
    "/list": "展示待办事项列表。用法：/list [all | pending | done] [搜索词]",
    "/add": "添加新待办。用法：/add <标题> [priority=high|medium|low] [category=分类名]",
    "/todo": "/add 命令的快捷别名。用法：/todo <标题>",
    "/done": "标记指定待办为已完成。用法：/done <ID>",
    "/undone": "恢复指定待办为待完成。用法：/undone <ID>",
    "/delete": "删除指定待办事项。用法：/delete <ID>",
    "/mode": "切换或交互式选择工作模式。用法：/mode 或 /mode <chat|agent|json>",
    "/chat": "快捷切换到常规聊天模式。用法：/chat",
    "/agent": "快捷切换到 Todo Agent 智能助理模式。用法：/agent",
    "/provider": "交互式选择或配置 AI 供应商。用法：/provider",
    "/model": "切换或交互式选择 LLM 模型。用法：/model 或 /model <模型名称>",
    "/think": "配置深度思考模式 (Thinking)。用法：/think [on | off | toggle | status]",
    "/prompt": "交互式选择预置 Prompt 模板。用法：/prompt",
    "/skill": "交互式切换 AI 技能角色。用法：/skill",
    "/statusbar": "配置底部状态栏显示内容。用法：/statusbar 或 /status（弹出 Checkbox 多选菜单），/statusbar reset（重置全选），/statusbar list（列出当前状态）",
    "/status": "/statusbar 命令的快捷别名。用法：/status",
    "/clear": "清空当前会话的历史对话记录。用法：/clear",
    "/cls": "清除屏幕并重绘欢迎横幅。用法：/cls",
    "/quit": "退出 Todo Agent 终端。用法：/quit 或 /exit",
    "/exit": "退出 Todo Agent 终端。用法：/exit",
}


def build_help_panel() -> Panel:
    """构建静态分组的斜线命令帮助内容面板（无箭头，纯内容呈现，无多余滚动）"""
    term_w = get_terminal_width(fallback=80)
    cmd_col_w = 26 if term_w >= 90 else 20

    groups = []
    for cat in COMMAND_CATEGORIES:
        table = Table.grid(padding=(0, 2))
        table.add_column(style=f"bold {cat['color']}", width=cmd_col_w)
        table.add_column(style="white")

        for cmd, desc in cat["commands"]:
            table.add_row(cmd, desc)

        panel = Panel(
            table,
            title=f"[bold]{cat['title']}[/bold]",
            title_align="left",
            border_style=cat["color"],
            padding=(0, 1),
        )
        groups.append(panel)

    return Panel(
        Group(*groups),
        title="📖 [bold cyan]Todo Agent 命令使用手册[/bold cyan]",
        subtitle="[dim]直接输入命令即可执行 | 亦可直接输入自然语言与 AI 对话[/dim]",
        subtitle_align="right",
        border_style="blue",
        padding=(1, 1),
    )


def build_command_detail_panel(cmd_name: str) -> Panel:
    """构建单个命令的详细说明面板"""
    name = cmd_name.strip()
    if not name.startswith("/"):
        name = "/" + name

    detail = COMMAND_DETAILS.get(name)
    if detail:
        content = f"[bold cyan]{name}[/bold cyan]\n\n{detail}"
        return Panel(content, title="📌 命令详情", border_style="cyan", padding=(1, 2))
    else:
        content = f"[yellow]未找到命令 '{cmd_name}' 的详细说明。[/yellow]\n输入 [bold green]/help[/bold green] 查看全部命令清单。"
        return Panel(content, title="⚠️ 提示", border_style="yellow", padding=(1, 2))


def print_help_view(cmd_name: Optional[str] = None, console: Optional[Console] = None) -> None:
    """打印帮助组件内容到终端中"""
    from .style import CLI_STYLE
    from ..commands.base import console as default_console
    c = console or default_console

    if cmd_name:
        panel = build_command_detail_panel(cmd_name)
    else:
        panel = build_help_panel()

    c.print(panel)
