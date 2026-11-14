"""P-011 RoundNumberRejectionFade - fade the first touch of a 50-point S&P level that the bar fails to close through
(US500; 5-minute bars, New York regular session only).

Rule, in words:
- LEVELS: every multiple of G = 50 index points (..., 4950, 5000, 5050, ...). b = 1.0 point touch tolerance. A bar
  TOUCHES level L if high >= L - b and low <= L + b.
- FRESH: L is fresh at bar t if no earlier bar of today's session (all bars from bar_in_day 0, including bars before
  the entry window and bars where a position was open) touched L. Each level is spent at its first touch of the day,
  traded or not.
- DAY FILTER: skip days with a scheduled FOMC statement (b3.events.mark_events kind FOMC).
- DECISION BARS: bars opening at minute_of_day 595 to 890 inclusive (09:55 to 14:50 New York); the order fills at the
  next bar's open, 10:00 to 14:55. No position may be open. Cp = close of the previous bar of the same session.
- SHORT (resistance rejection): a fresh L with Cp < L, high >= L - b, close < L and high < L * 1.0015 -> ENTER_SHORT,
  stop = tick_ceil(L * 1.0015).
- LONG (support rejection): a fresh L with Cp > L, low <= L + b, close > L and low > L * (1 - 0.0015) -> ENTER_LONG,
  stop = tick_floor(L * (1 - 0.0015)).
- If more than one level qualifies, the one nearest the close is used; if a long and a short both qualify on the same
  bar, no trade. A touch that closes through L, or that reaches the stop level, is not traded (the level is spent).
- EXIT: time exit at the open of the 12th bar after the entry bar (the entry bar is the bar whose open is the fill;
  hold 60 minutes: the EXIT is decided at the close of the bar 12 bars after the decision bar), the stop, or the
  engine's flatten 5 minutes before the close. No target, no re-entry on a spent level.
- MAX ENTRIES PER DAY = 2, enforced by the rule itself: `indicators` replays the day bar by bar (entry at the next
  open, stop hit when a bar from the entry bar on reaches the stop, time exit after 12 bars) and stops signalling after
  the second entry. BacktestConfig(max_entries_per_day=...) is not needed. The replay only uses bars up to the current
  one. (The backtester takes no decisions during the first `warmup` bars; a day inside that stretch can differ.)

Entry window note: the proposal lists `entry_end_before_close_min` = 65 (the last FILL at 14:55, 65 minutes before the
16:00 close) and, at the same time, decision bars up to the one opening at 14:50 inclusive (fill 14:55). The engine's
entry phase is half-open, [open + 30 min, close - N min), and is evaluated at the fill time, so N = 65 would veto the
14:50 bar; `rules` therefore uses N = 64 (phase open until 14:56) so that the stated decision bars 595..890 all fill.
`params` keeps the proposal's numbers (65 included). The decision-bar minutes are enforced by the rule itself.

Lookbacks: today's session bars (freshness) and the previous bar's close. `warmup` = 240 five-minute bars = three
78-bar sessions: the live window then always holds today's whole session.

Source: Osler (2003), Currency Orders and Exchange Rate Dynamics, Journal of Finance 58(5); Zhang, limit-order
clustering at round prices; Bourghelle & Cellier (EFMA 2007). Proposal: research/proxies/proposals/P-011.json.
"""

from __future__ import annotations

import math

import numpy as np

from b3.calendar import SessionRules
from b3.events import mark_events
from b3.markets import ProxyStrategy
from b3.strategy import ENTER_LONG, ENTER_SHORT, EXIT, HOLD, tick_ceil, tick_floor
from live.core.models import Signal

RULE_ID = "P-011"


class RoundNumberRejectionFade(ProxyStrategy):
    name = "P-011_round_number_rejection_fade"
    timeframe_min = 5
    warmup = 240          # three 78-bar sessions: today's whole session (freshness, replay) plus margin
    rules = SessionRules(entry_start_after_open_min=30, entry_end_before_close_min=64, flatten_before_close_min=5)
    params = {
        "level_grid_points": 50,
        "touch_tolerance_points": 1.0,
        "stop_beyond_level_frac": 0.0015,
        "first_decision_bar_open_minute": 595,
        "last_decision_bar_open_minute": 890,
        "entry_start_after_open_min": 30,
        "entry_end_before_close_min": 65,
        "hold_bars": 12,
        "max_hold_minutes": 60,
        "max_entries_per_day": 2,
        "skip_fomc_days": 1,
        "flatten_before_close_min": 5,
    }

    def indicators(self, df):
        p = self.params
        grid, tol, frac = float(p["level_grid_points"]), float(p["touch_tolerance_points"]), p["stop_beyond_level_frac"]
        first_min, last_min = p["first_decision_bar_open_minute"], p["last_decision_bar_open_minute"]
        hold_bars, max_entries = p["hold_bars"], p["max_entries_per_day"]
        tick = self.market.tick_size

        df = mark_events(df, ["FOMC"], self.timeframe_min)
        n = len(df)
        day = df["local_date"].to_numpy()
        minute = df["minute_of_day"].to_numpy()
        high = df["high"].to_numpy(dtype=float)
        low = df["low"].to_numpy(dtype=float)
        close = df["close"].to_numpy(dtype=float)
        prev_close = df.groupby("local_date")["close"].shift(1).to_numpy(dtype=float)
        fomc = df["FOMC_today"].to_numpy(dtype=bool)

        side = np.zeros(n, dtype=int)
        stop = np.full(n, np.nan)
        hold_exit = np.zeros(n, dtype=bool)

        start = 0
        while start < n:
            end = start + 1
            while end < n and day[end] == day[start]:
                end += 1
            touched = set()           # level indices (level = k * grid) touched by an earlier bar of this session
            in_pos, pos_stop, pos_bar, entries = 0, math.nan, -1, 0
            for i in range(start, end):
                h, lo, c, cp = high[i], low[i], close[i], prev_close[i]
                if in_pos != 0 and i > pos_bar:                      # stop, checked from the entry bar on
                    if (in_pos > 0 and lo <= pos_stop) or (in_pos < 0 and h >= pos_stop):
                        in_pos = 0
                k_lo = math.ceil((lo - tol) / grid - 1e-9)
                k_hi = math.floor((h + tol) / grid + 1e-9)
                fresh = [k for k in range(k_lo, k_hi + 1) if k not in touched]
                touched.update(range(k_lo, k_hi + 1))
                if in_pos != 0:
                    if i - pos_bar >= hold_bars:
                        hold_exit[i] = True
                        in_pos = 0
                    continue
                if (entries >= max_entries or fomc[i] or not (first_min <= minute[i] <= last_min)
                        or math.isnan(cp) or not fresh):
                    continue
                shorts, longs = [], []
                for k in fresh:
                    level = k * grid
                    if cp < level and c < level and h >= level - tol and h < level * (1 + frac):
                        shorts.append(level)
                    if cp > level and c > level and lo <= level + tol and lo > level * (1 - frac):
                        longs.append(level)
                if (shorts and longs) or not (shorts or longs):
                    continue
                if shorts:
                    level = min(shorts, key=lambda x: abs(x - c))
                    side[i], stop[i] = -1, tick_ceil(level * (1 + frac), tick)
                else:
                    level = min(longs, key=lambda x: abs(x - c))
                    side[i], stop[i] = 1, tick_floor(level * (1 - frac), tick)
                in_pos, pos_stop, pos_bar, entries = int(side[i]), stop[i], i, entries + 1
            start = end

        df["rn_side"] = side
        df["rn_stop"] = stop
        df["rn_hold_exit"] = hold_exit
        return df

    def decide(self, row, position):
        if position is not None:
            if row.rn_hold_exit:
                return Signal(EXIT, reason="time_exit_60min")
            return Signal(HOLD)
        if row.rn_side < 0:
            return Signal(ENTER_SHORT, stop_price=float(row.rn_stop), reason="resistance_rejection")
        if row.rn_side > 0:
            return Signal(ENTER_LONG, stop_price=float(row.rn_stop), reason="support_rejection")
        return Signal(HOLD)
