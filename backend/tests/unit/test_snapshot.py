import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from knowledge.snapshot import strip_frontmatter, SnapshotManager


GATES_MD = """---
id: gates
title: Gates and last-call
lang: en
source: nia_airport/gates.md
---

# Gates

Gates are grouped by terminal.
"""


class TestStripFrontmatter(unittest.TestCase):
    def test_removes_leading_block(self):
        self.assertEqual(strip_frontmatter(GATES_MD), "# Gates\n\nGates are grouped by terminal.\n")

    def test_no_frontmatter_is_unchanged(self):
        md = "# Gates\n\nNo frontmatter here.\n"
        self.assertEqual(strip_frontmatter(md), md)

    def test_unterminated_block_is_unchanged(self):
        md = "---\nid: gates\ntitle: Gates\n\n# Gates\n"
        self.assertEqual(strip_frontmatter(md), md)

    def test_empty_frontmatter(self):
        self.assertEqual(strip_frontmatter("---\n---\n# Gates\n"), "# Gates\n")

    def test_handles_bom(self):
        self.assertEqual(strip_frontmatter("﻿---\nid: gates\n---\n# Gates\n"), "# Gates\n")

    def test_horizontal_rule_in_body_is_not_frontmatter(self):
        md = "# Gates\n\n---\n\nMore text.\n"
        self.assertEqual(strip_frontmatter(md), md)

    def test_empty_string(self):
        self.assertEqual(strip_frontmatter(""), "")


class TestSnapshot(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)
        corpus = self.data_dir / "lck_airport"
        corpus.mkdir()
        (corpus / "gates.md").write_text(GATES_MD, encoding="utf-8")

        manifest = {
            "airport": "Test",
            "iata": "LCK",
            "closed_world": True,
            "documents": [
                {"id": "gates", "title": "Gates and last-call", "lang": "en", "source": "lck_airport/gates.md"}
            ],
            "do_not_ingest": ["manifest.json"],
        }
        self.manifest_path = self.data_dir / "manifest.json"
        self.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        patcher = patch.multiple(
            "knowledge.snapshot.settings",
            data_dir=str(self.data_dir),
            manifest_path=str(self.manifest_path),
            cache_knowledge_context=True,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tmp.cleanup)

        self.manager = SnapshotManager()

    def test_frontmatter_absent_from_context_and_chunks(self):
        snapshot = self.manager.create_snapshot()

        context = snapshot.get_full_context()
        self.assertNotIn("nia_airport", context)
        self.assertNotIn("lang: en", context)
        self.assertIn("Gates are grouped by terminal.", context)

        for chunk in snapshot.chunks:
            self.assertNotIn("nia_airport", chunk["text"])
            self.assertNotIn("lang: en", chunk["text"])

    def test_full_context_is_memoised(self):
        snapshot = self.manager.create_snapshot()
        self.assertIs(snapshot.get_full_context(), snapshot.get_full_context())

    def test_refresh_builds_a_new_context(self):
        first = self.manager.refresh()
        second = self.manager.refresh()
        self.assertIsNot(first, second)
        self.assertEqual(first.get_full_context(), second.get_full_context())

    def test_refresh_preserves_previous_snapshot_on_failure(self):
        good = self.manager.refresh()
        self.manifest_path.write_text("{ not valid json", encoding="utf-8")

        self.assertIs(self.manager.refresh(), good)
        self.assertIs(self.manager.active_snapshot, good)

    def test_version_format(self):
        self.assertTrue(self.manager.create_snapshot().version.startswith("v_"))


if __name__ == "__main__":
    unittest.main()
