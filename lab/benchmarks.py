"""Cash and buy-and-hold benchmarks computed directly from OHLCV feather data.

These are simple, auditable references for comparison in the manifest and
the gates. They do not model fees, slippage, or order execution; they
describe what a passive holder would have experienced over the same window.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def _load_candles(feather_path: Path, start_utc: str, end_utc: str) -> pd.DataFrame:
    frame = pd.read_feather(feather_path)
    frame["date"] = pd.to_datetime(frame["date"], utc=True)
    start = pd.Timestamp(start_utc)
    end = pd.Timestamp(end_utc)
    window = frame[(frame["date"] >= start) & (frame["date"] <= end)].sort_values("date")
    if window.empty:
        raise ValueError(
            f"no candles found between {start_utc} and {end_utc} in {feather_path}"
        )
    return window.reset_index(drop=True)


def cash_benchmark(start_utc: str, end_utc: str) -> dict:
    """Holding cash: zero return, zero drawdown, by definition."""
    return {
        "name": "cash",
        "start_utc": start_utc,
        "end_utc": end_utc,
        "return_pct": 0.0,
        "max_drawdown_pct": 0.0,
    }


def buy_and_hold_benchmark(feather_path: Path, start_utc: str, end_utc: str) -> dict:
    """Buy at the first close in the window, hold, no rebalancing or costs."""
    window = _load_candles(feather_path, start_utc, end_utc)
    close = window["close"]

    entry_price = float(close.iloc[0])
    exit_price = float(close.iloc[-1])
    return_pct = (exit_price / entry_price - 1.0) * 100

    running_max = close.cummax()
    drawdown = (close - running_max) / running_max
    max_drawdown_pct = float(drawdown.min() * -100)  # positive number

    return {
        "name": "buy_and_hold",
        "start_utc": start_utc,
        "end_utc": end_utc,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "candle_count": int(len(window)),
        "return_pct": return_pct,
        "max_drawdown_pct": max_drawdown_pct,
    }


def compute_benchmarks(feather_path: Path, start_utc: str, end_utc: str) -> dict:
    """Both benchmarks for a split, keyed by name, ready to store in the registry."""
    return {
        "cash": cash_benchmark(start_utc, end_utc),
        "buy_and_hold": buy_and_hold_benchmark(feather_path, start_utc, end_utc),
    }
