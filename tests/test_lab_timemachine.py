import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from lab import archive, registry, timemachine as tm


def synthetic_bars(days: int = 40, drift: float = 0.0, seed: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    index = pd.date_range("2023-01-01", periods=days * 96, freq="15min", tz="UTC")
    closes = 100 * np.exp(np.cumsum(rng.normal(drift, 0.003, len(index))))
    opens = np.concatenate([[100.0], closes[:-1]])
    spread = np.abs(rng.normal(0, 0.002, len(index))) * closes
    return pd.DataFrame({"open": opens, "high": np.maximum(opens, closes) + spread,
                         "low": np.minimum(opens, closes) - spread, "close": closes}, index=index)


class TimeMachineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bars = synthetic_bars()
        self.day = "2023-02-05"
        self.entry = float(self.bars.loc[f"{self.day} 01:45"].close)

    def plan(self, **kw):
        args = dict(entry_time="02:00", entry=self.entry, stop=self.entry * 0.99, target=self.entry * 1.02,
                    replays=2000, bars=self.bars)
        args.update(kw)
        return tm.run("BTC/USDT", self.day, **args)

    def test_the_same_seed_gives_the_same_numbers(self) -> None:
        self.assertEqual(self.plan()["mc"], self.plan()["mc"])
        self.assertNotEqual(self.plan(seed=7)["mc"]["p_target"], None)

    def test_the_odds_add_up_and_the_cost_lowers_r(self) -> None:
        mc = self.plan()["mc"]
        self.assertAlmostEqual(mc["p_target"] + mc["p_stop"] + mc["p_neither"], 1.0, places=3)
        self.assertLess(mc["avg_R_net"], mc["avg_R"])
        self.assertAlmostEqual(mc["cost_R"], 2 * 0.0015 * self.entry / (self.entry * 0.01), places=3)

    def test_only_sessions_before_the_plan_are_in_the_pool(self) -> None:
        past = tm.sessions_before(self.bars, pd.Timestamp(self.day, tz="UTC"), tm.Session(), 60)
        self.assertTrue(all(d < self.day for d, _ in past))
        self.assertEqual(len(past), 35)

    def test_bad_plans_are_refused_in_one_line(self) -> None:
        with self.assertRaises(tm.TMError):
            self.plan(stop=self.entry * 1.01)
        with self.assertRaises(tm.TMError):
            tm.run("BTC/USDT", "2023-01-10", entry_time="02:00", entry=100, stop=99, target=102, bars=self.bars)

    def test_a_stop_and_target_in_one_bar_counts_as_the_stop(self) -> None:
        pool = [[(1.0, 1.05, 0.95, 1.0)] for _ in range(4)]
        mc = tm.simulate(pool, 100.0, 99.0, 101.0, 0, 3, replays=10, window=0)
        self.assertEqual(mc["p_stop"], 1.0)

    def test_the_verdict_weighs_the_target_r(self) -> None:
        self.assertTrue(tm.verdict({"p_target": 0.30, "p_stop": 0.60, "r_at_target": 2.0}).startswith("Close to break-even"))
        self.assertTrue(tm.verdict({"p_target": 0.50, "p_stop": 0.50, "r_at_target": 1.0}).startswith("Close to a coin flip"))
        self.assertTrue(tm.verdict({"p_target": 0.20, "p_stop": 0.70, "r_at_target": 1.0}).startswith("Strongly toward the stop"))


class RestoreFromArchiveTests(unittest.TestCase):
    def test_a_restored_strategy_is_byte_identical_and_its_test_points_back(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            root = Path(tmp)
            (root / "user_data" / "strategies").mkdir(parents=True)
            (root / "tests").mkdir()
            strategy = root / "user_data" / "strategies" / "Demo_H007_v1.py"
            strategy.write_bytes(b"class Demo_H007_v1:\r\n    pass\r\n")
            original_test = 'ROOT = Path(__file__).parents[1]\nPATH = ROOT / "user_data" / "strategies" / "Demo_H007_v1.py"\n'
            (root / "tests" / "test_demo_h007_v1.py").write_text(original_test, encoding="utf-8")
            conn = registry.connect(root / "lab.sqlite")
            conn.execute("PRAGMA foreign_keys = OFF")  # no hypothesis rows in this throwaway registry
            archived = archive.archive_hypothesis(conn, "H-007", root=root, run_test=lambda *_: True)
            self.assertTrue(archived["archived"])
            restored = archive.restore_hypothesis(conn, "H-007", root=root)
            self.assertEqual(strategy.read_bytes(), b"class Demo_H007_v1:\r\n    pass\r\n")
            self.assertEqual(restored["sha256"], archived["sha256"])
            self.assertEqual((root / "tests" / "test_demo_h007_v1.py").read_text(encoding="utf-8"), original_test)
            self.assertFalse((root / "user_data" / "strategies" / "_archive" / "Demo_H007_v1.py").exists())
            self.assertIsNone(conn.execute("SELECT 1 FROM archived_strategies").fetchone())

    def test_a_tampered_archive_is_refused(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            root = Path(tmp)
            (root / "user_data" / "strategies").mkdir(parents=True)
            (root / "tests").mkdir()
            (root / "user_data" / "strategies" / "Demo_H008_v1.py").write_text("x = 1\n", encoding="utf-8")
            conn = registry.connect(root / "lab.sqlite")
            conn.execute("PRAGMA foreign_keys = OFF")  # no hypothesis rows in this throwaway registry
            archive.archive_hypothesis(conn, "H-008", root=root, run_test=lambda *_: True)
            (root / "user_data" / "strategies" / "_archive" / "Demo_H008_v1.py").write_text("x = 2\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                archive.restore_hypothesis(conn, "H-008", root=root)


if __name__ == "__main__":
    unittest.main()
