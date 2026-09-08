from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field



class TodoCreateRequest(BaseModel):
    title: str
    priority: str = "medium"
    category: str = "工作"
    remind_at: Optional[str] = None
    user_id: Optional[int] = None


class TodoUpdateRequest(BaseModel):
    id: int
    title: str
    priority: str = "medium"
    category: str = "工作"
    remind_at: Optional[str] = None
    user_id: Optional[int] = None


class TodoStatusRequest(BaseModel):
    id: int
    completed: bool
    user_id: Optional[int] = None


class LlmConfigSchema(BaseModel):
    provider: str = "siliconflow"
    base_url: str = "https://api.siliconflow.cn/v1"
    api_key: str = ""
    model: str = "deepseek-ai/DeepSeek-V4-Flash"
    enable_thinking: bool = False


class ExecuteAiCommandRequest(BaseModel):
    input: str
    config: Optional[LlmConfigSchema] = None
    user_id: Optional[int] = None
    history: Optional[List[Dict[str, str]]] = None
    system_prompt: Optional[str] = None


class FetchModelsRequest(BaseModel):
    base_url: str
    api_key: Optional[str] = ""


class InvokeRequest(BaseModel):
    cmd: str
    args: Dict[str, Any] = Field(default_factory=dict)
