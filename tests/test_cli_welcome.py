"""Tests for CLI welcome component."""

import pytest
from rich.console import Console, Group
from rich.panel import Panel
from backend.service.ai import LlmConfig
from backend.service.display_config import DisplayConfigService
from backend.cli.components.welcome import build_welcome_panel, print_welcome


def test_build_welcome_panel_structure():
    current_mode = {"display_name": "Agent助理"}
    llm_cfg = LlmConfig(provider="siliconflow", model="deepseek-ai/DeepSeek-V4-Flash", enable_thinking=True)
    welcome = build_welcome_panel(None, current_mode, llm_cfg)
    assert isinstance(welcome, Group)
    # 确保外层没有 Panel，内部包含子 Panel
    assert not isinstance(welcome, Panel)
    inner_panels = [item for item in welcome.renderables if isinstance(item, Panel)]
    assert len(inner_panels) == 2


def test_print_welcome_outputs_to_console():
    current_mode = {"display_name": "Agent助理"}
    llm_cfg = LlmConfig(provider="siliconflow", model="deepseek-ai/DeepSeek-V4-Flash", enable_thinking=False)
    
    outputs = []
    test_console = Console(record=True, width=100)
    print_welcome(None, current_mode, llm_cfg, console=test_console)
    rendered = test_console.export_text()
    
    assert "Todo Agent" in rendered
    assert "Agent助理" in rendered
    assert "siliconflow" in rendered
    assert "/help" in rendered
    assert "/list" in rendered
