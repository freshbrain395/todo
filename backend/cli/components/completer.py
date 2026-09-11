"""CLI slash commands auto-completer component and custom completion menu."""

from typing import Any, List, Tuple
from prompt_toolkit import PromptSession as _PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.layout.menus import CompletionsMenuControl, _get_menu_item_fragments
from prompt_toolkit.application.current import get_app
from ..layout import get_terminal_width, truncate_to_width

SLASH_COMMANDS: List[Tuple[str, str]] = [
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
    """Slash command auto-completion provider for prompt_toolkit."""

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # /mode 二级补全 (仅在输入空格后提供模式参数候选)
        if text.startswith("/mode "):
            sub = text[len("/mode "):].lower()
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
        if text.startswith("/think "):
            sub = text[len("/think "):].lower()
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
        if text.startswith("/list "):
            sub = text[len("/list "):].lower()
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
        if text.startswith("/provider "):
            sub = text[len("/provider "):].lower()
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
        if text.startswith("/model "):
            sub = text[len("/model "):].lower()
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
                        display=f"{opt:<12} {desc}",
                    )
            return

        # /prompt 二级补全
        if text.startswith("/prompt "):
            sub = text[len("/prompt "):].lower()
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
        if text.startswith("/skill "):
            sub = text[len("/skill "):].lower()
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
