import json
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends

from backend.repository.db import DbState
from backend.service.todo import TodoService
from backend.service.config import ConfigService
from backend.service.ai_config import AiConfigService
from backend.service.display_config import DisplayConfigService
from backend.service.local_user import LocalUserService
from backend.service.ai import (
    LlmConfig,
    fetch_models,
    parse_intent_and_execute,
)
from backend.api.schemas import (
    TodoCreateRequest,
    TodoUpdateRequest,
    TodoStatusRequest,
    ExecuteAiCommandRequest,
    FetchModelsRequest,
    InvokeRequest,
)

router = APIRouter()


def get_db() -> DbState:
    return DbState.get_instance()


# ==================== 待办模块 ====================

@router.get("/api/todos")
def get_todos_endpoint(
    filter: str = "all",
    search: str = "",
    user_id: Optional[int] = None,
    db: DbState = Depends(get_db),
):
    service = TodoService(db)
    return service.get_todos(filter, search, user_id)


@router.post("/api/todos")
def add_todo_endpoint(req: TodoCreateRequest, db: DbState = Depends(get_db)):
    service = TodoService(db)
    return service.add_todo(
        title=req.title,
        priority=req.priority,
        category=req.category,
        remind_at=req.remind_at,
        user_id=req.user_id,
    )


@router.put("/api/todos/{todo_id}")
def update_todo_endpoint(todo_id: int, req: TodoUpdateRequest, db: DbState = Depends(get_db)):
    service = TodoService(db)
    return service.update_todo(
        todo_id=todo_id,
        title=req.title,
        priority=req.priority,
        category=req.category,
        remind_at=req.remind_at,
        user_id=req.user_id,
    )


@router.patch("/api/todos/{todo_id}/status")
def update_todo_status_endpoint(
    todo_id: int, req: TodoStatusRequest, db: DbState = Depends(get_db)
):
    service = TodoService(db)
    return service.update_todo_status(todo_id, req.completed, req.user_id)


@router.delete("/api/todos/{todo_id}")
def delete_todo_endpoint(
    todo_id: int, user_id: Optional[int] = None, db: DbState = Depends(get_db)
):
    service = TodoService(db)
    return service.delete_todo(todo_id, user_id)


# ==================== AI 模块 ====================

@router.post("/api/ai/models")
async def fetch_models_endpoint(req: FetchModelsRequest):
    try:
        return await fetch_models(req.base_url, req.api_key or "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/ai/execute")
async def execute_ai_command_endpoint(
    req: ExecuteAiCommandRequest, db: DbState = Depends(get_db)
):
    cfg_data = req.config.model_dump() if req.config else {}
    llm_cfg = LlmConfig(
        provider=cfg_data.get("provider", "siliconflow"),
        base_url=cfg_data.get("base_url", "https://api.siliconflow.cn/v1"),
        api_key=cfg_data.get("api_key", ""),
        model=cfg_data.get("model", "deepseek-ai/DeepSeek-V4-Flash"),
        enable_thinking=cfg_data.get("enable_thinking", False),
    )
    result = await parse_intent_and_execute(
        user_input=req.input,
        config=llm_cfg,
        db=db,
        user_id=req.user_id,
        system_prompt=req.system_prompt,
        history=req.history,
    )
    return {
        "action": result.action,
        "data": result.data,
        "message": result.message,
        "should_refresh": result.should_refresh,
    }


# ==================== 统一 RPC 调用端点 (兼容前端 invokeApi) ====================

@router.post("/api/invoke")
async def invoke_endpoint(req: InvokeRequest, db: DbState = Depends(get_db)):
    cmd = req.cmd
    args = req.args

    todo_service = TodoService(db)
    config_service = ConfigService(db)
    ai_config_service = AiConfigService(db)
    local_user_service = LocalUserService(db)

    try:
        if cmd == "get_todos":
            return todo_service.get_todos(
                filter_type=args.get("filter", "all"),
                search=args.get("search", ""),
                user_id=args.get("user_id"),
            )

        elif cmd == "add_todo":
            return todo_service.add_todo(
                title=args.get("title", ""),
                priority=args.get("priority", "medium"),
                category=args.get("category", "工作"),
                remind_at=args.get("remind_at"),
                user_id=args.get("user_id"),
            )

        elif cmd == "update_todo_status":
            return todo_service.update_todo_status(
                todo_id=int(args.get("id", 0)),
                completed=bool(args.get("completed")),
                user_id=args.get("user_id"),
            )

        elif cmd == "update_todo":
            return todo_service.update_todo(
                todo_id=int(args.get("id", 0)),
                title=args.get("title", ""),
                priority=args.get("priority", "medium"),
                category=args.get("category", "工作"),
                remind_at=args.get("remind_at"),
                user_id=args.get("user_id"),
            )

        elif cmd == "delete_todo":
            return todo_service.delete_todo(
                todo_id=int(args.get("id", 0)),
                user_id=args.get("user_id"),
            )

        elif cmd == "fetch_models":
            return await fetch_models(args.get("base_url", ""), args.get("api_key", ""))

        elif cmd == "execute_ai_command":
            cfg_raw = args.get("config", {})
            llm_cfg = LlmConfig(
                provider=cfg_raw.get("provider", "siliconflow"),
                base_url=cfg_raw.get("base_url", "https://api.siliconflow.cn/v1"),
                api_key=cfg_raw.get("api_key", ""),
                model=cfg_raw.get("model", "deepseek-ai/DeepSeek-V4-Flash"),
                enable_thinking=cfg_raw.get("enable_thinking", False),
            )
            res = await parse_intent_and_execute(
                user_input=args.get("input", ""),
                config=llm_cfg,
                db=db,
                user_id=args.get("user_id"),
                system_prompt=args.get("system_prompt"),
                history=args.get("history"),
            )
            return {
                "action": res.action,
                "data": res.data,
                "message": res.message,
                "should_refresh": res.should_refresh,
            }

        elif cmd == "get_clock_config":
            return config_service.get_config("clock_config")

        elif cmd == "save_clock_config":
            config_service.save_config("clock_config", args.get("config_json", "{}"))
            return True

        elif cmd == "get_app_config":
            return config_service.get_config(args.get("key", ""))

        elif cmd == "save_app_config":
            config_service.save_config(args.get("key", ""), args.get("value", ""))
            return True

        elif cmd == "get_display_config":
            cfg = DisplayConfigService.load()
            return {
                "user_name": cfg.user_name,
                "user_prefix": cfg.user_prefix,
                "ai_name": cfg.ai_name,
                "ai_prefix": cfg.ai_prefix,
            }

        elif cmd == "save_display_config":
            from backend.config import DisplayConfig
            cfg = DisplayConfig(
                user_name=args.get("user_name", "用户"),
                user_prefix=args.get("user_prefix", "todo-agent"),
                ai_name=args.get("ai_name", "Todo Agent"),
                ai_prefix=args.get("ai_prefix", "🤖"),
            )
            DisplayConfigService.save(cfg)
            return True

        elif cmd == "get_ai_providers":
            return ai_config_service.get_providers()

        elif cmd == "save_ai_providers":
            ai_config_service.save_providers(args.get("providers_json", "[]"))
            return True

        elif cmd == "get_ai_prompts":
            return ai_config_service.get_prompts()

        elif cmd == "save_ai_prompts":
            ai_config_service.save_prompts(args.get("prompts_json", "[]"))
            return True

        elif cmd == "get_ai_skills":
            return ai_config_service.get_skills()

        elif cmd == "save_ai_skills":
            ai_config_service.save_skills(args.get("skills_json", "[]"))
            return True

        elif cmd == "get_ai_sessions":
            return ai_config_service.get_sessions()

        elif cmd == "save_ai_sessions":
            ai_config_service.save_sessions(args.get("sessions_json", "[]"))
            return True

        elif cmd == "get_tool_config":
            raw = config_service.get_config("agent_enabled_tools")
            return json.loads(raw) if raw else {}

        elif cmd == "save_tool_config":
            config_service.save_config("agent_enabled_tools", args.get("config_json", "{}"))
            return True

        elif cmd == "get_llm_config":
            return config_service.get_config("llm_config_v2")

        elif cmd == "save_llm_config":
            config_service.save_config("llm_config_v2", args.get("config_json", "{}"))
            return True

        elif cmd == "get_local_users":
            return local_user_service.get_local_users()

        elif cmd == "save_local_users":
            local_user_service.save_local_users(args.get("accounts_json", "{}"))
            return True

        else:
            raise HTTPException(status_code=400, detail=f"未知的 API 指令: {cmd}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
