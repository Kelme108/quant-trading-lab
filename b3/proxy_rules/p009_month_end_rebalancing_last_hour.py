"""P-009 MonthEndRebalancingLastHour - trade the last hour against the month-to-date move on the last 3 sessions
of each calendar month (US500; 5-minute bars, New York regular session only).

Rule, in words:
- TRADING DAYS: a session d qualifies when the number of trading days after d up to the end of d's calendar month
  (weekdays that the strategy calendar's is_trading_day accepts) is 0, 1 or 2 (the last 3 sessions of the month).
  Holidays are known in advance, so this uses no price.
- REFERENCE: ref = close of the last session bar of the last session of the previous calendar month. No trade until
  that month exists in the data.
- SIGNAL BAR: the bar that opens at 14:55 New York (minute_of_day 895) and closes at 15:00, 60 minutes before the
  close. C = its close. Month-to-date move R = C / ref - 1. If that bar does not exist (half day), no trade.
- FILTER: skip the day when an FOMC statement is scheduled on it (b3.events.mark_events).
- ENTRY, decided only on the signal bar (so at most one entry per day; the market order fills at the open of the
  next bar, 15:00): R >= +0.005 -> ENTER_SHORT; R <= -0.005 -> ENTER_LONG; |R| < 0.005 -> no trade.
- STOP on every entry: 0.4% of the price, away from it, on the price grid: long = tick_floor(C * 0.996), short =
  tick_ceil(C * 1.004) (C, the close of the signal bar, stands for the entry price, which is the next open).
- EXIT: time exit by the engine's flatten 5 minutes before the close (the 15:55 bar; longest hold 55 minutes) or the
  stop. No target, no re-entry after a stop.
- Entry window is exactly the minute after the signal bar closes (SessionRules: entry from open+330 min = 15:00 until
  15:01, i.e. 59 minutes before the 16:00 close). Max entries per day = 1 is enforced by the rule itself (the signal
  exists on one bar only); BacktestConfig(max_entries_per_day=...) is not needed.

Lookbacks: the previous month's last close only. `warmup` = 2400 five-minute bars = 30 sessions of 78 bars, which
covers the distance from the last session of the previous month to the 3rd-last session of the month (at most 22
sessions back) plus one full session.

Source: Harvey, Mazzoleni & Melone (2025), The Unintended Consequences of Rebalancing (SSRN 5122748). Proposal:
research/proxies/proposals/P-009.json.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from b3.calendar import SessionRules
from b3.events import mark_events
from b3.markets import ProxyStrategy
from b3.strategy import ENTER_LONG, ENTER_SHORT, HOLD, tick_ceil, tick_floor
from live.core.models import Signal

RULE_ID = "P-009"


class MonthEndRebalancingLastHour(ProxyStrategy):
    name = "P-009_month_end_rebalancing_last_hour"
    timeframe_min = 5
    warmup = 2400         # 30 sessions of 78 five-minute bars: previous month's last close is at most 22 sessions back
    rules = SessionRules(entry_start_after_open_min=330, entry_end_before_close_min=59, flatten_before_close_min=5)
    params = {
        "last_sessions_of_month": 3,
        "signal_bar_open_minute_of_day": 895,
        "entry_minutes_before_close": 60,
        "mtd_threshold_frac": 0.005,
        "stop_frac": 0.004,
        "flatten_before_close_min": 5,
        "max_hold_minutes": 55,
        "max_entries_per_day": 1,
        "skip_fomc_days": 1,
    }

    def _trading_days_left_in_month(self, d):
        """Trading days after d up to the end of d's calendar month, from the calendar only (no price)."""
        n, day = 0, d + timedelta(days=1)
        while day.month == d.month:
            if self.calendar.is_trading_day(day):
                n += 1
            day += timedelta(days=1)
        return n

    def indicators(self, df):
        df = mark_events(df, ["FOMC"], self.timeframe_min)
        order = list(dict.fromkeys(df["local_date"]))
        last = df.groupby("local_date")["close"].last()
        month_close = {}                                   # (year, month) -> close of that month's last session
        for d in order:
            month_close[(d.year, d.month)] = last[d]       # later sessions overwrite: ends on the month's last one
        ref, left = {}, {}
        for d in order:
            prev_month = (d.year, d.month - 1) if d.month > 1 else (d.year - 1, 12)
            ref[d] = month_close.get(prev_month, np.nan)
            left[d] = self._trading_days_left_in_month(d)
        df["ref_close"] = df["local_date"].map(ref).astype(float)
        df["month_end_zone"] = df["local_date"].map(left) < self.params["last_sessions_of_month"]
        at_signal = df["minute_of_day"] == self.params["signal_bar_open_minute_of_day"]
        df["mtd_move"] = (df["close"] / df["ref_close"] - 1.0).where(at_signal)
        return df

    def decide(self, row, position):
        p = self.params
        if position is not None or row.minute_of_day != p["signal_bar_open_minute_of_day"]:
            return Signal(HOLD)
        if not row.month_end_zone or row.FOMC_today or pd.isna(row.mtd_move):
            return Signal(HOLD)
        tick, f, r = self.market.tick_size, p["stop_frac"], row.mtd_move
        if r >= p["mtd_threshold_frac"]:
            return Signal(ENTER_SHORT, stop_price=tick_ceil(row.close * (1 + f), tick), reason="month_up_sell_flow")
        if r <= -p["mtd_threshold_frac"]:
            return Signal(ENTER_LONG, stop_price=tick_floor(row.close * (1 - f), tick), reason="month_down_buy_flow")
        return Signal(HOLD)
