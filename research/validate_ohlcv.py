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


def validate(path: Path, timeframe: str) -> dict:
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
            "gaps",
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
    args = parser.parse_args()
    result = validate(args.path, args.timeframe)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
