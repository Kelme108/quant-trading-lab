"""WIN and WDO history from the Clear demo export (b3/data/mt5_history.py --attach), for the research runner.

- `load_b3_bars(root, "5m")`: the continuous by-liquidity series without adjustment (WIN$N / WDO$N), in the
  backtester's format (time = UTC bar open; volume = contracts traded). Server clock = Sao Paulo.
- `roll_days(root)`: the days the $N series switches to the next contract, with the price gap (new - old,
  points, on the tick grid). Found where the ratio of the proportionally adjusted series (WIN$ / WDO$) to the
  unadjusted one changes on daily bars: 30 WIN rolls (every 2 months) and 60 WDO rolls (monthly) in
  2021-11..2026-11. The server keeps no expired contracts, so this is the only way to see them.
- `back_adjusted(bars, rolls)`: the $N series with every bar before a roll moved by that roll's gap (additive,
  on the tick grid), so indicators that span sessions see no artificial jump. Points and BRL per trade are the
  same as on raw prices (no position is held overnight); `adj_offset` gives raw = adjusted - adj_offset, and the
  runner measures returns against the RAW price.
- `history_calendar(root, bars, rules, skip)`: b3.calendar.B3SessionCalendar with the official holidays where
  b3/config/holidays.json has the year, closures inferred from the bars for the other years (HISTORY only:
  exchange holidays are announced in advance), and `skip` days (incomplete data) taking no session at all.
- `session_coverage(bars, cal, tf)` / `incomplete_days(...)`: share of the day's regular-session slots that hold
  a bar (b3/config/scope_b3.json min_session_coverage).
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from b3.calendar import SP_TZ, B3SessionCalendar, Holidays, SessionRules, UnknownCalendarYear
from b3.data.store import load_rates
from b3.instruments import INSTRUMENTS

DATA_DIR = Path(os.environ.get("MT5_B3_DATA") or
                Path(__file__).resolve().parents[1] / "user_data" / "data" / "b3" / "clear")
TIMEFRAMES = {"1m": "M1", "5m": "M5", "15m": "M15", "1d": "D1"}
ROLL_RATIO_CHANGE = 5e-4      # rounding noise of the adjusted series is < 1e-5; real rolls are > 2e-3


def _file(root: str, series: str, timeframe: str, data_dir: Path | None) -> Path:
    tf = TIMEFRAMES.get(timeframe, timeframe)
    return Path(data_dir or DATA_DIR) / f"{root}{series}-{tf}.csv.gz"


def load_b3_bars(root: str, timeframe: str = "5m", data_dir: Path | None = None) -> pd.DataFrame:
    """$N bars (unadjusted, by liquidity) of WIN or WDO, sorted, without duplicates."""
    df = load_rates(_file(root.upper(), "_S_N", timeframe, data_dir))
    df = df.drop_duplicates("time").sort_values("time").reset_index(drop=True)
    return df[["time", "open", "high", "low", "close", "volume", "tick_volume", "spread"]]


def roll_days(root: str, data_dir: Path | None = None) -> list[dict]:
    """[{"day": date, "gap_points": new - old}] from the daily $N and $ (proportionally adjusted) series."""
    root = root.upper()
    raw = load_rates(_file(root, "_S_N", "1d", data_dir))
    adj = load_rates(_file(root, "_S_", "1d", data_dir))
    m = raw.merge(adj, on="time", suffixes=("_n", "_a")).sort_values("time").reset_index(drop=True)
    factor = m["close_a"] / m["close_n"]
    tick = INSTRUMENTS[root].tick_size
    out = []
    for i in range(1, len(m)):
        change = factor.iloc[i - 1] / factor.iloc[i]          # = new / old at the roll
        if abs(change - 1.0) > ROLL_RATIO_CHANGE:
            old_close = float(m["close_n"].iloc[i - 1])
            gap = round(round(old_close * (change - 1.0) / tick) * tick, 10)
            out.append({"day": m["time"].iloc[i].tz_convert(SP_TZ).date(), "gap_points": gap})
    return out


def back_adjusted(bars: pd.DataFrame, rolls: list[dict]) -> pd.DataFrame:
    """Additive back-adjustment of the $N bars at the roll days; adds `adj_offset` (raw = price - adj_offset)."""
    out = bars.copy()
    day = out["time"].dt.tz_convert(SP_TZ).dt.date
    offset = pd.Series(0.0, index=out.index)
    for r in rolls:
        offset[day < r["day"]] += r["gap_points"]
    for c in ("open", "high", "low", "close"):
        out[c] = out[c] + offset
    out["adj_offset"] = offset
    return out


def roll_day_set(rolls: list[dict]) -> frozenset[date]:
    return frozenset(r["day"] for r in rolls)


# ---------------------------------------------------------------------------------------------
# Calendar for history
# ---------------------------------------------------------------------------------------------

class B3HistoryCalendar(B3SessionCalendar):
    """B3SessionCalendar where the `skip` days (incomplete data) have no session: no entry, no bar replayed."""

    def __init__(self, root: str, holidays: Holidays, rules: SessionRules, skip: frozenset[date] = frozenset()):
        super().__init__(root, holidays=holidays, rules=rules)
        self.skip = frozenset(skip)

    def is_trading_day(self, d: date) -> bool:
        return d not in self.skip and super().is_trading_day(d)


def holidays_for(bars: pd.DataFrame) -> Holidays:
    """Official years from holidays.json; every other year of the bars inferred (weekdays with no bar)."""
    official = Holidays.from_file()
    days = set(bars["time"].dt.tz_convert(SP_TZ).dt.date)
    first, last = min(days), max(days)
    years = [y for y in range(first.year, last.year + 1) if y not in official.known_years]
    closed, d = [], first
    while d <= last:
        if d.weekday() < 5 and d not in days:
            closed.append(d)
        d += timedelta(days=1)
    if not years:
        return official
    src = f"inferred from the Clear demo bars {first}..{last} (weekdays without bars; history only)"
    out = official.with_inferred(closed, years, src)
    # days before the first bar of the first inferred year would read as sessions: close them too
    pre = {date(first.year, 1, 1) + timedelta(days=i) for i in range((first - date(first.year, 1, 1)).days)}
    return Holidays(out.closed | frozenset(pre), out.special_open, out.known_years, out.sources)


def history_calendar(root: str, bars: pd.DataFrame, rules: SessionRules,
                     skip: frozenset[date] = frozenset()) -> B3HistoryCalendar:
    return B3HistoryCalendar(root.upper(), holidays_for(bars), rules, skip)


def session_only_b3(bars: pd.DataFrame, cal: B3SessionCalendar, timeframe_min: int) -> pd.DataFrame:
    """Bars that open and close inside the day's regular session (drops pre-open and after-hours bars)."""
    local = bars["time"].dt.tz_convert(SP_TZ)
    day = local.dt.date
    opens, closes = {}, {}
    for d in day.unique():
        try:
            s = cal.session(d)
        except UnknownCalendarYear:
            s = None
        opens[d] = pd.Timestamp(s.open) if s else pd.NaT
        closes[d] = pd.Timestamp(s.close) if s else pd.NaT
    o = pd.to_datetime(day.map(opens), utc=True)
    c = pd.to_datetime(day.map(closes), utc=True)
    t = bars["time"]
    keep = (t >= o) & (t + pd.Timedelta(minutes=timeframe_min) <= c)
    return bars[keep.fillna(False).to_numpy()].reset_index(drop=True)


def session_coverage(bars: pd.DataFrame, cal: B3SessionCalendar, timeframe_min: int) -> pd.Series:
    """Per local day with bars: bars inside the session / the session's slots (official or inferred hours).
    Use a calendar WITHOUT skip days (the skip set is what this measures)."""
    inside = session_only_b3(bars, cal, timeframe_min)
    local = inside["time"].dt.tz_convert(SP_TZ)
    counts = local.groupby(local.dt.date).size()
    out = {}
    for d, n in counts.items():
        s = cal.session(d)
        if s is None:
            out[d] = 0.0
            continue
        slots = (s.close - s.open).total_seconds() / 60 / timeframe_min
        out[d] = n / slots
    return pd.Series(out)


def incomplete_days(bars: pd.DataFrame, cal: B3SessionCalendar, timeframe_min: int,
                    min_coverage: float) -> frozenset[date]:
    cov = session_coverage(bars, cal, timeframe_min)
    return frozenset(cov.index[cov < min_coverage])
