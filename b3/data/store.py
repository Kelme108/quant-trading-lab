"""Read the files written by b3/data/mt5_history.py into the frame the backtester expects.

Bar time conversion: MT5 returns the bar's OPEN time on the trade SERVER's wall clock. For B3
brokers this is expected to be Sao Paulo time (with Brazil's daylight saving time until 2019), but
that is an assumption to confirm in F1.2 (b3/data/quality.py checks that the first bar of the day
sits at the same local time on both sides of a DST change). Pass `server_tz` (an IANA name) or a
fixed `server_utc_offset_hours`, never both.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

COLUMNS = ("time", "open", "high", "low", "close", "volume", "tick_volume", "spread")


def server_to_utc(server_epoch: pd.Series, server_tz: str | None = "America/Sao_Paulo",
                  server_utc_offset_hours: float | None = None) -> pd.Series:
    if (server_tz is None) == (server_utc_offset_hours is None):
        raise ValueError("give exactly one of server_tz or server_utc_offset_hours")
    wall = pd.to_datetime(server_epoch.astype("int64"), unit="s")
    if server_tz is not None:
        try:
            return wall.dt.tz_localize(server_tz, ambiguous="raise", nonexistent="raise").dt.tz_convert("UTC")
        except Exception as exc:  # pragma: no cover - message only
            raise ValueError(f"server times do not fit time zone {server_tz}: {exc}") from exc
    return (wall - pd.Timedelta(hours=server_utc_offset_hours)).dt.tz_localize("UTC")


def load_rates(path: str | Path, server_tz: str | None = "America/Sao_Paulo",
               server_utc_offset_hours: float | None = None) -> pd.DataFrame:
    """Bars with `time` (UTC, bar open), OHLC, `volume` (contracts traded: real_volume) and
    `tick_volume`. B3 bars carry real volume; a file where it is always zero is flagged by quality."""
    raw = pd.read_csv(path)
    out = pd.DataFrame({
        "time": server_to_utc(raw["time_server"], server_tz, server_utc_offset_hours),
        "open": raw["open"].astype(float), "high": raw["high"].astype(float),
        "low": raw["low"].astype(float), "close": raw["close"].astype(float),
        "volume": raw["real_volume"].astype(float), "tick_volume": raw["tick_volume"].astype(float),
        "spread": raw["spread"].astype(float),
    })
    return out.sort_values("time").reset_index(drop=True)


def read_manifest(path: str | Path) -> dict:
    p = Path(path)
    m = p if p.name.endswith(".manifest.json") else p.with_name(p.name.replace(".csv.gz", ".manifest.json"))
    return json.loads(m.read_text(encoding="utf-8"))
