"""Data-quality checks for the daily informative timeframe.

A daily candle used as an informative series must be (a) aligned to 00:00 UTC, (b) unique and ordered,
(c) CLOSED at the moment it is used, and (d) consistent with the 1h candles it summarises. Check (d) catches
exchange-side timezone shifts and incomplete days: open = first 1h open, high = max 1h high, low = min 1h low,
close = last 1h close, for every day with all 24 hourly candles present.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load(path: Path) -> pd.DataFrame:
    frame = pd.read_feather(path)
    frame["date"] = pd.to_datetime(frame["date"], utc=True)
    return frame.sort_values("date").reset_index(drop=True)


def check_daily(daily: pd.DataFrame, *, as_of: pd.Timestamp) -> list[str]:
    """Problems with a daily frame; empty list = fine. `as_of` is the moment the data is used (UTC)."""
    problems: list[str] = []
    dates = daily["date"]
    if dates.dt.tz is None:
        problems.append("dates are not timezone-aware (UTC expected)")
        return problems
    off_midnight = int(((dates.dt.hour != 0) | (dates.dt.minute != 0)).sum())
    if off_midnight:
        problems.append(f"{off_midnight} daily candle(s) not at 00:00 UTC")
    if dates.duplicated().any():
        problems.append("duplicated daily timestamps")
    if not dates.is_monotonic_increasing:
        problems.append("daily timestamps are not ordered")
    incomplete = daily[dates + pd.Timedelta(days=1) > as_of]
    if len(incomplete):
        problems.append(f"{len(incomplete)} daily candle(s) not closed at {as_of}: {list(incomplete['date'].dt.strftime('%Y-%m-%d'))}")
    for column in ("open", "high", "low", "close"):
        if daily[column].isna().any():
            problems.append(f"NaN in {column}")
    return problems


def compare_with_hourly(daily: pd.DataFrame, hourly: pd.DataFrame, *, tolerance: float = 1e-9) -> dict:
    """Days with all 24 hourly candles whose daily OHLC differs from the hourly aggregate."""
    h = hourly.copy()
    h["day"] = h["date"].dt.floor("D")
    grouped = h.groupby("day").agg(
        n=("close", "size"), open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last")
    )
    full = grouped[grouped["n"] == 24]
    merged = full.merge(daily.set_index("date")[["open", "high", "low", "close"]], left_index=True, right_index=True,
                        suffixes=("", "_d"), how="inner")
    mismatches = {}
    for column in ("open", "high", "low", "close"):
        rel = (merged[column] - merged[f"{column}_d"]).abs() / merged[f"{column}_d"].abs().clip(lower=1e-12)
        mismatches[column] = int((rel > tolerance).sum())
    return {"days_compared": int(len(merged)), "mismatches": mismatches}
