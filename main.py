import json
import os
import sys
import datetime
import urllib.error
import urllib.request
import re
from typing import List, Dict, Any, Optional, Literal, Tuple

# 解决 Windows 命令行中文与 Emoji 字符集问题
if sys.platform.startswith("win") and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 引入 Rich 终端可扩展高亮渲染库（优雅降级处理）
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from db_manager import TodoDatabase
from reminder_scheduler import global_reminder_scheduler, show_desktop_notification
from llm_client import (
    PerformanceMetrics,
    NativeOllamaLLM,
    SiliconFlowLLM,
    TOOLS_SCHEMA,
    load_config,
    save_config,
    mask_key,
    parse_user_intent,
    generate_todo_summary,
    prompt_select_llm,
    format_output_text,
    stream_print
)
from mode_config import (
    ModeConfig,
    get_mode_config,
    update_mode_config,
    register_custom_mode,
    list_all_modes,
    build_mode_messages
)


# =====================================================================
# TodoAgent 核心智能体控制器 (集成解耦模块与双模式引擎)
# =====================================================================

class TodoAgent:
    """结合 SQLite 数据库、定时调度器与大语言模型的智能待办事项 Agent"""

    def __init__(
        self,
        db_path: str = "todos.db",
        llm: Optional[Any] = None,
        show_detail: bool = False,
        enable_thinking: bool = False,
        enable_debug: bool = False,
        enable_sound: bool = True,
        mode: Literal["prompts", "agent", "chat"] = "agent"
    ):
        self.db = TodoDatabase(db_path)
        self.llm = llm
        self.show_detail = show_detail
        self.enable_thinking = enable_thinking
        self.enable_debug = enable_debug
        self.enable_sound = enable_sound
        self.mode = mode
        self.last_metrics: Optional[PerformanceMetrics] = None
        self.restore_reminders()

    def restore_reminders(self) -> None:
        """从数据库恢复活动中的定时提醒任务"""
        todos = self.db.get_pending_reminders()
        now = datetime.datetime.now()
        for t in todos:
            try:
                remind_dt = datetime.datetime.strptime(t["remind_at"], "%Y-%m-%d %H:%M:%S")
                delay = (remind_dt - now).total_seconds()
                if delay > 0:
                    global_reminder_scheduler.schedule_reminder(t["id"], t["title"], delay, enable_sound=self.enable_sound)
            except Exception:
                pass

    def print_debug_info(
        self,
        metrics: Optional[PerformanceMetrics],
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        parsed_action: Any = None
    ) -> None:
        """调试功能：全量交互日志展示"""
        if not self.enable_debug or not metrics:
            return

        print("\n🐛 " + "=" * 25 + " 【DEBUG: AI 交互全量信息】 " + "=" * 25)

        input_msgs = getattr(metrics, "input_messages", None)
        if input_msgs:
            print("🔹 【0. 用户上传的完整 Prompt 消息内容】:")
            try:
                print(json.dumps(input_msgs, ensure_ascii=False, indent=2))
            except Exception:
                print(str(input_msgs))

        raw = getattr(metrics, "raw_response", None)
        if raw is not None:
            print("🔹 【1. AI 原始响应内容 (Raw Response)】:")
            if isinstance(raw, (dict, list)):
                try:
                    print(json.dumps(raw, ensure_ascii=False, indent=2))
                except Exception:
                    print(str(raw))
            elif isinstance(raw, str):
                try:
                    parsed_json = json.loads(raw)
                    print(json.dumps(parsed_json, ensure_ascii=False, indent=2))
                except Exception:
                    print(raw)
            else:
                print(str(raw))

        if tool_calls is not None:
            print("\n🔹 【2. 工具调用信息 (Tool Calls)】:")
            if tool_calls:
                try:
                    print(json.dumps(tool_calls, ensure_ascii=False, indent=2))
                except Exception:
                    print(str(tool_calls))
            else:
                print("  (无工具调用)")

        if parsed_action is not None:
            print("\n🔹 【3. 解析后的意图对象 (Parsed Action)】:")
            if hasattr(parsed_action, "model_dump"):
                print(json.dumps(parsed_action.model_dump(), ensure_ascii=False, indent=2))
            elif hasattr(parsed_action, "dict"):
                print(json.dumps(parsed_action.dict(), ensure_ascii=False, indent=2))
            else:
                print(str(parsed_action))

        if self.enable_thinking and metrics.thinking_content:
            print("\n🔹 【4. 思考/推理过程 (Thinking Content)】:")
            print(metrics.thinking_content)

        think_status = "开启 🟢" if (getattr(metrics, "enable_thinking", False) or self.enable_thinking) else "关闭 🔴"
        print("\n🔹 【5. 性能与 Token 指标 (Performance Metrics)】:")
        print(f"  - 思考开关状态:      {think_status}")
        if (getattr(metrics, "enable_thinking", False) or self.enable_thinking) and metrics.thinking_duration > 0:
            print(f"  - 思考/推理耗时:    {metrics.thinking_duration:.3f} s")
        print(f"  - 首字延时 (TTFT):   {metrics.ttft * 1000:.1f} ms")
        print(f"  - 总共耗时:           {metrics.total_duration:.3f} s")
        print(f"  - 上传 Token:          {metrics.prompt_tokens}")
        print(f"  - 下载 Token:          {metrics.completion_tokens}")
        print("=" * 72 + "\n")

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """执行 Agent 原生 Tool Calling 工具函数"""
        if tool_name == "add_todo":
            title = args.get("title", "")
            if not title:
                return "⚠️ [Agent 工具调用] 任务标题不能为空。"
            priority = args.get("priority", "medium")
            category = args.get("category", "工作")
            delay_sec = args.get("delay_seconds")

            remind_at_str = None
            if delay_sec and delay_sec > 0:
                target_dt = datetime.datetime.now() + datetime.timedelta(seconds=delay_sec)
                remind_at_str = target_dt.strftime("%Y-%m-%d %H:%M:%S")

            new_id = self.db.add_todo(title, priority=priority, category=category, remind_at=remind_at_str)

            reminder_msg = ""
            if delay_sec and delay_sec > 0:
                global_reminder_scheduler.schedule_reminder(new_id, title, float(delay_sec), enable_sound=self.enable_sound)
                reminder_msg = f" ⏰ 已设置定时提醒：{delay_sec} 秒后 ({remind_at_str}) 桌面弹窗提醒！"

            return f"✅ [Agent 工具调用] 已成功添加待办事项 [{new_id}]: {title} (优先级: {priority}, 分类: {category}){reminder_msg}"

        elif tool_name == "list_todos":
            target_date = args.get("target_date")
            return self.get_list_text(target_date)

        elif tool_name == "complete_todo":
            todo_id = args.get("todo_id")
            if todo_id is None:
                return "⚠️ [Agent 工具调用] 请指定要完成的任务 ID。"
            if self.db.complete_todo(todo_id):
                global_reminder_scheduler.cancel_reminder(todo_id)
                return f"🎉 [Agent 工具调用] 已将任务 [{todo_id}] 标记为已完成！"
            return f"❌ [Agent 工具调用] 未找到 ID 为 {todo_id} 的任务。"

        elif tool_name == "uncomplete_todo":
            todo_id = args.get("todo_id")
            if todo_id is None:
                return "⚠️ [Agent 工具调用] 请指定要恢复为未完成的任务 ID。"
            if self.db.uncomplete_todo(todo_id):
                return f"↩️ [Agent 工具调用] 已将任务 [{todo_id}] 标记为未完成状态！"
            return f"❌ [Agent 工具调用] 未找到 ID 为 {todo_id} 的任务。"

        elif tool_name == "delete_todo":
            todo_id = args.get("todo_id")
            if todo_id is None:
                return "⚠️ [Agent 工具调用] 请指定要删除的任务 ID。"
            if self.db.delete_todo(todo_id):
                global_reminder_scheduler.cancel_reminder(todo_id)
                return f"🗑️ [Agent 工具调用] 已成功删除任务 [{todo_id}]。"
            return f"❌ [Agent 工具调用] 未找到 ID 为 {todo_id} 的任务。"

        elif tool_name == "update_todo":
            todo_id = args.get("todo_id")
            if todo_id is None:
                return "⚠️ [Agent 工具调用] 请指定要修改的任务 ID。"
            title = args.get("title")
            priority = args.get("priority")
            category = args.get("category")
            delay_sec = args.get("delay_seconds")

            remind_at_str = None
            if delay_sec and delay_sec > 0:
                target_dt = datetime.datetime.now() + datetime.timedelta(seconds=delay_sec)
                remind_at_str = target_dt.strftime("%Y-%m-%d %H:%M:%S")

            if self.db.update_todo(todo_id, title=title, priority=priority, category=category, remind_at=remind_at_str):
                if delay_sec and delay_sec > 0 and title:
                    global_reminder_scheduler.schedule_reminder(todo_id, title, float(delay_sec), enable_sound=self.enable_sound)
                return f"✏️ [Agent 工具调用] 已成功更新任务 [{todo_id}] 的属性！"
            return f"❌ [Agent 工具调用] 更新失败，未找到 ID 为 {todo_id} 的任务。"

        elif tool_name == "batch_complete_todos":
            todo_ids = args.get("todo_ids", [])
            if not todo_ids:
                return "⚠️ [Agent 工具调用] 请提供要完成的任务 ID 列表。"
            count = self.db.batch_complete(todo_ids)
            for tid in todo_ids:
                global_reminder_scheduler.cancel_reminder(tid)
            return f"🎉 [Agent 工具调用] 已批量将 {count} 个任务标记为已完成！"

        elif tool_name == "clear_completed":
            count = self.db.clear_completed()
            return f"🧹 [Agent 工具调用] 已清理全量 {count} 个已完成状态的待办事项。"

        elif tool_name == "query_todos":
            keyword = args.get("keyword", "")
            if not keyword:
                return "⚠️ [Agent 工具调用] 请提供搜索关键字。"
            matched = self.db.query_sql("""
                SELECT * FROM todos
                WHERE title LIKE ? OR category LIKE ?
                ORDER BY id DESC LIMIT 10
            """, (f"%{keyword}%", f"%{keyword}%"))
            if not matched:
                return f"🔍 [Agent 工具调用] 未找到包含 '{keyword}' 的任务。"
            lines = [f"🔍 **包含 '{keyword}' 的搜索结果 (SQL 过滤前10条)**:"]
            for item in matched:
                status = "✅" if item["completed"] else "🔲"
                lines.append(f"  {status} [{item['id']}] {item['title']}")
            return "\n".join(lines)

        elif tool_name == "summarize_todos":
            return self.summarize()

        return f"❓ 未知的工具调用名称: {tool_name}"

    def get_list_text(self, target_date: Optional[str] = None) -> str:
        """获取并格式化待办事项列表（支持 Rich 表格渲染）"""
        query_date = None
        date_label = ""
        now = datetime.datetime.now()

        if target_date:
            target_date_clean = target_date.strip().lower()
            if target_date_clean in ["today", "今天"]:
                query_date = now.strftime("%Y-%m-%d")
                date_label = f"今天 ({query_date})"
            elif target_date_clean in ["yesterday", "昨天"]:
                query_date = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                date_label = f"昨天 ({query_date})"
            elif target_date_clean in ["tomorrow", "明天"]:
                query_date = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                date_label = f"明天 ({query_date})"
            elif re.match(r'^\d{4}-\d{2}-\d{2}$', target_date_clean):
                query_date = target_date_clean
                date_label = query_date

        if query_date:
            todos = self.db.query_sql("""
                SELECT * FROM todos
                WHERE strftime('%Y-%m-%d', created_at) = ? OR strftime('%Y-%m-%d', remind_at) = ?
                ORDER BY completed ASC, id DESC
            """, (query_date, query_date))
            title_header = f"📋 {date_label} 的待办事项列表 (共 {len(todos)} 条):"
        else:
            todos = self.db.query_sql("SELECT * FROM todos ORDER BY completed ASC, id DESC LIMIT 20")
            title_header = "📋 当前待办事项列表 (前 20 条):"

        if not todos:
            if date_label:
                return f"📝 {date_label} 暂无任何待办事项。"
            return "📝 当前暂无任何待办事项。"

        if HAS_RICH:
            table = Table(title=title_header, show_header=True, header_style="bold cyan")
            table.add_column("ID", justify="right", style="bold yellow")
            table.add_column("状态", justify="center")
            table.add_column("任务标题", style="white")
            table.add_column("优先级", justify="center")
            table.add_column("分类", justify="center", style="magenta")
            table.add_column("提醒时间", style="green")

            for t in todos:
                status = "[green]✅ 已完成[/green]" if t["completed"] else "[yellow]🔲 待办[/yellow]"
                p = t.get("priority", "medium")
                p_str = "[red]High 🔴[/red]" if p == "high" else ("[yellow]Medium 🟡[/yellow]" if p == "medium" else "[blue]Low 🔵[/blue]")
                remind = t.get("remind_at") or "-"
                table.add_row(str(t["id"]), status, t["title"], p_str, t.get("category", "工作"), remind)

            console.print(table)
            return f"✅ 列表渲染完成 (共 {len(todos)} 条)"
        else:
            lines = [title_header]
            for t in todos:
                status = "✅" if t["completed"] else "🔲"
                p = t.get("priority", "medium")
                p_mark = "🔴" if p == "high" else ("🟡" if p == "medium" else "🔵")
                remind = f" ⏰ {t['remind_at']}" if t.get("remind_at") else ""
                lines.append(f"  {status} [{t['id']}] {t['title']} (优先级: {p_mark}{p}, 分类: {t.get('category', '工作')}){remind}")
            return "\n".join(lines)

    def summarize(self) -> str:
        """分析数据库数据并生成 AI 总结报告"""
        todos = self.db.query_sql("SELECT id, title, completed, priority, category, remind_at, created_at FROM todos")
        if not todos:
            return "📝 当前数据库无任何待办事项，无需生成总结报告。"

        total = len(todos)
        completed_count = sum(1 for t in todos if t["completed"])
        pending_count = total - completed_count
        high_priority_pending = [t for t in todos if not t["completed"] and t.get("priority") == "high"]

        summary_payload = {
            "statistics": {
                "total_todos": total,
                "completed_count": completed_count,
                "pending_count": pending_count,
                "completion_rate": f"{(completed_count / total) * 100:.1f}%"
            },
            "high_priority_urgent_tasks": high_priority_pending,
            "all_todos": todos
        }

        print("\n⏳ 正在分析 SQLite 数据并呼叫大模型生成智能总结报告...")
        summary_text, metrics = generate_todo_summary(summary_payload, self.llm)
        self.last_metrics = metrics
        return summary_text

    def check_api_key(self) -> bool:
        """检查当前选择的 Provider 是否已配置有效的 API Key"""
        if isinstance(self.llm, SiliconFlowLLM) and not self.llm.api_key:
            print("\n🔑 【未配置 API Key 提醒】")
            print("当前使用的是 硅基流动 (SiliconFlow) 在线 API 平台，但未检测到有效的 API Key。")
            print("可通过以下方式提供 Key：")
            print("  1. 输入 `/model` 命令重新配置并保存 Key")
            print("  2. 在 PowerShell 中设置环境变量：$env:SILICONFLOW_API_KEY=\"sk-xxxx\"")
            print("  3. 在 agent_config.json 中填入 \"siliconflow_api_key\": \"sk-xxxx\"\n")
            return False
        return True

    def run_agent_loop(self, user_input: str) -> None:
        """Agent 模式主逻辑 (Tool Calling 引擎)"""
        if not self.check_api_key():
            return

        mode_cfg = get_mode_config("agent")
        time_info = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        sys_prompt = f"{mode_cfg.system_prompt}\n当前时间: {time_info}"
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_input}
        ]

        if not self.llm or not hasattr(self.llm, "chat"):
            print("❌ 未配置有效 LLM。")
            return

        try:
            print("🤖 Agent 思考中...", end="", flush=True)
            if isinstance(self.llm, SiliconFlowLLM):
                url = f"{self.llm.host}/chat/completions"
                payload = {
                    "model": self.llm.model,
                    "messages": messages,
                    "tools": TOOLS_SCHEMA,
                    "tool_choice": "auto",
                    "stream": False
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.llm.api_key}"
                    },
                    method="POST"
                )
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                start_time = datetime.datetime.now()
                with opener.open(req, timeout=30) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))

                print("\r" + " " * 30 + "\r", end="", flush=True)
                choice = resp_data.get("choices", [{}])[0].get("message", {})
                tool_calls = choice.get("tool_calls", [])
                content = choice.get("content", "")

                metrics = PerformanceMetrics(
                    ttft=0.1,
                    total_duration=(datetime.datetime.now() - start_time).total_seconds(),
                    prompt_tokens=resp_data.get("usage", {}).get("prompt_tokens", 0),
                    completion_tokens=resp_data.get("usage", {}).get("completion_tokens", 0),
                    raw_response=resp_data,
                    input_messages=messages
                )
                self.print_debug_info(metrics, tool_calls=tool_calls)

                if tool_calls:
                    for tc in tool_calls:
                        fn_name = tc.get("function", {}).get("name")
                        fn_args_str = tc.get("function", {}).get("arguments", "{}")
                        try:
                            fn_args = json.loads(fn_args_str)
                        except Exception:
                            fn_args = {}

                        tool_res = self.execute_tool(fn_name, fn_args)
                        print(f"\n{tool_res}")
                elif content:
                    stream_print(content, prefix="🤖 Agent: ")
                else:
                    print("🤖 Agent: 我已为您处理完毕。")

            else:
                action, metrics = parse_user_intent(user_input, self.llm)
                print("\r" + " " * 30 + "\r", end="", flush=True)
                self.print_debug_info(metrics, parsed_action=action)
                self.handle_action(action)

        except urllib.error.HTTPError as http_err:
            print("\r" + " " * 30 + "\r", end="", flush=True)
            if http_err.code == 401:
                print("\n❌ [HTTP 401 Unauthorized 未授权错误]")
                print("访问 API 失败，原因：当前的 SiliconFlow API Key 无效或未提供。")
                print("请使用 `/model` 命令输入有效 Key，或设置环境变量 SILICONFLOW_API_KEY。")
            else:
                print(f"\n❌ [HTTP 请求异常 {http_err.code}]: {http_err.reason}")
        except Exception as e:
            print(f"\n❌ 执行 Agent 模式时发生异常: {e}")

    def run_prompts_loop(self, user_input: str) -> None:
        """Prompts 模式主逻辑"""
        if not self.check_api_key():
            return

        action, metrics = parse_user_intent(user_input, self.llm)
        self.print_debug_info(metrics, parsed_action=action)
        self.handle_action(action)

    def run_chat_loop(self, user_input: str) -> None:
        """Chat 纯聊天模式主逻辑"""
        if not self.check_api_key():
            return

        messages, mode_cfg = build_mode_messages("chat", user_input, enable_thinking=self.enable_thinking)
        if not self.llm or not hasattr(self.llm, "chat"):
            print("❌ 未配置有效 LLM。")
            return

        print("💬 AI: ", end="", flush=True)
        def on_token(token: str):
            sys.stdout.write(token)
            sys.stdout.flush()

        try:
            res_text, metrics = self.llm.chat(
                messages,
                json_format=False,
                temperature=mode_cfg.temperature,
                num_predict=mode_cfg.num_predict,
                on_token=on_token
            )
            sys.stdout.write("\n")
            self.print_debug_info(metrics)
        except urllib.error.HTTPError as http_err:
            print("\r" + " " * 30 + "\r", end="", flush=True)
            if http_err.code == 401:
                print("\n❌ [HTTP 401 Unauthorized 未授权错误] API Key 无效或失效。")

    def handle_action(self, action: Any) -> None:
        """根据解析的 TodoAction 执行对应数据逻辑"""
        act = getattr(action, "action", "chat")
        if act == "add":
            title = action.title or "无标题任务"
            new_id = self.db.add_todo(
                title=title,
                priority=action.priority or "medium",
                category=action.category or "工作",
                remind_at=action.remind_at
            )
            remind_str = f" ⏰ 已设置提醒时间：{action.remind_at}" if action.remind_at else ""
            print(f"✅ 已成功添加待办事项 [{new_id}]: {title}{remind_str}")
            if action.delay_seconds and action.delay_seconds > 0:
                global_reminder_scheduler.schedule_reminder(new_id, title, float(action.delay_seconds), enable_sound=self.enable_sound)

        elif act == "list":
            res = self.get_list_text(action.target_date)
            if not HAS_RICH or "渲染完成" not in res:
                print(res)

        elif act == "complete":
            if action.todo_id and self.db.complete_todo(action.todo_id):
                global_reminder_scheduler.cancel_reminder(action.todo_id)
                print(f"🎉 已将任务 [{action.todo_id}] 标记为已完成！")
            else:
                print(f"❌ 未找到 ID 为 {action.todo_id} 的任务。")

        elif act == "uncomplete":
            if action.todo_id and self.db.uncomplete_todo(action.todo_id):
                print(f"↩️ 已将任务 [{action.todo_id}] 恢复为未完成状态！")
            else:
                print(f"❌ 未找到 ID 为 {action.todo_id} 的任务。")

        elif act == "delete":
            if action.todo_id and self.db.delete_todo(action.todo_id):
                global_reminder_scheduler.cancel_reminder(action.todo_id)
                print(f"🗑️ 已成功删除任务 [{action.todo_id}]。")
            else:
                print(f"❌ 未找到 ID 为 {action.todo_id} 的任务。")

        elif act == "update":
            if action.todo_id and self.db.update_todo(action.todo_id, title=action.title, priority=action.priority, category=action.category):
                print(f"✏️ 已更新任务 [{action.todo_id}] 的属性！")
            else:
                print(f"❌ 修改失败，未找到 ID 为 {action.todo_id} 的任务。")

        elif act == "batch_complete":
            if action.todo_ids:
                count = self.db.batch_complete(action.todo_ids)
                print(f"🎉 已批量完成 {count} 个待办事项！")

        elif act == "clear_completed":
            count = self.db.clear_completed()
            print(f"🧹 已清理 {count} 个已完成的待办事项。")

        elif act == "query":
            kw = action.search_keyword or ""
            res = self.execute_tool("query_todos", {"keyword": kw})
            print(res)

        elif act == "chat":
            msg = action.reply_message or "您好！我是您的 Todo Agent 助手。"
            stream_print(msg, prefix="🤖 Agent: ")

        else:
            print("❓ 无法确定您的指令意图，请输入列表、添加任务或问答。")

    def process_command(self, user_input: str) -> None:
        """主路由控制"""
        if self.mode == "agent":
            self.run_agent_loop(user_input)
        elif self.mode == "prompts":
            self.run_prompts_loop(user_input)
        else:
            self.run_chat_loop(user_input)


# =====================================================================
# CLI 命令行入口与斜杠命令处理
# =====================================================================

def main():
    config = load_config()
    provider = config.get("provider", "siliconflow")
    model = config.get("model", "deepseek-ai/DeepSeek-V4-Flash")
    enable_thinking = config.get("enable_thinking", False)
    mode = config.get("mode", "agent")
    enable_debug = config.get("enable_debug", True)

    if provider == "siliconflow":
        api_key = config.get("siliconflow_api_key") or os.environ.get("SILICONFLOW_API_KEY", "")
        llm = SiliconFlowLLM(api_key=api_key, model=model, enable_thinking=enable_thinking)
    else:
        host = config.get("ollama_host", "http://localhost:11434")
        llm = NativeOllamaLLM(model=model, host=host, enable_thinking=enable_thinking)

    agent = TodoAgent(
        llm=llm,
        enable_thinking=enable_thinking,
        enable_debug=enable_debug,
        mode=mode
    )

    print("\n=======================================================")
    print("🚀 【Todo Agent 智能待办助手已准备就绪】")
    print(f"📌 当前 Provider: {provider} | 模型: {model}")
    print(f"⚙️ 当前工作模式: {mode} | Debug 调试: {'开启' if enable_debug else '关闭'}")
    print("💡 快捷命令: /mode 切换模式 | /think 控制思考 | /debug 调试 | exit 退出")
    print("=======================================================\n")

    while True:
        try:
            user_input = input("用户: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("👋 感谢使用 Todo Agent，再见！")
                break

            if user_input.startswith("/"):
                parts = user_input.split()
                cmd = parts[0].lower()
                if cmd == "/mode":
                    if len(parts) > 1 and parts[1] in ["agent", "prompts", "chat"]:
                        agent.mode = parts[1]
                        config["mode"] = parts[1]
                        save_config(config)
                        print(f"🔄 已切换模式为: {agent.mode}")
                    else:
                        print("用法: /mode agent | prompts | chat")
                elif cmd == "/think":
                    if len(parts) > 1 and parts[1] in ["on", "off"]:
                        val = (parts[1] == "on")
                        agent.enable_thinking = val
                        if hasattr(agent.llm, "enable_thinking"):
                            agent.llm.enable_thinking = val
                        config["enable_thinking"] = val
                        save_config(config)
                        print(f"🧠 思考推理状态设为: {val}")
                    else:
                        print("用法: /think on | off")
                elif cmd == "/debug":
                    agent.enable_debug = not agent.enable_debug
                    config["enable_debug"] = agent.enable_debug
                    save_config(config)
                    print(f"🐛 Debug 调试输出设为: {agent.enable_debug}")
                elif cmd == "/model":
                    llm_instance, new_cfg = prompt_select_llm(config)
                    agent.llm = llm_instance
                else:
                    print("未知斜杠命令，支持: /mode, /think, /debug, /model")
                continue

            agent.process_command(user_input)

        except (KeyboardInterrupt, EOFError):
            print("\n👋 程序已被中断。")
            break


if __name__ == "__main__":
    main()
