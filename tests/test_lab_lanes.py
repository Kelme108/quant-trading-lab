"""The futures dry-run lane (owner decision D2, docs/faixa-futuros.md): 1x, isolated, short allowed, spot untouched."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lab import costs, lanes, runner, strategy_check

ROOT = Path(__file__).parents[1]

STRATEGY = '''from freqtrade.strategy import IStrategy


class Thing_H900_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    startup_candle_count = 400
    can_short = {can_short}
    stoploss = -0.03

    def populate_indicators(self, dataframe, metadata):
        return dataframe

    def populate_entry_trend(self, dataframe, metadata):
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe, metadata):
        return dataframe
{extra}'''


def check(lane: str, can_short: str = "True", extra: str = "") -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "Thing_H900_v1.py"
        path.write_text(STRATEGY.format(can_short=can_short, extra=extra), encoding="utf-8")
        return strategy_check.check_strategy_source(path, lane=lane)


class LaneTests(unittest.TestCase):
    def test_pair_names_and_data_files(self) -> None:
        self.assertEqual(lanes.SPOT.pair("BTC/USDT"), "BTC/USDT")
        self.assertEqual(lanes.FUTURES.pair("BTC/USDT"), "BTC/USDT:USDT")
        self.assertEqual(lanes.FUTURES.pair("BTC/USDT:USDT"), "BTC/USDT:USDT")
        self.assertEqual(lanes.FUTURES.feather_path("ETH/USDT", "15m", Path("R")),
                         Path("R/user_data/data/binance/futures/ETH_USDT_USDT-15m-futures.feather"))
        self.assertEqual(lanes.SPOT.feather_path("ETH/USDT", "1h", Path("R")), Path("R/user_data/data/binance/ETH_USDT-1h.feather"))
        with self.assertRaises(ValueError):
            lanes.get("margin")

    def test_futures_costs_change_only_the_fee(self) -> None:
        for name in costs.REQUIRED_SCENARIO_NAMES:
            spot, fut = costs.lane_scenario(name, "spot"), costs.lane_scenario(name, "futures")
            self.assertIs(spot, costs.SCENARIOS[name])
            self.assertEqual(fut.fee_per_side, 0.00045)
            self.assertEqual((fut.slippage_per_side, fut.spread_total), (spot.slippage_per_side, spot.spread_total))
        trip = {s.name: 2 * s.effective_fee_per_side for s in costs.all_required_scenarios("futures")}
        self.assertAlmostEqual(trip["base"], 0.0024)
        self.assertAlmostEqual(trip["conservative"], 0.0039)
        self.assertEqual(costs.all_required_scenarios(), [costs.SCENARIOS[n] for n in costs.REQUIRED_SCENARIO_NAMES])

    def test_the_futures_config_is_dry_run_isolated_and_has_no_keys(self) -> None:
        cfg = json.loads((ROOT / "user_data" / "config.futures.dryrun.json").read_text(encoding="utf-8"))
        spot = json.loads((ROOT / "user_data" / "config.dryrun.json").read_text(encoding="utf-8"))
        self.assertIs(cfg["dry_run"], True)
        self.assertEqual((cfg["trading_mode"], cfg["margin_mode"]), ("futures", "isolated"))
        self.assertEqual((cfg["exchange"]["key"], cfg["exchange"]["secret"]), ("", ""))
        self.assertNotEqual(cfg["db_url"], spot["db_url"])
        self.assertTrue(all(p.endswith(":USDT") for p in cfg["exchange"]["pair_whitelist"]))
        self.assertFalse(cfg["api_server"]["enabled"])
        self.assertNotIn("leverage", json.dumps(cfg))

    def test_spot_strategies_still_may_not_short(self) -> None:
        problems = check("spot")
        self.assertTrue(any("can_short = False" in p for p in problems))
        self.assertTrue(any("'enter_short'" in p for p in problems))

    def test_a_futures_strategy_may_short_but_never_set_leverage(self) -> None:
        self.assertEqual(check("futures"), [])
        self.assertEqual(check("futures", can_short="False"), [])
        leverage = "\n    def leverage(self, pair, **kwargs):\n        return 3.0\n"
        self.assertIn("method 'leverage' is not allowed", check("futures", extra=leverage))
        self.assertTrue(any("True or False" in p for p in check("futures", can_short="1")))


class RunnerLaneTests(unittest.TestCase):
    def captured(self, call, **kwargs) -> list[str]:
        seen: list[str] = []

        def fake(args, cwd=None):
            seen.extend(args)
            return subprocess.CompletedProcess(args, returncode=1, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(runner, "run_compose", fake), \
                mock.patch.object(runner, "USER_DATA", Path(tmp) / "user_data"), \
                mock.patch.object(runner, "EXPERIMENTS_DIR", Path(tmp) / "experiments"):
            call(experiment_id="t", strategy="S", timerange="1-2", pair="BTC/USDT", **kwargs)
        return seen

    def test_every_freqtrade_call_uses_the_lane_config_and_pair(self) -> None:
        for call, extra in ((runner.run_backtest, {"fee": 0.001}), (runner.run_lookahead_analysis, {"fee": 0.001}),
                            (runner.run_recursive_analysis, {})):
            spot = self.captured(call, **extra)
            fut = self.captured(call, lane="futures", **extra)
            self.assertTrue(spot[spot.index("--config") + 1].endswith("/config.dryrun.json"), call.__name__)
            self.assertEqual(spot[spot.index("--pairs") + 1], "BTC/USDT")
            self.assertTrue(fut[fut.index("--config") + 1].endswith("/config.futures.dryrun.json"), call.__name__)
            self.assertEqual(fut[fut.index("--pairs") + 1], "BTC/USDT:USDT")


if __name__ == "__main__":
    unittest.main()
