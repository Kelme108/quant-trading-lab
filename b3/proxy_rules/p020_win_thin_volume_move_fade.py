"""P-020 WinThinVolumeMoveFade - fade a large 15-minute WIN move that came on no more than normal volume for its time
of day (WIN only; 5-minute bars, B3 regular session in Sao Paulo time).

Rule, in words:
- Bar t has open O, high H, low L, close C, volume V (contracts). MOVE: R_t = C_t / C_(t-3) - 1, with bars t-3..t all from
  today (bar_in_day >= 3), so no roll gap enters.
- SCALE S15 = mean |C_j / C_(j-3) - 1| over all bars j with bar_in_day >= 3 and minute_of_day >= 615 in the previous 20
  sessions (today excluded). No signal before 20 sessions exist.
- VOLUME BASELINE: SLOT = minute_of_day of the bar open. VBAR(slot) = mean V of that slot over the previous 20 sessions that
  have it (today excluded; at least 15 needed, else no signal). Relative volume rv_t = (V_(t-2) + V_(t-1) + V_t) /
  (VBAR(slot t-2) + VBAR(slot t-1) + VBAR(slot t)). S15 and VBAR span sessions and WIN rolls, but every term is inside one
  session or one bar.
- WINDOW: the signal bar t opens at minute_of_day >= 615 (10:15) and has minutes_to_close >= 45 at its close.
- SIGNAL at the close of bar t: |R_t| >= 1.5 * S15 AND rv_t <= 1.0, AND bar t-1 did not meet both conditions (first bar of
  the episode only; the two conditions are evaluated on every bar with the data, whatever the window, events or position).
  SHORT if R_t > 0 (a thin rally), LONG if R_t < 0 (a thin drop), by market order at the open of t+1, only if flat.
- EVENTS (b3.events.mark_events, kinds FOMC, CPI, NFP): no entry if any <kind>_min_since is in [0, 30] at t. On an FOMC day
  (FOMC_today) no entry from 15 minutes before the release on: the signal bar's close (= the fill time) at or after
  release - 15 minutes is blocked.
- STOP on every entry, fixed for the trade: D = min(max(|C_t - C_(t-3)|, 0.0020 * C_t), 0.0050 * C_t). Long stop =
  tick_floor(C_t - D), short stop = tick_ceil(C_t + D) (5-point tick).
- EXIT, first of: (a) target: M = (C_t + C_(t-3)) / 2, half the move. At the close of any bar from the entry bar on (the bar
  whose open is the fill) with close >= M (long) or close <= M (short), EXIT at the next open. (b) time: EXIT at the open of
  the 6th bar after the entry bar (30 minutes), decided at the close of the bar 6 bars after the signal bar. (c) the stop
  (checked from the entry bar on, first when one bar hits both a stop and the target). (d) the engine's flat-before-close.
- Signals while in a position are ignored. After an exit only a signal bar with a later index than the exit bar counts (the
  exit bar is the bar whose open is the exit fill, or the bar in which the stop was hit), and it must still be the first bar
  of its episode. One position.
- MAX 6 ENTRIES PER DAY, enforced by the rule itself: `indicators` replays each session bar by bar (entry at the next open,
  stop hit when a bar from the entry bar on reaches it, target and time exits as above) and stops signalling after the 6th
  entry. BacktestConfig(max_entries_per_day=...) is not needed. The replay uses only bars up to the current one. (The
  backtester takes no decisions during the first `warmup` bars; a day inside that stretch can differ.)

SessionRules note: a fill happens at the close of the signal bar. `entry_start_after_open_min` = 5 is the first possible
fill (the rule itself enforces minute_of_day >= 615); `entry_end_before_close_min` = 44 makes the engine's half-open entry
phase [start, close - 44 min) accept a fill at close - 45 min (the last window bar) and refuse a later one.

Lookbacks: 3 bars for R and rv, 1 bar for freshness, 20 sessions for S15 and VBAR. `warmup` = 2500 five-minute bars = 22
sessions of up to 113 bars: the live window then holds today's whole session and the 20 sessions before it.

Source: Hasbrouck (1991), Measuring the Information Content of Stock Trades, Journal of Finance 46(1); Foucault, Kadan &
Kandel, Limit Order Book as a Market for Liquidity; Obizhaeva & Wang, Resilient price impact of trading and the cost of
illiquidity. Proposal: research/b3/proposals/P-020.json.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.calendar import SessionRules
from b3.events import event_times, mark_events
from b3.markets import ProxyStrategy
from b3.strategy import ENTER_LONG, ENTER_SHORT, EXIT, HOLD, tick_ceil, tick_floor
from live.core.models import Signal

RULE_ID = "P-020"
EVENT_KINDS = ["FOMC", "CPI", "NFP"]


class WinThinVolumeMoveFade(ProxyStrategy):
    name = "P-020_win_thin_volume_move_fade"
    timeframe_min = 5
    warmup = 2500         # 20 earlier sessions + today at up to 113 five-minute bars each, plus margin
    rules = SessionRules(entry_start_after_open_min=5, entry_end_before_close_min=44, flatten_before_close_min=5)
    params = {
        "timeframe_min": 5,
        "move_lookback_bars": 3,
        "scale_lookback_sessions": 20,
        "volume_baseline_sessions": 20,
        "min_volume_baseline_sessions": 15,
        "move_mult": 1.5,
        "max_relative_volume": 1.0,
        "window_start_minute_of_day": 615,
        "min_minutes_to_close_at_signal": 45,
        "stop_min_frac": 0.002,
        "stop_max_frac": 0.005,
        "stop_move_mult": 1.0,
        "target_retrace_frac": 0.5,
        "max_hold_bars": 6,
        "event_block_after_min": 30,
        "fomc_block_before_min": 15,
        "max_entries_per_day": 6,
    }

    def _volume_baseline(self, df):
        """VBAR per row: mean volume of the row's slot over the previous `volume_baseline_sessions` sessions (today
        excluded), NaN unless at least `min_volume_baseline_sessions` of them hold the slot."""
        p = self.params
        order = list(dict.fromkeys(df["local_date"]))
        sess = df["local_date"].map({d: i for i, d in enumerate(order)}).to_numpy(dtype=int)
        slot = df["minute_of_day"].to_numpy(dtype=int)
        cell = pd.DataFrame({"s": sess, "slot": slot, "v": df["volume"].to_numpy(dtype=float)})
        mat = cell.groupby(["s", "slot"])["v"].last().unstack().reindex(range(len(order)))
        base = mat.shift(1).rolling(p["volume_baseline_sessions"], min_periods=p["min_volume_baseline_sessions"]).mean()
        return base.to_numpy(dtype=float)[sess, base.columns.get_indexer(slot)]

    def _scale(self, df, absr):
        """S15 per row: pooled mean of |R| over the bars with minute_of_day >= 615 of the previous 20 sessions."""
        p = self.params
        order = list(dict.fromkeys(df["local_date"]))
        counted = absr.where(df["minute_of_day"] >= p["window_start_minute_of_day"])
        g = counted.groupby(df["local_date"])
        sums = g.sum().reindex(order)
        cnts = g.count().reindex(order).astype(float)
        n = p["scale_lookback_sessions"]
        tot = sums.shift(1).rolling(n, min_periods=n).sum()
        num = cnts.shift(1).rolling(n, min_periods=n).sum()
        s15 = tot / num.where(num > 0)
        return df["local_date"].map(s15).to_numpy(dtype=float)

    def _event_block(self, df):
        """True where no entry is allowed because of a scheduled release (decided at the close of the signal bar)."""
        p = self.params
        blocked = np.zeros(len(df), dtype=bool)
        for kind in EVENT_KINDS:
            since = df[f"{kind}_min_since"].to_numpy(dtype=float)
            blocked |= (since >= 0) & (since <= p["event_block_after_min"])
        close_t = pd.to_datetime(df["time"], utc=True) + pd.Timedelta(minutes=self.timeframe_min)
        ny_date = close_t.dt.tz_convert("America/New_York").dt.date
        release_by_day = {t.tz_convert("America/New_York").date(): t for t in event_times("FOMC")}
        release = pd.to_datetime(ny_date.map(release_by_day), utc=True)
        to_release = ((release - close_t).dt.total_seconds() / 60.0).to_numpy(dtype=float)
        blocked |= df["FOMC_today"].to_numpy(dtype=bool) & (to_release <= p["fomc_block_before_min"])
        return blocked

    def indicators(self, df):
        p = self.params
        tick = self.market.tick_size
        k = p["move_lookback_bars"]
        df = mark_events(df, EVENT_KINDS, self.timeframe_min)
        n = len(df)

        close_s = df["close"].astype(float)
        ret = close_s / close_s.groupby(df["local_date"]).shift(k) - 1.0     # NaN while bar_in_day < k
        absr = ret.abs()
        df["tv_ret"] = ret
        df["tv_s15"] = s15 = self._scale(df, absr)

        vbar = pd.Series(self._volume_baseline(df), index=df.index)
        vol = df["volume"].astype(float)
        by_day_v = vol.groupby(df["local_date"])
        by_day_b = vbar.groupby(df["local_date"])
        vsum = vol + by_day_v.shift(1) + by_day_v.shift(2)
        bsum = vbar + by_day_b.shift(1) + by_day_b.shift(2)
        df["tv_vbar"] = vbar
        df["tv_rv"] = rv = (vsum / bsum.where(bsum > 0)).to_numpy(dtype=float)

        both = (absr.to_numpy(dtype=float) >= p["move_mult"] * s15) & (rv <= p["max_relative_volume"])   # NaN -> False
        prev_both = np.zeros(n, dtype=bool)
        prev_both[1:] = both[:-1]
        fresh = both & ~prev_both
        df["tv_both"] = both
        blocked = self._event_block(df)

        day = df["local_date"].to_numpy()
        minute = df["minute_of_day"].to_numpy()
        mtc = df["minutes_to_close"].to_numpy(dtype=float)
        high = df["high"].to_numpy(dtype=float)
        low = df["low"].to_numpy(dtype=float)
        close = close_s.to_numpy(dtype=float)
        ret_a = ret.to_numpy(dtype=float)
        win_start, min_mtc = p["window_start_minute_of_day"], p["min_minutes_to_close_at_signal"]
        max_entries, max_hold = p["max_entries_per_day"], p["max_hold_bars"]

        side = np.zeros(n, dtype=int)
        stop = np.full(n, np.nan)
        exit_code = np.zeros(n, dtype=int)         # 1 = target exit decided here, 2 = time exit decided here

        start = 0
        while start < n:
            end = start + 1
            while end < n and day[end] == day[start]:
                end += 1
            in_pos, pos_stop, pos_bar, pos_target, entries, block = 0, math.nan, -1, math.nan, 0, -1
            for i in range(start, end):
                if in_pos != 0:
                    # the stop, checked from the entry bar on (the first bar after the signal bar), before the exits
                    if (in_pos > 0 and low[i] <= pos_stop) or (in_pos < 0 and high[i] >= pos_stop):
                        in_pos, block = 0, i
                        continue
                    hit = close[i] >= pos_target if in_pos > 0 else close[i] <= pos_target
                    if hit:
                        exit_code[i] = 1
                    elif i - pos_bar >= max_hold:
                        exit_code[i] = 2
                    if exit_code[i]:
                        in_pos, block = 0, i + 1       # the exit fills at the open of the next bar = the exit bar
                    continue
                if (i <= block or entries >= max_entries or not fresh[i] or blocked[i] or minute[i] < win_start
                        or not mtc[i] >= min_mtc - 1e-9):
                    continue
                r = ret_a[i]
                if math.isnan(r) or r == 0:
                    continue
                c, c_prev = close[i], close[i - k]
                d = min(max(p["stop_move_mult"] * abs(c - c_prev), p["stop_min_frac"] * c), p["stop_max_frac"] * c)
                if r < 0:
                    side[i], stop[i] = 1, tick_floor(c - d, tick)
                else:
                    side[i], stop[i] = -1, tick_ceil(c + d, tick)
                pos_target = c_prev + p["target_retrace_frac"] * (c - c_prev)
                in_pos, pos_stop, pos_bar, entries = int(side[i]), stop[i], i, entries + 1
            start = end

        df["tv_side"] = side
        df["tv_stop"] = stop
        df["tv_exit"] = exit_code
        return df

    def decide(self, row, position):
        if position is not None:
            if row.tv_exit == 1:
                return Signal(EXIT, reason="target_half_retrace")
            if row.tv_exit == 2:
                return Signal(EXIT, reason="time_exit_30min")
            return Signal(HOLD)
        if row.tv_side > 0:
            return Signal(ENTER_LONG, stop_price=float(row.tv_stop), reason="fade_thin_volume_drop")
        if row.tv_side < 0:
            return Signal(ENTER_SHORT, stop_price=float(row.tv_stop), reason="fade_thin_volume_rally")
        return Signal(HOLD)
