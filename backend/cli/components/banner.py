"""CLI startup banner component."""

from rich.console import Console
from rich.panel import Panel

console = Console(force_terminal=True, legacy_windows=False)


def print_banner(display_cfg, current_mode_name: str = "agent", out_console: Console = None) -> None:
    """Print the startup banner card to console."""
    c = out_console or console
    banner_text = "[bold cyan]Todo Agent CLI[/bold cyan]\n"
    banner_text += f"[dim]当前模式：[bold green]{current_mode_name}[/bold green] | 输入 [green]/mode[/green] 查看或切换模式\n直接输入自然语言对话或管理待办，输入 [green]/help[/green] 查看全部命令[/dim]"
    c.print(Panel(banner_text, border_style="cyan", padding=(0, 2)))
