"""Data checks for B3 bars (plan, F1.4). Measures problems; never repairs, fills or interpolates.

Checks: duplicates and order, OHLC consistency, non-positive prices, bars with zero volume, bars
outside the session table, missing bar slots inside the session, weekdays without bars (holidays or
gaps), bars on official holidays, bar-to-bar jumps (roll artifacts in a broker's continuous series),
and the local time of each day's first bar across Brazil's DST changes (a test of the assumed server
time zone).
"""

from __future__ import annotations

from collections import Counter
from datetime import timedelta

import pandas as pd

from b3.calendar import SP_TZ, B3SessionCalendar, UnknownCalendarYear, UnknownSession, infer_closed_weekdays


def check_bars(df: pd.DataFrame, timeframe_min: int, calendar: B3SessionCalendar | None = None,
               jump_pct: float = 3.0) -> dict:
    rep: dict = {"bars": len(df)}
    if df.empty:
        return rep
    t = df["time"]
    rep["first"], rep["last"] = str(t.iloc[0]), str(t.iloc[-1])
    rep["duplicated_times"] = int(t.duplicated().sum())
    rep["not_sorted"] = bool(not t.is_monotonic_increasing)
    bad = (df["low"] > df[["open", "close"]].min(axis=1)) | (df["high"] < df[["open", "close"]].max(axis=1)) \
        | (df["low"] > df["high"])
    rep["ohlc_inconsistent"] = int(bad.sum())
    rep["non_positive_price"] = int((df[["open", "high", "low", "close"]] <= 0).any(axis=1).sum())
    rep["zero_volume"] = int((df["volume"] <= 0).sum())
    rep["volume_all_zero"] = bool((df["volume"] <= 0).all())

    ret = df["close"].pct_change().abs() * 100
    jumps = df.loc[ret > jump_pct, ["time", "close"]]
    rep["jumps_over_pct"] = jump_pct
    rep["jumps"] = [(str(a), float(b)) for a, b in zip(jumps["time"], jumps["close"])][:50]

    local = t.dt.tz_convert(SP_TZ)
    days = local.dt.date
    first_times = local.groupby(days).min().dt.strftime("%H:%M")
    rep["first_bar_local_time"] = dict(Counter(first_times).most_common(8))
    rep["weekdays_without_bars"] = [str(d) for d in infer_closed_weekdays(set(days), days.iloc[0], days.iloc[-1])]

    if calendar is not None:
        outside = missing = 0
        on_holiday, unknown = set(), set()
        tf = timedelta(minutes=timeframe_min)
        for d, grp in local.groupby(days):
            try:
                s = calendar.session(d)
            except (UnknownCalendarYear, UnknownSession):
                unknown.add(d.year if hasattr(d, "year") else d)
                continue
            if s is None:
                on_holiday.add(str(d))
                continue
            closes = grp + tf
            outside += int(((grp < s.open - timedelta(minutes=5)) | (closes > s.close)).sum())
            expected = int((s.close - s.open) / tf)
            inside = int(((grp >= s.open) & (closes <= s.close)).sum())
            missing += max(0, expected - inside)
        rep["bars_outside_session"] = outside
        rep["missing_slots_inside_session"] = missing
        rep["bars_on_official_holidays"] = sorted(on_holiday)
        rep["years_without_calendar"] = sorted(unknown)
    return rep
