import os
import sys
import json
import asyncio
from typing import List, Optional, Dict, Any
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
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
)

console = Console()

SLASH_COMMANDS = [
    ("/help", "显示可用命令帮助"),
    ("/todo", "创建待办任务 (/todo <标题>)"),
    ("/add", "新建待办任务 (/add <标题>)"),
    ("/list", "查看所有待办任务"),
    ("/done", "完成待办任务 (/done <ID>)"),
    ("/undone", "撤销完成状态 (/undone <ID>)"),
    ("/delete", "删除待办任务 (/delete <ID>)"),
    ("/chat", "切换到常规 AI 聊天模式"),
    ("/prompt", "选择并执行 Prompt 模板"),
    ("/agent", "切换并进入 Agent 角色模式"),
    ("/skill", "切换并启用 Skill 技能模式"),
    ("/provider", "管理/切换模型供应商"),
    ("/model", "查看/切换当前 LLM 模型"),
    ("/clear", "清空当前对话上下文历史"),
    ("/cls", "清空控制台屏幕"),
    ("/quit", "退出命令行程序"),
    ("/exit", "退出命令行程序"),
]


class SlashCommandCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith("/"):
            query = text.lower()
            for cmd, desc in SLASH_COMMANDS:
                if cmd.lower().startswith(query) or query in cmd.lower() or query.lstrip("/") in desc:
                    display_meta = desc
                    yield Completion(cmd, start_position=-len(text), display=f"{cmd:<12} {desc}", display_meta="")


def print_banner(display_cfg):
    banner_text = f"[bold cyan]🎯 Todo Agent CLI[/bold cyan] [dim](Python Edition)[/dim]\n"
    banner_text += f"[dim]输入 [green]/help[/green] 查看命令，或直接输入自然语言与 {display_cfg.ai_name} 交互[/dim]"
    console.print(Panel(banner_text, border_style="cyan", padding=(0, 2)))


def show_help():
    table = Table(title="📌 常用 Slash 命令帮助", title_style="bold green")
    table.add_column("命令", style="cyan", no_wrap=True)
    table.add_column("说明", style="white")

    for cmd, desc in SLASH_COMMANDS:
        table.add_row(cmd, desc)

    console.print(table)


def list_todos(db: DbState):
    service = TodoService(db)
    todos = service.get_todos("all", "")
    if not todos:
        console.print("[yellow]当前待办列表为空，使用 /add <标题> 新建一个吧！[/yellow]")
        return

    table = Table(title="📋 待办事项列表", title_style="bold blue")
    table.add_column("ID", style="dim", width=6)
    table.add_column("状态", width=8)
    table.add_column("优先级", width=10)
    table.add_column("分类", width=10)
    table.add_column("标题", style="bold")
    table.add_column("提醒时间", style="dim")

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


async def handle_command(
    cmd_line: str,
    db: DbState,
    llm_cfg: LlmConfig,
    history: List[Dict[str, str]],
    current_mode: Dict[str, Any],
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

    elif line == "/list":
        list_todos(db)
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

    elif line == "/chat":
        current_mode["role"] = "chat"
        current_mode["system_prompt"] = ""
        console.print("[cyan]已切换到常规 AI 聊天模式。[/cyan]")
        return True

    elif line == "/model":
        console.print(
            f"[cyan]当前模型: [bold]{llm_cfg.model}[/bold] (厂商: {llm_cfg.provider}, BaseUrl: {llm_cfg.base_url})[/cyan]"
        )
        return True

    elif line == "/provider":
        providers = ai_cfg_service.get_providers()
        if not providers:
            console.print("[yellow]当前未配置额外的 Provider 列表。[/yellow]")
        else:
            table = Table(title="🤖 已配置的 AI 模型供应商")
            table.add_column("ID", style="dim")
            table.add_column("名称", style="cyan")
            table.add_column("默认模型", style="green")
            table.add_column("Base URL", style="dim")
            for p in providers:
                table.add_row(p.get("id", ""), p.get("name", ""), p.get("model", ""), p.get("base_url", ""))
            console.print(table)
        return True

    # 其它自然语言或意图指令，调用 AI 执行
    with console.status(f"[cyan]{display_cfg.ai_name} 正在思考中...[/cyan]"):
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

            console.print(f"\n{result.message}\n")
            if result.should_refresh and result.action in ["add", "complete", "delete"]:
                list_todos(db)
        except Exception as e:
            console.print(f"[red]执行出错: {e}[/red]")

    return True


async def main_loop():
    db = DbState.get_instance()
    llm_cfg = load_current_llm_config(db)
    display_cfg = DisplayConfigService.load()

    # 处理单次 CLI 参数（如果用户直接传入子命令）
    if len(sys.argv) > 1:
        arg1 = sys.argv[1]
        if arg1 in ["--list", "-l", "list"]:
            list_todos(db)
            return
        elif arg1 in ["--help", "-h", "help"]:
            show_help()
            return
        elif arg1 in ["add", "todo"] and len(sys.argv) > 2:
            title = " ".join(sys.argv[2:])
            new_id = TodoService(db).add_todo(title)
            console.print(f"[green]✓ 已添加待办 #{new_id}: {title}[/green]")
            return

    print_banner(display_cfg)

    session = PromptSession(completer=SlashCommandCompleter())
    history: List[Dict[str, str]] = []
    current_mode: Dict[str, Any] = {"role": "chat", "system_prompt": ""}

    while True:
        try:
            prompt_str = f"<b><ansicyan>{display_cfg.user_prefix}</ansicyan></b> &gt; "
            user_input = await session.prompt_async(HTML(prompt_str))
            should_continue = await handle_command(
                user_input, db, llm_cfg, history, current_mode
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
