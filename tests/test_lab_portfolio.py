import json
import random
import sqlite3
import tempfile
import unittest
import zipfile
from datetime import date, timedelta
from pathlib import Path

from lab import portfolio, registry

PAIR = "BTC/USDT"
START = date(2026, 1, 1)
DAYS = 60


def make_series(values: list[float], pair: str = PAIR) -> dict[tuple[str, date], float]:
    return {(pair, START + timedelta(days=i)): v for i, v in enumerate(values)}


def noise(seed: int, n: int = DAYS) -> list[float]:
    rng = random.Random(seed)
    return [rng.uniform(-0.02, 0.02) for _ in range(n)]


def candidate(
    hypothesis_id: str,
    returns,
    profits: tuple[float, ...] = (0.1, 0.1),
    failures: list[str] | None = None,
    family: str = "Family",
) -> portfolio.Candidate:
    return portfolio.Candidate(
        hypothesis_id=hypothesis_id,
        family=family,
        eligibility_failures=failures or [],
        per_day_profits=list(profits),
        daily_returns=returns,
    )


def included_ids(result: dict) -> list[str]:
    return [entry["hypothesis_id"] for entry in result["included"]]


def evaluation(result: dict, hypothesis_id: str) -> dict:
    return next(e for e in result["evaluations"] if e["hypothesis_id"] == hypothesis_id)


class SelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.criteria = portfolio.load_criteria()

    def test_no_consistent_strategy_gives_a_valid_empty_portfolio(self) -> None:
        lopsided = candidate("H-001", make_series(noise(1)), profits=(0.2, 0.001))
        result = portfolio.select([lopsided], self.criteria)
        self.assertEqual(result["included"], [])
        self.assertFalse(evaluation(result, "H-001")["included"])
        self.assertTrue(any("inconsistent" in r for r in evaluation(result, "H-001")["reasons"]))

    def test_no_candidates_at_all_is_also_a_valid_empty_portfolio(self) -> None:
        result = portfolio.select([], self.criteria)
        self.assertEqual(result["included"], [])
        self.assertEqual(result["evaluations"], [])

    def test_good_on_one_pair_and_bad_on_another_is_excluded(self) -> None:
        failures = ["ETH/USDT/exploration: decision is 'rejected', required 'candidate_for_portfolio'"]
        c = candidate("H-001", None, profits=(), failures=failures)
        result = portfolio.select([c], self.criteria)
        self.assertEqual(result["included"], [])
        self.assertIn("ETH/USDT/exploration", evaluation(result, "H-001")["reasons"][0])

    def test_profit_that_is_good_on_one_cell_and_tiny_on_another_is_inconsistent(self) -> None:
        c = candidate("H-001", make_series(noise(1)), profits=(0.5, 0.05))
        result = portfolio.select([c], self.criteria)
        self.assertEqual(result["included"], [])
        self.assertAlmostEqual(evaluation(result, "H-001")["consistency_ratio"], 0.1)

    def test_a_losing_cell_gives_ratio_zero_and_excludes(self) -> None:
        c = candidate("H-001", make_series(noise(1)), profits=(0.5, -0.01))
        result = portfolio.select([c], self.criteria)
        self.assertEqual(result["included"], [])
        self.assertEqual(evaluation(result, "H-001")["consistency_ratio"], 0.0)

    def test_highly_correlated_second_strategy_is_excluded(self) -> None:
        base = noise(1)
        near_copy = [v + 0.0001 * (i % 3) for i, v in enumerate(base)]
        result = portfolio.select(
            [candidate("H-001", make_series(base)), candidate("H-002", make_series(near_copy))],
            self.criteria,
        )
        self.assertEqual(included_ids(result), ["H-001"])
        second = evaluation(result, "H-002")
        self.assertGreater(second["correlations"]["H-001"], 0.99)
        self.assertTrue(any("correlation with H-001" in r for r in second["reasons"]))

    def test_uncorrelated_strategies_are_both_included_with_equal_weights(self) -> None:
        result = portfolio.select(
            [
                candidate("H-001", make_series(noise(1))),
                candidate("H-002", make_series(noise(2))),
            ],
            self.criteria,
        )
        self.assertEqual(included_ids(result), ["H-001", "H-002"])
        self.assertEqual([e["weight"] for e in result["included"]], [0.5, 0.5])

    def test_consideration_order_is_registration_order_not_performance(self) -> None:
        """H-002 earns ten times more per day but is a near copy of H-001.
        Registration order decides, so the better-looking H-002 is the one
        dropped, whatever order the candidates are passed in."""
        base = noise(1)
        near_copy = [v + 0.0001 * (i % 3) for i, v in enumerate(base)]
        modest_first = candidate("H-001", make_series(base), profits=(0.05, 0.05))
        better_later = candidate("H-002", make_series(near_copy), profits=(0.5, 0.5))
        result = portfolio.select([better_later, modest_first], self.criteria)
        self.assertEqual(included_ids(result), ["H-001"])

    def test_ids_sort_numerically_not_alphabetically(self) -> None:
        """Alphabetically "H-100" sorts before "H-99"; numerically H-99 was
        registered first and must be the one that is kept."""
        base = noise(1)
        result = portfolio.select(
            [candidate("H-100", make_series(list(base))), candidate("H-99", make_series(base))],
            self.criteria,
        )
        self.assertEqual(included_ids(result), ["H-99"])

    def test_missing_trade_export_fails_closed_for_a_later_candidate(self) -> None:
        result = portfolio.select(
            [candidate("H-001", make_series(noise(1))), candidate("H-002", None)],
            self.criteria,
        )
        self.assertEqual(included_ids(result), ["H-001"])
        self.assertIsNone(evaluation(result, "H-002")["correlations"]["H-001"])
        self.assertTrue(any("undefined" in r for r in evaluation(result, "H-002")["reasons"]))

    def test_constant_series_makes_correlation_undefined_and_excludes(self) -> None:
        result = portfolio.select(
            [
                candidate("H-001", make_series(noise(1))),
                candidate("H-002", make_series([0.0] * DAYS)),
            ],
            self.criteria,
        )
        self.assertEqual(included_ids(result), ["H-001"])

    def test_too_few_shared_days_makes_correlation_undefined(self) -> None:
        short = self.criteria["correlation"]["min_overlap_days"] - 1
        result = portfolio.select(
            [
                candidate("H-001", make_series(noise(1, short))),
                candidate("H-002", make_series(noise(2, short))),
            ],
            self.criteria,
        )
        self.assertEqual(included_ids(result), ["H-001"])

    def test_the_first_candidate_needs_no_correlation_data(self) -> None:
        result = portfolio.select([candidate("H-001", None)], self.criteria)
        self.assertEqual(included_ids(result), ["H-001"])
        self.assertEqual(result["included"][0]["weight"], 1.0)


class SeriesTests(unittest.TestCase):
    def test_consistency_ratio(self) -> None:
        self.assertAlmostEqual(portfolio.consistency_ratio([0.1, 0.4]), 0.25)
        self.assertEqual(portfolio.consistency_ratio([0.1, 0.0]), 0.0)
        self.assertEqual(portfolio.consistency_ratio([0.1, -0.1]), 0.0)
        self.assertEqual(portfolio.consistency_ratio([]), 0.0)

    def test_trade_profit_is_spread_over_its_holding_days(self) -> None:
        trades = [
            {
                "open_date": "2026-01-02 15:00:00+00:00",
                "close_date": "2026-01-04 01:00:00+00:00",
                "profit_ratio": 0.03,
            }
        ]
        series = portfolio.daily_returns_from_trades(trades, date(2026, 1, 1), date(2026, 1, 6))
        self.assertEqual(series[date(2026, 1, 1)], 0.0)
        for day in (2, 3, 4):
            self.assertAlmostEqual(series[date(2026, 1, day)], 0.01)
        self.assertEqual(series[date(2026, 1, 5)], 0.0)
        self.assertEqual(len(series), 6)

    def test_part_of_a_trade_outside_the_window_is_dropped(self) -> None:
        trades = [
            {
                "open_date": "2025-12-31 12:00:00+00:00",
                "close_date": "2026-01-02 12:00:00+00:00",
                "profit_ratio": 0.03,
            }
        ]
        series = portfolio.daily_returns_from_trades(trades, date(2026, 1, 1), date(2026, 1, 3))
        self.assertAlmostEqual(series[date(2026, 1, 1)], 0.01)
        self.assertAlmostEqual(series[date(2026, 1, 2)], 0.01)
        self.assertEqual(series[date(2026, 1, 3)], 0.0)

    def test_a_trade_that_closes_before_it_opens_is_an_error(self) -> None:
        trades = [
            {
                "open_date": "2026-01-03 00:00:00+00:00",
                "close_date": "2026-01-02 00:00:00+00:00",
                "profit_ratio": 0.01,
            }
        ]
        with self.assertRaises(ValueError):
            portfolio.daily_returns_from_trades(trades, date(2026, 1, 1), date(2026, 1, 5))


class SnapshotAndRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.conn = registry.connect(self.root / "lab.sqlite")
        self.scenarios = {
            "pairs": [{"pair": PAIR, "enabled": True}],
            "timeframes": [{"timeframe": "1h", "enabled": True}],
        }
        self.splits = {
            "pairs": {
                PAIR: {
                    "exploration": {
                        "start_utc": "2026-01-01T00:00:00Z",
                        "end_utc": "2026-03-01T00:00:00Z",
                    },
                    "validation": {
                        "start_utc": "2026-03-02T00:00:00Z",
                        "end_utc": "2026-03-31T00:00:00Z",
                    },
                }
            },
            "final_test": {"final_test_unlocked": False},
        }

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def add_tested_hypothesis(
        self, hypothesis_id: str, decisions: dict[str, str], *, with_artifact: bool = True
    ) -> None:
        registry.add_hypothesis(
            self.conn,
            hypothesis_id=hypothesis_id,
            family="Family",
            ex_ante_rule="rule",
            proposed_at_utc="2026-01-01T00:00:00Z",
            data_visible_at_proposal="test",
        )
        for split, decision in decisions.items():
            experiment_id = f"{hypothesis_id}-{split}"
            artifact_path = None
            if with_artifact:
                artifact_path = f"artifacts/{experiment_id}.zip"
                self.write_artifact(artifact_path, split)
            registry.add_experiment(
                self.conn,
                experiment_id=experiment_id,
                hypothesis_id=hypothesis_id,
                strategy_file="x.py",
                strategy_sha256="0" * 64,
                cost_scenario="multi",
                split=split,
                command="",
                created_at_utc="2026-01-02T00:00:00Z",
                artifact_path=artifact_path,
                pair=PAIR,
            )
            # 0.1 per day: 5.9 over the 59-day exploration split, 2.9 over validation's 29.
            profit = 5.9 if split == "exploration" else 2.9
            registry.record_metrics(self.conn, experiment_id, {"net_profit_quote__base": profit})
            registry.record_decision(
                self.conn,
                experiment_id=experiment_id,
                decision=decision,
                reasons=[],
                gates_sha256="x",
                decided_at_utc="2026-01-03T00:00:00Z",
            )

    def write_artifact(self, relative_path: str, split: str) -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        first_day = "2026-01-05" if split == "exploration" else "2026-03-05"
        trade = {
            "open_date": f"{first_day} 10:00:00+00:00",
            "close_date": f"{first_day} 20:00:00+00:00",
            "profit_ratio": 0.02,
            "profit_abs": 2.0,
        }
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("result.json", json.dumps({"strategy": {"S": {"trades": [trade]}}}))

    def build(self) -> dict:
        return portfolio.build_portfolio(
            self.conn, splits=self.splits, scenarios=self.scenarios, root=self.root
        )

    def test_hypothesis_candidate_in_every_cell_is_included(self) -> None:
        self.add_tested_hypothesis(
            "H-001", {"exploration": "candidate_for_portfolio", "validation": "candidate_for_portfolio"}
        )
        snapshot = self.build()
        self.assertEqual(included_ids(snapshot), ["H-001"])
        self.assertEqual(snapshot["required_pairs"], [PAIR])
        self.assertFalse(snapshot["final_test_unlocked_at_selection"])
        self.assertEqual(len(snapshot["criteria_sha256"]), 64)

    def test_one_non_candidate_cell_excludes_the_hypothesis(self) -> None:
        self.add_tested_hypothesis(
            "H-001", {"exploration": "candidate_for_portfolio", "validation": "inconclusive"}
        )
        snapshot = self.build()
        self.assertEqual(snapshot["included"], [])
        self.assertTrue(
            any("validation" in r and "inconclusive" in r for r in evaluation(snapshot, "H-001")["reasons"])
        )

    def test_a_missing_cell_excludes_the_hypothesis(self) -> None:
        self.add_tested_hypothesis("H-001", {"exploration": "candidate_for_portfolio"})
        snapshot = self.build()
        self.assertEqual(snapshot["included"], [])
        self.assertTrue(
            any("validation: no decision recorded" in r for r in evaluation(snapshot, "H-001")["reasons"])
        )

    def test_final_test_rows_are_ignored(self) -> None:
        self.add_tested_hypothesis(
            "H-001",
            {
                "exploration": "candidate_for_portfolio",
                "validation": "candidate_for_portfolio",
                "final_test": "rejected",
            },
        )
        snapshot = self.build()
        self.assertEqual(included_ids(snapshot), ["H-001"])

    def test_nothing_tested_gives_an_empty_snapshot(self) -> None:
        snapshot = self.build()
        self.assertEqual(snapshot["included"], [])
        self.assertEqual(snapshot["evaluations"], [])

    def test_building_is_refused_once_final_test_is_unlocked(self) -> None:
        self.splits["final_test"]["final_test_unlocked"] = True
        with self.assertRaises(portfolio.PortfolioFrozenError):
            self.build()

    def test_snapshot_is_written_once_and_never_overwritten(self) -> None:
        snapshot = self.build()
        out_dir = self.root / "portfolio"
        path = portfolio.write_snapshot(snapshot, out_dir)
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["included"], [])
        with self.assertRaises(FileExistsError):
            portfolio.write_snapshot(snapshot, out_dir)

    def test_count_prior_variants_counts_only_earlier_ones_in_the_same_family(self) -> None:
        for number, family in ((1, "A"), (2, "B"), (3, "A"), (4, "A")):
            registry.add_hypothesis(
                self.conn,
                hypothesis_id=f"H-{number:03d}",
                family=family,
                ex_ante_rule="r",
                proposed_at_utc="2026-01-01T00:00:00Z",
                data_visible_at_proposal="t",
            )
        self.assertEqual(registry.count_prior_variants(self.conn, "H-001"), 0)
        self.assertEqual(registry.count_prior_variants(self.conn, "H-002"), 0)
        self.assertEqual(registry.count_prior_variants(self.conn, "H-003"), 1)
        self.assertEqual(registry.count_prior_variants(self.conn, "H-004"), 2)

    def test_database_created_before_the_pair_column_is_migrated(self) -> None:
        legacy_path = self.root / "legacy.sqlite"
        legacy = sqlite3.connect(legacy_path)
        legacy.executescript(
            "CREATE TABLE hypotheses (id TEXT PRIMARY KEY, family TEXT NOT NULL, "
            "ex_ante_rule TEXT NOT NULL, proposed_at_utc TEXT NOT NULL, "
            "data_visible_at_proposal TEXT NOT NULL, status TEXT NOT NULL, notes TEXT);"
            "CREATE TABLE experiments (id TEXT PRIMARY KEY, hypothesis_id TEXT NOT NULL, "
            "strategy_file TEXT NOT NULL, strategy_sha256 TEXT NOT NULL, "
            "cost_scenario TEXT NOT NULL, split TEXT NOT NULL, command TEXT NOT NULL, "
            "artifact_path TEXT, status TEXT NOT NULL, created_at_utc TEXT NOT NULL);"
            "INSERT INTO experiments VALUES ('old', 'H-001', 'x.py', 'h', 'base', "
            "'exploration', 'c', NULL, 'completed', 't');"
        )
        legacy.commit()
        legacy.close()

        conn = registry.connect(legacy_path)
        try:
            row = conn.execute("SELECT pair FROM experiments WHERE id = 'old'").fetchone()
            self.assertEqual(row["pair"], "BTC/USDT")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
