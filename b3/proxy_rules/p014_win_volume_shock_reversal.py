"""P-014 WinVolumeShockReversal - fade a 5-minute WIN bar whose volume and body are both abnormal for its time of
day (WIN only; 5-minute bars, B3 regular session in Sao Paulo time).

Rule, in words:
- Bar t has open O, high H, low L, close C, volume V (contracts); r = C / O - 1 (inside one bar). SLOT = minute_of_day of
  the bar open.
- BASELINES for bar t over the previous 20 sessions (today excluded) that have a bar in the same slot: VBAR = mean V,
  ABAR = mean |r|. No signal if fewer than 15 of those 20 sessions have the slot. The baselines span sessions and
  contract rolls: each term is one bar's volume or one bar's |r|, so no roll jump enters.
- WINDOW: the signal bar opens at or after 11:00 (minute_of_day >= 660) and has minutes_to_close >= 45 at its close
  (17:40 with an 18:25 close, 17:10 with a 17:55 close).
- DAY FILTER: no entries on days with a scheduled FOMC statement (b3.events.mark_events, kind FOMC).
- SIGNAL at the close of a window bar: V >= 2.0 * VBAR and |r| >= 1.5 * ABAR. LONG when C < O (a high-volume down bar):
  ENTER_LONG, filled at the open of the next bar. SHORT when C > O: ENTER_SHORT. A bar with C == O never signals.
- Signals are ignored while a position is open. After an exit only signal bars that close after the EXIT BAR count (the
  exit bar is the bar whose open is the exit fill for a retracement or time exit, and the bar in which the stop is hit
  for a stop): a signal bar must have a later index than the exit bar.
- STOP on every entry: D = min(max(1.0 * (H - L), 0.0015 * C), 0.006 * C) of the signal bar. Long stop =
  tick_floor(C - D), short stop = tick_ceil(C + D) (5-point tick).
- EXIT, first of: (a) retracement: at the close of any bar from the entry bar on with close >= O of the signal bar (long)
  or close <= O (short), exit at the next open; (b) time: at the open of the 6th bar after the entry bar (the entry bar
  is the bar whose open is the fill; 30 minutes), decided at the close of the bar 6 bars after the signal bar; (c) the
  stop (checked from the entry bar on, stop first when a bar both reaches the stop and retraces); (d) the engine's
  flatten 5 minutes before the close.
- MAX 4 ENTRIES PER DAY, enforced by the rule itself: `indicators` replays each session bar by bar (entry at the next
  open, stop hit when a bar from the entry bar on reaches it, retracement and time exits as above) and stops signalling
  after the 4th entry. BacktestConfig(max_entries_per_day=...) is not needed. The replay uses only bars up to the
  current one. (The backtester takes no decisions during the first `warmup` bars; a day inside that stretch can differ.)

SessionRules note: a fill happens at the close of the signal bar. `entry_start_after_open_min` = 5 is the first possible
fill (the rule itself enforces minute_of_day >= 660, so that a late-open day is not delayed further);
`entry_end_before_close_min` = 44 makes the engine's half-open entry phase [start, close - 44 min) accept a fill at
close - 45 min (the last window bar) and refuse a later one. `params` keeps the proposal's numbers.

Lookbacks: 1 bar for the signal, 20 sessions for VBAR and ABAR. `warmup` = 2500 five-minute bars = 22 sessions of up to
113 bars: the live window then holds today's whole session and the 20 sessions before it.

Source: Campbell, Grossman & Wang (1993), Trading Volume and Serial Correlation in Stock Returns, QJE 108(4);
Llorente, Michaely, Saar & Wang (2002), Dynamic Volume-Return Relation of Individual Stocks, RFS 15(4). Proposal:
research/b3/proposals/P-014.json.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.calendar import SessionRules
from b3.events import mark_events
from b3.markets import ProxyStrategy
from b3.strategy import ENTER_LONG, ENTER_SHORT, EXIT, HOLD, tick_ceil, tick_floor
from live.core.models import Signal

RULE_ID = "P-014"


class WinVolumeShockReversal(ProxyStrategy):
    name = "P-014_win_volume_shock_reversal"
    timeframe_min = 5
    warmup = 2500         # 20 earlier sessions + today at up to 113 five-minute bars each, plus margin
    rules = SessionRules(entry_start_after_open_min=5, entry_end_before_close_min=44, flatten_before_close_min=5)
    params = {
        "timeframe_min": 5,
        "baseline_sessions": 20,
        "min_baseline_sessions": 15,
        "volume_mult": 2.0,
        "abs_return_mult": 1.5,
        "window_start_minute_of_day": 660,
        "min_minutes_to_close_at_signal": 45,
        "stop_range_mult": 1.0,
        "stop_min_frac": 0.0015,
        "stop_max_frac": 0.006,
        "max_hold_bars": 6,
        "skip_fomc_days": 1,
        "max_entries_per_day": 4,
    }

    def _baselines(self, df):
        """VBAR and ABAR per row: mean over the previous `baseline_sessions` sessions (today excluded) with at least
        `min_baseline_sessions` of them holding the same slot."""
        p = self.params
        order = list(dict.fromkeys(df["local_date"]))
        sess = df["local_date"].map({d: i for i, d in enumerate(order)}).to_numpy(dtype=int)
        slot = df["minute_of_day"].to_numpy(dtype=int)
        absr = (df["close"].to_numpy(dtype=float) / df["open"].to_numpy(dtype=float) - 1.0)
        cell = pd.DataFrame({"s": sess, "slot": slot, "v": df["volume"].to_numpy(dtype=float), "a": np.abs(absr)})
        grouped = cell.groupby(["s", "slot"])
        out = []
        for col in ("v", "a"):
            mat = grouped[col].last().unstack().reindex(range(len(order)))
            base = mat.shift(1).rolling(p["baseline_sessions"], min_periods=p["min_baseline_sessions"]).mean()
            out.append(base.to_numpy(dtype=float)[sess, base.columns.get_indexer(slot)])
        return out[0], out[1]

    def indicators(self, df):
        p = self.params
        tick = self.market.tick_size
        df = mark_events(df, ["FOMC"], self.timeframe_min)
        vbar, abar = self._baselines(df)
        df["vbar"] = vbar
        df["abar"] = abar

        n = len(df)
        day = df["local_date"].to_numpy()
        minute = df["minute_of_day"].to_numpy()
        mtc = df["minutes_to_close"].to_numpy(dtype=float)
        open_ = df["open"].to_numpy(dtype=float)
        high = df["high"].to_numpy(dtype=float)
        low = df["low"].to_numpy(dtype=float)
        close = df["close"].to_numpy(dtype=float)
        volume = df["volume"].to_numpy(dtype=float)
        fomc = df["FOMC_today"].to_numpy(dtype=bool) if p["skip_fomc_days"] else np.zeros(n, dtype=bool)
        win_start, min_mtc = p["window_start_minute_of_day"], p["min_minutes_to_close_at_signal"]
        max_entries, max_hold = p["max_entries_per_day"], p["max_hold_bars"]

        side = np.zeros(n, dtype=int)
        stop = np.full(n, np.nan)
        exit_code = np.zeros(n, dtype=int)         # 1 = retracement exit decided here, 2 = time exit decided here

        start = 0
        while start < n:
            end = start + 1
            while end < n and day[end] == day[start]:
                end += 1
            in_pos, pos_stop, pos_bar, pos_open, entries, block = 0, math.nan, -1, math.nan, 0, -1
            for i in range(start, end):
                if in_pos != 0:
                    # the stop, checked from the entry bar on (the first bar after the signal bar), before the exits
                    if (in_pos > 0 and low[i] <= pos_stop) or (in_pos < 0 and high[i] >= pos_stop):
                        in_pos, block = 0, i
                        continue
                    back = close[i] >= pos_open if in_pos > 0 else close[i] <= pos_open
                    if back:
                        exit_code[i] = 1
                    elif i - pos_bar >= max_hold:
                        exit_code[i] = 2
                    if exit_code[i]:
                        in_pos, block = 0, i + 1       # the exit fills at the open of the next bar = the exit bar
                    continue
                if (i <= block or entries >= max_entries or fomc[i] or minute[i] < win_start
                        or not mtc[i] >= min_mtc - 1e-9):
                    continue
                vb, ab = vbar[i], abar[i]
                if math.isnan(vb) or math.isnan(ab) or close[i] == open_[i]:
                    continue
                move = abs(close[i] / open_[i] - 1.0)
                if not (volume[i] >= p["volume_mult"] * vb and move >= p["abs_return_mult"] * ab):
                    continue
                c = close[i]
                d = min(max(p["stop_range_mult"] * (high[i] - low[i]), p["stop_min_frac"] * c), p["stop_max_frac"] * c)
                if c < open_[i]:
                    side[i], stop[i] = 1, tick_floor(c - d, tick)
                else:
                    side[i], stop[i] = -1, tick_ceil(c + d, tick)
                in_pos, pos_stop, pos_bar, pos_open, entries = int(side[i]), stop[i], i, open_[i], entries + 1
            start = end

        df["vs_side"] = side
        df["vs_stop"] = stop
        df["vs_exit"] = exit_code
        return df

    def decide(self, row, position):
        if position is not None:
            if row.vs_exit == 1:
                return Signal(EXIT, reason="retracement")
            if row.vs_exit == 2:
                return Signal(EXIT, reason="time_exit_30min")
            return Signal(HOLD)
        if row.vs_side > 0:
            return Signal(ENTER_LONG, stop_price=float(row.vs_stop), reason="fade_high_volume_down_bar")
        if row.vs_side < 0:
            return Signal(ENTER_SHORT, stop_price=float(row.vs_stop), reason="fade_high_volume_up_bar")
        return Signal(HOLD)
