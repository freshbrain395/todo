import pytest
from llm_client import (
    extract_time_delay,
    sanitize_and_build_action,
    TodoAction,
    mask_key
)


def test_extract_time_delay():
    assert extract_time_delay("10秒后提醒我") == 10
    assert extract_time_delay("请在 5 分钟后 提醒") == 300
    assert extract_time_delay("2小时后开会") == 7200
    assert extract_time_delay("没有任何时间") is None


def test_sanitize_and_build_action():
    raw_data = {
        "act": "add",
        "t": "写代码",
        "p": "high",
        "c": "工作",
        "d": "60"
    }
    action = sanitize_and_build_action(raw_data)
    assert action.action == "add"
    assert action.title == "写代码"
    assert action.priority == "high"
    assert action.category == "工作"
    assert action.delay_seconds == 60


def test_mask_key():
    assert mask_key("") == "未配置"
    assert mask_key("sk-1234567890abcdef") == "sk-123...cdef"
