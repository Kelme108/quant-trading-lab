"""D1 (2026-11-13): a dry-run bot is judged against the activity of its own exploration, bursts included."""

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from lab import activity, dryrun, registry  # noqa: E402

UTC = timezone.utc
START = datetime(2023, 1, 1, tzinfo=UTC)
END = datetime(2024, 1, 1, tzinfo=UTC)
WINDOWS = {"A/USDT": (START.isoformat(), END.isoformat()), "B/USDT": ("2022-06-01T00:00:00+00:00", END.isoformat())}


def steady(per_day: int) -> list[datetime]:
    out, t = [], START
    while t < END:
        out += [t + timedelta(hours=1 + i * 24 / per_day) for i in range(per_day)]
        t += timedelta(days=1)
    return out


def bursty() -> list[datetime]:
    """Ten trades on one day every ten days, nothing in between: ~1 trade a day on average, but 9 empty days in 10."""
    out, t = [], START
    while t < END:
        out += [t + timedelta(hours=10, minutes=5 * i) for i in range(10)]
        t += timedelta(days=10)
    return out


CFG = json.loads((ROOT / "lab" / "config" / "dryrun.json").read_text(encoding="utf-8"))


def bot(days: float, trades: int, quiet: float | None) -> dict:
    return {"days_running": days, "trades": trades, "days_since_last_trade": quiet, "trades_per_day": trades / days,
            "eta_days_to_min_trades": None}


class ExpectationTests(unittest.TestCase):
    def test_the_record_measures_pace_gaps_and_percentiles_on_the_common_window(self) -> None:
        rec = activity.expectation({"A/USDT": steady(2), "B/USDT": []}, WINDOWS)
        self.assertEqual(rec["window_utc"][0], START.isoformat())         # B starts earlier: the common window starts at A
        self.assertAlmostEqual(rec["trades_per_day"], 2.0, delta=0.05)
        self.assertLess(rec["max_gap_days"], 1.0)
        p1, p5 = (rec["closed_trades_percentile_by_days"][k] for k in ("1", "5"))
        self.assertEqual(len(p1), activity.HORIZON_DAYS)
        self.assertTrue(all(p1[str(d)] <= p5[str(d)] for d in range(1, 61)))
        self.assertTrue(all(p1[str(d)] <= p1[str(d + 1)] for d in range(1, 60)))
        self.assertGreaterEqual(p1["3"], 5)

    def test_a_short_common_window_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            activity.expectation({"A/USDT": steady(1)}, {"A/USDT": ((END - timedelta(days=30)).isoformat(), END.isoformat())})

    def test_floor_needs_a_full_day_and_scales_past_the_last_horizon(self) -> None:
        rec = activity.expectation({"A/USDT": steady(2)}, {"A/USDT": WINDOWS["A/USDT"]})
        self.assertIsNone(activity.floor_for(rec, 0.5))
        last = rec["closed_trades_percentile_by_days"]["1"]["60"]
        self.assertEqual(activity.floor_for(rec, 120.0), int(last * 2))

    def test_exploration_closes_reads_the_latest_completed_run_of_each_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            conn = registry.connect(Path(tmp) / "lab.sqlite")
            registry.add_hypothesis(conn, hypothesis_id="H-001", family="F", ex_ante_rule="r", proposed_at_utc="2026-01-01",
                                    data_visible_at_proposal="d", status="x")
            for when, art in (("2026-01-01", "old.zip"), ("2026-02-01", "new.zip")):
                eid = f"e-{art}"
                registry.add_experiment(conn, experiment_id=eid, hypothesis_id="H-001", strategy_file="s", strategy_sha256="0" * 64,
                                        cost_scenario="multi", split="exploration", command="", created_at_utc=when, pair="A/USDT")
                registry.set_experiment_status(conn, eid, "completed", artifact_path=art)
            read = {"new.zip": [{"close_date": "2023-05-01 10:00:00+00:00"}], "old.zip": []}
            closes = activity.exploration_closes(conn, "H-001", ["A/USDT"], Path(tmp), lambda p: read[p.name])
            self.assertEqual(closes, {"A/USDT": [datetime(2023, 5, 1, 10, tzinfo=UTC)]})
            with self.assertRaises(ValueError):
                activity.exploration_closes(conn, "H-001", ["B/USDT"], Path(tmp), lambda p: [])
            conn.close()


class DryRunRuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertEqual(CFG["inactivity"]["mode"], "expected_vs_observed")       # the owner's D1 is what is configured
        self.bursty = activity.expectation({"A/USDT": bursty()}, {"A/USDT": WINDOWS["A/USDT"]})
        self.steady = activity.expectation({"A/USDT": steady(5)}, {"A/USDT": WINDOWS["A/USDT"]})

    def test_a_bursty_rule_is_not_retired_by_a_calm_couple_of_days(self) -> None:
        state, reasons = dryrun.verdict({**bot(3.0, 0, None), **self._m(0)}, CFG, expected=self.bursty)
        self.assertEqual(state, "collecting", reasons)
        legacy, _ = dryrun.verdict({**bot(3.0, 0, None), **self._m(0)}, CFG)        # the earlier rule would retire it
        self.assertEqual(legacy, "inactive")

    def test_a_bot_quiet_for_longer_than_any_stretch_of_its_exploration_is_retired(self) -> None:
        gap = self.bursty["max_gap_days"]
        state, reasons = dryrun.verdict({**bot(gap + 5, 10, gap + 1), **self._m(10)}, CFG, expected=self.bursty)
        self.assertEqual(state, "inactive")
        self.assertIn("longest stretch", reasons[-1])

    def test_a_broken_bot_on_a_steady_rule_is_retired_within_days(self) -> None:
        state, reasons = dryrun.verdict({**bot(3.0, 0, None), **self._m(0)}, CFG, expected=self.steady)
        self.assertEqual(state, "inactive")
        self.assertIn("1st percentile", reasons[-1])

    def test_a_bot_on_pace_is_collecting_and_a_slow_one_is_warned(self) -> None:
        ok, _ = dryrun.verdict({**bot(3.0, 15, 0.1), **self._m(15)}, CFG, expected=self.steady)
        self.assertEqual(ok, "collecting")
        p1 = activity.floor_for(self.steady, 3.0, 1)
        p5 = activity.floor_for(self.steady, 3.0, 5)
        if p5 > p1:
            _, notes = dryrun.verdict({**bot(3.0, p1, 0.1), **self._m(p1)}, CFG, expected=self.steady)
            self.assertTrue(any(n.startswith("warning") for n in notes))

    @staticmethod
    def _m(trades: int) -> dict:
        return {"trades": trades, "days": 0.0, "profit_factor": None, "net_profit": 0.0}


if __name__ == "__main__":
    unittest.main()
