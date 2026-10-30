import json
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from lab import context, registry

BUDGET = {"max_hypotheses_per_cycle": 3, "max_variants_per_family": 2}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ContextTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.conn = registry.connect(self.root / "lab.sqlite")

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def hypothesis(self, number: int, family: str = "Fam") -> str:
        hypothesis_id = f"H-{number:03d}"
        registry.add_hypothesis(
            self.conn, hypothesis_id=hypothesis_id, family=family, ex_ante_rule=f"rule {number}",
            proposed_at_utc=now(), data_visible_at_proposal="t",
        )
        return hypothesis_id

    def experiment(self, hypothesis_id: str, split: str, pair: str, metrics: dict,
                   decision: str | None = None, artifact: str | None = None) -> str:
        experiment_id = f"{hypothesis_id}-{split}-{pair.replace('/', '-')}"
        registry.add_experiment(
            self.conn, experiment_id=experiment_id, hypothesis_id=hypothesis_id,
            strategy_file="x.py", strategy_sha256="0" * 64, cost_scenario="multi", split=split,
            command="", created_at_utc=now(), pair=pair, artifact_path=artifact,
        )
        registry.record_metrics(self.conn, experiment_id, metrics)
        registry.set_experiment_status(self.conn, experiment_id, "completed", artifact_path=artifact)
        if decision:
            registry.record_decision(
                self.conn, experiment_id=experiment_id, decision=decision, reasons=["r"],
                gates_sha256="x", decided_at_utc=now(),
            )
        return experiment_id


class ResearchContextTests(ContextTestCase):
    def render(self, hypothesis_id: str = "H-009") -> str:
        return context.research_context(
            self.conn, hypothesis_id=hypothesis_id, budget=BUDGET, hypotheses_proposed_this_cycle=0
        )

    def test_cost_facts_come_from_the_cost_module(self) -> None:
        text = self.render()
        self.assertIn("| base | 0.175% | 0.350% |", text)
        self.assertIn("| conservative | 0.250% | 0.500% |", text)

    def test_exploration_numbers_are_shown(self) -> None:
        hypothesis = self.hypothesis(1)
        self.experiment(
            hypothesis, "exploration", "BTC/USDT",
            {"trades__base": 123, "net_profit_quote__base": -4.5, "max_drawdown_pct__base": 61.0},
            decision="rejected",
        )
        text = self.render()
        self.assertIn("BTC/USDT: rejected", text)
        self.assertIn("trades=123", text)
        self.assertIn("net profit=-4.5", text)

    def test_validation_numbers_and_verdicts_are_withheld(self) -> None:
        hypothesis = self.hypothesis(1)
        self.experiment(
            hypothesis, "validation", "BTC/USDT",
            {"trades__base": 777, "net_profit_quote__base": 31.337}, decision="candidate_for_portfolio",
        )
        text = self.render()
        self.assertIn("numbers withheld on purpose", text)
        for leaked in ("777", "31.337", "candidate_for_portfolio"):
            self.assertNotIn(leaked, text)

    def test_a_validation_run_without_a_verdict_is_still_marked_as_run(self) -> None:
        hypothesis = self.hypothesis(1)
        self.experiment(hypothesis, "validation", "BTC/USDT", {"trades__base": 1})
        self.assertIn("numbers withheld on purpose", self.render())

    def test_families_at_their_cap_are_flagged(self) -> None:
        self.hypothesis(1, "Fam")
        self.hypothesis(2, "Fam")
        self.hypothesis(3, "Other")
        text = self.render()
        self.assertIn("Fam: 2 of 2 allowed variants used (CAP REACHED", text)
        self.assertIn("Other: 1 of 2 allowed variants used\n", text)

    def test_an_untested_hypothesis_says_so(self) -> None:
        self.hypothesis(1)
        self.assertIn("Not tested under the corrected harness", self.render())


class ReviewFactsTests(ContextTestCase):
    def write_zip(self, name: str, trades: list[dict]) -> str:
        path = self.root / name
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("r.json", json.dumps({"strategy": {"S": {"trades": trades}}}))
        return name

    def trades(self, profits: list[float]) -> list[dict]:
        return [
            {"open_date": "2020-01-01 00:00:00+00:00", "close_date": "2020-01-02 00:00:00+00:00",
             "trade_duration": 1440, "profit_ratio": p / 100, "profit_abs": p, "exit_reason": "x"}
            for p in profits
        ]

    def test_facts_trades_and_a_matching_crosscheck_are_written(self) -> None:
        hypothesis = self.hypothesis(1)
        artifact = self.write_zip("a.zip", self.trades([5.0, -2.0, 1.0]))
        self.experiment(
            hypothesis, "exploration", "BTC/USDT",
            {"trades__base": 3, "net_profit_quote__base": 4.0}, decision="rejected", artifact=artifact,
        )
        directory = context.write_review_facts(self.conn, hypothesis, "exploration", self.root)
        self.assertEqual(directory.name, "H-001-exploration")

        facts = json.loads((directory / "facts.json").read_text(encoding="utf-8"))
        pair = facts["pairs"]["BTC/USDT"]
        self.assertEqual(pair["decision"], "rejected")
        self.assertEqual(pair["metrics"]["trades__base"], 3)

        crosscheck = json.loads((directory / "crosscheck.json").read_text(encoding="utf-8"))
        self.assertTrue(crosscheck["BTC/USDT"]["matches"])
        self.assertEqual(crosscheck["BTC/USDT"]["trades_in_export"], 3)
        rows = (directory / "trades-btc-usdt.csv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(rows), 4)

    def test_a_stored_number_that_disagrees_with_the_export_is_flagged(self) -> None:
        hypothesis = self.hypothesis(1)
        artifact = self.write_zip("a.zip", self.trades([5.0, -2.0, 1.0]))
        self.experiment(
            hypothesis, "exploration", "BTC/USDT",
            {"trades__base": 3, "net_profit_quote__base": 99.0}, artifact=artifact,
        )
        directory = context.write_review_facts(self.conn, hypothesis, "exploration", self.root)
        crosscheck = json.loads((directory / "crosscheck.json").read_text(encoding="utf-8"))
        self.assertFalse(crosscheck["BTC/USDT"]["matches"])

    def test_a_different_trade_count_is_flagged(self) -> None:
        hypothesis = self.hypothesis(1)
        artifact = self.write_zip("a.zip", self.trades([5.0, -2.0]))
        self.experiment(
            hypothesis, "exploration", "BTC/USDT",
            {"trades__base": 3, "net_profit_quote__base": 3.0}, artifact=artifact,
        )
        directory = context.write_review_facts(self.conn, hypothesis, "exploration", self.root)
        crosscheck = json.loads((directory / "crosscheck.json").read_text(encoding="utf-8"))
        self.assertFalse(crosscheck["BTC/USDT"]["matches"])

    def test_a_missing_export_is_reported_not_crashed_on(self) -> None:
        hypothesis = self.hypothesis(1)
        self.experiment(hypothesis, "exploration", "ETH/USDT", {"trades__base": 3})
        directory = context.write_review_facts(self.conn, hypothesis, "exploration", self.root)
        crosscheck = json.loads((directory / "crosscheck.json").read_text(encoding="utf-8"))
        self.assertIn("error", crosscheck["ETH/USDT"])

    def test_only_the_requested_split_is_included(self) -> None:
        hypothesis = self.hypothesis(1)
        self.experiment(hypothesis, "exploration", "BTC/USDT", {"trades__base": 1})
        self.experiment(hypothesis, "validation", "BTC/USDT", {"trades__base": 2})
        directory = context.write_review_facts(self.conn, hypothesis, "exploration", self.root)
        facts = json.loads((directory / "facts.json").read_text(encoding="utf-8"))
        self.assertEqual(facts["pairs"]["BTC/USDT"]["metrics"]["trades__base"], 1)


if __name__ == "__main__":
    unittest.main()
