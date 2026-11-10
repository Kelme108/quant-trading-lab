import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from lab import registry, sources


def fake_fetch_factory(stars):
    def fake_fetch(url):
        return {"items": [{"full_name": "a/bot", "stargazers_count": stars, "description": "a bot", "pushed_at": "2026-11-01T00:00:00Z",
                           "license": {"spdx_id": "MIT"}, "language": "Python"}]}
    return fake_fetch


class SourcesTests(unittest.TestCase):
    def test_refresh_flags_new_and_rising_repositories(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            root = Path(tmp)
            (root / "research").mkdir()
            now = datetime(2026, 11, 10, tzinfo=timezone.utc)
            first = sources.refresh_catalog(root, fetch=fake_fetch_factory(1000), sleep=lambda s: None, now=now)
            self.assertEqual((first["new"], first["rising"]), (1, 0))
            second = sources.refresh_catalog(root, fetch=fake_fetch_factory(1005), sleep=lambda s: None, now=now)
            self.assertEqual((second["new"], second["rising"]), (0, 0))
            third = sources.refresh_catalog(root, fetch=fake_fetch_factory(1300), sleep=lambda s: None, now=now)
            self.assertEqual(third["rising"], 1)
            self.assertIn("github.com/a/bot", (root / sources.NEW_REPORT).read_text(encoding="utf-8"))
            self.assertEqual(json.loads((root / sources.CATALOG).read_text(encoding="utf-8"))["repos"][0]["first_seen"], "2026-11-10")

    def test_a_failing_query_does_not_stop_the_refresh(self) -> None:
        def broken(url):
            raise OSError("rate limit")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            root = Path(tmp)
            (root / "research").mkdir()
            result = sources.refresh_catalog(root, fetch=broken, sleep=lambda s: None)
            self.assertEqual(len(result["failed_queries"]), len(sources.QUERIES) + 1)

    def test_source_keys(self) -> None:
        self.assertEqual(sources.source_key("https://github.com/Owner/Repo/tree/main/x"), "github:owner/repo")
        self.assertEqual(sources.source_key("https://www.example.org/a"), "example.org")

    def test_yield_counts_ideas_hypotheses_and_passing_pairs(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            conn = registry.connect(Path(tmp) / "lab.sqlite")
            idea = {"title": "t", "source": {"type": "repo", "url": "https://github.com/x/y", "title": "T", "license": "MIT"},
                    "rule_summary": "r", "mechanism": "m", "timeframe": "1h", "longest_lookback": 5, "free_parameters": 1,
                    "fixed_parameters": True, "expected_trades_per_year": 100, "expected_gross_move_pct": 1.0, "family_hint": "FamX"}
            registry.add_idea(conn, idea_id="I-001", run_id="r", idea=idea, rule_hash="h1", created_at_utc="2026-11-01")
            registry.add_idea(conn, idea_id="I-002", run_id="r", idea={**idea, "title": "t2"}, rule_hash="h2", created_at_utc="2026-11-01")
            rows = sources.yield_table(conn)
            self.assertEqual(rows[0]["source"], "github:x/y")
            self.assertEqual((rows[0]["ideas"], rows[0]["registered"], rows[0]["passing"]), (2, 0, 0))
            self.assertIn("github:x/y", sources.yield_markdown(conn))
            conn.close()


if __name__ == "__main__":
    unittest.main()
