"""CLI Application for Todo Agent.

Integrates compact bordered prompt session, live integrated status-bar border,
auto-completing slash commands, and AI agent execution.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if not __package__:
    _cli_parent = str(Path(__file__).resolve().parent.parent)
    if _cli_parent not in sys.path:
        sys.path.insert(0, _cli_parent)
    __package__ = "cli"

if sys.platform == "win32":
    try:
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from prompt_toolkit.output.win32 import NoConsoleScreenBufferError
except ImportError:
    class NoConsoleScreenBufferError(Exception):
        pass

from dataclasses import dataclass

@dataclass
class ActionResult:
    message: str


class DbState:
    """CLI 独立数据库状态"""
    _instance = None

    @classmethod
    def get_instance(cls, path: Optional[str] = None):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


class DisplayConfig:
    """CLI 显示配置"""
    @classmethod
    def load(cls):
        return cls()


DEFAULT_AGENT_PROMPT = "你是一个全能的 Todo 智能助理，可以帮用户管理待办事项与回答问题。"
DEFAULT_CHAT_PROMPT = "你是一个亲切友好的对话助理。"
DEFAULT_JSON_PROMPT = "你是一个以结构化 JSON 格式响应的助理。"


async def parse_intent_and_execute(
    user_input: str,
    config: Optional[Any] = None,
    db: Optional[Any] = None,
    system_prompt: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> ActionResult:
    """处理用户自然语言输入（独立 CLI 模式）"""
    if not config or not getattr(config, "api_key", None):
        return ActionResult(
            message=f"已收到输入: \"{user_input}\"\n[dim]当前处于独立 CLI 模式（未配置 API Key）。可使用 [/dim][green]/provider set-key <id> <key>[/green][dim] 配置模型密钥，或使用 [/dim][green]/provider[/green][dim] 查看配置。[/dim]"
        )
    return ActionResult(message=f"已收到: \"{user_input}\"（供应商: {config.provider}, 模型: {config.model}）")


from .components.slash import (
    console,
    dispatch_command,
    CommandContext,
    get_registered_commands,
    load_current_llm_config,
    LlmConfig,
)
from .components.status_bar import (
    load_status_bar_items,
    save_status_bar_items,
)
from .components import (
    BoxedInputSession,
    CLI_STYLE,
    run_checkbox_menu,
    run_number_menu,
    run_radio_menu,
)
from .config import load_cli_config, show_welcome
from .utils import (
    display_width,
    get_terminal_height,
    get_terminal_width,
    pad_to_width,
    strip_ansi,
    truncate_to_width,
)


def get_border(cols: Optional[int] = None) -> str:
    """动态获取终端列宽，生成横线"""
    width = cols or get_terminal_width(80)
    return "─" * max(20, width - 2)


class CliAgentApp:
    """CLI Agent 核心会话与调度器"""

    def __init__(self, db_path: Optional[str] = None):
        self.db = DbState.get_instance(db_path) if db_path else DbState.get_instance()
        self.cli_cfg: Dict[str, Any] = load_cli_config()
        self.llm_cfg: LlmConfig = load_current_llm_config(self.db)
        self.display_cfg = DisplayConfig.load()
        self.status_bar_state: Dict[str, Any] = {"items": load_status_bar_items(self.db)}
        self.current_mode: Dict[str, Any] = {
            "name": "agent",
            "role": "agent",
            "display_name": "Agent助理",
            "status_text": "就绪",
            "system_prompt": DEFAULT_AGENT_PROMPT,
            "output_format": "text",
        }
        self.history: List[Dict[str, str]] = []

    async def handle_input(self, text: str, session: Optional[Any] = None) -> Optional[bool]:
        """
        分发处理输入：斜线指令、系统指令或 AI 对话。
        返回 False 表示退出程序，返回 True 表示处理完毕，返回 None 表示继续。
        """
        trimmed = text.strip()
        if not trimmed:
            return True

        # 1. 优先通过命令注册器分发斜线指令与常用快捷系统别名 (如 /quit, quit, /exit, exit, /clear, cls 等)
        if trimmed.startswith("/") or trimmed.lower() in ("exit", "quit", "clear", "cls", "exit()", "quit()", ":q"):
            cmd_res = await self._dispatch_slash_command(trimmed, session=session)
            if cmd_res is False:
                return False
            return True

        # 2. 自然语言对话与 Agent 意图识别执行
        await self._process_ai_interaction(trimmed)
        return True

    async def _dispatch_slash_command(self, trimmed: str, session: Optional[Any] = None) -> Optional[bool]:
        """内部派发斜线命令（通过注册器自动分发）"""
        ctx = CommandContext(
            app=self,
            db=self.db,
            llm_cfg=self.llm_cfg,
            current_mode=self.current_mode,
            display_cfg=self.display_cfg,
            status_bar_state=self.status_bar_state,
            menu_runner=run_number_menu,
            extra={
                "history": self.history,
                "checkbox_runner": run_checkbox_menu,
                "session": session,
            },
        )
        res = await dispatch_command(trimmed, ctx)
        if res is not None:
            return res

        # 未知斜线指令
        cmd_name = trimmed.split()[0]
        ctx.current_cmd = cmd_name
        ctx.show_result(
            f"[red]未知斜线命令: [bold]{cmd_name}[/bold][/red]\n请输入 [green]/help[/green] 查看所有可用命令与详细用法。",
            status="error",
            hint="输入 / 配合 Tab 键可快速联想补全可用命令",
        )
        return True

    def _trim_history(self, max_turns: int = 30) -> None:
        """修剪对话历史记录"""
        max_msgs = max_turns * 2
        if len(self.history) > max_msgs:
            self.history = self.history[-max_msgs:]

    async def _process_ai_interaction(self, user_msg: str) -> None:
        """处理与 AI 的对话交互"""
        self.history.append({"role": "user", "content": user_msg})
        self._trim_history()

        mode_name = self.current_mode.get("display_name", "Agent助理")
        console.print(f"[dim]🤖 {mode_name} 思考中...[/dim]")

        try:
            action_result = await parse_intent_and_execute(
                user_input=user_msg,
                config=self.llm_cfg,
                db=self.db,
                system_prompt=self.current_mode.get("system_prompt"),
                history=self.history[:-1],
            )
            reply = action_result.message
            console.print(f"[bold cyan]🤖 {mode_name}:[/bold cyan] {reply}\n")
            self.history.append({"role": "assistant", "content": reply})
            self._trim_history()
        except Exception as e:
            console.print(f"[red]请求异常: {e}[/red]\n")


async def run_prompt_toolkit_async() -> None:
    """异步运行适配最新输入框与状态栏的 prompt_toolkit 交互循环"""
    app = CliAgentApp()

    # 启动时优先显示欢迎信息（来自 cli/config.json）
    show_welcome(app.cli_cfg, console=console)

    # 统一使用抽取的自适应输入框组件会话
    input_session = BoxedInputSession(app)
    last_interrupt_time = 0.0

    while True:
        try:
            mode_name = app.current_mode.get("display_name", "Agent")
            text = await input_session.prompt_async(rprompt_text=mode_name)
            if not text:
                continue

            # 分发处理斜线指令或 AI 对话（传入 session 供清屏等命令精准复位）
            ret = await app.handle_input(text, session=input_session.session)
            if ret is False:
                break

            # 执行完命令后，重置 renderer 状态，确保下一轮输入时边框和状态栏紧随当前物理光标
            input_session.reset_renderer()

        except KeyboardInterrupt:
            import time
            now = time.monotonic()
            if now - last_interrupt_time < 1.5:
                console.print("\n[bold yellow]👋 退出 Todo Agent，再见！[/bold yellow]")
                break
            last_interrupt_time = now
            console.print("\n[dim]提示: 按 Ctrl+C 再次退出，或输入 'exit' 退出程序。[/dim]")
            input_session.reset_renderer()
            continue
        except EOFError:
            console.print("\n[bold yellow]👋 退出 Todo Agent，再见！[/bold yellow]")
            break


def run_prompt_toolkit() -> None:
    """同步包装入口"""
    asyncio.run(run_prompt_toolkit_async())


def run_fallback() -> None:
    """非交互式控制台环境下的降级实现"""
    app = CliAgentApp()
    show_welcome(app.cli_cfg, console=console)
    print("=== Todo Agent [标准输入降级模式] (输入 'exit' 退出) ===")
    while True:
        try:
            line = input("❯ ")
            text = line.strip()
            if not text:
                continue
            ret = asyncio.run(app.handle_input(text))
            if ret is False:
                break
        except (KeyboardInterrupt, EOFError):
            print("\n退出程序。")
            break


def main() -> None:
    """主启动入口"""
    try:
        run_prompt_toolkit()
    except NoConsoleScreenBufferError:
        print("[提示] 检测到当前非交互式控制台环境，自动降级为标准输入模式。")
        run_fallback()


run_cli = main

__all__ = [
    "main",
    "run_cli",
    "run_prompt_toolkit",
    "run_prompt_toolkit_async",
    "run_fallback",
    "CliAgentApp",
    "load_cli_config",
    "show_welcome",
    "get_border",
    "get_terminal_width",
    "get_terminal_height",
    "truncate_to_width",
    "pad_to_width",
    "display_width",
    "strip_ansi",
    "run_number_menu",
    "run_radio_menu",
    "run_checkbox_menu",
]

if __name__ == "__main__":
    main()
