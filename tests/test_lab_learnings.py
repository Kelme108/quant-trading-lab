import tempfile
import unittest
from pathlib import Path

from lab import learnings, registry


def add_run(conn, hid, pair, split, *, trades, net_base, net_opt, decision):
    exp = f"{hid.lower()}-{split}-{pair.split('/')[0].lower()}"
    registry.add_experiment(conn, experiment_id=exp, hypothesis_id=hid, strategy_file="x.py", strategy_sha256="0",
                            cost_scenario="base", split=split, command="x", artifact_path=None, status="completed",
                            created_at_utc="2026-11-01T00:00:00+00:00", pair=pair)
    registry.record_metrics(conn, exp, {"trades__base": trades, "net_profit_quote__base": net_base,
                                        "net_profit_quote__optimistic": net_opt})
    registry.record_decision(conn, experiment_id=exp, decision=decision, reasons=["net_profit[base]: FAIL (x)"],
                             gates_sha256="0", decided_at_utc="2026-11-01T00:00:00+00:00")


class LearningsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.conn = registry.connect(Path(self.tmp.name) / "lab.sqlite")
        for hid, fam in (("H-001", "FamA"), ("H-002", "FamB")):
            registry.add_hypothesis(self.conn, hypothesis_id=hid, family=fam, ex_ante_rule="rule", proposed_at_utc="2026-11-01",
                                    data_visible_at_proposal="x", status="rejected at exploration", notes="")

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def test_gross_move_is_recovered_from_the_two_cost_scenarios(self) -> None:
        # notional = (net_opt - net_base) / 0.001 = 50000; net edge = 50 / 50000 = 0.10%; gross = 0.40%
        figures = learnings._pair_figures({"trades__base": 100, "net_profit_quote__base": 50.0, "net_profit_quote__optimistic": 100.0})
        self.assertAlmostEqual(figures["net_edge_pct"], 0.10, places=6)
        self.assertAlmostEqual(figures["gross_pct"], 0.40, places=6)

    def test_validation_results_never_enter_the_digest(self) -> None:
        add_run(self.conn, "H-001", "BTC/USDT", "exploration", trades=100, net_base=50.0, net_opt=100.0, decision="rejected")
        add_run(self.conn, "H-002", "BTC/USDT", "validation", trades=999, net_base=7.0, net_opt=9.0, decision="rejected")
        rows = learnings.hypothesis_rows(self.conn)
        self.assertEqual([r["id"] for r in rows], ["H-001"])
        text = learnings.digest(self.conn)
        self.assertIn("H-001", text)
        self.assertNotIn("H-002", text)

    def test_an_empty_registry_says_so(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            conn = registry.connect(Path(tmp) / "empty.sqlite")
            self.assertIn("No exploration results yet", learnings.digest(conn))
            conn.close()


if __name__ == "__main__":
    unittest.main()
