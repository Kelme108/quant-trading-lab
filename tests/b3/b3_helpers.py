"""Synthetic B3 sessions for the b3 tests. Nothing here is market data.

Sessions follow b3/config/sessions.json for WIN (09:00-18:25 Sao Paulo, valid from 2026-03-09):
113 five-minute bars per day. Prices move on the WIN tick grid (5 points).
"""

from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta, timezone

import pandas as pd

from b3.calendar import SP_TZ, B3SessionCalendar, SessionRules
from b3.strategy import ENTER_LONG, ENTER_SHORT, EXIT, HOLD, B3Strategy, tick_ceil, tick_floor
from live.core.models import Bar, Signal

UTC = timezone.utc
TF = 5
TICK = 5.0
WIN_DAYS = [date(2026, 11, 9), date(2026, 11, 10), date(2026, 11, 11), date(2026, 11, 12), date(2026, 11, 13)]


def session_times(days, open_=time(9, 0), close=time(18, 25), tf=TF) -> list[pd.Timestamp]:
    out = []
    for d in days:
        t = datetime.combine(d, open_, SP_TZ)
        end = datetime.combine(d, close, SP_TZ)
        while t + timedelta(minutes=tf) <= end:
            out.append(pd.Timestamp(t.astimezone(UTC)))
            t += timedelta(minutes=tf)
    return out


def random_walk_frame(days=WIN_DAYS, seed=7, start=172_000.0, max_ticks=8) -> pd.DataFrame:
    rng = random.Random(seed)
    times = session_times(days)
    rows, prev = [], start
    for t in times:
        o = prev
        c = o + TICK * rng.randint(-max_ticks, max_ticks)
        h = max(o, c) + TICK * rng.randint(0, 4)
        lo = min(o, c) - TICK * rng.randint(0, 4)
        rows.append((t, o, h, lo, c, float(rng.randint(500, 5000))))
        prev = c
    return pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])


def frame_from_closes(closes, days=WIN_DAYS, start=172_000.0, wick=TICK) -> pd.DataFrame:
    times = session_times(days)[:len(closes)]
    rows, prev = [], start
    for t, c in zip(times, closes):
        o = prev
        rows.append((t, o, max(o, c) + wick, min(o, c) - wick, c, 1000.0))
        prev = c
    return pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])


def to_bars(frame: pd.DataFrame) -> list[Bar]:
    return [Bar(r.time.to_pydatetime(), r.open, r.high, r.low, r.close, r.volume)
            for r in frame.itertuples(index=False)]


class ChannelBreakout(B3Strategy):
    """Test strategy (not a hypothesis): long above the 6-bar high, exit below the 4-bar mean."""

    name, root, timeframe_min, warmup = "test_channel", "WIN", TF, 10
    rules = SessionRules(entry_start_after_open_min=15, entry_end_before_close_min=30, flatten_before_close_min=10)
    allow_short = False

    def indicators(self, df):
        df["hi6"] = df["high"].shift(1).rolling(6).max()
        df["lo6"] = df["low"].shift(1).rolling(6).min()
        df["mean4"] = df["close"].rolling(4).mean()
        return df

    def decide(self, row, position):
        if pd.isna(row.hi6):
            return Signal(HOLD)
        if position is None:
            if row.close > row.hi6:     # stop: the 6-bar low, but never more than 6 ticks away
                return Signal(ENTER_LONG, stop_price=tick_floor(max(row.lo6, row.close - 6 * TICK), TICK), reason="up")
            if self.allow_short and row.close < row.lo6:
                return Signal(ENTER_SHORT, stop_price=tick_ceil(min(row.hi6, row.close + 6 * TICK), TICK), reason="down")
            return Signal(HOLD)
        if position.volume > 0 and row.close < row.mean4:
            return Signal(EXIT, reason="below mean")
        if position.volume < 0 and row.close > row.mean4:
            return Signal(EXIT, reason="above mean")
        return Signal(HOLD)


class ChannelBreakoutBothSides(ChannelBreakout):
    name = "test_channel_both"
    allow_short = True


def calendar(rules: SessionRules | None = None) -> B3SessionCalendar:
    return B3SessionCalendar("WIN", rules=rules or ChannelBreakout.rules)
