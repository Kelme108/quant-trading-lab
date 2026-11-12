import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from lab import knowledge, registry

SPLITS = {"pairs": {"BTC/USDT": {"exploration": {"start_utc": "2020-01-01T00:00:00Z", "end_utc": "2022-01-01T00:00:00Z"}}}}


def write_zip(path: Path, trades: list[dict], timeframe="1h") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("backtest-result.json", json.dumps({"strategy": {"X": {"timeframe": timeframe, "trades": trades}}}))
        zf.writestr("backtest-result_config.json", "{}")


def trade(day, hours, gross, cost=0.003):
    return {"open_date": f"2021-{1 + day // 28:02d}-{1 + day % 28:02d} 00:00:00", "open_rate": 100.0, "close_rate": 100.0 * (1 + gross),
            "trade_duration": int(hours * 60), "profit_ratio": gross - cost}


class KnowledgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.tmp.name)
        (self.root / "lab" / "config").mkdir(parents=True)
        (self.root / "lab" / "config" / "splits.json").write_text(json.dumps(SPLITS), encoding="utf-8")
        self.conn = registry.connect(self.root / "lab.sqlite")
        knowledge._cache.clear()

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def add(self, hid, split, trades):
        registry.add_hypothesis(self.conn, hypothesis_id=hid, family="F" + hid, ex_ante_rule="r", proposed_at_utc="2026-11-01",
                                data_visible_at_proposal="x", status="rejected at exploration", notes="")
        art = f"research/experiments/{hid}-{split}/raw/backtest-result-1.zip"
        write_zip(self.root / art, trades)
        exp = f"{hid}-{split}"
        registry.add_experiment(self.conn, experiment_id=exp, hypothesis_id=hid, strategy_file=f"user_data/strategies/S_{hid[2:]}.py",
                                strategy_sha256="0", cost_scenario="base", split=split, command="x", artifact_path=art,
                                status="completed", created_at_utc="2026-11-01T00:00:00+00:00", pair="BTC/USDT")
        registry.record_decision(self.conn, experiment_id=exp, decision="rejected", reasons=[], gates_sha256="0",
                                 decided_at_utc="2026-11-01T00:00:00+00:00")

    def test_frequency_holding_time_and_moves_come_from_the_trade_list(self) -> None:
        self.add("H-001", "exploration", [trade(i, 3, 0.001) for i in range(300)])     # 150/yr, 3h holds, 0.1% gross
        self.add("H-002", "exploration", [trade(i, 72, 0.02) for i in range(20)])      # 10/yr, 3-day holds, 2% gross
        rows = {r["id"]: r for r in knowledge.rows(self.conn, self.root)}
        a, b = rows["H-001"], rows["H-002"]
        self.assertAlmostEqual(a["trades_per_year_pair"], 300 / (731 / 365.25))
        self.assertTrue(a["day_trade"] and a["frequent"])
        self.assertAlmostEqual(a["gross_pct"], 0.1, places=6)
        self.assertAlmostEqual(a["net_pct"], -0.2, places=6)
        self.assertFalse(b["day_trade"])
        text = knowledge.daytrade_section(self.conn, self.root)
        self.assertIn("1 of those trade at least 100 times a year per pair, and 0 of THOSE", text)
        self.assertIn("H-001 S_001", text)                                              # listed as noise (gross <= 0.10%)
        self.assertIn("H-002", text)                                                    # the slow rule, out of scope

    def test_validation_trades_never_enter_the_knowledge_base(self) -> None:
        self.add("H-003", "validation", [trade(i, 3, 0.05) for i in range(50)])
        self.assertEqual(knowledge.rows(self.conn, self.root), [])
        self.assertNotIn("H-003", knowledge.daytrade_section(self.conn, self.root))

    def test_the_curated_evidence_is_shipped_with_sources(self) -> None:
        text = knowledge.evidence_section()
        self.assertIn("Outside evidence on intraday crypto", text)
        self.assertGreaterEqual(text.count("https://"), 5)


if __name__ == "__main__":
    unittest.main()
