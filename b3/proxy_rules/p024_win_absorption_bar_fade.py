"""P-024 WinAbsorptionBarFade - fade a 30-minute WIN run when a 5-minute bar trades heavy volume for its time of day but
barely moves (effort without result = absorption by a passive counterparty). WIN only; 5-minute bars, B3 regular session
in Sao Paulo time.

Rule, in words:
- Bar t has high H, low L, close C, volume V (contracts). RNG_t = max(H - L, 1 tick) / C (one tick = 5 points: the floor is
  `range_floor_ticks` ticks).
- SLOT = minute_of_day of the bar open. vol_norm_t = V_t / median V of that slot over the previous 20 sessions (today
  excluded); rng_norm_t = RNG_t / median RNG of that slot over the same previous sessions. The median is taken over those of
  the 20 previous sessions that hold the slot (a slot missing in a session is skipped). Everything is a ratio of volumes or of
  shares of price, so contract rolls (WIN$N is unadjusted) do not distort it.
- Effort-to-result er_t = vol_norm_t / rng_norm_t.
- P85 (once per session, from earlier sessions only): the 85th percentile (numpy, linear interpolation) of er over all bars
  of the previous 20 sessions that lie in the ENTRY WINDOW (bar_in_day >= 7 and minutes_to_close at the bar's close >= 60).
- RUN_t = C_(t-1) / C_(t-7) - 1, both bars from today's session (6 bars = 30 minutes; needs bar_in_day >= 7).
- ABSORPTION BAR: er_t >= P85 AND vol_norm_t >= 1.0.
- SIGNAL at the close of bar t (bar_in_day >= 7 and minutes_to_close >= 60 at the close of t): absorption bar and
  RUN_t >= +0.10% -> SHORT; absorption bar and RUN_t <= -0.10% -> LONG; market order at the open of t+1, only if flat.
- STOP on every entry, fixed for the trade (the entry price is the open of t+1, unknown at the decision, so the close of bar
  t stands for it): short: raw = max(high of bars t-6..t) + 2 ticks; long: raw = min(low of bars t-6..t) - 2 ticks; the
  distance |entry - raw| is clamped to [0.10%, 0.30%] of the entry price; short stop = tick_ceil(entry + distance), long stop
  = tick_floor(entry - distance) (5-point grid: the rounding goes away from the price, so a clamp at 0.30% can come out up
  to one tick wider).
- EXIT, first of: the stop (checked from the entry bar on); the time exit at the open of the 10th bar after the entry
  (the entry bar is the 1st; 9 bars = 45 minutes held), decided at the close of the bar 9 bars after the signal bar; the
  engine's flatten before the close (every entry is >= 60 minutes before the close, so the time exit always comes first).
  No profit target, no reversal on an opposite signal.
- ONE POSITION: a signal on a bar where the position is open (or is being exited by the time exit) is ignored. After a time
  exit decided at bar i the next possible signal bar is i + 1 (flat at its close). After a stop that was hit in bar i the book
  is flat at the close of bar i, so bar i itself can signal (this mirrors the backtester and the live engine, which decide
  after the stop was processed).
- 20 COMPLETED SESSIONS of history are needed before the first trade (P85 is NaN until 20 earlier sessions exist). The
  baseline medians use the earlier sessions that exist, up to 20 (at least 1); the very first sessions of a history therefore
  have shorter baselines, but they feed a P85 only after 20 sessions and `warmup` keeps them out of any decision.
- MAX 6 ENTRIES PER DAY, enforced by the rule itself: `indicators` replays each session bar by bar (entry at the next open,
  stop when a bar from the entry bar on reaches it, time exit as above) and stops signalling after the 6th entry.
  BacktestConfig(max_entries_per_day=...) is not needed. The replay uses only bars up to the current one. (The backtester
  takes no decisions during the first `warmup` bars; a day inside that stretch can differ.)

SessionRules note: the fill happens at the close of the signal bar. `entry_start_after_open_min` = 40 is the close of bar 7
(the rule itself enforces bar_in_day >= 7); `entry_end_before_close_min` = 59 makes the engine's half-open entry phase
[start, close - 59 min) accept a fill at close - 60 min (the last window bar) and refuse a later one.

Lookbacks: 7 bars for the run and the stop, 20 sessions for the baselines and for P85, and the er of those 20 sessions
themselves need 20 sessions before them: `warmup` = 5000 five-minute bars = 44 sessions of at most 113 bars, so the live
window holds today and the 40 sessions the decision depends on.

Source: Frey & Sandas, The Impact of Iceberg Orders in Limit Order Books (CFR WP 09-06); Bessembinder, Panayides &
Venkataraman (2009), Hidden liquidity: order exposure strategies, JFE 94(3); Kaniel & Liu (2006), So What Orders Do
Informed Traders Use?, Journal of Business 79(4). Proposal: research/b3/proposals/P-024.json.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.calendar import SessionRules
from b3.markets import ProxyStrategy
from b3.strategy import ENTER_LONG, ENTER_SHORT, EXIT, HOLD, tick_ceil, tick_floor
from live.core.models import Signal

RULE_ID = "P-024"


class WinAbsorptionBarFade(ProxyStrategy):
    name = "P-024_win_absorption_bar_fade"
    timeframe_min = 5
    warmup = 5000         # today + 40 earlier sessions (20 for P85, 20 more for the baselines of those) at up to 113 bars
    rules = SessionRules(entry_start_after_open_min=40, entry_end_before_close_min=59, flatten_before_close_min=5)
    params = {
        "baseline_sessions": 20,
        "er_percentile": 85,
        "min_vol_norm": 1.0,
        "run_bars": 6,
        "min_run_pct": 0.1,
        "min_bar_in_day": 7,
        "min_minutes_to_close_at_signal": 60,
        "stop_buffer_ticks": 2,
        "stop_lookback_bars": 7,
        "min_stop_pct": 0.1,
        "max_stop_pct": 0.3,
        "hold_bars": 9,
        "max_entries_per_day": 6,
        "range_floor_ticks": 1,
    }

    def _slot_median(self, df, values):
        """Per row: median of `values` at the row's slot (minute_of_day) over the previous `baseline_sessions` sessions
        (today excluded) that hold the slot; NaN if none does."""
        order = list(dict.fromkeys(df["local_date"]))
        sess = df["local_date"].map({d: i for i, d in enumerate(order)}).to_numpy(dtype=int)
        slot = df["minute_of_day"].to_numpy(dtype=int)
        cell = pd.DataFrame({"s": sess, "slot": slot, "v": np.asarray(values, dtype=float)})
        mat = cell.groupby(["s", "slot"])["v"].last().unstack().reindex(range(len(order)))
        base = mat.shift(1).rolling(self.params["baseline_sessions"], min_periods=1).median()
        return base.to_numpy(dtype=float)[sess, base.columns.get_indexer(slot)]

    def _er_threshold(self, er, in_window, day):
        """Per row: P85 of er over the in-window bars of the previous `baseline_sessions` sessions (NaN until that many
        earlier sessions exist, or if none of their bars has an er)."""
        p = self.params
        n = len(er)
        out = np.full(n, np.nan)
        starts = [0] + [i for i in range(1, n) if day[i] != day[i - 1]]
        ends = starts[1:] + [n]
        usable = in_window & np.isfinite(er)
        per_session = [er[a:b][usable[a:b]] for a, b in zip(starts, ends)]
        k = p["baseline_sessions"]
        for s, (a, b) in enumerate(zip(starts, ends)):
            if s < k:
                continue
            pool = np.concatenate(per_session[s - k:s])
            if len(pool):
                out[a:b] = np.percentile(pool, p["er_percentile"])
        return out

    def indicators(self, df):
        p = self.params
        tick = self.market.tick_size
        n = len(df)

        close_s = df["close"].astype(float)
        high_s = df["high"].astype(float)
        low_s = df["low"].astype(float)
        vol = df["volume"].astype(float)
        by_day_c = close_s.groupby(df["local_date"])

        rng = np.maximum((high_s - low_s).to_numpy(dtype=float), p["range_floor_ticks"] * tick) / close_s.to_numpy(dtype=float)
        med_v = self._slot_median(df, vol.to_numpy(dtype=float))
        med_r = self._slot_median(df, rng)
        with np.errstate(divide="ignore", invalid="ignore"):
            vol_norm = np.where(med_v > 0, vol.to_numpy(dtype=float) / med_v, np.nan)
            rng_norm = np.where(med_r > 0, rng / med_r, np.nan)
            er = vol_norm / rng_norm
        df["ab_vol_norm"] = vol_norm
        df["ab_er"] = er

        bar = df["bar_in_day"].to_numpy(dtype=int)
        mtc = df["minutes_to_close"].to_numpy(dtype=float)
        day = df["local_date"].to_numpy()
        in_window = (bar >= p["min_bar_in_day"]) & (mtc >= p["min_minutes_to_close_at_signal"] - 1e-9)
        df["ab_p85"] = p85 = self._er_threshold(er, in_window, day)

        run = (by_day_c.shift(1) / by_day_c.shift(p["run_bars"] + 1) - 1.0).to_numpy(dtype=float)   # NaN if bar_in_day < 7
        df["ab_run"] = run
        lookback = p["stop_lookback_bars"]
        hi_n = high_s.groupby(df["local_date"]).rolling(lookback, min_periods=lookback).max().reset_index(level=0, drop=True)
        lo_n = low_s.groupby(df["local_date"]).rolling(lookback, min_periods=lookback).min().reset_index(level=0, drop=True)
        hi_n = hi_n.reindex(df.index).to_numpy(dtype=float)
        lo_n = lo_n.reindex(df.index).to_numpy(dtype=float)

        thr = p["min_run_pct"] / 100.0
        absorb = (er >= p85) & (vol_norm >= p["min_vol_norm"])             # NaN -> False
        up = absorb & in_window & (run >= thr - 1e-12)
        down = absorb & in_window & (run <= -thr + 1e-12)
        df["ab_absorb"] = absorb

        close = close_s.to_numpy(dtype=float)
        high = high_s.to_numpy(dtype=float)
        low = low_s.to_numpy(dtype=float)
        buffer = p["stop_buffer_ticks"] * tick
        min_d, max_d = p["min_stop_pct"] / 100.0, p["max_stop_pct"] / 100.0
        max_entries, hold = p["max_entries_per_day"], p["hold_bars"]

        side = np.zeros(n, dtype=int)
        stop = np.full(n, np.nan)
        exit_code = np.zeros(n, dtype=int)         # 1 = time exit decided at this bar

        start = 0
        while start < n:
            end = start + 1
            while end < n and day[end] == day[start]:
                end += 1
            in_pos, pos_stop, pos_bar, entries = 0, math.nan, -1, 0
            for i in range(start, end):
                if in_pos != 0:
                    # the stop, checked from the entry bar (the first bar after the signal bar) on
                    if (in_pos > 0 and low[i] <= pos_stop) or (in_pos < 0 and high[i] >= pos_stop):
                        in_pos = 0                       # flat at the close of this bar: it may signal below
                    else:
                        if i - pos_bar >= hold:
                            exit_code[i] = 1             # the exit fills at the open of the next bar
                            in_pos = 0
                        continue
                if entries >= max_entries or not (up[i] or down[i]):
                    continue
                c = close[i]
                if up[i]:                                # buyers pushed, a passive seller absorbed: SHORT
                    d = min(max(hi_n[i] + buffer - c, min_d * c), max_d * c)
                    side[i], stop[i] = -1, tick_ceil(c + d, tick)
                else:                                    # sellers pushed, a passive buyer absorbed: LONG
                    d = min(max(c - (lo_n[i] - buffer), min_d * c), max_d * c)
                    side[i], stop[i] = 1, tick_floor(c - d, tick)
                in_pos, pos_stop, pos_bar, entries = int(side[i]), stop[i], i, entries + 1
            start = end

        df["ab_side"] = side
        df["ab_stop"] = stop
        df["ab_exit"] = exit_code
        return df

    def decide(self, row, position):
        if position is not None:
            if row.ab_exit == 1:
                return Signal(EXIT, reason="time_exit_45min")
            return Signal(HOLD)
        if row.ab_side > 0:
            return Signal(ENTER_LONG, stop_price=float(row.ab_stop), reason="fade_absorbed_drop")
        if row.ab_side < 0:
            return Signal(ENTER_SHORT, stop_price=float(row.ab_stop), reason="fade_absorbed_rally")
        return Signal(HOLD)
