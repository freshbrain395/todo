"""CLI welcome component: displays welcome banner, status, and quick guides upon startup."""

from typing import Dict, Any, Optional
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from ..app import get_terminal_width

default_console = Console(force_terminal=True, legacy_windows=False)


def build_welcome_panel(
    display_cfg: Any = None,
    current_mode: Optional[Dict[str, Any]] = None,
    llm_cfg: Any = None,
) -> Group:
    """构建精美的 CLI 启动欢迎面板，包含应用名称、当前状态卡片及常用指令引导。"""
    app_title = getattr(display_cfg, "ai_name", "Todo Agent") if display_cfg else "Todo Agent"
    mode_name = current_mode.get("display_name", "Agent助理") if current_mode else "Agent助理"

    prov_name = getattr(llm_cfg, "provider", "siliconflow") if llm_cfg else "默认"
    model_name = getattr(llm_cfg, "model", "deepseek-ai/DeepSeek-V4-Flash") if llm_cfg else "默认"
    thinking_on = getattr(llm_cfg, "enable_thinking", False) if llm_cfg else False
    thinking_text = "[bold green]开启[/bold green]" if thinking_on else "[dim]关闭[/dim]"

    term_w = get_terminal_width(fallback=80)

    # 1. 顶部 Header
    header_text = Text()
    header_text.append("✨ ", style="bold yellow")
    header_text.append(f"{app_title} 智能命令行终端", style="bold cyan")
    header_text.append(" (v2.0)\n", style="dim")
    header_text.append("基于大语言模型的全功能任务管理与智能协作助理", style="italic white")

    # 2. 状态信息表格
    status_table = Table.grid(padding=(0, 2))
    status_table.add_column(style="bold dim")
    status_table.add_column()
    status_table.add_column(style="bold dim")
    status_table.add_column()

    status_table.add_row(
        "工作模式:", f"[cyan]{mode_name}[/cyan]",
        "AI 供应商:", f"[green]{prov_name}[/green]",
    )
    status_table.add_row(
        "当前模型:", f"[bold white]{model_name}[/bold white]",
        "思考模式:", thinking_text,
    )

    # 3. 常用指令快速指引
    guide_table = Table.grid(padding=(0, 1))
    guide_table.add_column(style="bold yellow", width=14 if term_w >= 80 else 10)
    guide_table.add_column(style="dim")

    guide_table.add_row("/help", "查看所有命令完整手册与单命令详情")
    guide_table.add_row("/list", "查看待办任务列表 (支持 /list pending / done)")
    guide_table.add_row("/add <标题>", "快速添加待办任务 (别名: /todo)")
    guide_table.add_row("/mode", "切换工作模式 (chat 聊天 / agent 助理 / json 模式)")
    guide_table.add_row("/provider", "选择或配置 AI 模型供应商与 API Key")
    guide_table.add_row("直接输入内容", "与 AI 智能助理自然语言对话或自动执行任务")

    # 组合渲染内容
    content_group = Group(
        header_text,
        Text(""),
        Panel(status_table, title="⚙ 系统状态", title_align="left", border_style="dim"),
        Text(""),
        Panel(guide_table, title="🚀 快捷指令", title_align="left", border_style="dim"),
        Text(""),
        Text("输入 /help 获取更多帮助 | /quit 退出", style="dim"),
    )

    return content_group


def print_welcome(
    display_cfg: Any = None,
    current_mode: Optional[Dict[str, Any]] = None,
    llm_cfg: Any = None,
    console: Optional[Console] = None,
) -> None:
    """在终端直接打印欢迎组件"""
    c = console or default_console
    panel = build_welcome_panel(display_cfg, current_mode, llm_cfg)
    c.print(panel)
