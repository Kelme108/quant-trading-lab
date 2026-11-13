import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

freqtrade = types.ModuleType("freqtrade")
strategy_module = types.ModuleType("freqtrade.strategy")
strategy_module.IStrategy = object
strategy_module.merge_informative_pair = lambda *a, **k: a[0]
freqtrade.strategy = strategy_module
sys.modules.setdefault("freqtrade", freqtrade)
sys.modules.setdefault("freqtrade.strategy", strategy_module)
talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib_abstract.SMA = lambda dataframe, timeperiod: dataframe["close"].rolling(timeperiod).mean()
talib_abstract.RSI = lambda dataframe, timeperiod: pd.Series(50.0, index=dataframe.index)
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[2]
NAME = "BrooksH2Pullback_H132_v1"


def load():
    path = ROOT / "user_data" / "strategies" / "_archive" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load()
Strategy = getattr(MODULE, NAME)

START = pd.Timestamp("2024-01-01 00:00", tz="UTC")
P_EPOCH = int((START + pd.Timedelta(minutes=15 * 50)).timestamp())


def dates(n):
    return pd.date_range(START, periods=n, freq="15min")


def random_frame(n=900, seed=5):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.003, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.003, n))
    volume = rng.lognormal(3, 0.8, n)
    return pd.DataFrame(
        {"date": dates(n), "open": open_, "high": high, "low": low, "close": close, "volume": volume}
    )


def setbars(frame, bars):
    for index, (o, h, l, c) in bars.items():
        frame.loc[index, ["open", "high", "low", "close"]] = [o, h, l, c]
    return frame


def crafted(n=120, m=55):
    """Flat 100 base. P = bar 50 (high 105, new 24-bar high). H1 = bar 52 (high 104.9 > 104.8,
    < 105; L1 = 103.5). Second leg = bar 53 (low 102 < 103.5). H2 candidate m (default 55:
    close 103.1 > high(54) = 103, < 105). PL = 101 (bar 54). Depth 3.8%, entry-to-PL 2.04%."""
    frame = pd.DataFrame(
        {"date": dates(n), "open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0, "volume": 10.0}
    )
    setbars(
        frame,
        {
            50: (100.0, 105.0, 100.0, 104.5),
            51: (104.5, 104.8, 103.5, 104.0),
            52: (103.8, 104.9, 103.5, 104.6),
            53: (104.5, 104.6, 102.0, 102.5),
            54: (102.5, 103.0, 101.0, 101.5),
        },
    )
    for index in range(55, m):  # quiet bars: close below the previous high, no candidate
        setbars(frame, {index: (102.0, 102.5, 101.5, 102.0)})
    setbars(frame, {m: (101.5 if m == 55 else 102.0, 103.2, 101.2, 103.1)})
    for index in range(m + 1, n):
        setbars(frame, {index: (103.0, 103.5, 102.5, 103.0)})
    return frame


def run(frame):
    strategy = Strategy()
    out = strategy.populate_indicators(frame.copy(), {})
    return strategy.populate_exit_trend(strategy.populate_entry_trend(out, {}), {})


def entries(out):
    if "enter_long" not in out:
        return []
    return out.index[out["enter_long"].fillna(0) == 1].tolist()


class BrooksH2PullbackTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.10)
        self.assertTrue(Strategy.use_custom_stoploss)
        self.assertGreaterEqual(Strategy.startup_candle_count, 400)

    def test_signal_columns_are_binary(self):
        for frame in (random_frame(), crafted()):
            out = run(frame)
            for column in ("enter_long", "exit_long"):
                if column in out:
                    self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_indicator_recursions_match_talib_convention(self):
        values = np.arange(1.0, 31.0)
        ema = MODULE.ema_talib(values, 20)
        self.assertTrue(np.isnan(ema[:19]).all())
        self.assertAlmostEqual(ema[19], 10.5)
        self.assertAlmostEqual(ema[20], 10.5 + 2 / 21 * (21 - 10.5))
        high = np.full(40, 101.0)
        low = np.full(40, 99.0)
        close = np.full(40, 100.0)
        atr = MODULE.atr_talib(high, low, close, 14)
        self.assertTrue(np.isnan(atr[:14]).all())
        self.assertAlmostEqual(atr[14], 2.0)
        self.assertAlmostEqual(atr[39], 2.0)
        high[20] = 111.0  # TR 12 -> (2*13 + 12) / 14 at the next recursion step
        atr = MODULE.atr_talib(high, low, close, 14)
        self.assertAlmostEqual(atr[20], (2.0 * 13 + 12.0) / 14)

    def test_crafted_setup_gives_one_entry_with_tag(self):
        out = run(crafted())
        self.assertEqual(out["h2_cand"].sum(), 1)
        self.assertEqual(entries(out), [55])
        self.assertEqual(out.loc[55, "enter_tag"], f"h2pb:101.0:{P_EPOCH}")
        self.assertEqual(out.loc[55, "h2_pl"], 101.0)
        self.assertEqual(out.loc[55, "h2_phigh"], 105.0)
        self.assertTrue(out.loc[50, "h2_setup"])

    def test_zero_volume_gives_no_signal(self):
        self.assertEqual(entries(run(crafted().assign(volume=0.0))), [])
        frame = crafted()
        frame.loc[55, "volume"] = 0.0
        self.assertEqual(entries(run(frame)), [])
        self.assertEqual(entries(run(random_frame().assign(volume=0.0))), [])

    def test_undefined_startup_values_give_no_signal(self):
        out = run(random_frame())
        self.assertEqual([i for i in entries(out) if i < 24], [])
        self.assertTrue(out["ema20"].iloc[:19].isna().all())
        self.assertTrue(out["atrp"].iloc[:14].isna().all())
        self.assertTrue(out["h2_setup"].iloc[:24].eq(False).all())
        # NaN indicator values at the candidate bar block the entry
        strategy = Strategy()
        for column in ("atrp", "ema20", "h2_pl", "h2_phigh", "h2_ptime"):
            out = strategy.populate_indicators(crafted(), {})
            out.loc[55, column] = np.nan
            self.assertEqual(entries(strategy.populate_entry_trend(out, {})), [], column)
        out = strategy.populate_indicators(crafted(), {})
        out.loc[51, "ema20"] = np.nan  # EMA20(m-4) undefined
        self.assertEqual(entries(strategy.populate_entry_trend(out, {})), [])
        # a candle inside the first 24 bars cannot be a setup bar
        frame = crafted()
        setbars(frame, {10: (100.0, 130.0, 100.0, 125.0)})
        self.assertFalse(run(frame).loc[10, "h2_setup"])

    def test_filters(self):
        strategy = Strategy()
        base = strategy.populate_indicators(crafted(), {})
        self.assertEqual(entries(strategy.populate_entry_trend(base.copy(), {})), [55])
        # (3) EMA slope
        out = base.copy()
        out.loc[51, "ema20"] = out.loc[55, "ema20"]
        self.assertEqual(entries(strategy.populate_entry_trend(out, {})), [])
        out.loc[51, "ema20"] = out.loc[55, "ema20"] - 1e-9
        self.assertEqual(entries(strategy.populate_entry_trend(out, {})), [55])
        # (4) ATRp, 0.4% inclusive
        out = base.copy()
        out.loc[55, "atrp"] = 0.00399
        self.assertEqual(entries(strategy.populate_entry_trend(out, {})), [])
        out.loc[55, "atrp"] = 0.004
        self.assertEqual(entries(strategy.populate_entry_trend(out, {})), [55])
        # (1) depth >= 1% of high(P)
        out = base.copy()
        out.loc[55, "h2_pl"] = 105.0 * 0.9901
        self.assertEqual(entries(strategy.populate_entry_trend(out, {})), [])
        out.loc[55, "h2_pl"] = 105.0 * 0.989
        self.assertEqual(entries(strategy.populate_entry_trend(out, {})), [55])
        # (2) (close - PL) / close <= 2.5%
        out = base.copy()
        out.loc[55, "h2_pl"] = 103.1 * (1 - 0.0251)
        self.assertEqual(entries(strategy.populate_entry_trend(out, {})), [])
        out.loc[55, "h2_pl"] = 103.1 * (1 - 0.0249)
        self.assertEqual(entries(strategy.populate_entry_trend(out, {})), [55])

    def test_filters_on_price_paths(self):
        # shallow pullback (< 1% of 105): no entry
        frame = crafted()
        setbars(
            frame,
            {
                51: (104.5, 104.8, 104.5, 104.7),
                52: (104.6, 104.9, 104.6, 104.85),
                53: (104.7, 104.7, 104.2, 104.4),
                54: (104.4, 104.5, 104.3, 104.4),
                55: (104.4, 104.9, 104.4, 104.8),
            },
        )
        out = run(frame)
        self.assertTrue(out.loc[55, "h2_cand"])
        self.assertEqual(entries(out), [])
        # entry too far above the pullback low (2.79%): no entry
        frame = crafted()
        setbars(frame, {55: (101.5, 104.0, 101.2, 103.9)})
        out = run(frame)
        self.assertTrue(out.loc[55, "h2_cand"])
        self.assertEqual(entries(out), [])

    def test_no_second_leg_gives_no_candidate(self):
        frame = crafted()
        setbars(
            frame,
            {
                53: (104.6, 104.7, 103.6, 104.0),
                54: (103.8, 104.0, 103.6, 103.8),
                55: (103.8, 104.5, 103.7, 104.4),
            },
        )
        frame.loc[56:, ["open", "high", "low", "close"]] = [104.0, 104.1, 103.6, 104.0]
        out = run(frame)
        self.assertEqual(out["h2_cand"].sum(), 0)
        self.assertEqual(entries(out), [])

    def test_no_h1_gives_no_candidate(self):
        # highs fall after P, so no bar has high > previous high: no H1, no candidate
        frame = crafted()
        setbars(
            frame,
            {
                51: (104.5, 104.8, 103.5, 104.0),
                52: (104.0, 104.7, 103.5, 104.0),
                53: (104.0, 104.6, 102.0, 102.5),
                54: (102.5, 104.5, 101.0, 101.5),
                55: (101.5, 104.4, 101.2, 103.1),
            },
        )
        frame.loc[56:, ["open", "high", "low", "close"]] = [103.0, 103.1, 102.5, 103.0]
        out = run(frame)
        self.assertEqual(out["h2_cand"].sum(), 0)

    def test_h1_not_before_p_plus_2(self):
        # bar P+1 higher than P's neighbours does not count as H1; the first H1 bar is P+2
        frame = crafted()
        setbars(frame, {51: (104.5, 104.8, 103.5, 104.0), 52: (103.8, 104.7, 103.5, 104.6)})
        out = run(frame)
        # 52 has high 104.7 < 104.8 -> not H1; 53 (high 104.6) is not either; 55 has 103.2...
        self.assertEqual(out["h2_cand"].sum(), 0)

    def test_newer_setup_replaces_older(self):
        frame = crafted()
        setbars(frame, {55: (101.5, 105.5, 101.2, 105.2)})  # new 24-bar high at the candidate bar
        out = run(frame)
        self.assertTrue(out.loc[55, "h2_setup"])
        self.assertEqual(entries(out), [])

    def test_close_must_stay_below_setup_high(self):
        frame = crafted()
        setbars(frame, {55: (101.5, 105.0, 101.2, 105.0)})  # close == high(P): not < high(P)
        self.assertEqual(entries(run(frame)), [])

    def test_setup_life_is_24_bars(self):
        self.assertEqual(entries(run(crafted(m=74))), [74])  # m - P = 24
        self.assertEqual(entries(run(crafted(m=75))), [])  # m - P = 25: expired

    def test_candidate_is_the_only_shot(self):
        frame = crafted()
        # a second qualifying close after the first candidate must not trade
        setbars(frame, {56: (103.0, 103.2, 102.9, 103.0), 57: (103.0, 103.4, 102.9, 103.3)})
        self.assertEqual(entries(run(frame)), [55])
        # failed filters still use up the setup
        frame = crafted()
        setbars(frame, {55: (101.5, 104.0, 101.2, 103.9), 56: (103.0, 103.2, 102.9, 103.0),
                        57: (103.0, 103.4, 102.9, 103.3)})
        out = run(frame)
        self.assertEqual(out["h2_cand"].sum(), 1)
        self.assertEqual(entries(out), [])

    def test_stop_is_frozen_below_entry(self):
        strategy = Strategy()
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        # tight pullback low: distance floors at 0.8%
        trade = types.SimpleNamespace(open_rate=100.0, enter_tag="h2pb:99.9:1700000000")
        self.assertAlmostEqual(strategy.custom_stoploss("BTC/USDT", trade, now, 100.0, 0.0), -0.008)
        ratio = strategy.custom_stoploss("BTC/USDT", trade, now, 101.0, 0.01)
        self.assertAlmostEqual(101.0 * (1 + ratio), 99.2)
        # deep pullback: stop at PL
        trade = types.SimpleNamespace(open_rate=100.0, enter_tag="h2pb:97.0:1700000000")
        stop = 100.0 * (1 + strategy.custom_stoploss("BTC/USDT", trade, now, 100.0, 0.0))
        self.assertAlmostEqual(stop, 97.0)
        self.assertLess(strategy.custom_stoploss("BTC/USDT", trade, now, 90.0, -0.1), 0)
        trade = types.SimpleNamespace(open_rate=100.0, enter_tag=None)
        self.assertIsNone(strategy.custom_stoploss("BTC/USDT", trade, now, 100.0, 0.0))

    def test_take_profit_is_1p5_r(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, tzinfo=timezone.utc)
        soon = opened + timedelta(hours=1)
        # d = 0.02 -> target +3%
        trade = types.SimpleNamespace(open_rate=100.0, open_date_utc=opened, enter_tag="h2pb:98.0:1700000000")
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, soon, 102.9, 0.0299))
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, soon, 103.0, 0.03001), "take_profit_1p5R")
        # d floors at 0.008 -> target +1.2%
        trade = types.SimpleNamespace(open_rate=100.0, open_date_utc=opened, enter_tag="h2pb:99.9:1700000000")
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, soon, 101.1, 0.0119))
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, soon, 101.2, 0.012), "take_profit_1p5R")

    def test_time_exit_after_12_hours(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_rate=100.0, open_date_utc=opened, enter_tag="h2pb:98.0:1700000000")
        before = opened + timedelta(hours=11, minutes=45)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, before, 100.0, 0.0))
        at = opened + timedelta(hours=12)
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, at, 100.0, -0.005), "time_exit_12h")

    def test_rearm_blocks_setups_started_before_the_last_exit(self):
        strategy = Strategy()
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        setup_epoch = int(datetime(2024, 12, 31, 12, 0, tzinfo=timezone.utc).timestamp())
        tag = f"h2pb:98.0:{setup_epoch}"
        closed_before = types.SimpleNamespace(close_date_utc=datetime(2024, 12, 31, 11, 45, tzinfo=timezone.utc))
        closed_after = types.SimpleNamespace(close_date_utc=datetime(2024, 12, 31, 12, 15, tzinfo=timezone.utc))
        closed_at = types.SimpleNamespace(close_date_utc=datetime(2024, 12, 31, 12, 0, tzinfo=timezone.utc))
        persistence = types.ModuleType("freqtrade.persistence")
        state = {"trades": []}
        persistence.Trade = types.SimpleNamespace(get_trades_proxy=lambda **kw: state["trades"])
        previous = sys.modules.get("freqtrade.persistence")
        sys.modules["freqtrade.persistence"] = persistence
        try:
            args = ("BTC/USDT", "limit", 1.0, 100.0, "GTC", now, tag, "long")
            self.assertTrue(strategy.confirm_trade_entry(*args))
            state["trades"] = [closed_before]
            self.assertTrue(strategy.confirm_trade_entry(*args))
            state["trades"] = [closed_at]
            self.assertTrue(strategy.confirm_trade_entry(*args))  # P at the exit bar is allowed
            state["trades"] = [closed_before, closed_after]
            self.assertFalse(strategy.confirm_trade_entry(*args))
        finally:
            if previous is None:
                del sys.modules["freqtrade.persistence"]
            else:
                sys.modules["freqtrade.persistence"] = previous

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        columns = [
            "ema20", "atr14", "atrp", "h2_setup", "h2_cand", "h2_pl", "h2_phigh", "h2_ptime",
            "enter_long", "enter_tag",
        ]
        cases = [
            (random_frame(1500), 900),
            (crafted(), 50),
            (crafted(), 54),
            (crafted(), 55),
            (crafted(), 56),
            (crafted(m=74), 60),
        ]
        for frame, n in cases:
            short = run(frame.iloc[:n])
            long = run(frame)
            for column in columns:
                a = (short[column] if column in short else pd.Series(np.nan, index=short.index)).reset_index(drop=True)
                b = (long[column] if column in long else pd.Series(np.nan, index=long.index)).iloc[:n].reset_index(drop=True)
                pd.testing.assert_series_equal(a, b, check_dtype=False, check_names=False)

    def test_random_series_produces_some_candidates_without_lookahead(self):
        out = run(random_frame(3000, seed=11))
        self.assertGreater(int(out["h2_cand"].sum()), 0)


if __name__ == "__main__":
    unittest.main()
