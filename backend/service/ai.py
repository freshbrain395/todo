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


DEFAULT_SYSTEM_PROMPT = """你是一个待办事项智能助手。根据用户的自然语言输入，解析其意图并返回固定格式的 JSON 对象（不要添加任何 markdown 代码块标记以外的文字）。
JSON 格式标准：
{
  "action": "add" | "complete" | "delete" | "query" | "chat",
  "data": {
    "title": "任务标题（如果 action 是 add）",
    "priority": "high" | "medium" | "low",
    "category": "工作" | "生活" | "学习" | "个人",
    "remind_at": "YYYY-MM-DD HH:MM:SS" (可选),
    "id": 123 (如果 action 是 complete 或 delete)
  },
  "raw_response": "给用户的亲切回复文本"
}"""


async def ensure_ollama_running(base_url: str) -> None:
    if "11434" not in base_url:
        return

    check_url = "http://127.0.0.1:11434/api/tags"
    try:
        async with httpx.AsyncClient(timeout=0.8) as client:
            resp = await client.get(check_url)
            if resp.is_success:
                return
    except Exception:
        pass

    try:
        if platform.system().lower() == "windows":
            # CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen(
                ["ollama", "serve"],
                creationflags=0x08000000,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception:
        pass

    for _ in range(12):
        await asyncio.sleep(0.5)
        try:
            async with httpx.AsyncClient(timeout=0.5) as client:
                resp = await client.get(check_url)
                if resp.is_success:
                    break
        except Exception:
            continue


async def fetch_models(base_url: str, api_key: str = "") -> List[str]:
    await ensure_ollama_running(base_url)
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
        async with httpx.AsyncClient(timeout=10.0) as client:
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
    # 启发式规则解析
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
            "raw_response": f"（本地规则解析）已为你识别并创建待办事项：{title}",
        }

    match_done = re.search(r"(?:完成|搞定|做完)(?:任务)?\s*#?(\d+)", trimmed)
    if match_done:
        return {
            "action": "complete",
            "data": {"id": int(match_done.group(1))},
            "raw_response": f"（本地规则解析）标记任务 #{match_done.group(1)} 为已完成",
        }

    match_del = re.search(r"(?:删除|移除|删掉)(?:任务)?\s*#?(\d+)", trimmed)
    if match_del:
        return {
            "action": "delete",
            "data": {"id": int(match_del.group(1))},
            "raw_response": f"（本地规则解析）删除任务 #{match_del.group(1)}",
        }

    if any(k in trimmed for k in ["查看", "列表", "有哪些", "待办清单", "未完成"]):
        return {
            "action": "query",
            "data": {},
            "raw_response": "已为您检索当前待办清单。",
        }

    return {
        "action": "chat",
        "data": {},
        "raw_response": f"已收到消息：{user_input}（提示：{reason}）",
    }


async def parse_intent_and_execute(
    user_input: str,
    config: LlmConfig,
    db: DbState,
    user_id: Optional[int] = None,
    system_prompt: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> AiActionResult:
    await ensure_ollama_running(config.base_url)

    sys_prompt = DEFAULT_SYSTEM_PROMPT
    if system_prompt and system_prompt.strip():
        sys_prompt = f"{DEFAULT_SYSTEM_PROMPT}\n\n{system_prompt.strip()}"

    is_siliconflow = config.provider.lower() in ["siliconflow", "openai", "deepseek", "qwen"]

    url = (
        f"{config.base_url.rstrip('/')}/chat/completions"
        if is_siliconflow
        else f"{config.base_url.rstrip('/')}/api/generate"
    )

    if is_siliconflow:
        messages = [{"role": "system", "content": sys_prompt}]
        if history:
            for m in history:
                messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})
        messages.append({"role": "user", "content": user_input})
        body: Dict[str, Any] = {
            "model": config.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        if config.enable_thinking:
            body["enable_thinking"] = True
    else:
        body = {
            "model": config.model,
            "system": sys_prompt,
            "prompt": user_input,
            "stream": False,
            "format": "json",
        }

    headers = {}
    if is_siliconflow and config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key.strip()}"

    parsed_result = None
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, json=body, headers=headers)
            if resp.is_success:
                res_json = resp.json()
                if is_siliconflow:
                    content_text = res_json.get("choices", [{}])[0].get("message", {}).get("content", "")
                else:
                    content_text = res_json.get("response", "")

                clean_json = (
                    content_text.strip()
                    .removeprefix("```json")
                    .removeprefix("```")
                    .removesuffix("```")
                    .strip()
                )
                try:
                    parsed_result = json.loads(clean_json)
                except Exception:
                    parsed_result = {
                        "action": "chat",
                        "data": {},
                        "raw_response": content_text,
                    }
            else:
                err_text = resp.text
                parsed_result = fallback_intent_parse(user_input, f"API 返回错误: {err_text}")
    except Exception as e:
        parsed_result = fallback_intent_parse(user_input, f"网络请求失败: {e}")

    action = parsed_result.get("action", "chat")
    data = parsed_result.get("data", {})
    if not isinstance(data, dict):
        data = {}

    display_cfg = DisplayConfigService.load()
    ai_prefix = display_cfg.ai_prefix

    if action == "add":
        title = data.get("title") or user_input
        priority = data.get("priority") or "medium"
        category = data.get("category") or "工作"
        remind_at = data.get("remind_at")

        todo_id = todo_repo.add_todo(db, title, priority, category, remind_at, user_id)
        reply = parsed_result.get("raw_response") or "已为您智能创建待办事项！"
        return AiActionResult(
            action="add",
            data={"id": todo_id, "title": title, "priority": priority, "category": category},
            message=f"{ai_prefix} {reply} \n\n✨ 任务详情：[{title}] (分类: {category}, 优先级: {priority})",
            should_refresh=True,
        )

    elif action == "complete":
        t_id = data.get("id") or 0
        if t_id and int(t_id) > 0:
            todo_repo.update_todo_status(db, int(t_id), True, user_id)
            return AiActionResult(
                action="complete",
                data={"id": int(t_id)},
                message=f"✅ 已成功标记任务 ID [{t_id}] 为已完成！",
                should_refresh=True,
            )
        else:
            reply = parsed_result.get("raw_response") or "收到指令，请提供具体的任务 ID 或明确说明要完成哪一项。"
            return AiActionResult(
                action="complete",
                data={},
                message=f"{ai_prefix} {reply}",
                should_refresh=False,
            )

    elif action == "delete":
        t_id = data.get("id") or 0
        if t_id and int(t_id) > 0:
            todo_repo.delete_todo(db, int(t_id), user_id)
            return AiActionResult(
                action="delete",
                data={"id": int(t_id)},
                message=f"🗑️ 已成功删除任务 ID [{t_id}]！",
                should_refresh=True,
            )
        else:
            reply = parsed_result.get("raw_response") or "收到指令，请提供具体的任务 ID 或明确说明要删除哪一项。"
            return AiActionResult(
                action="delete",
                data={},
                message=f"{ai_prefix} {reply}",
                should_refresh=False,
            )

    elif action == "query":
        todos = todo_repo.get_todos(db, "pending", "", user_id)
        if not todos:
            return AiActionResult(
                action="query",
                data={"todos": []},
                message=f"{ai_prefix} 您当前没有任何未完成的任务，太棒了！🎉",
                should_refresh=False,
            )
        lines = [f"{ai_prefix} 📋 您当前共有 {len(todos)} 条未完成的待办事项："]
        for idx, t in enumerate(todos[:10], 1):
            pri_tag = "🔴 [高]" if t["priority"] == "high" else ("🟡 [中]" if t["priority"] == "medium" else "🟢 [低]")
            lines.append(f"{idx}. #{t['id']} [{t['category']}] {t['title']} {pri_tag}")
        if len(todos) > 10:
            lines.append(f"... 还有 {len(todos) - 10} 项未列出")
        return AiActionResult(
            action="query",
            data={"todos": todos},
            message="\n".join(lines),
            should_refresh=False,
        )

    else:
        # 普通聊天
        reply = parsed_result.get("raw_response") or "好的，我已记录您的信息。"
        return AiActionResult(
            action="chat",
            data=data,
            message=f"{ai_prefix} {reply}",
            should_refresh=False,
        )
