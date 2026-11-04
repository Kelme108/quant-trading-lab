"""Trades -> equity curve -> daily returns, for the statistics in lab/stats.py.

Freqtrade exports one row per closed trade. The Sharpe/DSR/PBO machinery needs a return SERIES, so the curve is
rebuilt here, mark-to-market on the hourly closes:

- A trade invests `exposure` of the account at its entry (the lab's fixed-exposure model); the rest stays in cash.
- Value of the position, relative to its cost: bars before the exit = close/open_rate/(1+f); exit bar =
  close_rate/open_rate * (1-f)/(1+f). f is the per-side effective cost of the scenario (lab/costs.py).
- Account equity during the trade = E0 * (1 - w + w * position value), E0 = equity before entry.

By construction the account equity after a trade equals E0 * (1 + w * profit_ratio) with the exported net
profit_ratio, so the curve compounds exactly like the backtest (tested). Trades must not overlap (the lab runs one
position per pair). Nothing is re-simulated: this only reads what Freqtrade exported.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _to_utc(value) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def equity_curve(trades: list[dict], hourly: pd.DataFrame, *, exposure: float = 1.0, fee_per_side: float = 0.0,
                 start=None, end=None) -> pd.Series:
    """Hourly account equity (starts at 1.0), indexed by the hourly candle open time."""
    frame = hourly.sort_values("date").reset_index(drop=True)
    dates = pd.DatetimeIndex(pd.to_datetime(frame["date"], utc=True))
    closes = frame["close"].to_numpy(dtype=float)
    equity = np.ones(len(frame))
    ordered = sorted(trades, key=lambda t: str(t["open_date"]))
    cursor, balance = 0, 1.0
    for trade in ordered:
        e = int(dates.searchsorted(_to_utc(trade["open_date"])))
        x = int(dates.searchsorted(_to_utc(trade["close_date"])))
        if e >= len(frame) or e < cursor:
            raise ValueError("trades overlap or fall outside the data")
        x = min(max(x, e), len(frame) - 1)
        equity[cursor:e] = balance
        open_rate, close_rate = float(trade["open_rate"]), float(trade["close_rate"])
        for i in range(e, x + 1):
            if i == x:
                value = close_rate / open_rate * (1.0 - fee_per_side) / (1.0 + fee_per_side)
            else:
                value = closes[i] / open_rate / (1.0 + fee_per_side)
            equity[i] = balance * (1.0 - exposure + exposure * value)
        balance = equity[x]
        cursor = x + 1
    equity[cursor:] = balance
    series = pd.Series(equity, index=dates)
    if start is not None:
        series = series[series.index >= _to_utc(start)]
    if end is not None:
        series = series[series.index <= _to_utc(end)]
    return series


def daily_returns(equity: pd.Series) -> pd.Series:
    """Daily (UTC) returns from an hourly equity series: last equity of each day; the first day is measured
    against the first value of the series."""
    daily = equity.groupby(equity.index.floor("D")).last()
    previous = daily.shift(1)
    previous.iloc[0] = equity.iloc[0]
    return daily / previous - 1.0


def buy_and_hold_equity(hourly: pd.DataFrame, *, start, end, fee_per_side: float = 0.0) -> pd.Series:
    """Equity of buying at the open of the first candle of the window and holding. One entry cost at the start and
    one exit cost applied on the last value, so the figure is comparable with a closed trade."""
    frame = hourly[(hourly["date"] >= _to_utc(start)) & (hourly["date"] <= _to_utc(end))].sort_values("date")
    first_open = float(frame["open"].iloc[0])
    values = frame["close"].to_numpy(dtype=float) / first_open / (1.0 + fee_per_side)
    values[-1] *= 1.0 - fee_per_side
    return pd.Series(values, index=pd.DatetimeIndex(pd.to_datetime(frame["date"], utc=True)))


def summarise(equity: pd.Series) -> dict:
    """Return, max relative drawdown (peak to trough on the hourly curve) and annualised daily Sharpe."""
    from lab import stats

    peak = equity.cummax()
    daily = daily_returns(equity)
    return {
        "return": float(equity.iloc[-1] / equity.iloc[0] - 1.0),
        "max_drawdown": float((1.0 - equity / peak).max()),
        "sharpe_annualised": stats.annualise(stats.sharpe(daily.to_numpy())),
        "days": int(len(daily)),
    }
