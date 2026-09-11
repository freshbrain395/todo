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
        from backend.service.ai_config import AiConfigService
        from backend.repository.ai_config import DEFAULT_PROVIDERS
        self.ai_cfg_service = AiConfigService(self.db)
        self.ai_cfg_service.save_providers([dict(p) for p in DEFAULT_PROVIDERS])

    def tearDown(self):
        from backend.repository.ai_config import DEFAULT_PROVIDERS
        self.ai_cfg_service.save_providers([dict(p) for p in DEFAULT_PROVIDERS])

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

    def test_mode_param_completions(self):
        completer = SlashCommandCompleter()
        event = CompleteEvent()

        # 验证 /mode 未输入空格时匹配 /mode 一级命令本身，不提前展开二级选项
        comps_mode = [c.text for c in completer.get_completions(Document("/mode"), event)]
        self.assertTrue(any(c.startswith("/mode") for c in comps_mode))
        self.assertNotIn("/mode chat", comps_mode)

        # 验证 /mode 输入空格后才提供二级模式参数补全
        comps_space = [c.text for c in completer.get_completions(Document("/mode "), event)]
        self.assertIn("/mode chat", comps_space)
        self.assertIn("/mode agent", comps_space)
        self.assertIn("/mode json", comps_space)


    def test_unified_secondary_completions(self):
        completer = SlashCommandCompleter()
        event = CompleteEvent()

        # /think 二级补全
        comps_think = [c.text for c in completer.get_completions(Document("/think "), event)]
        self.assertIn("/think toggle", comps_think)
        self.assertIn("/think on", comps_think)
        self.assertIn("/think off", comps_think)

        # /list 二级补全
        comps_list = [c.text for c in completer.get_completions(Document("/list "), event)]
        self.assertIn("/list all", comps_list)
        self.assertIn("/list pending", comps_list)
        self.assertIn("/list completed", comps_list)

        # /provider 二级补全
        comps_prov = [c.text for c in completer.get_completions(Document("/provider "), event)]
        self.assertIn("/provider custom", comps_prov)
        self.assertNotIn("/provider key", comps_prov)
        self.assertIn("/provider ollama", comps_prov)

        # /model 二级补全
        comps_model = [c.text for c in completer.get_completions(Document("/model "), event)]
        self.assertIn("/model deepseek-chat", comps_model)

        # /prompt 二级补全
        comps_prompt = [c.text for c in completer.get_completions(Document("/prompt "), event)]
        self.assertIn("/prompt p1", comps_prompt)

        # /skill 二级补全
        comps_skill = [c.text for c in completer.get_completions(Document("/skill "), event)]
        self.assertIn("/skill skill-gtd", comps_skill)

    def test_provider_custom_add_command(self):
        # 模拟通过交互提示添加自定义 provider
        mock_session = AsyncMock()
        mock_session.prompt_async.side_effect = [
            "my-test-provider",              # ID
            "My Test Provider",              # Name
            "https://test.provider.com/v1",  # Base URL
            "sk-test-123456",                # API Key
            "test-model-v1",                 # Model
        ]
        with patch("backend.cli.app.run_interactive_selection_menu", new_callable=AsyncMock) as mock_menu:
            mock_menu.return_value = ("confirm", {"id": "add"})
            ret = asyncio.run(
                handle_command("/provider custom", self.db, self.cfg, self.history, self.current_mode, session=mock_session)
            )
            self.assertTrue(ret)
            self.assertEqual(self.cfg.provider, "my-test-provider")
            self.assertEqual(self.cfg.base_url, "https://test.provider.com/v1")
            self.assertEqual(self.cfg.api_key, "sk-test-123456")
            self.assertEqual(self.cfg.model, "test-model-v1")

    def test_provider_edit_custom_command(self):
        # 确保存在待编辑的自定义 provider
        provs = self.ai_cfg_service.get_providers()
        provs.append({
            "id": "my-test-provider",
            "name": "My Test Provider",
            "base_url": "https://old.test.provider.com/v1",
            "api_key": "old-key",
            "model": "old-model",
            "is_custom": True,
        })
        self.ai_cfg_service.save_providers(provs)

        self.cfg.provider = "my-test-provider"
        mock_session = AsyncMock()
        mock_session.prompt_async.side_effect = [
            "https://new.test.provider.com/v1",  # Base URL
            "sk-new-key-8888",                   # API Key
            "test-model-v2",                     # Model
        ]
        ret = asyncio.run(
            handle_command("/provider edit my-test-provider", self.db, self.cfg, self.history, self.current_mode, session=mock_session)
        )
        self.assertTrue(ret)
        self.assertEqual(self.cfg.base_url, "https://new.test.provider.com/v1")
        self.assertEqual(self.cfg.api_key, "sk-new-key-8888")
        self.assertEqual(self.cfg.model, "test-model-v2")

    def test_provider_edit_builtin_only_apikey(self):
        # 内置 provider 只提示修改 API Key，保持其预设 Base URL
        self.cfg.provider = "deepseek"
        mock_session = AsyncMock()
        mock_session.prompt_async.side_effect = [
            "sk-deepseek-9999",  # API Key
        ]
        ret = asyncio.run(
            handle_command("/provider edit deepseek", self.db, self.cfg, self.history, self.current_mode, session=mock_session)
        )
        self.assertTrue(ret)
        self.assertEqual(self.cfg.api_key, "sk-deepseek-9999")
        # Base URL 仍然为默认的 https://api.deepseek.com/v1
        p_deepseek = next(p for p in self.ai_cfg_service.get_providers() if p.get("id") == "deepseek")
        self.assertEqual(p_deepseek.get("base_url"), "https://api.deepseek.com/v1")

    def test_provider_delete_custom_command(self):
        # 准备一个自定义 provider
        provs = self.ai_cfg_service.get_providers()
        provs.append({
            "id": "my-del-provider",
            "name": "To Delete",
            "base_url": "https://del.test/v1",
            "api_key": "del-key",
            "model": "del-model",
            "is_custom": True,
        })
        self.ai_cfg_service.save_providers(provs)

        mock_session = AsyncMock()
        mock_session.prompt_async.side_effect = ["y"]
        ret = asyncio.run(
            handle_command("/provider delete my-del-provider", self.db, self.cfg, self.history, self.current_mode, session=mock_session)
        )
        self.assertTrue(ret)
        ids = [p.get("id") for p in self.ai_cfg_service.get_providers()]
        self.assertNotIn("my-del-provider", ids)

    def test_provider_delete_builtin_prevented(self):
        # 内置 provider 不可删除
        mock_session = AsyncMock()
        ret = asyncio.run(
            handle_command("/provider delete deepseek", self.db, self.cfg, self.history, self.current_mode, session=mock_session)
        )
        self.assertTrue(ret)
        ids = [p.get("id") for p in self.ai_cfg_service.get_providers()]
        self.assertIn("deepseek", ids)

    def test_interactive_selection_menu_borderless_and_indented(self):
        from prompt_toolkit.application import Application
        from backend.cli.app import run_interactive_selection_menu

        captured_app = {}
        orig_init = Application.__init__

        def custom_init(self, *args, **kwargs):
            orig_init(self, *args, **kwargs)
            captured_app["app"] = self

        items = [
            {"id": "opt1", "name": "Option 1"},
            {"id": "opt2", "name": "Option 2"},
        ]

        with patch.object(Application, "__init__", custom_init):
            with patch.object(Application, "run_async", new_callable=AsyncMock):
                asyncio.run(
                    run_interactive_selection_menu(
                        title="测试菜单",
                        items=items,
                        current_id="opt1",
                    )
                )

        app = captured_app["app"]
        tokens = app.layout.container.children[0].content.text()
        full_text = "".join(t[1] for t in tokens)

        # 验证二级菜单取消了边框字符
        self.assertNotIn("╭", full_text)
        self.assertNotIn("╮", full_text)
        self.assertNotIn("╰", full_text)
        self.assertNotIn("╯", full_text)

        # 验证所有选项新增了一个缩进 (以 "  ❯ " 或 "    " 开头)
        lines = full_text.split("\n")
        self.assertTrue(lines[0].startswith("  ❯ Option 1"))
        self.assertTrue(lines[1].startswith("    Option 2"))

        # 验证菜单标题与提示行放置在最底部
        self.assertTrue(lines[2].startswith("测试菜单"))

    def test_interactive_selection_menu_scroll_indicators_indented(self):
        from prompt_toolkit.application import Application
        from backend.cli.app import run_interactive_selection_menu

        captured_app = {}
        orig_init = Application.__init__

        def custom_init(self, *args, **kwargs):
            orig_init(self, *args, **kwargs)
            captured_app["app"] = self

        items = [{"id": f"id_{i}", "name": f"Option {i}"} for i in range(15)]

        with patch.object(Application, "__init__", custom_init):
            with patch.object(Application, "run_async", new_callable=AsyncMock):
                asyncio.run(
                    run_interactive_selection_menu(
                        title="多项菜单",
                        items=items,
                        current_id="id_0",
                        max_visible_items=5,
                    )
                )

        app = captured_app["app"]
        tokens = app.layout.container.children[0].content.text()
        full_text = "".join(t[1] for t in tokens)

        # 验证向下滚动指示符存在且有缩进
        self.assertIn("    ▼ 更多项目...", full_text)

    def test_help_command_interactive_esc(self):
        from backend.cli.app import show_help

        # 验证 /help 触发交互式菜单，而非直接打印输出
        with patch("backend.cli.app.run_interactive_selection_menu", new_callable=AsyncMock) as mock_menu:
            mock_menu.return_value = ("cancel", None)
            ret = asyncio.run(handle_command("/help", self.db, self.cfg, self.history, self.current_mode))
            self.assertTrue(ret)
            self.assertTrue(mock_menu.called)
            kwargs = mock_menu.call_args.kwargs
            self.assertEqual(kwargs["title"], "📌 常用 Slash 命令帮助")
            self.assertIn("Esc", kwargs["help_hint"])
            self.assertIn("q", kwargs.get("extra_bindings", {}))

    def test_help_command_without_slash(self):
        with patch("backend.cli.app.run_interactive_selection_menu", new_callable=AsyncMock) as mock_menu:
            mock_menu.return_value = ("cancel", None)
            ret = asyncio.run(handle_command("help", self.db, self.cfg, self.history, self.current_mode))
            self.assertTrue(ret)
            self.assertTrue(mock_menu.called)

    def test_interactive_selection_menu_erases_when_done(self):
        from prompt_toolkit.application import Application
        from backend.cli.app import run_interactive_selection_menu

        captured_app = {}
        orig_init = Application.__init__

        def custom_init(self, *args, **kwargs):
            orig_init(self, *args, **kwargs)
            captured_app["app"] = self

        items = [{"id": "1", "name": "Test"}]

        with patch.object(Application, "__init__", custom_init):
            with patch.object(Application, "run_async", new_callable=AsyncMock):
                asyncio.run(
                    run_interactive_selection_menu(
                        title="测试擦除",
                        items=items,
                    )
                )

        app = captured_app["app"]
        # 验证菜单退出时开启自动擦除屏幕内容，不留残影
        self.assertTrue(getattr(app, "erase_when_done", False))


if __name__ == "__main__":
    unittest.main()
