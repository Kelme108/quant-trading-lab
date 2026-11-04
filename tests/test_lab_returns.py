import unittest

import numpy as np
import pandas as pd

from lab import returns


def hourly(n=200, start="2022-01-01", seed=2):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    open_ = np.concatenate([[100.0], close[:-1]])
    return pd.DataFrame({"date": pd.date_range(start, periods=n, freq="h", tz="UTC"), "open": open_, "close": close,
                         "high": np.maximum(open_, close), "low": np.minimum(open_, close)})


def trade(frame, e, x, fee):
    open_rate = float(frame["open"].iloc[e])
    close_rate = float(frame["close"].iloc[x])
    return {"open_date": frame["date"].iloc[e], "close_date": frame["date"].iloc[x], "open_rate": open_rate,
            "close_rate": close_rate, "profit_ratio": close_rate / open_rate * (1 - fee) / (1 + fee) - 1}


class EquityCurveTests(unittest.TestCase):
    def test_equity_compounds_like_the_exported_trades(self):
        frame = hourly()
        fee, w = 0.00175, 0.25
        trades = [trade(frame, 10, 30, fee), trade(frame, 50, 51, fee), trade(frame, 80, 150, fee)]
        curve = returns.equity_curve(trades, frame, exposure=w, fee_per_side=fee)
        expected = 1.0
        for t in trades:
            expected *= 1 + w * t["profit_ratio"]
        self.assertAlmostEqual(float(curve.iloc[-1]), expected, places=12)

    def test_flat_outside_trades_and_full_length(self):
        frame = hourly()
        curve = returns.equity_curve([trade(frame, 20, 40, 0.0)], frame)
        self.assertEqual(len(curve), len(frame))
        self.assertTrue((curve.iloc[:20] == 1.0).all())
        self.assertTrue((curve.iloc[41:] == curve.iloc[40]).all())

    def test_a_zero_move_trade_loses_exactly_the_round_trip_cost(self):
        frame = hourly(60)
        frame["close"] = 100.0
        frame["open"] = 100.0
        fee = 0.00175
        curve = returns.equity_curve([trade(frame, 5, 20, fee)], frame, fee_per_side=fee)
        self.assertAlmostEqual(float(curve.iloc[-1]), (1 - fee) / (1 + fee), places=12)

    def test_overlapping_trades_are_rejected(self):
        frame = hourly()
        with self.assertRaises(ValueError):
            returns.equity_curve([trade(frame, 10, 40, 0), trade(frame, 30, 60, 0)], frame)

    def test_daily_returns_chain_to_the_final_equity(self):
        frame = hourly(24 * 9)
        curve = returns.equity_curve([trade(frame, 30, 100, 0.001)], frame, exposure=0.5, fee_per_side=0.001)
        daily = returns.daily_returns(curve)
        self.assertAlmostEqual(float((1 + daily).prod()), float(curve.iloc[-1]), places=10)

    def test_buy_and_hold_charges_one_entry_and_one_exit(self):
        frame = hourly(48)
        eq = returns.buy_and_hold_equity(frame, start=frame["date"].iloc[0], end=frame["date"].iloc[-1], fee_per_side=0.002)
        expected = frame["close"].iloc[-1] / frame["open"].iloc[0] * (1 - 0.002) / (1 + 0.002)
        self.assertAlmostEqual(float(eq.iloc[-1]), float(expected), places=12)

    def test_summarise_drawdown_and_return(self):
        idx = pd.date_range("2022-01-01", periods=72, freq="h", tz="UTC")
        values = np.concatenate([np.linspace(1, 1.5, 24), np.linspace(1.5, 0.9, 24), np.linspace(0.9, 1.2, 24)])
        s = returns.summarise(pd.Series(values, index=idx))
        self.assertAlmostEqual(s["max_drawdown"], 1 - 0.9 / 1.5, places=9)
        self.assertAlmostEqual(s["return"], 0.2, places=9)


if __name__ == "__main__":
    unittest.main()
