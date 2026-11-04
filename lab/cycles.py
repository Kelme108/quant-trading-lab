"""Market cycles and data-use labels for the comparative report.

Cycles are fixed calendar windows (no choice based on results): 2018 (bear), 2019 (recovery), 2020-21 (bull),
2022 (bear), 2023+ (recovery and the later bull, up to the cut-off). Every window ends BEFORE the prospective
holdout (lab/config/holdout.json), which no historical report may read.

Labels used for each period of data in the report:
- IS / OOS: the per-pair exploration and validation splits of lab/config/splits.json.
- semi-contaminated: the last 12 months before the cut-off (already seen by earlier experiments).
- prospective holdout: data after the cut-off; excluded from everything here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

CONFIG = Path(__file__).parent / "config" / "holdout.json"


def _utc(value: str) -> pd.Timestamp:
    return pd.Timestamp(value).tz_convert("UTC") if pd.Timestamp(value).tzinfo else pd.Timestamp(value, tz="UTC")


def holdout_config(path: Path = CONFIG) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def prospective_start(path: Path = CONFIG) -> pd.Timestamp:
    return _utc(holdout_config(path)["prospective_holdout"]["start_utc"])


def cycles(path: Path = CONFIG) -> dict[str, tuple[pd.Timestamp, pd.Timestamp]]:
    """name -> (start, end) inclusive, UTC. The last window ends one second before the prospective holdout."""
    cutoff = prospective_start(path)
    last_end = cutoff - pd.Timedelta(seconds=1)
    return {
        "2018": (_utc("2018-01-01"), _utc("2018-12-31 23:59:59")),
        "2019": (_utc("2019-01-01"), _utc("2019-12-31 23:59:59")),
        "2020-21": (_utc("2020-01-01"), _utc("2021-12-31 23:59:59")),
        "2022": (_utc("2022-01-01"), _utc("2022-12-31 23:59:59")),
        "2023+": (_utc("2023-01-01"), last_end),
    }


def semi_contaminated_window(path: Path = CONFIG) -> tuple[pd.Timestamp, pd.Timestamp]:
    window = holdout_config(path)["semi_contaminated_window"]
    return _utc(window["start_utc"]), _utc(window["end_utc"])


def labelled_periods(pair: str, splits: dict, path: Path = CONFIG) -> dict[str, tuple[pd.Timestamp, pd.Timestamp]]:
    """In-sample (exploration), out-of-sample (validation) and the semi-contaminated last 12 months of one pair."""
    pair_splits = splits["pairs"][pair]
    periods = {
        "IS (exploration)": (_utc(pair_splits["exploration"]["start_utc"]), _utc(pair_splits["exploration"]["end_utc"])),
        "OOS (validation)": (_utc(pair_splits["validation"]["start_utc"]), _utc(pair_splits["validation"]["end_utc"])),
    }
    periods["last 12m (semi-contaminated)"] = semi_contaminated_window(path)
    return periods


def assert_before_holdout(end: pd.Timestamp, path: Path = CONFIG) -> None:
    """Guard for any historical report: refuse a window that reaches the prospective holdout."""
    if pd.Timestamp(end).tz_convert("UTC") >= prospective_start(path):
        raise ValueError(f"window ends {end}, inside the prospective holdout (from {prospective_start(path)})")
