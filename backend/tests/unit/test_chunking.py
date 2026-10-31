import unittest

from retrieval.chunking import extract_markdown_tables, chunk_document


class TestChunking(unittest.TestCase):
    def test_table_extraction(self):
        md = """
# Parking Rates
| Vehicle | Duration | Rate |
|---|---|---|
| Car | 0-30 min | ₹50 |
| Car | 30-120 min | ₹100 |
"""
        tables = extract_markdown_tables(md)
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0]["headers"], ["Vehicle", "Duration", "Rate"])
        self.assertEqual(len(tables[0]["rows"]), 2)
        self.assertEqual(tables[0]["rows"][0]["Rate"], "₹50")

    def test_chunking_preserves_table(self):
        md = """
# Terminal 1 Facilities
Here is general information about the gates and terminals.

| Gate | Flight | Status |
|---|---|---|
| G1 | AI 401 | On Time |
| G2 | 6E 202 | Boarding |
"""
        chunks = chunk_document("test_doc", "Facilities", md, chunk_size=50)
        self.assertGreaterEqual(len(chunks), 1)
        table_chunks = [c for c in chunks if c.get("is_table")]
        self.assertEqual(len(table_chunks), 1)
        self.assertIn("AI 401", table_chunks[0]["text"])


if __name__ == "__main__":
    unittest.main()
