#!/usr/bin/env python3
"""Validate a Freqtrade OHLCV file without modifying it."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {"date", "open", "high", "low", "close", "volume"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(path: Path, timeframe: str, max_gap_hours: float | None = None) -> dict:
    """Validate an OHLCV file.

    `gaps` always counts every missing stretch. `max_gap_hours` is an optional
    tolerance for documented exchange outages: a gap whose MISSING time is at
    most that long does not make the file invalid, but is still counted in
    `gaps` and reported, never hidden. The default (None) keeps the strict
    rule that any gap makes the file invalid.
    """
    frame = pd.read_feather(path)
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")

    dates = pd.to_datetime(frame["date"], utc=True, errors="coerce")
    expected_delta = pd.Timedelta(timeframe)
    invalid_ohlc = (
        (frame["open"] <= 0)
        | (frame["high"] <= 0)
        | (frame["low"] <= 0)
        | (frame["close"] <= 0)
        | (frame["high"] < frame[["open", "close"]].max(axis=1))
        | (frame["low"] > frame[["open", "close"]].min(axis=1))
        | (frame["low"] > frame["high"])
    )
    invalid_volume = frame["volume"].isna() | (frame["volume"] < 0)
    deltas = dates.diff().dropna()
    gaps = int((deltas > expected_delta).sum())
    missing_time = (deltas - expected_delta)[deltas > expected_delta]
    tolerance = pd.Timedelta(hours=max_gap_hours) if max_gap_hours is not None else pd.Timedelta(0)
    gaps_over_tolerance = int((missing_time > tolerance).sum())
    largest_gap_missing_hours = (
        float(missing_time.max() / pd.Timedelta(hours=1)) if len(missing_time) else 0.0
    )
    duplicates = int(dates.duplicated().sum())
    non_monotonic = int((deltas <= pd.Timedelta(0)).sum())
    nan_cells = int(frame[list(REQUIRED_COLUMNS)].isna().sum().sum())

    result = {
        "path": str(path),
        "sha256": sha256_file(path),
        "rows": int(len(frame)),
        "columns": list(frame.columns),
        "first_candle_utc": dates.min().isoformat() if len(dates) else None,
        "last_candle_utc": dates.max().isoformat() if len(dates) else None,
        "timezone_normalized": True,
        "gaps": gaps,
        "gaps_over_tolerance": gaps_over_tolerance,
        "largest_gap_missing_hours": largest_gap_missing_hours,
        "max_gap_hours_tolerated": max_gap_hours if max_gap_hours is not None else 0,
        "duplicate_timestamps": duplicates,
        "non_monotonic_intervals": non_monotonic,
        "nan_cells_required_columns": nan_cells,
        "invalid_ohlc_rows": int(invalid_ohlc.fillna(True).sum()),
        "invalid_volume_rows": int(invalid_volume.fillna(True).sum()),
        "timeframe": timeframe,
    }
    result["valid"] = all(
        result[key] == 0
        for key in (
            "gaps_over_tolerance",
            "duplicate_timestamps",
            "non_monotonic_intervals",
            "nan_cells_required_columns",
            "invalid_ohlc_rows",
            "invalid_volume_rows",
        )
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument(
        "--max-gap-hours",
        type=float,
        default=None,
        help="tolerate gaps with at most this many missing hours (default: none)",
    )
    args = parser.parse_args()
    result = validate(args.path, args.timeframe, args.max_gap_hours)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
