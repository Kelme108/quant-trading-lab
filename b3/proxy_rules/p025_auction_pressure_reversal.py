"""P-025 AuctionPressureReversal - fade the 20-minute impulse around three scheduled auction anchors of the WIN session:
the B3 cash open, the NYSE open and the B3/NYSE closing call. WIN only; 1-minute bars, B3 regular session in Sao Paulo
time; a bar is labelled by its open time.

Rule, in words:
- THREE ANCHORS per session, all fixed clock times: A1 = B3 cash equity open, 10:00 Sao Paulo (minute 600);
  A2 = NYSE open, 09:30 America/New_York converted to Sao Paulo (10:30 while New York is on EDT, 11:30 on EST);
  A3 = B3 cash close / end of the closing call, aligned with the NYSE close: 16:00 America/New_York converted to Sao Paulo
  (17:00 on EDT, 18:00 on EST). The conversion uses the tz database (America/New_York, America/Sao_Paulo), by session date.
- IMPULSE(A) = close of the bar opening at A+4 min (it closes at A+5) / open of the bar opening at A-15 min - 1: a 20-minute
  within-session return. The anchor is skipped for that session if either bar is missing (this also covers an anchor outside
  the day's session, e.g. a late-open day).
- SCALE(A) = median of |IMPULSE| at the same anchor (A1, A2 and A3 are kept apart) over the previous 20 sessions that had it
  (sessions with a computable impulse; today excluded). Returns only, so the unadjusted roll between sessions never enters
  it. No trade at an anchor until 20 such past values exist.
- ENTRY: if |IMPULSE| >= 0.5 x SCALE(A), the signal is taken at the close of bar A+4 and the market order fills at the open of
  bar A+5: SHORT if IMPULSE > 0, LONG if IMPULSE < 0 (symmetric). (The comparison carries a 1e-12 tolerance so that a ratio
  of exactly 0.5 is not lost to floating-point noise.) An impulse of exactly 0 gives no direction and no trade.
- STOP, fixed for the trade: the entry price is the open of bar A+5, unknown at the decision, so the close of bar A+4 stands for
  it. distance = max(1.0 x |IMPULSE| x entry, 0.20% x entry); a short's stop is tick_ceil(entry + distance) and a long's
  stop is tick_floor(entry - distance), i.e. rounded away from the entry to the 5-point tick.
- EXIT, first of: the stop (checked from the entry bar on); the time exit at the open of the 25th bar after the entry (the
  entry bar is bar A+5, so the exit fills at the open of bar A+30 = 25 minutes held; it is decided at the close of the bar 25
  bars after the signal bar); the engine's flatten 5 minutes before the close.
- ONE POSITION: an anchor whose signal bar finds the position open (or being exited by the time exit) is skipped. After a stop
  hit in bar i the book is flat at the close of bar i, so bar i can itself be a signal bar (the backtester and the live engine
  decide after the stop was processed).
- SESSION RULES: entry_start_after_open_min 60, entry_end_before_close_min 15, flatten_before_close_min 5 (the engine vetoes an
  entry whose fill time is outside [open + 60 min, close - 15 min); the replay below applies the same test so that its state
  matches the book). With the 18:25 close an A3 at 18:00 enters 18:05 and is flattened 18:20.
- MAX 3 ENTRIES PER DAY (one per anchor) is structural: `indicators` replays every session (entry at the next open, stop when
  a bar from the entry bar on reaches it, time exit as above) and emits at most one signal per anchor, so
  BacktestConfig(max_entries_per_day=...) is not needed. The replay uses only bars up to the current one.
- No events filter, no other indicator.

Lookbacks: 20 sessions of the same anchor (at most 570 one-minute bars each) plus today's session: `warmup` = 14000 bars is
about 24 full sessions, so the live window holds today and the 20+ sessions the scale depends on, with room for a few
sessions that lack an anchor.

Source: Berkman, Koch, Tuttle & Zhang (2012), Paying Attention: Overnight Returns and the Hidden Cost of Buying at the Open,
JFQA 47(4); Boyarchenko, Larsen & Whelan, The Overnight Drift (NY Fed Staff Report 917); B3 hours notices for the cash session
and closing call. Proposal: research/b3/proposals/P-025.json.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.calendar import SessionRules
from b3.markets import ProxyStrategy
from b3.strategy import ENTER_LONG, ENTER_SHORT, EXIT, HOLD, tick_ceil, tick_floor
from live.core.models import Signal

RULE_ID = "P-025"

NEW_YORK = "America/New_York"
SAO_PAULO = "America/Sao_Paulo"
KEY = 10_000          # (session index, minute of day) -> one integer key


class AuctionPressureReversal(ProxyStrategy):
    name = "P-025_auction_pressure_reversal"
    timeframe_min = 1
    warmup = 14000        # today + 20 earlier sessions of up to 570 one-minute bars, plus margin (~24 sessions)
    rules = SessionRules(entry_start_after_open_min=60, entry_end_before_close_min=15, flatten_before_close_min=5)
    params = {
        "cash_open_minute_sao_paulo": 600,
        "nyse_open_minute_new_york": 570,
        "nyse_close_minute_new_york": 960,
        "pre_anchor_min": 15,
        "post_anchor_min": 5,
        "scale_lookback_sessions": 20,
        "threshold_mult_of_scale": 0.5,
        "stop_min_pct": 0.2,
        "stop_impulse_mult": 1.0,
        "hold_min": 25,
        "max_entries_per_day": 3,
        "entry_start_after_open_min": 60,
        "entry_end_before_close_min": 15,
        "flatten_before_close_min": 5,
    }

    def _anchor_minutes(self, dates):
        """(sessions, 3) Sao Paulo minute-of-day of A1, A2, A3 for each session date."""
        p = self.params
        out = np.zeros((len(dates), 3), dtype=int)
        for r, d in enumerate(dates):
            out[r, 0] = p["cash_open_minute_sao_paulo"]
            for c, m in ((1, p["nyse_open_minute_new_york"]), (2, p["nyse_close_minute_new_york"])):
                ny = pd.Timestamp(year=d.year, month=d.month, day=d.day, hour=m // 60, minute=m % 60, tz=NEW_YORK)
                sp = ny.tz_convert(SAO_PAULO)
                out[r, c] = sp.hour * 60 + sp.minute
        return out

    def indicators(self, df):
        p = self.params
        tick = self.market.tick_size
        tf = self.timeframe_min
        n = len(df)

        close = df["close"].to_numpy(dtype=float)
        open_ = df["open"].to_numpy(dtype=float)
        high = df["high"].to_numpy(dtype=float)
        low = df["low"].to_numpy(dtype=float)
        mod = df["minute_of_day"].to_numpy(dtype=int)
        mtc = df["minutes_to_close"].to_numpy(dtype=float)

        dates = list(dict.fromkeys(df["local_date"]))
        n_sess = len(dates)
        sess = df["local_date"].map({d: i for i, d in enumerate(dates)}).to_numpy(dtype=int)
        starts = [0] + [i for i in range(1, n) if sess[i] != sess[i - 1]]
        ends = starts[1:] + [n]
        first_minute = df["minute_of_day"].groupby(df["local_date"]).transform("first").to_numpy(dtype=int)

        where = {}
        for i in range(n):
            where[int(sess[i]) * KEY + int(mod[i])] = i
        anchor_min = self._anchor_minutes(dates)

        # impulse and scale per anchor and session; both live on the signal bar (the bar opening at A+4) only
        imp_col = np.full(n, np.nan)
        scale_col = np.full(n, np.nan)
        anchor_col = np.zeros(n, dtype=int)
        cand = [[] for _ in range(n_sess)]          # per session: (signal row, side, anchor, impulse)
        look, mult = p["scale_lookback_sessions"], p["threshold_mult_of_scale"]
        for a in range(3):
            hist = []                                # |impulse| of the earlier sessions that had this anchor
            for s in range(n_sess):
                am = int(anchor_min[s, a])
                pre = where.get(s * KEY + am - p["pre_anchor_min"])
                post = where.get(s * KEY + am + p["post_anchor_min"] - tf)
                if pre is None or post is None or not open_[pre] > 0 or not np.isfinite(close[post]):
                    continue
                imp = close[post] / open_[pre] - 1.0
                if not np.isfinite(imp):
                    continue
                scale = float(np.median(hist[-look:])) if len(hist) >= look else math.nan
                hist.append(abs(imp))
                imp_col[post], scale_col[post], anchor_col[post] = imp, scale, a + 1
                if np.isfinite(scale) and imp != 0.0 and abs(imp) >= mult * scale - 1e-12:
                    cand[s].append((post, -1 if imp > 0 else 1, a + 1, imp))
        df["ap_imp"] = imp_col
        df["ap_scale"] = scale_col
        df["ap_anchor"] = anchor_col

        elapsed = mod + tf - first_minute
        window_ok = (elapsed >= p["entry_start_after_open_min"]) & (mtc > p["entry_end_before_close_min"] + 1e-9)

        side = np.zeros(n, dtype=int)
        stop = np.full(n, np.nan)
        exit_code = np.zeros(n, dtype=int)           # 1 = time exit decided at this bar (fills at the next open)
        floor_pct = p["stop_min_pct"] / 100.0
        for s in range(n_sess):
            b_idx = ends[s]
            free_from = starts[s]                    # first bar where a new signal may be taken
            entries = 0
            for i, sd, _anchor, imp in sorted(cand[s]):
                if i < free_from or not window_ok[i] or entries >= p["max_entries_per_day"]:
                    continue
                c = close[i]
                dist = max(p["stop_impulse_mult"] * abs(imp), floor_pct) * c
                if sd < 0:
                    st = tick_ceil(c + dist, tick)
                else:
                    st = tick_floor(c - dist, tick)
                    if st <= 0:
                        continue
                side[i], stop[i] = sd, st
                entries += 1
                free_from = b_idx                    # held to the flatten unless the loop below ends it
                for j in range(i + 1, b_idx):
                    if (sd > 0 and low[j] <= st) or (sd < 0 and high[j] >= st):
                        free_from = j                # flat at the close of bar j: bar j itself may signal
                        break
                    if j - i >= p["hold_min"] // tf:
                        exit_code[j] = 1             # the exit fills at the open of the next bar
                        free_from = j + 1
                        break
        df["ap_side"] = side
        df["ap_stop"] = stop
        df["ap_exit"] = exit_code
        return df

    def decide(self, row, position):
        if position is not None:
            if row.ap_exit == 1:
                return Signal(EXIT, reason="time_exit_25min")
            return Signal(HOLD)
        if row.ap_side > 0:
            return Signal(ENTER_LONG, stop_price=float(row.ap_stop), reason="fade_down_impulse")
        if row.ap_side < 0:
            return Signal(ENTER_SHORT, stop_price=float(row.ap_stop), reason="fade_up_impulse")
        return Signal(HOLD)
