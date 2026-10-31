import unittest
from unittest.mock import patch

from strategies.okf import OKFStrategy, OKF_KNOWLEDGE_TEMPLATE


class _FakeSnapshot:
    def __init__(self, context="--- DOCUMENT: Gates ---\nGates are grouped by terminal.\n"):
        self._context = context

    def get_full_context(self):
        return self._context


class TestOKFPromptPrefix(unittest.TestCase):
    """
    The knowledge block must stay byte-identical across requests, languages and both the
    buffered and streaming paths, or the model cannot reuse its cached prompt prefix.
    """

    def setUp(self):
        patcher = patch("strategies.okf.snapshot_manager")
        self.manager = patcher.start()
        self.manager.active_snapshot = _FakeSnapshot()
        self.addCleanup(patcher.stop)

        with patch("strategies.okf.LLMClient"):
            self.strategy = OKFStrategy()

    def test_knowledge_block_is_first_and_static(self):
        messages = self.strategy._build_messages("Where is gate C22?", [], "en")
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("--- OFFICIAL KNOWLEDGE BASE ---", messages[0]["content"])
        self.assertNotIn("English", messages[0]["content"])

    def test_prefix_identical_across_languages(self):
        prefixes = {
            self.strategy._build_messages("q", [], lang)[0]["content"]
            for lang in ("en", "hi", "es")
        }
        self.assertEqual(len(prefixes), 1)

    def test_language_directive_follows_the_knowledge_block(self):
        messages = self.strategy._build_messages("q", [], "hi")
        self.assertIn("Hindi", messages[1]["content"])
        self.assertEqual(messages[-1], {"role": "user", "content": "q"})

    def test_history_sits_between_system_and_query(self):
        history = [{"role": "user", "content": "earlier"}, {"role": "assistant", "content": "reply"}]
        messages = self.strategy._build_messages("now", history, "en")
        self.assertEqual(messages[2:4], history)

    def test_prefix_unaffected_by_history_and_query(self):
        bare = self.strategy._build_messages("a", [], "en")[0]["content"]
        loaded = self.strategy._build_messages(
            "b", [{"role": "user", "content": "x"}], "es"
        )[0]["content"]
        self.assertEqual(bare, loaded)

    def test_language_template_is_not_inside_the_knowledge_template(self):
        self.assertNotIn("{language_instruction}", OKF_KNOWLEDGE_TEMPLATE)

    def test_refreshes_when_no_active_snapshot(self):
        self.manager.active_snapshot = None
        self.manager.refresh.return_value = _FakeSnapshot()
        self.strategy._build_messages("q", [], "en")
        self.manager.refresh.assert_called_once()


if __name__ == "__main__":
    unittest.main()
