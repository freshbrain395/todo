import json
import re
import asyncio
import subprocess
import platform
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import httpx

from backend.repository.db import DbState
from backend.repository import todo as todo_repo
from backend.service.display_config import DisplayConfigService


@dataclass
class LlmConfig:
    provider: str = "siliconflow"
    base_url: str = "https://api.siliconflow.cn/v1"
    api_key: str = ""
    model: str = "deepseek-ai/DeepSeek-V4-Flash"
    enable_thinking: bool = False


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class AiActionResult:
    action: str
    data: Dict[str, Any]
    message: str
    should_refresh: bool


DEFAULT_AGENT_PROMPT = """你是一个智能、高效且亲切的 Todo Agent 个人助手。
你不仅可以与用户自由畅聊、解答疑问，还可以根据自然语言管理用户的待办事项。

【行为规范】
1. 当用户输入属于日常问候、聊天、倾诉、询问建议或与待办操作无关时：
   - 将 action 设为 "chat"
   - 在 raw_response 中给出自然、亲切、富有同理心的回复（例如："你好！有什么我可以帮你的？"）
2. 当用户意图涉及待办操作（新建、标记完成、修改、删除、查询）：
   - add: 新建待办。data 包含 title, priority ("high"|"medium"|"low", 默认 "medium"), category (默认 "工作"), remind_at (可选, 格式 YYYY-MM-DD HH:MM:SS)
   - complete: 标记完成。data 包含 id (任务ID整数)
   - update: 修改已有任务（如调整优先级、修改标题或提醒时间）。data 包含 id (整数)，以及被修改字段
   - delete: 删除任务。data 包含 id (整数)
   - query: 查询任务。data 可包含 filter_type ("all"|"pending"|"completed", 默认 "all") 与 search (搜索关键词字符串, 可选)。在 raw_response 中直接根据上下文向用户总结汇报任务
   - 在 raw_response 中给出简明有力的反馈（例如："✓ 已创建待办 #23", "✓ 已将 #23 设置为高优先级"）
3. 严格输出标准 JSON 格式，不输出额外的 markdown 标记外的闲聊字符。

JSON 输出格式标准：
{
  "action": "chat" | "add" | "complete" | "update" | "delete" | "query",
  "data": {
    "id": 123,
    "title": "任务标题",
    "priority": "high" | "medium" | "low",
    "category": "工作" | "生活" | "学习" | "个人",
    "remind_at": "YYYY-MM-DD HH:MM:SS",
    "filter_type": "all" | "pending" | "completed",
    "search": "关键词"
  },
  "raw_response": "给用户的亲切回复文本"
}"""

DEFAULT_SYSTEM_PROMPT = DEFAULT_AGENT_PROMPT
DEFAULT_CHAT_PROMPT = "你是一个亲切友好的 AI 对话助手。请以自然语言与用户畅聊、解答疑问，不主动进行待办事项调度与修改。"
DEFAULT_JSON_PROMPT = """你现在处于 JSON 模式。
必须只返回合法 JSON，禁止 Markdown 标记（不要包含 ```json 或 ```），禁止任何 JSON 之外的问候或解释文字。

输出 JSON 格式要求：
{
  "action": "chat" | "add" | "complete" | "update" | "delete" | "query",
  "data": {
    "id": 123,
    "title": "任务标题",
    "priority": "high" | "medium" | "low",
    "category": "工作" | "生活" | "学习" | "个人",
    "remind_at": "YYYY-MM-DD HH:MM:SS",
    "filter_type": "all" | "pending" | "completed",
    "search": "关键词"
  },
  "raw_response": "执行结果反馈或回答"
}"""



import os
import shutil


async def ensure_ollama_running(base_url: str, provider: str = "") -> bool:
    """检查 Ollama 服务是否已启动，若未启动则自动启动并在后台运行"""
    is_ollama = (provider and provider.lower() == "ollama") or "11434" in (base_url or "")
    if not is_ollama:
        return True

    # 优先检测本地 11434 端口
    check_url = "http://127.0.0.1:11434/api/tags"
    try:
        async with httpx.AsyncClient(trust_env=False, timeout=1.0) as client:
            resp = await client.get(check_url)
            if resp.is_success:
                return True
    except Exception:
        pass

    # 寻找 ollama 可执行文件路径
    ollama_bin = shutil.which("ollama")
    if not ollama_bin and platform.system().lower() == "windows":
        candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
            os.path.expandvars(r"%USERPROFILE%\scoop\shims\ollama.exe"),
            os.path.expandvars(r"%ProgramFiles%\Ollama\ollama.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Ollama\ollama.exe"),
        ]
        for c in candidates:
            if os.path.isfile(c):
                ollama_bin = c
                break

    if not ollama_bin:
        ollama_bin = "ollama"

    # 后台启动 ollama serve
    try:
        if platform.system().lower() == "windows":
            # 0x08000000 = CREATE_NO_WINDOW, 0x00000008 = DETACHED_PROCESS
            creationflags = 0x08000000 | 0x00000008
            subprocess.Popen(
                [ollama_bin, "serve"],
                creationflags=creationflags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
        else:
            subprocess.Popen(
                [ollama_bin, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
    except Exception:
        return False

    # 循环等待服务就绪
    for _ in range(16):
        await asyncio.sleep(0.5)
        try:
            async with httpx.AsyncClient(trust_env=False, timeout=0.8) as client:
                resp = await client.get(check_url)
                if resp.is_success:
                    return True
        except Exception:
            continue

    return False


async def fetch_models(base_url: str, api_key: str = "", provider: str = "") -> List[str]:
    await ensure_ollama_running(base_url, provider)
    clean_url = base_url.strip().rstrip("/")
    if "11434" in clean_url:
        if not clean_url.endswith("/api") and not clean_url.endswith("/v1"):
            api_url = f"{clean_url}/api/tags"
        elif clean_url.endswith("/api"):
            api_url = f"{clean_url}/tags"
        else:
            api_url = f"{clean_url}/models"
    else:
        if not clean_url.endswith("/v1") and "/models" not in clean_url:
            api_url = f"{clean_url}/models"
        elif clean_url.endswith("/v1"):
            api_url = f"{clean_url}/models"
        else:
            api_url = clean_url

    headers = {}
    if api_key and api_key.strip():
        headers["Authorization"] = f"Bearer {api_key.strip()}"

    try:
        async with httpx.AsyncClient(trust_env=False, timeout=15.0) as client:
            resp = await client.get(api_url, headers=headers)
            if not resp.is_success:
                raise ValueError(f"HTTP 状态错误: {resp.status_code}")
            json_val = resp.json()
    except Exception as e:
        raise RuntimeError(f"网络请求失败: {e}")

    model_names: List[str] = []
    if isinstance(json_val, dict):
        if "data" in json_val and isinstance(json_val["data"], list):
            for m in json_val["data"]:
                if isinstance(m, dict) and "id" in m:
                    model_names.append(str(m["id"]))
        elif "models" in json_val and isinstance(json_val["models"], list):
            for m in json_val["models"]:
                if isinstance(m, dict) and "name" in m:
                    model_names.append(str(m["name"]))

    if not model_names:
        raise ValueError("解析成功但未发现任何可用模型")

    return model_names


def fallback_intent_parse(user_input: str, reason: str) -> Dict[str, Any]:
    trimmed = user_input.strip()
    match_add = re.search(r"^(帮我|请|新建|添加|创建)(?:一个|一项)?(?:待办|任务)?[:：\s]*(.*)$", trimmed)
    if match_add and match_add.group(2).strip():
        title = match_add.group(2).strip()
        priority = "high" if "紧急" in trimmed or "重要" in trimmed else "medium"
        category = "工作"
        if "生活" in trimmed:
            category = "生活"
        elif "学习" in trimmed:
            category = "学习"
        return {
            "action": "add",
            "data": {
                "title": title,
                "priority": priority,
                "category": category,
            },
            "raw_response": f"已自动通过规则为您创建待办：{title}",
        }

    match_done = re.search(r"^(完成|已完成|搞定)(?:任务)?\s*#?(\d+)$", trimmed)
    if match_done:
        return {
            "action": "complete",
            "data": {"id": int(match_done.group(2))},
            "raw_response": f"已完成任务 #{match_done.group(2)}",
        }

    match_del = re.search(r"^(删除|移除)(?:任务)?\s*#?(\d+)$", trimmed)
    if match_del:
        return {
            "action": "delete",
            "data": {"id": int(match_del.group(2))},
            "raw_response": f"已删除任务 #{match_del.group(2)}",
        }

    if trimmed in ["查看待办", "待办列表", "有什么任务", "任务列表", "list"]:
        return {
            "action": "query",
            "data": {},
            "raw_response": "正在为您查询未完成任务...",
        }

    return {
        "action": "chat",
        "data": {},
        "raw_response": f"已收到消息：{user_input}（提示：{reason}）",
    }


def clean_llm_response(text: str) -> str:
    """清理大模型输出中的 think 标签或 markdown 格式"""
    # 移除 <think>...</think> 标签（常用于 DeepSeek R1 / Qwen 推理模型）
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return cleaned


async def parse_intent_and_execute(
    user_input: str,
    config: LlmConfig,
    db: DbState,
    user_id: Optional[int] = None,
    system_prompt: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> AiActionResult:
    await ensure_ollama_running(config.base_url, config.provider)

    import datetime
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_todos = todo_repo.get_todos(db, "pending", "", user_id)
    todos_context_lines = [f"【当前系统时间】: {now_str}"]
    if current_todos:
        todos_context_lines.append("【用户当前未完成待办清单】:")
        for t in current_todos[:15]:
            rem = f", 提醒: {t['remind_at']}" if t.get("remind_at") else ""
            todos_context_lines.append(f"- #{t['id']} [{t['category']}] {t['title']} (优先级: {t['priority']}{rem})")
    else:
        todos_context_lines.append("【用户当前暂无未完成待办】")
    context_str = "\n".join(todos_context_lines)

    base_prompt = system_prompt.strip() if (system_prompt and system_prompt.strip()) else DEFAULT_AGENT_PROMPT
    sys_prompt = f"{base_prompt}\n\n{context_str}"

    is_openai_compat = config.provider.lower() in ["siliconflow", "openai", "deepseek", "qwen"] or "11434" not in config.base_url

    # 针对本地服务如 localhost/127.0.0.1 禁用系统代理，避免被代理软件拦截
    clean_base = config.base_url.rstrip("/")
    if "localhost" in clean_base:
        clean_base = clean_base.replace("localhost", "127.0.0.1")

    url = (
        f"{clean_base}/chat/completions"
        if is_openai_compat
        else f"{clean_base}/api/generate"
    )

    headers = {}
    if config.api_key and config.api_key.strip():
        headers["Authorization"] = f"Bearer {config.api_key.strip()}"

    # 构造请求体
    if is_openai_compat:
        messages = [{"role": "system", "content": sys_prompt}]
        if history:
            for m in history:
                messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})
        messages.append({"role": "user", "content": user_input})

        body: Dict[str, Any] = {
            "model": config.model,
            "messages": messages,
            "temperature": 0.4,
        }
        if config.enable_thinking:
            body["enable_thinking"] = True
    else:
        body = {
            "model": config.model,
            "system": sys_prompt,
            "prompt": user_input,
            "stream": False,
            "think": bool(config.enable_thinking),
        }

    content_text = ""
    try:
        req_timeout = httpx.Timeout(300.0, connect=15.0)
        async with httpx.AsyncClient(trust_env=False, timeout=req_timeout) as client:
            resp = await client.post(url, json=body, headers=headers)
            if resp.is_success:
                res_json = resp.json()
                if is_openai_compat:
                    content_text = res_json.get("choices", [{}])[0].get("message", {}).get("content", "")
                else:
                    # Ollama 原生 API 返回 response 字段；当 think: true 时，思考内容可能单独放在 thinking 字段，content 放在 response
                    content_text = res_json.get("response", "")
                    if not content_text and res_json.get("message"):
                        content_text = res_json.get("message", {}).get("content", "")
            else:
                err_msg = f"API 状态码: {resp.status_code} - {resp.text}"
                fallback = fallback_intent_parse(user_input, err_msg)
                return AiActionResult(
                    action=fallback.get("action", "chat"),
                    data=fallback.get("data", {}),
                    message=fallback.get("raw_response", ""),
                    should_refresh=False,
                )
    except Exception as e:
        is_local = config.provider.lower() == "ollama" or "11434" in config.base_url
        if is_local:
            if isinstance(e, httpx.TimeoutException):
                err_msg = "本地模型生成超时（CPU 计算耗时较长），请稍候或选用轻量模型"
            elif isinstance(e, httpx.ConnectError):
                err_msg = "本地 Ollama 服务未连接，请确认服务已启动 (ollama serve)"
            else:
                err_msg = f"本地模型调用异常: {e}"
        else:
            if isinstance(e, httpx.TimeoutException):
                err_msg = "大模型服务请求超时，请检查网络"
            else:
                err_msg = f"连接失败: {e}"
        fallback = fallback_intent_parse(user_input, err_msg)
        return AiActionResult(
            action=fallback.get("action", "chat"),
            data=fallback.get("data", {}),
            message=fallback.get("raw_response", ""),
            should_refresh=False,
        )

    content_text = clean_llm_response(content_text)

    # 尝试解析 JSON 动作
    clean_json = (
        content_text.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )

    parsed_result = None
    try:
        parsed_result = json.loads(clean_json)
    except Exception:
        json_match = re.search(r"\{[\s\S]*\}", clean_json)
        if json_match:
            try:
                parsed_result = json.loads(json_match.group(0))
            except Exception:
                pass

    if not isinstance(parsed_result, dict):
        return AiActionResult(
            action="chat",
            data={},
            message=content_text if content_text else "你好！有什么我可以帮你的？",
            should_refresh=False,
        )

    action = parsed_result.get("action", "chat")
    data = parsed_result.get("data", {})
    if not isinstance(data, dict):
        data = {}

    if action == "add":
        title = data.get("title") or user_input
        priority = data.get("priority") or "medium"
        category = data.get("category") or "工作"
        remind_at = data.get("remind_at")

        todo_id = todo_repo.add_todo(db, title, priority, category, remind_at, user_id)
        reply = parsed_result.get("raw_response")
        if not reply or "{" in reply:
            reply = f"✓ 已创建待办 #{todo_id}"
        elif f"#{todo_id}" not in reply:
            reply = f"✓ 已创建待办 #{todo_id}"
        return AiActionResult(
            action="add",
            data={"id": todo_id, "title": title, "priority": priority, "category": category},
            message=reply,
            should_refresh=True,
        )

    elif action == "complete":
        t_id = data.get("id") or 0
        if t_id and int(t_id) > 0:
            todo_repo.update_todo_status(db, int(t_id), True, user_id)
            reply = parsed_result.get("raw_response") or f"✓ 已将 #{t_id} 标记为已完成"
            return AiActionResult(
                action="complete",
                data={"id": int(t_id)},
                message=reply,
                should_refresh=True,
            )
        else:
            reply = parsed_result.get("raw_response") or "请说明要完成哪一项待办（如：完成 #23）。"
            return AiActionResult(
                action="complete",
                data={},
                message=reply,
                should_refresh=False,
            )

    elif action == "update":
        t_id = data.get("id") or 0
        if t_id and int(t_id) > 0:
            existing = None
            for item in todo_repo.get_todos(db, "all", "", user_id):
                if item["id"] == int(t_id):
                    existing = item
                    break
            if existing:
                title = data.get("title") or existing["title"]
                priority = data.get("priority") or existing["priority"]
                category = data.get("category") or existing["category"]
                remind_at = data.get("remind_at") if "remind_at" in data else existing.get("remind_at")
                todo_repo.update_todo(db, int(t_id), title, priority, category, remind_at, user_id)
                reply = parsed_result.get("raw_response") or f"✓ 已将 #{t_id} 更新完成"
                return AiActionResult(
                    action="update",
                    data={"id": int(t_id), "title": title, "priority": priority, "category": category},
                    message=reply,
                    should_refresh=True,
                )
            else:
                return AiActionResult(
                    action="update",
                    data={},
                    message=f"未找到待办 #{t_id}。",
                    should_refresh=False,
                )
        else:
            reply = parsed_result.get("raw_response") or "请说明要修改哪个待办任务（例如：把 #23 改成高优先级）。"
            return AiActionResult(
                action="update",
                data={},
                message=reply,
                should_refresh=False,
            )

    elif action == "delete":
        t_id = data.get("id") or 0
        if t_id and int(t_id) > 0:
            todo_repo.delete_todo(db, int(t_id), user_id)
            reply = parsed_result.get("raw_response") or f"✓ 已删除待办 #{t_id}"
            return AiActionResult(
                action="delete",
                data={"id": int(t_id)},
                message=reply,
                should_refresh=True,
            )
        else:
            reply = parsed_result.get("raw_response") or "请说明要删除哪一项任务（例如：删除 #23）。"
            return AiActionResult(
                action="delete",
                data={},
                message=reply,
                should_refresh=False,
            )

    elif action == "query":
        filter_type = data.get("filter_type") or "all"
        if filter_type not in ["all", "pending", "completed"]:
            filter_type = "all"
        search = data.get("search") or ""

        reply = parsed_result.get("raw_response")
        if reply and "{" not in reply:
            return AiActionResult(
                action="query",
                data={"filter_type": filter_type, "search": search},
                message=reply,
                should_refresh=False,
            )
        todos = todo_repo.get_todos(db, filter_type, search, user_id)
        if not todos:
            empty_msg = "未找到符合条件的待办任务。" if (filter_type != "all" or search) else "你当前没有任何待办任务，太棒了！🎉"
            return AiActionResult(
                action="query",
                data={"filter_type": filter_type, "search": search, "todos": []},
                message=empty_msg,
                should_refresh=False,
            )
        lines = [f"为你找到 {len(todos)} 个待办："]
        for idx, t in enumerate(todos[:10], 1):
            pri_tag = "高" if t["priority"] == "high" else ("中" if t["priority"] == "medium" else "低")
            status_tag = "✓已完成" if t.get("completed") else "待办"
            lines.append(f"  {idx}. #{t['id']} [{status_tag}] [{t['category']}] {t['title']} ({pri_tag}优先级)")
        if len(todos) > 10:
            lines.append(f"  ... 还有 {len(todos) - 10} 项未列出")
        return AiActionResult(
            action="query",
            data={"filter_type": filter_type, "search": search, "todos": todos},
            message="\n".join(lines),
            should_refresh=False,
        )

    else:
        # 普通聊天
        reply = parsed_result.get("raw_response") or content_text or "你好！有什么我可以帮你的？"
        return AiActionResult(
            action="chat",
            data=data,
            message=reply,
            should_refresh=False,
        )
