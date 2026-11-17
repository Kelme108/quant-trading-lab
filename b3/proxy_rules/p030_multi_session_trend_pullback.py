"""P-030 MultiSessionTrendPullback - buy 30-minute dips in a 5-session up-trend, sell rallies in a down-trend
(WIN only; 5-minute bars, B3 regular session in Sao Paulo time).

Rule, in words (the proposal counts bars from 1 where it says "bar_in_day >= 6"; the engine's `bar_in_day` is 0-based and
the rule below needs today's bar t and today's bar t-6 to exist):
- Trend T (fixed for the day): the sum, over the 5 previous completed sessions, of ln(last close of the session / first
  open of the session). Only intraday session returns, never the overnight gap, so the unadjusted roll does not enter T.
  T == 0, or fewer than 5 previous sessions: no trade that day.
- Scale s (fixed for the day): the standard deviation (sample, ddof = 1: the proposal does not say; the pandas default) of
  the 5-minute close-to-close log returns inside the 5 previous sessions (pairs of bars of the same local_date only, so
  the first bar's gap is excluded; the returns of the 5 sessions are pooled), times sqrt(6). s <= 0 or not finite: no trade.
- Pullback R30 at the close of bar t: ln(close_t / close_(t-6)), both bars on today's local_date.
  LONG: T > 0 and R30 <= -1.0 s.  SHORT: T < 0 and R30 >= +1.0 s.  Never against the sign of T.
- Entry window: the signal bar closes at or after minute_of_day 600 (10:00) and minutes_to_close at its close >= 60.
- ENTRY (ENTER_LONG / ENTER_SHORT, fill at the open of bar t+1). Stop on every entry: entry price -/+ 1.5 s x entry price.
  The entry price is the open of bar t+1, which a signal cannot know: the stop is computed from Close(t), the last known
  price, and rounded away from it to the 5-point tick (tick_floor for a long, tick_ceil for a short). If the rounded stop
  is not strictly on the right side of Close(t), no entry.
- EXIT, first that occurs: (a) the stop (the engine checks it from the entry bar, the bar whose open is the fill, on);
  (b) time exit at the open of the 9th bar after entry (9 bars held = 45 minutes: decided at the close of signal bar + 9,
  filled at the next open); (c) at the first bar with minutes_to_close <= 15 (EXIT decided at its close, filled at the
  next open; the engine's own flatten, 5 minutes before the close, remains as a last guard).
- COOLDOWN of 2 bars after an exit: if the exit is stamped at the open of bar x (time exit / flatten: decided at bar x-1;
  stop: hit during bar x-1), bars x and x+1 cannot signal; the first bar that may signal is x+2, and the signal is
  evaluated from scratch on that bar (a setup that began during the cooldown still counts if it holds at its close).
- At most one position, MAX 4 ENTRIES PER DAY, enforced by the rule itself: `indicators` replays each session bar by bar
  (entry at the next open, stop hit when a bar from the entry bar on reaches it, exits as above) using only bars up to
  the current one, and stops signalling after the 4th entry. BacktestConfig(max_entries_per_day=...) is not needed. (The
  backtester takes no decisions during the first `warmup` bars; a session inside that stretch can differ from the replay.)

SessionRules note: a fill happens at the close of the signal bar. `entry_start_after_open_min` = 60 makes the first
possible fill 10:00 (the WIN session opens at 09:00); `entry_end_before_close_min` = 59 makes the half-open entry phase
[start, close - 59 min) accept a signal at close - 60 min (minutes_to_close = 60) and refuse a later one.

Lookbacks: 5 previous sessions plus today (at most 6 x 113 five-minute bars). `warmup` = 1000 bars: the live window
(warmup + 4 bars) then holds today's whole session and at least 7 earlier ones.

Source: Moskowitz, Ooi & Pedersen (2012), Time Series Momentum (JFE 104); Nagel (2012), Evaporating Liquidity (RFS 25);
Grossman & Miller (1988), Liquidity and Market Structure (NBER WP 2641). Proposal: research/b3/proposals/P-030.json.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.calendar import SessionRules
from b3.markets import ProxyStrategy
from b3.strategy import ENTER_LONG, ENTER_SHORT, EXIT, HOLD, tick_ceil, tick_floor
from live.core.models import Signal

RULE_ID = "P-030"
EPS = 1e-9


class MultiSessionTrendPullback(ProxyStrategy):
    name = "P-030_multi_session_trend_pullback"
    timeframe_min = 5
    warmup = 1000         # 5 previous sessions (at most 113 bars each) plus today's whole session, with margin
    rules = SessionRules(entry_start_after_open_min=60, entry_end_before_close_min=59, flatten_before_close_min=5)
    params = {
        "trend_sessions": 5,
        "scale_sessions": 5,
        "pullback_bars": 6,
        "scale_horizon_bars": 6,
        "z_entry": 1.0,
        "stop_scale_mult": 1.5,
        "hold_bars": 9,
        "entry_start_minute_of_day": 600,
        "min_minutes_to_close_entry": 60,
        "flatten_minutes_to_close": 15,
        "cooldown_bars": 2,
        "max_entries_per_day": 4,
    }

    def indicators(self, df):
        p = self.params
        tick = self.market.tick_size
        n = len(df)
        pb = p["pullback_bars"]

        day = df["local_date"].to_numpy()
        opn = df["open"].to_numpy(dtype=float)
        high = df["high"].to_numpy(dtype=float)
        low = df["low"].to_numpy(dtype=float)
        close = df["close"].to_numpy(dtype=float)
        mtc = df["minutes_to_close"].to_numpy(dtype=float)
        mod = df["minute_of_day"].to_numpy(dtype=float)

        starts = [0]
        for i in range(1, n):
            if day[i] != day[i - 1]:
                starts.append(i)
        bounds = list(zip(starts, starts[1:] + [n]))

        sess_ret, sess_rets = [], []
        with np.errstate(divide="ignore", invalid="ignore"):
            for s, e in bounds:
                sess_ret.append(math.log(close[e - 1] / opn[s]) if opn[s] > 0 and close[e - 1] > 0 else math.nan)
                sess_rets.append(np.log(close[s + 1:e] / close[s:e - 1]))     # same-day pairs only

        trend = np.full(n, np.nan)      # T, fixed per day
        scale = np.full(n, np.nan)      # s (30-minute scale), fixed per day
        r30 = np.full(n, np.nan)
        with np.errstate(divide="ignore", invalid="ignore"):
            for k, (s, e) in enumerate(bounds):
                ts, ss = p["trend_sessions"], p["scale_sessions"]
                if k >= ts:
                    trend[s:e] = float(np.sum(sess_ret[k - ts:k]))
                if k >= ss:
                    pooled = np.concatenate(sess_rets[k - ss:k])
                    if len(pooled) >= 2:
                        scale[s:e] = float(np.std(pooled, ddof=1)) * math.sqrt(p["scale_horizon_bars"])
                if e - s > pb:
                    r30[s + pb:e] = np.log(close[s + pb:e] / close[s:e - pb])

            z = p["z_entry"]
            ok = np.isfinite(trend) & np.isfinite(scale) & (scale > 0) & np.isfinite(r30)
            raw = np.zeros(n, dtype=int)                 # +1 long setup, -1 short setup (before window / state rules)
            raw[ok & (trend > 0) & (r30 <= -z * scale * (1.0 - EPS))] = 1
            raw[ok & (trend < 0) & (r30 >= z * scale * (1.0 - EPS))] = -1

        df["tm_trend"] = trend
        df["tm_scale"] = scale
        df["tm_r30"] = r30
        df["tm_raw"] = raw

        side = np.zeros(n, dtype=int)
        stop = np.full(n, np.nan)
        exit_flag = np.zeros(n, dtype=int)               # 1 time exit, 2 late-session exit

        hold, max_entries, cool = p["hold_bars"], p["max_entries_per_day"], p["cooldown_bars"]
        start_min, min_mtc = p["entry_start_minute_of_day"], p["min_minutes_to_close_entry"]
        flat_mtc, mult = p["flatten_minutes_to_close"], p["stop_scale_mult"]
        tf = self.timeframe_min

        for s, e in bounds:
            in_pos, pos_stop, pos_bar, entries, next_ok = 0, math.nan, -1, 0, s
            for i in range(s, e):
                if in_pos != 0:
                    if (in_pos > 0 and low[i] <= pos_stop) or (in_pos < 0 and high[i] >= pos_stop):
                        in_pos = 0                         # stopped in this bar; exit stamped at the next bar's open
                        next_ok = i + 1 + cool
                    elif mtc[i] <= flat_mtc + EPS:
                        exit_flag[i] = 2
                        in_pos = 0
                        next_ok = i + 1 + cool
                        continue
                    elif i - pos_bar >= hold:
                        exit_flag[i] = 1
                        in_pos = 0
                        next_ok = i + 1 + cool
                        continue
                    else:
                        continue
                if entries >= max_entries or i < next_ok or i - s < pb:
                    continue
                if mod[i] + tf < start_min or not mtc[i] >= min_mtc - EPS:
                    continue
                c = close[i]
                if raw[i] > 0:
                    st = tick_floor(c * (1.0 - mult * scale[i]), tick)
                    if st < c:
                        side[i], stop[i] = 1, st
                        in_pos, pos_stop, pos_bar, entries = 1, st, i, entries + 1
                elif raw[i] < 0:
                    st = tick_ceil(c * (1.0 + mult * scale[i]), tick)
                    if st > c:
                        side[i], stop[i] = -1, st
                        in_pos, pos_stop, pos_bar, entries = -1, st, i, entries + 1

        df["tm_side"] = side
        df["tm_stop"] = stop
        df["tm_exit"] = exit_flag
        return df

    def decide(self, row, position):
        if position is not None:
            if row.tm_exit == 1:
                return Signal(EXIT, reason="time_exit_9_bars")
            if row.tm_exit == 2:
                return Signal(EXIT, reason="late_session_exit")
            return Signal(HOLD)
        if row.tm_side > 0:
            return Signal(ENTER_LONG, stop_price=float(row.tm_stop), reason="trend_pullback_long")
        if row.tm_side < 0:
            return Signal(ENTER_SHORT, stop_price=float(row.tm_stop), reason="trend_pullback_short")
        return Signal(HOLD)
