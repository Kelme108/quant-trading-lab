"""P-008 LargeOpeningMoveReversal - fade a large opening move for one hour (US500, USTEC; 5-minute bars,
New York regular session only).

Rule, in words:
- prev_close = close of the last bar of the previous session. Signal bar = the bar with bar_in_day == 2 (it closes
  15 minutes after the open); C is its close. Opening move M = C / prev_close - 1.
- Scale S = mean of |M| over the previous 20 sessions that have a valid M (today excluded; no trade until 20 are
  available).
- Skip the day when a CPI or NFP release is scheduled on it (b3.events.mark_events): the opening move is news there.
- ENTRY, only on the signal bar (so at most one entry per day; the market order fills at the open of the next
  bar, 15 minutes after the open): M >= +1.5*S and M >= +0.002 -> ENTER_SHORT; M <= -1.5*S and M <= -0.002 ->
  ENTER_LONG. Symmetric.
- STOP on every entry, on the price grid, away from the price: short = tick_ceil(C + 0.5*(C - prev_close)); long =
  tick_floor(C - 0.5*(prev_close - C)) (the opening move extends by another half of itself).
- EXITS: (1) gap fill: at the close of any bar after the entry, short and close <= prev_close, or long and
  close >= prev_close -> EXIT at the next bar open; (2) time: at the close of the bar with bar_in_day == 14 (75
  minutes after the open) -> EXIT at the next bar open (longest hold 60 minutes); (3) the stop; (4) the engine's
  flatten 5 minutes before the close (only matters on half days).
- Entry window is exactly minute 15 after the open (SessionRules: entry from open+15 min, until open+16 min,
  i.e. 374 minutes before the 16:00 close of the 390-minute session). Max entries per day = 1 is enforced by
  the rule itself (the signal exists on one bar only); BacktestConfig(max_entries_per_day=...) is not needed.

Lookbacks: 20 sessions for S, 1 session for prev_close. `warmup` = 1800 five-minute bars = 23 sessions of 78 bars.

Source: Fung, Mok & Lam (2000), Intraday price reversals for index futures in the US and Hong Kong, Journal of
Banking & Finance 24(7); Grant, Wolf & Yu (2005), Intraday price reversals in the US stock index futures market,
Journal of Banking & Finance 29(5). Proposal: research/proxies/proposals/P-008.json.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from b3.calendar import SessionRules
from b3.events import mark_events
from b3.markets import ProxyStrategy
from b3.strategy import ENTER_LONG, ENTER_SHORT, EXIT, HOLD, tick_ceil, tick_floor
from live.core.models import Signal

RULE_ID = "P-008"


class LargeOpeningMoveReversal(ProxyStrategy):
    name = "P-008_large_opening_move_reversal"
    timeframe_min = 5
    warmup = 1800         # 20 sessions of S + the previous session + today, at up to 78 five-minute bars each
    rules = SessionRules(entry_start_after_open_min=15, entry_end_before_close_min=374, flatten_before_close_min=5)
    params = {
        "signal_bar_in_day": 2,
        "signal_minutes_after_open": 15,
        "scale_lookback_sessions": 20,
        "threshold_mult": 1.5,
        "min_abs_move_frac": 0.002,
        "stop_extension_frac_of_move": 0.5,
        "time_exit_bar_in_day": 14,
        "max_hold_minutes": 60,
        "max_entries_per_day": 1,
        "flatten_before_close_min": 5,
    }

    def indicators(self, df):
        p = self.params
        df = mark_events(df, ["CPI", "NFP"], self.timeframe_min)
        order = list(dict.fromkeys(df["local_date"]))
        last = df.groupby("local_date")["close"].last()
        prev = {d: (last[order[i - 1]] if i > 0 else np.nan) for i, d in enumerate(order)}
        df["prev_close"] = df["local_date"].map(prev)
        at_signal = df["bar_in_day"] == p["signal_bar_in_day"]
        df["open_move"] = (df["close"] / df["prev_close"] - 1.0).where(at_signal)
        # |M| of each earlier session (valid ones only), in order; S = mean of the last 20 strictly before the day
        abs_move = df.loc[at_signal & df["open_move"].notna()].drop_duplicates("local_date")
        abs_move = dict(zip(abs_move["local_date"], abs_move["open_move"].abs()))
        n, history, scale = p["scale_lookback_sessions"], [], {}
        for d in order:
            scale[d] = float(np.mean(history[-n:])) if len(history) >= n else np.nan
            if d in abs_move:
                history.append(abs_move[d])
        df["move_scale"] = df["local_date"].map(scale)
        return df

    def decide(self, row, position):
        p = self.params
        if position is not None:
            if pd.isna(row.prev_close):
                return Signal(HOLD)
            if position.volume < 0 and row.close <= row.prev_close:
                return Signal(EXIT, reason="gap_filled")
            if position.volume > 0 and row.close >= row.prev_close:
                return Signal(EXIT, reason="gap_filled")
            if row.bar_in_day >= p["time_exit_bar_in_day"]:
                return Signal(EXIT, reason="time_exit")
            return Signal(HOLD)
        if row.bar_in_day != p["signal_bar_in_day"]:
            return Signal(HOLD)
        if row.CPI_today or row.NFP_today:
            return Signal(HOLD)
        if pd.isna(row.open_move) or pd.isna(row.move_scale) or pd.isna(row.prev_close):
            return Signal(HOLD)
        tick, m, s = self.market.tick_size, row.open_move, row.move_scale
        threshold, floor = p["threshold_mult"] * s, p["min_abs_move_frac"]
        ext = p["stop_extension_frac_of_move"]
        if m >= threshold and m >= floor:
            stop = tick_ceil(row.close + ext * (row.close - row.prev_close), tick)
            return Signal(ENTER_SHORT, stop_price=stop, reason="fade_large_up_open")
        if m <= -threshold and m <= -floor:
            stop = tick_floor(row.close - ext * (row.prev_close - row.close), tick)
            return Signal(ENTER_LONG, stop_price=stop, reason="fade_large_down_open")
        return Signal(HOLD)
