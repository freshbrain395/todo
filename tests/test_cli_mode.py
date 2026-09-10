import unittest
import asyncio
from unittest.mock import patch, AsyncMock
from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent
from backend.repository.db import DbState
from backend.service.ai import (
    LlmConfig,
    DEFAULT_AGENT_PROMPT,
    DEFAULT_CHAT_PROMPT,
    DEFAULT_JSON_PROMPT,
)
from backend.cli import (
    handle_command,
    SlashCommandCompleter,
    MODE_OPTIONS,
    select_mode_interactive,
    apply_mode_switch,
)


class TestCliModeSystem(unittest.TestCase):
    def setUp(self):
        self.db = DbState.get_instance()
        self.cfg = LlmConfig()
        self.history = []
        self.current_mode = {
            "name": "agent",
            "role": "agent",
            "display_name": "Agent助理",
            "status_text": "就绪",
            "system_prompt": DEFAULT_AGENT_PROMPT,
            "output_format": "text",
        }

    @patch("backend.cli.select_mode_interactive", new_callable=AsyncMock)
    def test_mode_interactive_selection(self, mock_select):
        # 模拟用户在独立二级菜单中选择了 'chat'
        mock_select.return_value = "chat"
        ret = asyncio.run(handle_command("/mode", self.db, self.cfg, self.history, self.current_mode))
        self.assertTrue(ret)
        self.assertEqual(self.current_mode["name"], "chat")
        self.assertEqual(self.current_mode["display_name"], "聊天模式")

    @patch("backend.cli.select_mode_interactive", new_callable=AsyncMock)
    def test_mode_interactive_cancel(self, mock_select):
        # 模拟用户按 Esc 取消选择
        mock_select.return_value = None
        ret = asyncio.run(handle_command("/mode", self.db, self.cfg, self.history, self.current_mode))
        self.assertTrue(ret)
        self.assertEqual(self.current_mode["name"], "agent")

    def test_switch_mode_chat_direct(self):
        ret = asyncio.run(handle_command("/mode chat", self.db, self.cfg, self.history, self.current_mode))
        self.assertTrue(ret)
        self.assertEqual(self.current_mode["name"], "chat")
        self.assertEqual(self.current_mode["role"], "chat")
        self.assertEqual(self.current_mode["display_name"], "聊天模式")
        self.assertEqual(self.current_mode["system_prompt"], DEFAULT_CHAT_PROMPT)
        self.assertEqual(self.current_mode["output_format"], "text")

    def test_switch_mode_json_direct(self):
        ret = asyncio.run(handle_command("/mode json", self.db, self.cfg, self.history, self.current_mode))
        self.assertTrue(ret)
        self.assertEqual(self.current_mode["name"], "json")
        self.assertEqual(self.current_mode["role"], "json")
        self.assertEqual(self.current_mode["display_name"], "JSON模式")
        self.assertEqual(self.current_mode["system_prompt"], DEFAULT_JSON_PROMPT)
        self.assertEqual(self.current_mode["output_format"], "json")

    def test_switch_mode_agent_direct(self):
        asyncio.run(handle_command("/mode json", self.db, self.cfg, self.history, self.current_mode))
        ret = asyncio.run(handle_command("/mode agent", self.db, self.cfg, self.history, self.current_mode))
        self.assertTrue(ret)
        self.assertEqual(self.current_mode["name"], "agent")
        self.assertEqual(self.current_mode["role"], "agent")
        self.assertEqual(self.current_mode["display_name"], "Agent助理")
        self.assertEqual(self.current_mode["system_prompt"], DEFAULT_AGENT_PROMPT)
        self.assertEqual(self.current_mode["output_format"], "text")

    def test_chat_alias(self):
        ret = asyncio.run(handle_command("/chat", self.db, self.cfg, self.history, self.current_mode))
        self.assertTrue(ret)
        self.assertEqual(self.current_mode["name"], "chat")
        self.assertEqual(self.current_mode["role"], "chat")
        self.assertEqual(self.current_mode["system_prompt"], DEFAULT_CHAT_PROMPT)
        self.assertEqual(self.current_mode["output_format"], "text")

    def test_agent_alias(self):
        asyncio.run(handle_command("/mode chat", self.db, self.cfg, self.history, self.current_mode))
        ret = asyncio.run(handle_command("/agent", self.db, self.cfg, self.history, self.current_mode))
        self.assertTrue(ret)
        self.assertEqual(self.current_mode["name"], "agent")
        self.assertEqual(self.current_mode["role"], "agent")
        self.assertEqual(self.current_mode["system_prompt"], DEFAULT_AGENT_PROMPT)
        self.assertEqual(self.current_mode["output_format"], "text")

    def test_invalid_mode(self):
        old_mode = dict(self.current_mode)
        ret = asyncio.run(handle_command("/mode unknown_mode", self.db, self.cfg, self.history, self.current_mode))
        self.assertTrue(ret)
        self.assertEqual(self.current_mode["name"], old_mode["name"])

    def test_mode_options_structure(self):
        self.assertEqual([opt[0] for opt in MODE_OPTIONS], ["chat", "agent", "json"])

    def test_mode_not_generate_param_completions(self):
        completer = SlashCommandCompleter()
        event = CompleteEvent()

        # 验证 /mode 作为一级命令，不展开参数补全 (/mode chat, /mode agent, /mode json)
        comps_mode = [c.text for c in completer.get_completions(Document("/mode"), event)]
        self.assertIn("/mode", comps_mode)
        self.assertNotIn("/mode chat", comps_mode)
        self.assertNotIn("/mode agent", comps_mode)
        self.assertNotIn("/mode json", comps_mode)

        # 验证 /mode 带空格时不匹配任何子命令
        comps_space = [c.text for c in completer.get_completions(Document("/mode "), event)]
        self.assertEqual(comps_space, [])


if __name__ == "__main__":
    unittest.main()
