"""The futures lane through the pipeline (docs/faixa-futuros.md): a strategy declares LAB_MARKET = "futures", and its
checks, calibration, experiments and validation then use the futures splits, costs and config. Spot is untouched."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from lab import autopilot, calibrate, checks, costs, lanes, registry, runner, strategy_check  # noqa: E402

FUTURES_STRATEGY = '''from freqtrade.strategy import IStrategy

LAB_MARKET = "{market}"


class Thing_H901_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    startup_candle_count = 400
    can_short = True
    stoploss = -0.03

    def populate_indicators(self, dataframe, metadata):
        return dataframe

    def populate_entry_trend(self, dataframe, metadata):
        dataframe["enter_short"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe, metadata):
        return dataframe
'''


def write(tmp: str, market: str = "futures") -> Path:
    path = Path(tmp) / "Thing_H901_v1.py"
    path.write_text(FUTURES_STRATEGY.format(market=market), encoding="utf-8")
    return path


class DeclaredMarketTests(unittest.TestCase):
    def test_the_market_comes_from_the_file_and_defaults_to_spot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(lanes.strategy_market(write(tmp)), "futures")
            plain = Path(tmp) / "Plain_H902_v1.py"
            plain.write_text("timeframe = '1h'\n", encoding="utf-8")
            self.assertEqual(lanes.strategy_market(plain), "spot")
            with self.assertRaises(ValueError):
                lanes.strategy_market(write(tmp, "margin"))

    def test_the_strategy_check_uses_the_declared_market(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(strategy_check.check_strategy_source(write(tmp)), [])
            self.assertTrue(any("LAB_MARKET" in p for p in strategy_check.check_strategy_source(write(tmp, "margin"))))
            spot = write(tmp, "spot")
            self.assertTrue(any("can_short = False" in p for p in strategy_check.check_strategy_source(spot)))

    def test_every_strategy_in_the_repository_is_spot(self) -> None:
        for path in (ROOT / "user_data" / "strategies").glob("*.py"):
            self.assertEqual(lanes.strategy_market(path), "spot", path.name)


class FuturesSplitsTests(unittest.TestCase):
    def test_futures_splits_keep_every_spot_boundary(self) -> None:
        spot, fut = runner.load_splits(), runner.load_splits(lane="futures")
        self.assertEqual(set(spot["pairs"]), set(fut["pairs"]))
        self.assertEqual(spot["final_test"], fut["final_test"])
        for pair, cell in spot["pairs"].items():
            f = fut["pairs"][pair]
            self.assertEqual(f["exploration"]["end_utc"], cell["exploration"]["end_utc"], pair)
            self.assertEqual(f["validation"], cell["validation"], pair)
            self.assertGreaterEqual(f["exploration"]["start_utc"], cell["exploration"]["start_utc"], pair)
            self.assertEqual(f["futures_pair"], pair + ":USDT")
        self.assertEqual(runner.resolve_split_timerange("validation", fut, pair="BTC/USDT"),
                         runner.resolve_split_timerange("validation", spot, pair="BTC/USDT"))


class LanePlumbingTests(unittest.TestCase):
    def test_causality_checks_run_in_the_lane(self) -> None:
        seen = []

        class Run:
            load_splits = staticmethod(runner.load_splits)
            resolve_split_timerange = staticmethod(runner.resolve_split_timerange)
            enabled_pairs = staticmethod(runner.enabled_pairs)

            @staticmethod
            def smoke_backtest(**kw):
                seen.append(("smoke", kw.get("lane")))
                return True, ""

            @staticmethod
            def run_lookahead_analysis(**kw):
                seen.append(("lookahead", kw.get("lane"), kw["fee"]))
                return {"lookahead_has_bias": False}

            @staticmethod
            def run_recursive_analysis(**kw):
                seen.append(("recursive", kw.get("lane")))
                return {"recursive_is_stable": True}

        with tempfile.TemporaryDirectory() as tmp:
            checks.run_checks("S", root=Path(tmp), run=Run, lane="futures")
        self.assertTrue(seen and all(s[1] == "futures" for s in seen))
        fee = costs.lane_scenario("base", "futures").effective_fee_per_side
        self.assertTrue(all(s[2] == fee for s in seen if s[0] == "lookahead"))

    def test_calibration_and_experiments_run_in_the_lane(self) -> None:
        calls = {"backtest": [], "experiment": []}

        def backtest(**kw):
            calls["backtest"].append(kw)
            return {"status": "completed", "artifact_path": "x.zip"}

        class Explorer:
            def freqtrade_version(self):
                return "fake"

            def run_experiment(self, conn, **kw):
                calls["experiment"].append(kw)
                eid = f"e-{kw['pair']}"
                registry.add_experiment(conn, experiment_id=eid, hypothesis_id="H-901", strategy_file="s", strategy_sha256="0" * 64,
                                        cost_scenario="futures:multi", split="exploration", command="", created_at_utc="2026",
                                        pair=kw["pair"])
                return eid

            def decide_experiment(self, conn, eid, hid):
                return "rejected", ["fake"]

        trades = [{"open_date": f"2020-01-{1 + i % 28:02d} 00:00:00+00:00", "profit_ratio": 0.03 if i % 3 == 0 else -0.01}
                  for i in range(60)]
        with tempfile.TemporaryDirectory() as tmp:
            conn = registry.connect(Path(tmp) / "lab.sqlite")
            registry.add_hypothesis(conn, hypothesis_id="H-901", family="F", ex_ante_rule="r", proposed_at_utc="2026",
                                    data_visible_at_proposal="d", status="implemented")
            pairs = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
            calibrate.calibrate_and_explore(conn, "H-901", strategy_name="S", strategy_file="s", root=Path(tmp),
                                            backtest=backtest, read_trades=lambda p: trades, experiments=Explorer(),
                                            pairs=pairs, workers=1, lane="futures")
            conn.close()
        fee = costs.lane_scenario("base", "futures").effective_fee_per_side
        self.assertEqual({c["lane"] for c in calls["backtest"]}, {"futures"})
        self.assertEqual({c["fee"] for c in calls["backtest"]}, {fee})
        futures_splits = runner.load_splits(lane="futures")
        self.assertEqual(calls["backtest"][0]["timerange"], futures_splits["pairs"]["BTC/USDT"]["exploration"]["timerange"])
        self.assertTrue(calls["experiment"] and {c["lane"] for c in calls["experiment"]} == {"futures"})


class ContaminationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.conn = registry.connect(Path(self.tmp.name) / "lab.sqlite")
        for hid, family in (("H-001", "Fam"), ("H-002", "Fam"), ("H-003", "Other"), ("H-004", "FamRVol"), ("H-005", "Famous")):
            registry.add_hypothesis(self.conn, hypothesis_id=hid, family=family,
                                    ex_ante_rule="r", proposed_at_utc="2026", data_visible_at_proposal="d", status="x")

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def experiment(self, hid: str, split: str, scenario: str = "multi:optimistic,base,conservative,stress") -> None:
        registry.add_experiment(self.conn, experiment_id=f"{hid}-{split}-{scenario[:3]}", hypothesis_id=hid, strategy_file="s",
                                strategy_sha256="0" * 64, cost_scenario=scenario, split=split, command="",
                                created_at_utc="2026", pair="BTC/USDT")

    def test_a_spot_validation_in_the_family_blocks_the_futures_validation(self) -> None:
        self.assertEqual(autopilot.family_spot_validations(self.conn, "H-002"), [])
        self.experiment("H-001", "exploration")
        self.experiment("H-003", "validation")                       # another family
        self.experiment("H-001", "validation", "futures:multi:optimistic,base,conservative,stress")
        self.assertEqual(autopilot.family_spot_validations(self.conn, "H-002"), [])
        self.experiment("H-001", "validation")
        self.assertEqual(autopilot.family_spot_validations(self.conn, "H-002"), ["H-001"])
        self.assertEqual(autopilot.family_spot_validations(self.conn, "H-004"), ["H-001"])   # a variant name extends "Fam"
        self.assertEqual(autopilot.family_spot_validations(self.conn, "H-003"), [])
        self.assertEqual(autopilot.family_spot_validations(self.conn, "H-001"), [])

    def test_read_validation_refuses_a_futures_hypothesis_of_a_spot_validated_family(self) -> None:
        self.experiment("H-001", "validation")
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(autopilot, "exploration_passed", return_value=True), \
                mock.patch.object(registry, "has_approval", return_value=True), \
                mock.patch.object(autopilot.forward, "find_strategy", return_value=write(tmp)):
            with self.assertRaises(autopilot.PolicyError) as caught:
                autopilot.read_validation(self.conn, "H-002", 0.25, root=Path(tmp), pairs=["BTC/USDT"],
                                          run_experiment=lambda *a, **k: self.fail("validation was read"))
        self.assertIn("SPOT validation", str(caught.exception))


if __name__ == "__main__":
    unittest.main()


class FuturesDryRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_futures_bot_files_use_futures_pairs_config_and_freeze_hash(self) -> None:
        from lab import forward
        files = autopilot.write_forward_files("H-901", ["BTC/USDT", "ETH/USDT"], 0.25, "Thing_H901_v1", self.root, lane="futures")
        overlay = json.loads((self.root / files[0]).read_text(encoding="utf-8"))
        compose = (self.root / files[1]).read_text(encoding="utf-8")
        self.assertEqual(overlay["exchange"]["pair_whitelist"], ["BTC/USDT:USDT", "ETH/USDT:USDT"])
        self.assertIn("--config /freqtrade/user_data/config.futures.dryrun.json", compose)
        self.assertNotIn("config.dryrun.json --config", compose)
        self.assertIn("FUTURES lane", compose)
        self.assertEqual(forward.pair_keys("H-901", self.root), ["btc", "eth"])
        self.assertTrue(forward.is_futures("H-901", self.root))
        (self.root / "user_data" / "strategies").mkdir(parents=True)
        (self.root / "user_data" / "strategies" / "Thing_H901_v1.py").write_text("x = 1\n", encoding="utf-8")
        self.assertIn(forward.FUTURES_CONFIG, forward.tracked_files("H-901", self.root))
        spot = autopilot.write_forward_files("H-902", ["BTC/USDT"], 0.25, "Thing_H902_v1", self.root)
        self.assertEqual(json.loads((self.root / spot[0]).read_text(encoding="utf-8"))["exchange"]["pair_whitelist"], ["BTC/USDT"])
        self.assertFalse(forward.is_futures("H-902", self.root))
        with self.assertRaises(ValueError):
            autopilot.write_forward_files("H-903", ["BTC/USDT"], 0.25, "T", self.root, layout=forward.PER_PAIR, lane="futures")

    def test_a_futures_database_is_read_under_the_spot_pair_key(self) -> None:
        import sqlite3
        from lab import forward
        db = self.root / "bot.sqlite"
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE trades (id INTEGER, pair TEXT, open_date TEXT)")
        conn.execute("CREATE TABLE orders (id INTEGER, ft_trade_id INTEGER, order_date TEXT)")
        conn.executemany("INSERT INTO trades VALUES (?, ?, ?)", [(1, "BTC/USDT:USDT", "2026-11-13"), (2, "ETH/USDT:USDT", "2026-11-13")])
        conn.execute("INSERT INTO orders VALUES (1, 1, '2026-11-13')")
        conn.commit()
        conn.close()
        trades, orders = forward.read_database(Path(forward.pair_selector(str(db), "BTC/USDT")))
        self.assertEqual([t["id"] for t in trades], [1])
        self.assertEqual(len(orders), 1)

    def test_short_slippage_is_signed_for_the_short_side(self) -> None:
        from lab import forward
        long_ = {"open_rate": 101.0, "open_rate_requested": 100.0, "is_open": False, "close_rate": 99.0, "close_rate_requested": 100.0}
        short = {**long_, "is_short": True}
        worse = forward.execution_quality([long_], [])
        better = forward.execution_quality([short], [])
        keys = [k for k, v in worse.items() if isinstance(v, float) and "slip" in k]
        self.assertTrue(keys)
        for k in keys:
            self.assertAlmostEqual(worse[k], -better[k], msg=k)


class ShortTradeArithmeticTests(unittest.TestCase):
    def test_scoreboard_excursions_and_equity_treat_a_short_as_a_short(self) -> None:
        import pandas as pd
        from lab import returns, tradereview
        short = {"open_date": "2024-01-01 01:00:00+00:00", "close_date": "2024-01-01 03:00:00+00:00", "open_rate": 100.0,
                 "close_rate": 90.0, "min_rate": 88.0, "max_rate": 103.0, "is_short": True, "profit_ratio": 0.0985,
                 "funding_fees": 0.01}
        mae, mfe = tradereview.excursions(short)
        self.assertAlmostEqual(mae, -0.03)
        self.assertAlmostEqual(mfe, 0.12)
        long_ = {**short, "is_short": False}
        self.assertAlmostEqual(tradereview.excursions(long_)[0], -0.12)
        hourly = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=6, freq="1h", tz="UTC"),
                               "close": [100.0, 100.0, 95.0, 90.0, 90.0, 90.0]})
        curve = returns.equity_curve([short], hourly, exposure=0.5, fee_per_side=0.001)
        self.assertAlmostEqual(curve.iloc[-1], 1.0 + 0.5 * 0.0985)          # exits at exactly 1 + w * profit_ratio
        self.assertGreater(curve.iloc[2], 1.0)                              # marked up while the price falls
        spot = {k: v for k, v in long_.items() if k not in ("is_short", "funding_fees")}
        spot["profit_ratio"] = 90.0 / 100.0 * 0.999 / 1.001 - 1.0
        self.assertAlmostEqual(returns.equity_curve([spot], hourly, exposure=0.5, fee_per_side=0.001).iloc[-1],
                               1.0 + 0.5 * spot["profit_ratio"])
