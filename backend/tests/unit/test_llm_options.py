import unittest
from unittest.mock import patch

from llm.client import LLMClient


class TestProviderOptions(unittest.TestCase):
    """
    Ollama defaults to a 2048-token context and truncates silently, which drops most of the
    knowledge snapshot. num_ctx must be sent for Ollama models and withheld from hosted ones.
    """

    def test_num_ctx_sent_for_ollama(self):
        with patch("llm.client.settings.llm_num_ctx", 16384):
            self.assertEqual(LLMClient("ollama/qwen2.5:7b")._provider_options(), {"num_ctx": 16384})

    def test_num_ctx_covers_ollama_chat_prefix(self):
        self.assertIn("num_ctx", LLMClient("ollama_chat/qwen2.5:7b")._provider_options())

    def test_num_ctx_withheld_from_hosted_providers(self):
        for model in ("gpt-4o-mini", "openai/gpt-4o", "anthropic/claude-sonnet-4", "gemini/gemini-2.0-flash"):
            self.assertEqual(LLMClient(model)._provider_options(), {}, msg=model)

    def test_num_ctx_exceeds_full_snapshot(self):
        """The snapshot measures ~7.6k prompt tokens; the default must leave room for it."""
        with patch("llm.client.settings.llm_num_ctx", 16384):
            self.assertGreater(LLMClient("ollama/qwen2.5:7b")._provider_options()["num_ctx"], 8000)


if __name__ == "__main__":
    unittest.main()
