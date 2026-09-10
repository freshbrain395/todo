import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from backend.service.ai import (
    LlmConfig,
    clean_llm_response,
    parse_intent_and_execute,
)
from backend.repository.db import DbState


class TestAiThinking(unittest.TestCase):
    def test_clean_llm_response_removes_think_tags(self):
        text = "<think>Here is some internal thinking</think>{\"action\":\"chat\",\"raw_response\":\"hello\"}"
        cleaned = clean_llm_response(text)
        self.assertEqual(cleaned, '{\"action\":\"chat\",\"raw_response\":\"hello\"}')

    @patch("backend.service.ai.httpx.AsyncClient")
    @patch("backend.service.ai.ensure_ollama_running", new_callable=AsyncMock)
    def test_ollama_thinking_false(self, mock_ensure, mock_client_cls):
        db = DbState.get_instance()
        config = LlmConfig(
            provider="ollama",
            base_url="http://127.0.0.1:11434",
            model="qwen3.5:0.8b",
            enable_thinking=False,
        )

        mock_resp = MagicMock()
        mock_resp.is_success = True
        mock_resp.json.return_value = {
            "response": '{\"action\":\"chat\",\"data\":{},\"raw_response\":\"你好\"}'
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        import asyncio
        res = asyncio.run(parse_intent_and_execute("你好", config, db))

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        called_url = call_args[0][0]
        called_json = call_args[1]["json"]

        self.assertIn("/api/generate", called_url)
        self.assertEqual(called_json["model"], "qwen3.5:0.8b")
        self.assertIn("think", called_json)
        self.assertFalse(called_json["think"])
        self.assertEqual(res.message, "你好")

    @patch("backend.service.ai.httpx.AsyncClient")
    @patch("backend.service.ai.ensure_ollama_running", new_callable=AsyncMock)
    def test_ollama_thinking_true(self, mock_ensure, mock_client_cls):
        db = DbState.get_instance()
        config = LlmConfig(
            provider="ollama",
            base_url="http://127.0.0.1:11434",
            model="qwen3.5:0.8b",
            enable_thinking=True,
        )

        mock_resp = MagicMock()
        mock_resp.is_success = True
        mock_resp.json.return_value = {
            "response": '{\"action\":\"chat\",\"data\":{},\"raw_response\":\"你好，已思考完毕\"}',
            "thinking": "我正在思考...",
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        import asyncio
        res = asyncio.run(parse_intent_and_execute("你好", config, db))

        called_json = mock_client.post.call_args[1]["json"]
        self.assertIn("think", called_json)
        self.assertTrue(called_json["think"])
        self.assertEqual(res.message, "你好，已思考完毕")

    def test_cli_think_command(self):
        import asyncio
        from backend.cli import handle_command

        db = DbState.get_instance()
        cfg = LlmConfig(enable_thinking=False)
        history = []
        mode = {"role": "chat", "display_name": "聊天", "status_text": "就绪"}

        # 测试 /think 切换 (toggle: False -> True)
        asyncio.run(handle_command("/think", db, cfg, history, mode))
        self.assertTrue(cfg.enable_thinking)

        # 测试 /think off (True -> False)
        asyncio.run(handle_command("/think off", db, cfg, history, mode))
        self.assertFalse(cfg.enable_thinking)

        # 测试 /think on (False -> True)
        asyncio.run(handle_command("/think on", db, cfg, history, mode))
        self.assertTrue(cfg.enable_thinking)

        # 测试 /think toggle (True -> False)
        asyncio.run(handle_command("/think toggle", db, cfg, history, mode))
        self.assertFalse(cfg.enable_thinking)


if __name__ == "__main__":
    unittest.main()
