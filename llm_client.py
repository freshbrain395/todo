import json
import os
import sys
import subprocess
import urllib.request
import urllib.error
import datetime
import time
import re
from typing import List, Dict, Any, Optional, Literal, Tuple
from pydantic import BaseModel, Field

# 解决 Windows 命令行中文与 Emoji 字符集问题
if sys.platform.startswith("win") and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 自动禁用 localhost 的网络代理，防止请求走系统代理触发 502 Bad Gateway 错误
os.environ["NO_PROXY"] = "localhost,127.0.0.1," + os.environ.get("NO_PROXY", "")
os.environ["no_proxy"] = "localhost,127.0.0.1," + os.environ.get("no_proxy", "")

for env_var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    os.environ.pop(env_var, None)
os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"


# =====================================================================
# 1. 原生 Agent 工具调用 (Tool Calling / Function Calling) 定义
# =====================================================================

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "add_todo",
            "description": "添加新的待办事项，支持标题、任务优先级、分类标签以及相对延时提醒秒数。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "待办事项标题或任务描述"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "优先级，如 low, medium, high"},
                    "category": {"type": "string", "description": "分类标签，如工作、学习、生活、个人"},
                    "delay_seconds": {"type": "integer", "description": "相对延时提醒秒数（例如 10秒后填 10，10分钟后填 600）"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_todos",
            "description": "查询待办事项列表，支持按日期（如今天、明天、昨天或 YYYY-MM-DD）进行筛选。",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_date": {"type": "string", "description": "目标筛选日期，如 today, tomorrow, yesterday 或 2026-07-31"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "complete_todo",
            "description": "将指定编号 (ID) 的待办事项标记为已完成。",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {"type": "integer", "description": "待完成任务的数字 ID 编号"}
                },
                "required": ["todo_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "uncomplete_todo",
            "description": "将指定编号 (ID) 的已完成待办事项重新标记为未完成状态。",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {"type": "integer", "description": "待恢复为未完成状态的任务数字 ID 编号"}
                },
                "required": ["todo_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_todo",
            "description": "从数据库中删除指定编号 (ID) 的待办事项。",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {"type": "integer", "description": "待删除任务的数字 ID 编号"}
                },
                "required": ["todo_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_todo",
            "description": "更新已有的待办事项属性，例如修改标题、优先级、分类标签或定时提醒秒数。",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {"type": "integer", "description": "待修改任务的数字 ID 编号"},
                    "title": {"type": "string", "description": "新的任务标题"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "新的优先级"},
                    "category": {"type": "string", "description": "新的分类标签"},
                    "delay_seconds": {"type": "integer", "description": "重新设定的提醒延迟秒数"}
                },
                "required": ["todo_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "batch_complete_todos",
            "description": "一次性批量完成多个待办事项 ID。",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "需要标记完成的待办事项 ID 列表，例如 [1, 2, 3]"
                    }
                },
                "required": ["todo_ids"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "clear_completed",
            "description": "清理或批量删除所有已完成状态的待办事项。",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_todos",
            "description": "按关键字模糊搜索相关的待办事项。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜索关键字"}
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_todos",
            "description": "分析并生成当前所有待办事项的进度总结与改进建议报告。",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


# =====================================================================
# 2. 性能指标统计与格式化工具
# =====================================================================

class PerformanceMetrics:
    """性能与 Token 统计数据模型"""
    def __init__(
        self,
        ttft: float = 0.0,
        total_duration: float = 0.0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        thinking_content: str = "",
        raw_response: Any = None,
        enable_thinking: bool = False,
        thinking_duration: float = 0.0,
        reasoning_tokens: int = 0,
        input_messages: Optional[List[Dict[str, str]]] = None
    ):
        self.ttft = ttft
        self.total_duration = total_duration
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.thinking_content = thinking_content
        self.raw_response = raw_response
        self.enable_thinking = enable_thinking
        self.thinking_duration = thinking_duration
        self.reasoning_tokens = reasoning_tokens
        self.input_messages = input_messages

    def format_summary(self) -> str:
        """格式化输出性能详情字符串"""
        ttft_ms = self.ttft * 1000
        think_status = "开启 🟢" if self.enable_thinking else "关闭 🔴"
        think_duration_str = f" | 思考耗时: {self.thinking_duration:.3f}s" if self.enable_thinking and self.thinking_duration > 0 else ""
        reasoning_token_str = f" | 思考 Token: {self.reasoning_tokens}" if self.enable_thinking and self.reasoning_tokens > 0 else ""
        return (
            f"📊 【性能详情】 "
            f"思考开关: {think_status}"
            f"{think_duration_str}"
            f"{reasoning_token_str} | "
            f"首字延时: {ttft_ms:.1f}ms ({self.ttft:.3f}s) | "
            f"总耗时: {self.total_duration:.3f}s | "
            f"上传 Token: {self.prompt_tokens} | "
            f"下载 Token: {self.completion_tokens}"
        )


def format_output_text(text: str) -> str:
    """清理并规范化文本格式"""
    if not text:
        return ""
    cleaned = re.sub(r'\n{3,}', '\n\n', text)
    return cleaned.strip()


def stream_print(text: str, prefix: str = "", delay: float = 0.004) -> None:
    """在控制台打印打字流式文本"""
    cleaned_text = format_output_text(text)
    if not cleaned_text:
        return

    if prefix:
        sys.stdout.write(prefix)
        sys.stdout.flush()

    for char in cleaned_text:
        sys.stdout.write(char)
        sys.stdout.flush()
        if char in ["\n", "。", "！", "？", "!", "?", "；", ";"]:
            time.sleep(delay * 3)
        else:
            time.sleep(delay)

    sys.stdout.write("\n")
    sys.stdout.flush()


def mask_key(api_key: str) -> str:
    """脱敏遮蔽敏感 API Key"""
    if not api_key:
        return "未配置"
    if len(api_key) <= 10:
        return "*******"
    return f"{api_key[:6]}...{api_key[-4:]}"


# =====================================================================
# 3. 原生 Ollama API 客户端
# =====================================================================

class NativeOllamaLLM:
    """高性能 Ollama 客户端"""

    def __init__(self, model: str = "qwen3.5:0.8b", host: str = "http://localhost:11434", enable_thinking: bool = False):
        if not host.startswith("http://") and not host.startswith("https://"):
            host = f"http://{host}"
        self.host = host.rstrip("/")
        self.model = model
        self.enable_thinking = enable_thinking

    def chat(
        self,
        messages: List[Dict[str, str]],
        json_format: bool = True,
        temperature: float = 0.0,
        num_predict: int = 128,
        on_token: Optional[Any] = None,
        on_think: Optional[Any] = None
    ) -> Tuple[str, PerformanceMetrics]:
        url = f"{self.host}/api/chat"
        payload_dict: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "think": self.enable_thinking,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict
            }
        }
        if json_format:
            payload_dict["format"] = "json"

        payload = json.dumps(payload_dict).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        metrics = PerformanceMetrics(enable_thinking=self.enable_thinking, input_messages=messages)
        start_time = time.perf_counter()
        first_token_time = None
        first_think_time = None
        first_content_time = None
        full_chunks: List[str] = []
        thinking_chunks: List[str] = []

        try:
            with opener.open(req, timeout=60) as response:
                for line in response:
                    if not line:
                        continue
                    try:
                        data = json.loads(line.decode("utf-8"))
                        msg = data.get("message", {})

                        reasoning = msg.get("reasoning_content", "")
                        if reasoning:
                            if self.enable_thinking:
                                if first_think_time is None:
                                    first_think_time = time.perf_counter()
                                thinking_chunks.append(reasoning)
                                if on_think:
                                    on_think(reasoning)

                        content = msg.get("content", "")
                        if content:
                            if first_content_time is None:
                                first_content_time = time.perf_counter()
                            full_chunks.append(content)
                            if on_token:
                                on_token(content)

                        if (reasoning or content) and first_token_time is None:
                            first_token_time = time.perf_counter()
                            metrics.ttft = first_token_time - start_time

                        if data.get("done", False):
                            metrics.prompt_tokens = data.get("prompt_eval_count", 0)
                            metrics.completion_tokens = data.get("eval_count", 0)
                    except Exception:
                        pass
        except Exception as e:
            metrics.total_duration = time.perf_counter() - start_time
            raise e

        end_time = time.perf_counter()
        metrics.total_duration = end_time - start_time
        if metrics.ttft == 0:
            metrics.ttft = metrics.total_duration
        if first_think_time and first_content_time:
            metrics.thinking_duration = first_content_time - first_think_time

        metrics.thinking_content = "".join(thinking_chunks)
        final_text = "".join(full_chunks)
        metrics.raw_response = final_text
        return final_text, metrics


def get_ollama_models(host: str = "http://localhost:11434") -> List[str]:
    """获取可用 Ollama 模型列表"""
    default_models = ["qwen2.5:0.5b", "qwen2.5:1.5b", "deepseek-r1:1.5b"]
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"http://{host}"
    host = host.rstrip("/")

    url = f"{host}/api/tags"
    try:
        req = urllib.request.Request(url, method="GET")
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                return [m["name"] for m in data.get("models", []) if isinstance(m, dict) and "name" in m]
    except Exception:
        pass

    try:
        res = subprocess.run(["ollama", "list"], capture_output=True, text=True, errors="ignore", timeout=5)
        if res.returncode == 0 and res.stdout:
            lines = res.stdout.strip().splitlines()
            models = []
            for line in lines[1:]:
                parts = line.split()
                if parts:
                    models.append(parts[0])
            return models
    except Exception:
        pass

    return default_models


# =====================================================================
# 4. 硅基流动 (SiliconFlow) API 客户端 (支持重试与环境变量)
# =====================================================================

class SiliconFlowLLM:
    """支持指数退避重试与环境变量降级的 SiliconFlow 客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-ai/DeepSeek-V4-Flash",
        host: str = "https://api.siliconflow.cn/v1",
        enable_thinking: bool = False,
        max_retries: int = 3
    ):
        if not host.startswith("http://") and not host.startswith("https://"):
            host = f"https://{host}"
        self.host = host.rstrip("/")
        self.api_key = (api_key or os.environ.get("SILICONFLOW_API_KEY") or "").strip()
        self.model = model
        self.enable_thinking = enable_thinking
        self.max_retries = max_retries

    def chat(
        self,
        messages: List[Dict[str, str]],
        json_format: bool = True,
        temperature: float = 0.7,
        num_predict: int = 512,
        on_token: Optional[Any] = None,
        on_think: Optional[Any] = None
    ) -> Tuple[str, PerformanceMetrics]:
        url = f"{self.host}/chat/completions"
        payload_dict: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
            "max_tokens": num_predict,
            "enable_thinking": self.enable_thinking,
            "think": self.enable_thinking
        }
        if json_format:
            payload_dict["response_format"] = {"type": "json_object"}

        payload = json.dumps(payload_dict).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            method="POST"
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        metrics = PerformanceMetrics(enable_thinking=self.enable_thinking, input_messages=messages)
        start_time = time.perf_counter()

        for attempt in range(self.max_retries):
            first_token_time = None
            first_think_time = None
            first_content_time = None
            full_chunks: List[str] = []
            thinking_chunks: List[str] = []

            try:
                with opener.open(req, timeout=60) as response:
                    for line in response:
                        if not line:
                            continue
                        line_str = line.decode("utf-8").strip()
                        if line_str.startswith("data: "):
                            line_str = line_str[6:].strip()
                        if line_str == "[DONE]":
                            break
                        if not line_str:
                            continue
                        try:
                            data = json.loads(line_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})

                            reasoning = delta.get("reasoning_content", "")
                            if reasoning:
                                if self.enable_thinking:
                                    if first_think_time is None:
                                        first_think_time = time.perf_counter()
                                    thinking_chunks.append(reasoning)
                                    if on_think:
                                        on_think(reasoning)

                            content = delta.get("content", "")
                            if content:
                                if first_content_time is None:
                                    first_content_time = time.perf_counter()
                                full_chunks.append(content)
                                if on_token:
                                    on_token(content)

                            if (reasoning or content) and first_token_time is None:
                                first_token_time = time.perf_counter()
                                metrics.ttft = first_token_time - start_time

                            usage = data.get("usage")
                            if usage:
                                metrics.prompt_tokens = usage.get("prompt_tokens", 0)
                                metrics.completion_tokens = usage.get("completion_tokens", 0)
                                details = usage.get("completion_tokens_details") or {}
                                metrics.reasoning_tokens = details.get("reasoning_tokens") or usage.get("reasoning_tokens", 0)
                        except Exception:
                            pass

                end_time = time.perf_counter()
                metrics.total_duration = end_time - start_time
                if metrics.ttft == 0:
                    metrics.ttft = metrics.total_duration
                if first_think_time and first_content_time:
                    metrics.thinking_duration = first_content_time - first_think_time

                metrics.thinking_content = "".join(thinking_chunks)
                final_text = "".join(full_chunks)
                metrics.raw_response = final_text
                return final_text, metrics

            except Exception as e:
                if attempt == self.max_retries - 1:
                    metrics.total_duration = time.perf_counter() - start_time
                    raise e
                time.sleep(1.5 * (attempt + 1))


def get_siliconflow_models(api_key: Optional[str] = None) -> List[str]:
    """获取可用 SiliconFlow 模型列表"""
    default_models = [
        "deepseek-ai/DeepSeek-V4-Flash",
        "deepseek-ai/DeepSeek-V3",
        "deepseek-ai/DeepSeek-R1",
        "Qwen/Qwen2.5-7B-Instruct",
        "THUDM/glm-4-9b-chat"
    ]
    key = (api_key or os.environ.get("SILICONFLOW_API_KEY") or "").strip()
    if not key:
        return default_models

    url = "https://api.siliconflow.cn/v1/models"
    try:
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {key}"},
            method="GET"
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                models = [m["id"] for m in data.get("data", []) if isinstance(m, dict) and "id" in m]
                return models if models else default_models
    except Exception:
        pass

    return default_models


# =====================================================================
# 5. 配置持久化与读取 (融入环境变量)
# =====================================================================

CONFIG_FILE = "agent_config.json"

def load_config() -> Dict[str, Any]:
    """读取配置文件，并融合环境变量"""
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            pass

    env_key = os.environ.get("SILICONFLOW_API_KEY", "").strip()
    if env_key and not config.get("siliconflow_api_key"):
        config["siliconflow_api_key"] = env_key

    return config

def save_config(config: Dict[str, Any]) -> None:
    """保存配置信息"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# =====================================================================
# 6. 系统 Prompt 与意图解析引擎
# =====================================================================

class TodoAction(BaseModel):
    """自然语言待办事项意图解析模型"""
    action: Literal["add", "list", "complete", "uncomplete", "delete", "update", "batch_complete", "clear_completed", "query", "chat", "unknown"] = Field(
        description="操作类型"
    )
    todo_id: Optional[int] = Field(default=None, description="待办事项编号/ID")
    todo_ids: Optional[List[int]] = Field(default=None, description="待办事项编号列表 (用于批量操作)")
    title: Optional[str] = Field(default=None, description="待办事项标题或内容描述")
    priority: Optional[Literal["low", "medium", "high"]] = Field(default="medium", description="任务优先级")
    category: Optional[str] = Field(default="工作", description="分类标签，如：工作、学习、生活、个人")
    search_keyword: Optional[str] = Field(default=None, description="搜索关键字")
    delay_seconds: Optional[int] = Field(default=None, description="从现在开始需延迟提醒的秒数")
    remind_at: Optional[str] = Field(default=None, description="提醒目标时间点")
    target_date: Optional[str] = Field(default=None, description="目标查询日期，格式为 YYYY-MM-DD 或 today/yesterday/tomorrow")
    reply_message: Optional[str] = Field(default=None, description="给用户的即时自然语言回复")


INTENT_SYSTEM_PROMPT = """你是一个智能待办事项 (Todo Agent) 的意图识别与结构化提取引擎。
你的任务是将用户的自然语言转换为准确的操作指令 JSON。

当前系统参考时间: {current_time}

核心要求：
1. 必须直接输出 JSON 对象！严禁输出任何说明！
2. 【严格禁用思考】：请勿输出任何 <think>...</think> 思考过程，必须直接输出最终 JSON。

操作类型定义与 JSON 字段说明：
- action: "add" | "list" | "complete" | "uncomplete" | "delete" | "update" | "batch_complete" | "clear_completed" | "query" | "chat" | "unknown"
- todo_id: 数字
- todo_ids: 数字数组 (仅 batch_complete 需要)
- title: 任务名称
- priority: "low" | "medium" | "high"
- category: "工作" | "学习" | "生活" | "个人"
- delay_seconds: 相对延迟秒数
- target_date: 目标查询日期 ("today", "tomorrow", "yesterday", "YYYY-MM-DD")
- search_keyword: 仅当用户明确要求“查找/搜索/包含XXX”时填入具体的关键字
- reply_message: 闲聊回复

意图识别与映射规则：
1. 用户输入“今天的待办”、“今天是”、“查一下今天”等提到今天/日期时，必须输出 {{"action": "list", "target_date": "today"}}。
2. 只有当用户显式提出“搜索XXX”或“查找包含XXX”时才使用 "query" 动作。
"""

SUMMARY_SYSTEM_PROMPT = """你是一个高效率、温暖贴心的待办事项管家。
请分析以下待办事项 JSON 数据，为用户生成一份结构清晰、有条理且富有鼓励性的总结与建议报告。
"""


def extract_time_delay(user_input: str) -> Optional[int]:
    """正则提取时间延迟"""
    sec_match = re.search(r'(\d+)\s*(?:秒钟|秒|sec|seconds)', user_input)
    if sec_match:
        return int(sec_match.group(1))

    min_match = re.search(r'(\d+)\s*(?:分钟|分|min|minutes)', user_input)
    if min_match:
        return int(min_match.group(1)) * 60

    hr_match = re.search(r'(\d+)\s*(?:小时|钟头|hour|hours)', user_input)
    if hr_match:
        return int(hr_match.group(1)) * 3600

    day_match = re.search(r'(\d+)\s*(?:天|day|days)', user_input)
    if day_match:
        return int(day_match.group(1)) * 86400

    return None


KEY_ALIAS_MAP = {
    "a": "action",
    "act": "action",
    "action": "action",
    "r": "reply_message",
    "reply": "reply_message",
    "reply_message": "reply_message",
    "t": "title",
    "task": "title",
    "time": "title",
    "title": "title",
    "p": "priority",
    "priority": "priority",
    "c": "category",
    "category": "category",
    "d": "delay_seconds",
    "delay": "delay_seconds",
    "delay_seconds": "delay_seconds",
    "id": "todo_id",
    "todo_id": "todo_id",
    "ids": "todo_ids",
    "todo_ids": "todo_ids",
    "s": "search_keyword",
    "search_keyword": "search_keyword",
    "date": "target_date",
    "target_date": "target_date"
}


def sanitize_and_build_action(data: dict, user_input: str = "") -> TodoAction:
    """规范化字段与智能退避容错处理"""
    normalized = {}
    for k, v in data.items():
        clean_key = str(k).strip()
        full_key = KEY_ALIAS_MAP.get(clean_key, clean_key)
        normalized[full_key] = v

    action = normalized.get("action")
    valid_actions = ["add", "list", "complete", "uncomplete", "delete", "update", "batch_complete", "clear_completed", "query", "chat", "unknown"]
    if not isinstance(action, str) or action.strip() not in valid_actions:
        normalized["action"] = "unknown"
    else:
        normalized["action"] = action.strip()

    # 智能容错修正 1：当解析出的 action == "query" 但 search_keyword 为空或无效时
    kw = normalized.get("search_keyword")
    if normalized["action"] == "query" and (not kw or not str(kw).strip()):
        if "今天" in user_input or "today" in user_input.lower():
            normalized["action"] = "list"
            normalized["target_date"] = "today"
        elif "明天" in user_input or "tomorrow" in user_input.lower():
            normalized["action"] = "list"
            normalized["target_date"] = "tomorrow"
        else:
            normalized["action"] = "list"

    p = normalized.get("priority")
    if isinstance(p, str) and p.strip() in ["low", "medium", "high"]:
        normalized["priority"] = p.strip()
    else:
        normalized["priority"] = "medium"

    cat = normalized.get("category")
    if isinstance(cat, str) and cat.strip():
        normalized["category"] = cat.strip()
    else:
        normalized["category"] = "工作"

    title = normalized.get("title")
    if isinstance(title, str):
        title = title.strip()
        normalized["title"] = title if title else None

    ds = normalized.get("delay_seconds")
    if ds is not None:
        try:
            if isinstance(ds, str):
                ds_num = re.sub(r'\D', '', ds)
                ds = int(ds_num) if ds_num else None
            elif isinstance(ds, (int, float)):
                ds = int(ds)
            normalized["delay_seconds"] = ds
        except Exception:
            normalized["delay_seconds"] = None

    tid = normalized.get("todo_id")
    if tid is not None:
        try:
            if isinstance(tid, str):
                tid_num = re.sub(r'\D', '', tid)
                tid = int(tid_num) if tid_num else None
            elif isinstance(tid, (int, float)):
                tid = int(tid)
            normalized["todo_id"] = tid
        except Exception:
            normalized["todo_id"] = None

    reply = normalized.get("reply_message")
    if isinstance(reply, str):
        reply = reply.strip()
        normalized["reply_message"] = reply if reply else None

    return TodoAction(**normalized)


def extract_fallback_dict(text: str) -> dict:
    """从正则救回 JSON"""
    data = {}
    act_m = re.search(r'"(?:action|a|act)"\s*:\s*"([^"]+)"', text)
    if act_m:
        data["action"] = act_m.group(1)
    rep_m = re.search(r'"(?:reply_message|reply|r)"\s*:\s*"([^"]+)"', text)
    if rep_m:
        data["reply_message"] = rep_m.group(1)
    title_m = re.search(r'"(?:title|t|task|time)"\s*:\s*"([^"]+)"', text)
    if title_m:
        data["title"] = title_m.group(1)

    if not data:
        data = {"action": "chat", "reply_message": "您好！我是您的 Todo Agent 助手。有什么我可以帮您的吗？"}
    return data


def parse_user_intent(user_input: str, llm: Any) -> Tuple[TodoAction, PerformanceMetrics]:
    """处理自然语言意图并生成 TodoAction"""
    now = datetime.datetime.now()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    current_time_str = f"{now.strftime('%Y-%m-%d %H:%M:%S')} ({weekdays[now.weekday()]})"

    system_content = INTENT_SYSTEM_PROMPT.format(current_time=current_time_str)
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": f"用户输入: {user_input}"}
    ]

    try:
        if hasattr(llm, "chat"):
            raw_response, metrics = llm.chat(messages, json_format=True, temperature=0.0, num_predict=512)
        else:
            metrics = PerformanceMetrics()
            raw_response = "{}"

        cleaned = re.sub(r'<think>.*?</think>', '', raw_response, flags=re.DOTALL)
        cleaned = re.sub(r'<think>.*$', '', cleaned, flags=re.DOTALL).strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        cleaned_json_str = re.sub(r'[\r\n]+', ' ', cleaned)

        try:
            action_data = json.loads(cleaned_json_str)
        except Exception:
            json_match = re.search(r'\{.*\}', cleaned_json_str)
            if json_match:
                try:
                    action_data = json.loads(json_match.group(0))
                except Exception:
                    action_data = extract_fallback_dict(cleaned_json_str)
            else:
                action_data = extract_fallback_dict(cleaned_json_str)

        action_result = sanitize_and_build_action(action_data, user_input=user_input)

        regex_delay = extract_time_delay(user_input)
        if regex_delay is not None and action_result.action == "add":
            action_result.delay_seconds = regex_delay
            action_result.remind_at = (now + datetime.timedelta(seconds=regex_delay)).strftime("%Y-%m-%d %H:%M:%S")

        return action_result, metrics
    except Exception as e:
        metrics = PerformanceMetrics()
        return TodoAction(
            action="chat",
            reply_message=f"抱歉，理解您的指令时遇到点问题 ({e})，请问有什么可以帮您？"
        ), metrics


def generate_todo_summary(summary_payload: Dict[str, Any], llm: Any) -> Tuple[str, PerformanceMetrics]:
    """生成待办事项总结报告"""
    payload_json = json.dumps(summary_payload, ensure_ascii=False, indent=2)
    messages = [
        {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
        {"role": "user", "content": f"待办事项列表数据:\n{payload_json}"}
    ]
    try:
        if hasattr(llm, "chat"):
            summary_text, metrics = llm.chat(messages, json_format=False, num_predict=512)
        else:
            summary_text = "未配置有效 LLM"
            metrics = PerformanceMetrics()
        return summary_text, metrics
    except Exception as e:
        return f"生成任务总结时发生错误: {e}", PerformanceMetrics()


def prompt_select_llm(existing_config: Optional[Dict[str, Any]] = None) -> Tuple[Any, Dict[str, Any]]:
    """交互式引导选择 LLM"""
    config = existing_config if existing_config is not None else load_config()

    print("\n=================== 模型 Provider 选择 ===================")
    print("  [1] Ollama (支持本地 127.0.0.1 或 自定义云端 Host)")
    print("  [2] 硅基流动 SiliconFlow (OpenAI 兼容 API，输入 API Key)")
    print("==========================================================")

    provider_choice = input("请选择 Provider 编号 (默认 1): ").strip()
    if provider_choice == "2":
        selected_provider = "siliconflow"
        saved_key = config.get("siliconflow_api_key") or os.environ.get("SILICONFLOW_API_KEY", "")
        if saved_key:
            masked = mask_key(saved_key)
            prompt_key = f"请输入硅基流动 API Key (按回车使用历史/环境变量 Key {masked}): "
        else:
            prompt_key = "请输入硅基流动 API Key: "

        api_key_input = input(prompt_key).strip()
        api_key = api_key_input if api_key_input else saved_key

        config["siliconflow_api_key"] = api_key
        print("⏳ 正在获取硅基流动可用模型列表...")
        models = get_siliconflow_models(api_key=api_key)

        print("\n=== 可用的硅基流动 (SiliconFlow) 模型 ===")
        for idx, model_name in enumerate(models, 1):
            print(f"  [{idx}] {model_name}")
        print("=========================================")

        choice = input(f"请选择模型编号或输入模型名称 (默认 1): ").strip()
        if not choice:
            selected_model = models[0]
        elif choice.isdigit() and 1 <= int(choice) <= len(models):
            selected_model = models[int(choice) - 1]
        else:
            selected_model = choice

        config["provider"] = "siliconflow"
        config["model"] = selected_model
        save_config(config)

        print(f"\n✅ 已配置 硅基流动 平台, 模型: {selected_model}")
        llm = SiliconFlowLLM(api_key=api_key, model=selected_model)

    else:
        selected_provider = "ollama"
        print("\n---------------- Ollama 服务位置选择 ----------------")
        print("  [1] 本地默认 (http://localhost:11434)")
        print("  [2] 云端 / 自定义 Host URL")
        print("-----------------------------------------------------")
        host_choice = input("请选择 Ollama 服务位置 (默认 1): ").strip()
        if host_choice == "2":
            default_host = config.get("ollama_host", "http://localhost:11434")
            host = input(f"请输入 Ollama Host 地址 (默认 {default_host}): ").strip()
            if not host:
                host = default_host
        else:
            host = "http://localhost:11434"

        print(f"⏳ 正在拉取 Ollama 可用模型列表 (Host: {host})...")
        models = get_ollama_models(host=host)
        if not models:
            print(f"⚠️ 未在该 Ollama 服务检测到已有模型，请输入要调用的模型名称 (如 qwen2.5:0.5b 或 deepseek-r1:1.5b):")
            selected_model = input("模型名称: ").strip() or "qwen2.5:0.5b"
        else:
            print(f"\n=== 可用的 Ollama ({host}) 模型列表 ===")
            for idx, model_name in enumerate(models, 1):
                print(f"  [{idx}] {model_name}")
            print("===========================================")

            choice = input("请选择模型编号或输入模型名称 (默认 1): ").strip()
            if not choice:
                selected_model = models[0]
            elif choice.isdigit() and 1 <= int(choice) <= len(models):
                selected_model = models[int(choice) - 1]
            else:
                selected_model = choice

        config["provider"] = "ollama"
        config["ollama_host"] = host
        config["model"] = selected_model
        save_config(config)

        print(f"\n✅ 已配置 Ollama Host: {host}, 模型: {selected_model}")
        llm = NativeOllamaLLM(model=selected_model, host=host)

    return llm, config


def test_llm_performance() -> None:
    """性能与响应时间测试入口"""
    print("\n==================================================")
    print("🚀 【LLM 响应时间与性能测试工具】")
    print("==================================================")

    config = load_config()
    provider = config.get("provider", "ollama")
    model = config.get("model", "qwen3.5:0.8b")
    enable_thinking = config.get("enable_thinking", False)

    if provider == "siliconflow":
        api_key = config.get("siliconflow_api_key") or os.environ.get("SILICONFLOW_API_KEY", "")
        print(f"📡 Provider: 硅基流动 SiliconFlow | Key: {mask_key(api_key)} | Model: {model} | 开关思考: {enable_thinking}")
        llm = SiliconFlowLLM(api_key=api_key, model=model, enable_thinking=enable_thinking)
    else:
        host = config.get("ollama_host", "http://localhost:11434")
        print(f"📡 Provider: Ollama ({host}) | Model: {model} | 开关思考: {enable_thinking}")
        llm = NativeOllamaLLM(model=model, host=host, enable_thinking=enable_thinking)

    test_prompt = "请用 50 字以内简要介绍一下什么是 Todo List 以及它的核心价值。"
    print(f"\n💬 测试 Prompt: '{test_prompt}'")
    print("⏳ 发起 HTTP 请求测速中...")

    messages = [{"role": "user", "content": test_prompt}]

    try:
        response_text, metrics = llm.chat(messages, json_format=False, num_predict=256)
        speed = (metrics.completion_tokens / metrics.total_duration) if metrics.total_duration > 0 and metrics.completion_tokens > 0 else 0.0

        print("\n------------------ 测试结果 ------------------")
        if metrics.thinking_content:
            formatted_thinking = "\n".join([f"> {line}" for line in metrics.thinking_content.splitlines() if line.strip()])
            print(f"🧠 **【思考过程】**:\n{formatted_thinking}\n")

        print(f"📝 **【模型回答】**:\n{response_text}\n")
        print("------------------ 性能指标 ------------------")
        print(f"⏱️  首字延时 (TTFT): {metrics.ttft * 1000:.1f} ms ({metrics.ttft:.3f} s)")
        print(f"⏱️  总共耗时:         {metrics.total_duration:.3f} s")
        print(f"📊 上传 Token:        {metrics.prompt_tokens}")
        print(f"📊 下载 Token:        {metrics.completion_tokens}")
        if speed > 0:
            print(f"⚡ 生成速度:          {speed:.2f} tokens/s")
        print("==================================================\n")

    except Exception as e:
        print(f"❌ 测试过程发生异常: {e}")


if __name__ == "__main__":
    test_llm_performance()
