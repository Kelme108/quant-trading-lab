import importlib.util
import sys
import types
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parents[2]
STRATEGIES = ROOT / "user_data" / "strategies"
ARCHIVE = STRATEGIES / "_archive"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(STRATEGIES))

from lab import causality, strategy_check  # noqa: E402


def merge_informative_pair(dataframe, informative, timeframe, timeframe_inf, ffill=True):
    """Test double with the real visibility rule: the daily candle of day D is seen from the 1h row dated 23:00 of D."""
    inf = informative.copy()
    inf = inf.rename(columns={c: f"{c}_{timeframe_inf}" for c in inf.columns})
    inf["date_merge"] = inf["date_1d"] + pd.Timedelta(days=1) - pd.Timedelta(hours=1)
    merged = pd.merge_asof(dataframe.sort_values("date"), inf.drop(columns=["date_1d"]).sort_values("date_merge"),
                           left_on="date", right_on="date_merge")
    return merged.drop(columns=["date_merge"])


freqtrade = sys.modules.setdefault("freqtrade", types.ModuleType("freqtrade"))
strategy_module = sys.modules.setdefault("freqtrade.strategy", types.ModuleType("freqtrade.strategy"))
freqtrade.strategy = strategy_module
if not hasattr(strategy_module, "IStrategy"):
    strategy_module.IStrategy = object
strategy_module.merge_informative_pair = merge_informative_pair

NAME = "TimeSeriesMomentum_H015_v1"


def load():
    spec = importlib.util.spec_from_file_location(NAME, ARCHIVE / f"{NAME}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


module = load()


class FakeDP:
    def __init__(self, daily):
        self.daily = daily

    def get_pair_dataframe(self, pair, timeframe):
        return self.daily.copy()


def daily_frame(n=500, seed=5):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.02, n)))
    return pd.DataFrame({"date": pd.date_range("2020-01-01", periods=n, freq="D", tz="UTC"),
                         "open": close, "high": close * 1.01, "low": close * 0.99, "close": close, "volume": 1.0})


def hourly_from_daily(daily):
    dates = pd.date_range(daily["date"].iloc[0], daily["date"].iloc[-1] + pd.Timedelta(hours=23), freq="h", tz="UTC")
    closes = daily.set_index("date")["close"].reindex(dates.floor("D")).to_numpy()
    return pd.DataFrame({"date": dates, "open": closes, "high": closes, "low": closes, "close": closes, "volume": 1.0})


def build(daily, n_days=90, use_regime=False):
    module.N_DAYS, module.USE_REGIME = n_days, use_regime
    strategy = module.TimeSeriesMomentum_H015_v1.__new__(module.TimeSeriesMomentum_H015_v1)
    strategy.dp = FakeDP(daily)
    hourly = hourly_from_daily(daily)
    out = strategy.populate_indicators(hourly, {"pair": "BTC/USDT"})
    out["enter_long"], out["exit_long"] = 0, 0
    out = strategy.populate_entry_trend(out, {})
    out = strategy.populate_exit_trend(out, {})
    return out


class RuleTests(unittest.TestCase):
    def tearDown(self):
        module.N_DAYS, module.USE_REGIME = 90, False

    def test_momentum_positive_matches_definition_and_is_false_while_undefined(self):
        close = daily_frame()["close"]
        flag = module.momentum_positive(close, 60)
        self.assertTrue(flag.equals((close > close.shift(60)).fillna(False)))
        self.assertFalse(flag.iloc[:60].any())

    def test_equal_close_is_not_positive(self):
        close = pd.Series([1.0, 1.0, 1.0, 1.0])
        self.assertFalse(module.momentum_positive(close, 2).any())

    def test_entry_on_a_rising_market_and_exit_on_a_falling_one(self):
        rising = np.linspace(100, 300, 200)
        falling = np.linspace(300, 100, 200)
        close = np.concatenate([rising, falling])
        daily = daily_frame(400)
        daily["close"] = close
        out = build(daily, 30)
        self.assertGreater(out["enter_long"].sum(), 0)
        self.assertGreater(out["exit_long"].sum(), 0)
        first_entry = out.index[out["enter_long"] == 1][0]
        first_exit = out.index[(out["exit_long"] == 1) & (out.index > first_entry)][0]
        self.assertLess(first_entry, first_exit)
        self.assertEqual(int(out["enter_long"].iloc[: 30 * 24].sum()), 0)   # nothing before N days exist

    def test_regime_flag_gates_the_entry(self):
        daily = daily_frame(500)
        daily["close"] = np.concatenate([np.linspace(300, 100, 250), np.linspace(100, 160, 250)])
        free = build(daily, 30, use_regime=False)
        gated = build(daily, 30, use_regime=True)
        self.assertGreater(free["enter_long"].sum(), gated["enter_long"].sum())   # rising from below the SMA(200)

    def test_signal_uses_closed_days_only(self):
        daily = daily_frame(300)
        out = build(daily, 30)
        # the 1h row dated 22:00 of day D must not yet see day D
        row = out[out["date"] == pd.Timestamp("2020-08-01 22:00", tz="UTC")].iloc[0]
        expected_day = pd.Timestamp("2020-07-31", tz="UTC")
        mom = module.momentum_positive(daily.set_index("date")["close"], 30)
        self.assertEqual(int(row["mom_1d"]), int(mom[expected_day]))


class CausalityTests(unittest.TestCase):
    def test_function_prefix_invariance_and_future_corruption(self):
        frame = daily_frame()[["close"]]
        fn = lambda f: pd.DataFrame({"x": module.momentum_positive(f["close"], 60).astype(float)})  # noqa: E731
        self.assertEqual(causality.prefix_invariance(fn, frame, [100, 250, 400]), [])
        self.assertEqual(causality.future_corruption(fn, frame, 300), [])

    def test_whole_strategy_signals_do_not_change_when_the_future_is_cut_or_corrupted(self):
        daily = daily_frame(420)
        full = build(daily, 60).set_index("date")[["mom_1d", "enter_long", "exit_long"]].fillna(-1)
        for cut_day in (200, 300, 380):
            cut = daily["date"].iloc[cut_day]
            part = build(daily[daily["date"] < cut], 60).set_index("date")[["mom_1d", "enter_long", "exit_long"]].fillna(-1)
            self.assertTrue(part.equals(full.loc[part.index]), cut)
            broken = daily.copy()
            broken.loc[broken["date"] >= cut, ["open", "high", "low", "close"]] = 7.0e5
            after = build(broken, 60).set_index("date")[["mom_1d", "enter_long", "exit_long"]].fillna(-1)
            self.assertTrue(after[after.index < cut].equals(full[full.index < cut]), cut)


class ContractTests(unittest.TestCase):
    def test_passes_the_static_screen_with_no_warnings(self):
        path = ARCHIVE / f"{NAME}.py"
        self.assertEqual(strategy_check.check_strategy_source(path, expected_hypothesis_id="H-015"), [])
        self.assertEqual(strategy_check.warmup_warnings(path), [])

    def test_constants_and_contract(self):
        cls = module.TimeSeriesMomentum_H015_v1
        self.assertEqual((cls.timeframe, cls.can_short, cls.startup_candle_count), ("1h", False, 400))
        source = (ARCHIVE / f"{NAME}.py").read_text(encoding="utf-8")
        for forbidden in ("shift(-", "iloc[-1]", "custom_stake_amount", "adjust_trade_position", "leverage"):
            self.assertNotIn(forbidden, source)
        self.assertIn("merge_informative_pair", source)


if __name__ == "__main__":
    unittest.main()
