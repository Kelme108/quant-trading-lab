"""Scheduled US macro events (FOMC statement, CPI, payrolls) from b3/config/events_us.json, whose dates come
from federalreserve.gov and bls.gov (sources inside the file). Only SCHEDULED releases: their date and time are
public well in advance, so a rule may use them on the day without looking ahead.

    event_times("FOMC")            -> UTC timestamps of every scheduled FOMC statement
    mark_events(bars, ["CPI"])     -> per bar: minutes since today's CPI release (NaN if none today / not yet)
"""

from __future__ import annotations

import json
from datetime import datetime, time
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

PATH = Path(__file__).resolve().parent / "config" / "events_us.json"
KINDS = ("FOMC", "CPI", "NFP")


@lru_cache(maxsize=None)
def _load(path: str = str(PATH)) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def event_times(kind: str, path: Path = PATH) -> pd.DatetimeIndex:
    cfg = _load(str(path))
    if kind not in cfg["events"]:
        raise ValueError(f"unknown event {kind!r}; expected one of {sorted(cfg['events'])}")
    ev, tz = cfg["events"][kind], ZoneInfo(cfg["time_zone"])
    hh, mm = map(int, ev["time_local"].split(":"))
    stamps = [datetime.combine(datetime.fromisoformat(d).date(), time(hh, mm), tz) for d in ev["dates"]]
    return pd.DatetimeIndex(pd.to_datetime(stamps, utc=True))


def mark_events(bars: pd.DataFrame, kinds, timeframe_min: int, path: Path = PATH) -> pd.DataFrame:
    """Adds, for every kind, `<kind>_today` (an event of that kind is scheduled on the bar's New York date) and
    `<kind>_min_since` (minutes from the release to the CLOSE of the bar; NaN before the release or on other days).
    A bar that closes at or after the release time has already seen it."""
    out = bars.copy()
    close_t = pd.to_datetime(out["time"], utc=True) + pd.Timedelta(minutes=timeframe_min)
    ny_date = close_t.dt.tz_convert("America/New_York").dt.date
    for kind in kinds:
        times = event_times(kind, path)
        by_day = {t.tz_convert("America/New_York").date(): t for t in times}
        ev = ny_date.map(by_day)
        out[f"{kind}_today"] = ev.notna().to_numpy()
        since = (close_t - pd.to_datetime(ev, utc=True)).dt.total_seconds() / 60
        out[f"{kind}_min_since"] = since.where(since >= 0, np.nan).to_numpy()
    return out
