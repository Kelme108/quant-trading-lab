"""P-017 WinStopSweepFailureFade - fade a 1-minute break of a standing 60-minute high/low that closes back inside within
5 bars (WIN only; 1-minute bars, B3 regular session in Sao Paulo time, everything from ONE session: nothing from
earlier sessions is used and the WIN$N roll never enters).

Rule, in words (H, L, C = high, low, close of a bar; tick = 5 points):
- LEVELS at bar b with bar_in_day >= 60: Lhi(b) = max High and Llo(b) = min Low over the previous 60 bars of today
  (b-60..b-1). R(b) = Lhi - Llo, mid M(b) = (Lhi + Llo) / 2.
- STANDING: Lhi(b) was last set by a bar at least 15 bars before b (the LATEST bar of the 60 whose High equals Lhi; same
  for Llo with the Low).
- UP-BREAK at b: H_b > Lhi(b), Lhi standing, R(b) >= 0.20% of Lhi. The event freezes Lhi, M, R from b. FAILURE (short):
  the first bar f in b..b+4 with C_f <= Lhi - 1 tick. X = max High over b..f. The event is void if X - Lhi > 0.25% of
  Lhi, or if there is no failure by b+4. SHORT at the close of f if flat: ENTER_SHORT (fill at the open of f+1), stop =
  tick_ceil(max(X + 2 ticks, C_f * 1.0012)); no entry if that stop is more than 0.40% above C_f.
- DOWN-BREAK at b (symmetric): L_b < Llo(b), Llo standing, R(b) >= 0.20% (of Llo, the broken level); failure = first f in
  b..b+4 with C_f >= Llo + 1 tick; X = min Low over b..f; void if Llo - X > 0.25% of Llo; ENTER_LONG; stop =
  tick_floor(min(X - 2 ticks, C_f * 0.9988)); no entry if more than 0.40% below C_f.
- If a long and a short failure (of non-void events) fire on the same bar, neither is taken.
- WINDOW: the failure bar f has minute_of_day >= 615 (opens 10:15 or later) and minutes_to_close >= 45 at its close.
- EVENTS (b3.events.mark_events, kinds FOMC, CPI, NFP): no entry if any <kind>_min_since is in [0, 30] at f. On a day with
  an FOMC statement, no entry from 15 minutes before the release (b3.events.event_times) on (the close of f is the fill
  time and is compared with the release minus 15 minutes).
- EXIT, first of: (a) target: at the close of a bar from the entry bar on (the entry bar is the bar whose open is the
  fill), C <= M (short) or C >= M (long) -> EXIT at the next open; (b) time: EXIT at the open of the 30th bar after the
  entry bar (decided at the close of the bar 30 bars after f); (c) the stop, fixed for the trade, checked from the entry
  bar on and before the exits; (d) the engine's flatten 5 minutes before the close.
- ONE ENTRY PER BREAK EVENT: an event is consumed at its first failure (taken or not), at a void or at b+4. No event
  starts while a position is open or on/before the exit bar (the exit bar is the bar whose open is the exit fill for a
  target or time exit, and the bar in which the stop is hit for a stop): a new event needs a break bar after the exit
  bar. At most one position.
- MAX 6 ENTRIES PER DAY, enforced by the rule itself: `indicators` replays each session bar by bar (entry at the next
  open, stop hit when a bar from the entry bar on reaches it, target and time exits as above) and stops signalling after
  the 6th entry. BacktestConfig(max_entries_per_day=...) is not needed. The replay uses only bars up to the current one.
  (The backtester takes no decisions during the first `warmup` bars; a day inside that stretch can differ.)

SessionRules note: a fill happens at the close of the failure bar. `entry_start_after_open_min` = 1 is the first possible
fill (the rule itself enforces minute_of_day >= 615); `entry_end_before_close_min` = 44 makes the engine's half-open entry
phase [start, close - 44 min) accept a fill at close - 45 min (the last window bar) and refuse a later one. The proposal
names no flatten offset: 5 minutes before the close, as in the other B3 rules.

Lookbacks: 60 bars for the levels, 15 bars standing age, 5-bar failure window. `warmup` = 700 one-minute bars: the live
window then holds today's whole session (at most 565 bars: 09:00-18:25) plus the 60-bar lookback.

Source: Osler (2003), Currency Orders and Exchange Rate Dynamics, Journal of Finance 58(5); Osler, Stop-Loss Orders and
Price Cascades in Currency Markets, NY Fed Staff Report 150; Chague, De-Losso & Giovannetti, Day Trading for a Living?
Proposal: research/b3/proposals/P-017.json.
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

RULE_ID = "P-017"
EPS = 1e-9
EVENT_KINDS = ["FOMC", "CPI", "NFP"]


class WinStopSweepFailureFade(ProxyStrategy):
    name = "P-017_win_stop_sweep_failure_fade"
    timeframe_min = 1
    warmup = 700          # today's whole session (at most 565 one-minute bars) + the 60-bar lookback, plus margin
    rules = SessionRules(entry_start_after_open_min=1, entry_end_before_close_min=44, flatten_before_close_min=5)
    params = {
        "timeframe_min": 1,
        "level_lookback_bars": 60,
        "min_level_age_bars": 15,
        "min_range_frac": 0.002,
        "failure_window_bars": 5,
        "failure_close_ticks_inside": 1,
        "max_sweep_excursion_frac": 0.0025,
        "stop_ticks_beyond_sweep": 2,
        "min_stop_frac": 0.0012,
        "max_stop_frac": 0.004,
        "max_hold_bars": 30,
        "window_start_minute_of_day": 615,
        "min_minutes_to_close_at_signal": 45,
        "event_block_after_min": 30,
        "fomc_block_before_min": 15,
        "max_entries_per_day": 6,
    }

    def _levels(self, high, low):
        """Per bar of ONE session: Lhi, Llo over the previous `level_lookback_bars` bars of the session, and the age (in
        bars) of the latest bar that set each. NaN before the lookback is filled."""
        n, w = len(high), self.params["level_lookback_bars"]
        lhi, llo = np.full(n, np.nan), np.full(n, np.nan)
        age_hi, age_lo = np.full(n, np.nan), np.full(n, np.nan)
        if n > w:
            wh = np.lib.stride_tricks.sliding_window_view(high, w)[: n - w]      # row j = bars j..j+w-1, used at b = j+w
            wl = np.lib.stride_tricks.sliding_window_view(low, w)[: n - w]
            lhi[w:] = wh.max(axis=1)
            llo[w:] = wl.min(axis=1)
            age_hi[w:] = w - (w - 1 - np.argmax(wh[:, ::-1] == lhi[w:, None], axis=1))
            age_lo[w:] = w - (w - 1 - np.argmax(wl[:, ::-1] == llo[w:, None], axis=1))
        return lhi, llo, age_hi, age_lo

    def indicators(self, df):
        p = self.params
        tick = self.market.tick_size
        df = mark_events(df, EVENT_KINDS, self.timeframe_min)
        n = len(df)

        # FOMC: the close of the bar (= the fill time of an entry) is at or after the release minus `fomc_block_before_min`
        close_t = pd.to_datetime(df["time"], utc=True) + pd.Timedelta(minutes=self.timeframe_min)
        ny_date = close_t.dt.tz_convert("America/New_York").dt.date
        release = ny_date.map({t.tz_convert("America/New_York").date(): t for t in event_times("FOMC")})
        release = pd.to_datetime(release, utc=True)
        fomc_before = (release.notna() & (close_t >= release - pd.Timedelta(minutes=p["fomc_block_before_min"]))).to_numpy()
        blocked_event = fomc_before.copy()
        for kind in EVENT_KINDS:
            since = df[f"{kind}_min_since"].to_numpy(dtype=float)
            blocked_event |= (since >= 0.0) & (since <= p["event_block_after_min"])       # NaN compares False

        day = df["local_date"].to_numpy()
        minute = df["minute_of_day"].to_numpy()
        mtc = df["minutes_to_close"].to_numpy(dtype=float)
        high = df["high"].to_numpy(dtype=float)
        low = df["low"].to_numpy(dtype=float)
        close = df["close"].to_numpy(dtype=float)

        lhi, llo = np.full(n, np.nan), np.full(n, np.nan)
        age_hi, age_lo = np.full(n, np.nan), np.full(n, np.nan)
        starts = [0]
        for i in range(1, n):
            if day[i] != day[i - 1]:
                starts.append(i)
        bounds = list(zip(starts, starts[1:] + [n]))
        for s, e in bounds:
            lhi[s:e], llo[s:e], age_hi[s:e], age_lo[s:e] = self._levels(high[s:e], low[s:e])

        side = np.zeros(n, dtype=int)
        stop = np.full(n, np.nan)
        exit_code = np.zeros(n, dtype=int)         # 1 = target decided here, 2 = time exit decided here

        w_fail, min_age = p["failure_window_bars"], p["min_level_age_bars"]
        k_in, k_beyond = p["failure_close_ticks_inside"] * tick, p["stop_ticks_beyond_sweep"] * tick
        win_start, min_mtc = p["window_start_minute_of_day"], p["min_minutes_to_close_at_signal"]
        max_entries, max_hold = p["max_entries_per_day"], p["max_hold_bars"]
        min_range, max_exc = p["min_range_frac"], p["max_sweep_excursion_frac"]
        min_stop, max_stop = p["min_stop_frac"], p["max_stop_frac"]

        for s, e in bounds:
            in_pos, pos_stop, pos_mid, pos_bar, entries, block = 0, math.nan, math.nan, -1, 0, -1
            up = None          # pending break event: [break bar, level, mid, extreme X]
            dn = None
            for i in range(s, e):
                if in_pos != 0:
                    # the stop, checked from the entry bar on (the first bar after the failure bar), before the exits
                    if (in_pos > 0 and low[i] <= pos_stop) or (in_pos < 0 and high[i] >= pos_stop):
                        in_pos, block = 0, i
                        continue
                    hit_mid = close[i] >= pos_mid if in_pos > 0 else close[i] <= pos_mid
                    if hit_mid:
                        exit_code[i] = 1
                    elif i - pos_bar >= max_hold:
                        exit_code[i] = 2
                    if exit_code[i]:
                        in_pos, block = 0, i + 1       # the exit fills at the open of the next bar = the exit bar
                    continue
                if i <= block:
                    up = dn = None
                    continue

                fail_up = fail_dn = None               # (level, mid, X) of a valid failure firing on this bar
                # ---- up side
                if up is not None and i - up[0] > w_fail - 1:
                    up = None                          # no failure by b+4
                if up is None and not math.isnan(lhi[i]) and high[i] > lhi[i] and age_hi[i] >= min_age \
                        and lhi[i] - llo[i] >= min_range * lhi[i] - EPS:
                    up = [i, lhi[i], (lhi[i] + llo[i]) / 2.0, -math.inf]
                if up is not None:
                    up[3] = max(up[3], high[i])
                    if close[i] <= up[1] - k_in + EPS:
                        if up[3] - up[1] <= max_exc * up[1] + EPS:
                            fail_up = (up[1], up[2], up[3])
                        up = None
                # ---- down side
                if dn is not None and i - dn[0] > w_fail - 1:
                    dn = None
                if dn is None and not math.isnan(llo[i]) and low[i] < llo[i] and age_lo[i] >= min_age \
                        and lhi[i] - llo[i] >= min_range * llo[i] - EPS:
                    dn = [i, llo[i], (lhi[i] + llo[i]) / 2.0, math.inf]
                if dn is not None:
                    dn[3] = min(dn[3], low[i])
                    if close[i] >= dn[1] + k_in - EPS:
                        if dn[1] - dn[3] <= max_exc * dn[1] + EPS:
                            fail_dn = (dn[1], dn[2], dn[3])
                        dn = None

                if (fail_up is None) == (fail_dn is None):
                    continue                           # no failure, or both fired: neither is taken
                if (entries >= max_entries or minute[i] < win_start or not mtc[i] >= min_mtc - 1e-9
                        or blocked_event[i]):
                    continue
                c = close[i]
                if fail_up is not None:
                    st = tick_ceil(max(fail_up[2] + k_beyond, c * (1.0 + min_stop)), tick)
                    if st - c > max_stop * c + EPS:
                        continue
                    side[i], stop[i], pos_mid = -1, st, fail_up[1]
                else:
                    st = tick_floor(min(fail_dn[2] - k_beyond, c * (1.0 - min_stop)), tick)
                    if c - st > max_stop * c + EPS:
                        continue
                    side[i], stop[i], pos_mid = 1, st, fail_dn[1]
                in_pos, pos_stop, pos_bar, entries = int(side[i]), st, i, entries + 1
                up = dn = None

        df["sw_side"] = side
        df["sw_stop"] = stop
        df["sw_exit"] = exit_code
        return df

    def decide(self, row, position):
        if position is not None:
            if row.sw_exit == 1:
                return Signal(EXIT, reason="target_midpoint")
            if row.sw_exit == 2:
                return Signal(EXIT, reason="time_exit_30_bars")
            return Signal(HOLD)
        if row.sw_side > 0:
            return Signal(ENTER_LONG, stop_price=float(row.sw_stop), reason="down_sweep_failure_long")
        if row.sw_side < 0:
            return Signal(ENTER_SHORT, stop_price=float(row.sw_stop), reason="up_sweep_failure_short")
        return Signal(HOLD)
