"""Tests for CLI help_view component."""

import pytest
from rich.console import Console
from rich.panel import Panel
from backend.cli.components.help_view import (
    build_help_panel,
    build_command_detail_panel,
    print_help_view,
    COMMAND_CATEGORIES,
)


def test_build_help_panel_has_no_arrow_and_has_categories():
    panel = build_help_panel()
    assert isinstance(panel, Panel)
    
    test_console = Console(record=True, width=120)
    test_console.print(panel)
    output = test_console.export_text()
    
    # 确认没有交互式光标箭头
    assert "❯" not in output
    assert "  ❯ " not in output
    
    # 确认包含各分类标题
    assert "待办事项管理" in output
    assert "工作模式切换" in output
    assert "AI 模型与配置" in output
    assert "系统与界面" in output
    
    # 确认包含核心命令
    assert "/list" in output
    assert "/add" in output
    assert "/mode" in output
    assert "/provider" in output
    assert "/help" in output


def test_build_command_detail_panel():
    panel = build_command_detail_panel("add")
    assert isinstance(panel, Panel)
    
    test_console = Console(record=True, width=100)
    test_console.print(panel)
    output = test_console.export_text()
    assert "/add" in output
    assert "添加新待办" in output


def test_print_help_view_outputs():
    test_console = Console(record=True, width=100)
    print_help_view(console=test_console)
    output = test_console.export_text()
    assert "命令使用手册" in output
    assert "❯" not in output
