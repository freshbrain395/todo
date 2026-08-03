import json
import os
import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict

# =====================================================================
# 1. 模式控制配置数据模型 (ModeConfig)
# =====================================================================

@dataclass
class ModeConfig:
    """定义单个模式的详细控制与定制参数"""
    name: str                           # 模式标识码: 'agent', 'prompts', 'chat'
    label: str                          # 界面显示名称与 Emoji 描述
    description: str                    # 模式功能与应用场景说明
    system_prompt: str                  # 核心系统提示词 (System Prompt)
    temperature: float = 0.7            # 大模型生成随机度/采样温度 (0.0 - 1.0)
    num_predict: int = 512              # 单次生成允许的最大 Token 数量
    use_tools: bool = False             # 是否使用原生 Tool Calling 工具集
    json_format: bool = False           # 是否强制模型输出 JSON 格式
    disable_thinking_prompt: str = ""   # 当关闭思考过程 (/think off) 时自动追加的附加提示文本

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ModeConfig":
        return cls(**d)


# =====================================================================
# 2. 默认模式配置注册表 (Default Mode Registry)
# =====================================================================

DEFAULT_MODE_CONFIGS: Dict[str, ModeConfig] = {
    "agent": ModeConfig(
        name="agent",
        label="🛠️ Agent 模式 (原生 Tool Calling 工具调用)",
        description="基于原生 Tool Calling 函数调用引擎，支持智能识别并执行待办事项增删改查 SQL 操作。",
        system_prompt=(
            "你是一个功能强大的 Todo Agent 助手。\n"
            "你拥有管理待办事项的原生 Tool Calling 工具集。请根据用户的需求，直接决定并选择调用最合适的工具完成任务。\n"
            "如果用户只是打招呼、询问身份、表达感谢或闲聊（例如 '你好'、'你是'、'今天是' 等），无需调用任何工具，直接简短友好地回答用户即可，不要输出多余的符号或重复的引号。"
        ),
        temperature=0.0,
        num_predict=256,
        use_tools=True,
        json_format=False,
        disable_thinking_prompt="\n禁用思考推理过程，绝对不要输出任何 <think> 标签或思考步骤，直接简短回答。"
    ),

    "prompts": ModeConfig(
        name="prompts",
        label="📝 Prompts 模式 (提示词意图提取)",
        description="基于提示词结构化解析引擎，将用户自然语言精准提取为 JSON Action 指令。",
        system_prompt="",  # 运行时由 INTENT_SYSTEM_PROMPT 结合动态时间格式化填充
        temperature=0.0,
        num_predict=512,
        use_tools=False,
        json_format=True,
        disable_thinking_prompt=""
    ),

    "chat": ModeConfig(
        name="chat",
        label="💬 Chat 模式 (纯聊天)",
        description="纯文本对话聊天模式，不触发任何 SQL 或工具调用，支持空白系统提示词或自定义闲聊 Prompt。",
        system_prompt="",  # 默认空白系统提示词，也可自由配置修改
        temperature=0.7,
        num_predict=512,
        use_tools=False,
        json_format=False,
        disable_thinking_prompt=""
    )
}


# 全局运行期模式注册表缓存
_active_mode_registry: Dict[str, ModeConfig] = {k: v for k, v in DEFAULT_MODE_CONFIGS.items()}


# =====================================================================
# 3. 模式配置管理 API
# =====================================================================

def get_mode_config(mode_name: str) -> ModeConfig:
    """获取指定模式的配置对象，若不存在则回退至 chat 纯聊天模式"""
    return _active_mode_registry.get(mode_name.lower().strip(), _active_mode_registry["chat"])


def update_mode_config(mode_name: str, **kwargs) -> ModeConfig:
    """
    从不同角度动态更新指定模式的控制细节 (如 system_prompt, temperature, num_predict 等)
    """
    config = get_mode_config(mode_name)
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    return config


def register_custom_mode(mode_config: ModeConfig) -> None:
    """注册新的自定义模式控制细节"""
    _active_mode_registry[mode_config.name.lower().strip()] = mode_config


def list_all_modes() -> Dict[str, ModeConfig]:
    """返回当前支持的所有模式配置注册表"""
    return _active_mode_registry


# =====================================================================
# 4. 精确时间上下文与消息构造器 (Time-Aware Message Builder)
# =====================================================================

def get_current_time_info() -> str:
    """获取当前精准到秒的系统真实时间与星期字符串"""
    now = datetime.datetime.now()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return f"当前系统真实时间: {now.strftime('%Y-%m-%d %H:%M:%S')} ({weekdays[now.weekday()]})"


def build_mode_messages(
    mode_name: str,
    user_input: str,
    enable_thinking: bool = True
) -> Tuple[List[Dict[str, str]], ModeConfig]:
    """
    为指定模式构造携带提问时刻精确到秒的系统时间上下文与完整的 messages 数组
    """
    mode_cfg = get_mode_config(mode_name)
    time_info = get_current_time_info()

    system_prompt = mode_cfg.system_prompt.strip()
    if system_prompt:
        combined_sys_prompt = f"{system_prompt}\n{time_info}"
    else:
        combined_sys_prompt = time_info

    if not enable_thinking and mode_cfg.disable_thinking_prompt:
        combined_sys_prompt += mode_cfg.disable_thinking_prompt

    messages = [
        {"role": "system", "content": combined_sys_prompt},
        {"role": "user", "content": user_input}
    ]
    return messages, mode_cfg
