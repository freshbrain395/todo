import json
from typing import List, Dict, Any, Optional
from backend.config import read_raw_config, write_raw_config
from backend.repository.db import DbState


DEFAULT_PROVIDERS: List[Dict[str, Any]] = [
    {
        "id": "siliconflow",
        "name": "SiliconFlow (硅基流动云端 API)",
        "base_url": "https://api.siliconflow.cn/v1",
        "api_key": "",
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "is_custom": False,
    },
    {
        "id": "ollama",
        "name": "Native Ollama (本地大模型服务)",
        "base_url": "http://localhost:11434",
        "api_key": "",
        "model": "llama3:latest",
        "is_custom": False,
    },
    {
        "id": "deepseek",
        "name": "DeepSeek (深度求索官方 API)",
        "base_url": "https://api.deepseek.com/v1",
        "api_key": "",
        "model": "deepseek-chat",
        "is_custom": False,
    },
    {
        "id": "openai",
        "name": "OpenAI (官方 API)",
        "base_url": "https://api.openai.com/v1",
        "api_key": "",
        "model": "gpt-4o-mini",
        "is_custom": False,
    },
]

DEFAULT_PROMPTS: List[Dict[str, Any]] = [
    {
        "id": "p1",
        "category": "时间管理",
        "title": "高效工作日程划分",
        "text": "请帮我规划今天的工作日程，把重要且紧急的任务安排在上午最清醒的时候。",
        "jsonFormat": "",
        "enabled": True,
        "isActive": True,
    },
    {
        "id": "p2",
        "category": "任务拆解",
        "title": "复杂大项目细化",
        "text": "帮我把'完成项目上线'拆解为 5 个具体的、可落地的子待办事项。",
        "jsonFormat": "",
        "enabled": True,
        "isActive": False,
    },
    {
        "id": "p3",
        "category": "周报生成",
        "title": "工作总结整理",
        "text": "请根据我已完成的待办事项，帮我撰写一份简明扼要的本周工作总结。",
        "jsonFormat": "",
        "enabled": True,
        "isActive": False,
    },
    {
        "id": "p4",
        "category": "优先级评估",
        "title": "待办四象限排序",
        "text": "分析我现有的待办列表，并给出最推荐优先处理的前 3 项任务建议。",
        "jsonFormat": "",
        "enabled": True,
        "isActive": False,
    },
]

DEFAULT_SKILLS: List[Dict[str, Any]] = [
    {
        "id": "skill-gtd",
        "title": "GTD 四象限任务规划",
        "category": "时间管理",
        "description": "根据紧急与重要维度自动解析待办清单，智能规划当日高效率执行顺序。",
        "systemPrompt": "请将用户提交的任务按紧急/重要四象限进行分类，并给出第一优先级的 3 个具体执行建议。",
        "enabled": True,
    },
    {
        "id": "skill-pomodoro",
        "title": "番茄工作法轮巡规划",
        "category": "专注执行",
        "description": "自动将大块工作时间拆解为 25 分钟专注 + 5 分钟休息的番茄钟节奏，并启动系统倒计时。",
        "systemPrompt": "将大任务拆分为若干 25 分钟的番茄专注时段，并自动触发倒计时工具。",
        "enabled": True,
    },
    {
        "id": "skill-weekly-report",
        "title": "周报与工作总结整理",
        "category": "总结输出",
        "description": "按完成状态、任务分类整理已完成列表，自动提炼生成结构化 Markdown 周报。",
        "systemPrompt": "分析已完成待办，提炼本周核心产出、未完成风险及下周计划。",
        "enabled": True,
    },
    {
        "id": "skill-smart-alarm",
        "title": "自然语言时间解构与提醒",
        "category": "日程提醒",
        "description": "精准识别模糊时间表述（如“明早八点半”、“今晚8点”）并自动联动应用闹钟提醒。",
        "systemPrompt": "提取时间点与事件主体，自动调用 set_alarm 工具创建响铃提醒。",
        "enabled": True,
    },
    {
        "id": "skill-breakdown",
        "title": "目标分解与微习惯提炼",
        "category": "任务拆解",
        "description": "把抽象的大目标（如“准备考试”）一键拆解为 3-5 项单日可完成的细化待办。",
        "systemPrompt": "拆解复杂目标为具体、可衡量、有清晰动作的子待办事项。",
        "enabled": True,
    },
]


def _get_full_config() -> Dict[str, Any]:
    """读取包含系统、提供商、提示词、技能等的完整配置"""
    data = read_raw_config()
    changed = False
    if "system" not in data:
        data["system"] = {
            "user_name": "用户",
            "user_prefix": "todo-agent",
            "ai_name": "Todo Agent",
            "ai_prefix": "🤖",
        }
        changed = True
    if "app_config" not in data:
        data["app_config"] = {}
        changed = True
    if "providers" not in data or not isinstance(data["providers"], list):
        data["providers"] = DEFAULT_PROVIDERS
        changed = True
    if "prompts" not in data or not isinstance(data["prompts"], list):
        data["prompts"] = DEFAULT_PROMPTS
        changed = True
    if "skills" not in data or not isinstance(data["skills"], list):
        data["skills"] = DEFAULT_SKILLS
        changed = True
    if "sessions" not in data or not isinstance(data["sessions"], list):
        data["sessions"] = []
        changed = True
    if changed:
        write_raw_config(data)
    return data


# ============ AI Providers ============

def load_providers(db: Optional[DbState] = None) -> List[Dict[str, Any]]:
    data = _get_full_config()
    providers = data.get("providers")
    if not providers or not isinstance(providers, list):
        return [dict(p) for p in DEFAULT_PROVIDERS]
    return providers


def save_providers(db: Optional[DbState], providers_json: Any) -> None:
    providers = json.loads(providers_json) if isinstance(providers_json, str) else providers_json
    if not isinstance(providers, list):
        providers = []
    data = _get_full_config()
    data["providers"] = providers
    write_raw_config(data)


# ============ AI Prompts ============

def load_prompts(db: Optional[DbState] = None) -> List[Dict[str, Any]]:
    data = _get_full_config()
    prompts = data.get("prompts")
    if not prompts or not isinstance(prompts, list):
        return [dict(p) for p in DEFAULT_PROMPTS]
    return prompts


def save_prompts(db: Optional[DbState], prompts_json: Any) -> None:
    prompts = json.loads(prompts_json) if isinstance(prompts_json, str) else prompts_json
    if not isinstance(prompts, list):
        prompts = []
    data = _get_full_config()
    data["prompts"] = prompts
    write_raw_config(data)


# ============ AI Skills ============

def load_skills(db: Optional[DbState] = None) -> List[Dict[str, Any]]:
    data = _get_full_config()
    skills = data.get("skills")
    if not skills or not isinstance(skills, list):
        return [dict(s) for s in DEFAULT_SKILLS]
    return skills


def save_skills(db: Optional[DbState], skills_json: Any) -> None:
    skills = json.loads(skills_json) if isinstance(skills_json, str) else skills_json
    if not isinstance(skills, list):
        skills = []
    data = _get_full_config()
    data["skills"] = skills
    write_raw_config(data)


# ============ AI Sessions ============

def load_sessions(db: Optional[DbState] = None) -> List[Dict[str, Any]]:
    data = _get_full_config()
    sessions = data.get("sessions")
    if not sessions or not isinstance(sessions, list):
        return []
    return sessions


def save_sessions(db: Optional[DbState], sessions_json: Any) -> None:
    sessions = json.loads(sessions_json) if isinstance(sessions_json, str) else sessions_json
    if not isinstance(sessions, list):
        sessions = []
    data = _get_full_config()
    data["sessions"] = sessions
    write_raw_config(data)
