"""P-032 WinBoxFadeTrailing - FADE a 1-minute close outside a 2-hour box that is tight for its time of day, with a stop of
half the box that moves to breakeven and then trails (WIN only; 1-minute bars, B3 regular session, Sao Paulo time).

Origin: the P-026 focused study (owner 2026-11-18: "pegasse essa P26... gere versoes melhores, de outros sentidos, teste
take profit, stop loss"), b3/config/p026_lab.json registered before any read, results
research/b3/p026_lab/20261118T192250Z.json. The pre-registered pick on WIN was tf 1, box 120 min, ratio 0.8, direction
FADE, exit BT: +R$2.37/trade measured cost (+0.67 at p90), 398 trades/year, beats random entries (-1.88), plateau 1.00.
720 versions were read; validation is untouched (read once, for this version only, before any real-account decision).
This file is the rule as the lab computed it, for the Clear DEMO next to the original P-026. NOT evidence.

Rule, in words (bar t = the 1-minute bar that has just closed; tick = 5 points):
- BOX before t: the 120 bars t-120..t-1 of TODAY's session; H/L = their max high / min low (no box before 120 bars of
  today exist). R(t) = (H - L) / close(t-1).
- NORM: the median of R at the same minute of day over the 20 previous sessions (at least 10 of them with a value).
- COMPRESSED: R(t) <= 0.8 x norm.
- FADE: compressed and close(t) >= H + 1 tick -> SHORT; compressed and close(t) <= L - 1 tick -> LONG. At the close of
  bar t (fill at the next 1-minute open), only while flat, minutes_to_close(t) >= 75, inside the entry window of the
  study (15 min after the open to 30 min before the close).
- B = half the box = (H - L) / 2, rounded UP to the tick (at least 1 tick).
- STOP (server, sent with the entry): 1 B from close(t) (the fill is not known yet).
- MANAGEMENT at every 1-minute close while in the trade (long coordinates; mirror for a short): best = the highest high
  of the bars since the entry; the stop level for the next minute is max(entry, best) - B, i.e. breakeven once the price
  has gone 1 B our way, then 1 B behind the best price. Equivalent to the lab's "breakeven at +1 B, trailing 1 B" (the
  trailing level is above the entry exactly when the breakeven condition holds). The rule asks the engine to tighten the
  server stop (MOVE_STOP); the engine never loosens it. If the last close is already through the new level, EXIT.
- TIME EXIT: 60 minutes after the entry (EXIT at the close of the bar that ends at entry + 60 min).
- FLATTEN 10 minutes before the close (engine). At most 4 entries per session: the demo config's
  risk.max_entries_per_day = 4 (the engine counts them), one position at a time.

Trade state (B, entry time) is kept by the rule instance when it sends the entry. After a restart while a trade is open,
B is taken from the latest signal of the position's side today at or before the entry (the bars hold it), the entry time
from that signal bar's close.

The research backtester cannot replay MOVE_STOP; the lab (b3/p026_lab.py) is the reference simulation, and
tests/b3/test_p032_rule.py checks that this rule's entries equal the lab's entries on the same bars.
"""

from __future__ import annotations

import math
from datetime import timedelta

import numpy as np
import pandas as pd

from b3.calendar import SessionRules
from b3.markets import ProxyStrategy
from b3.pattern_search import _same_minute_stat
from b3.strategy import ENTER_LONG, ENTER_SHORT, EXIT, HOLD, MOVE_STOP, bars_to_frame
from live.core.models import Signal

RULE_ID = "P-032"
EPS = 1e-9


class WinBoxFadeTrailing(ProxyStrategy):
    name = "P-032_win_box_fade_trailing"
    symbol = "WIN"
    timeframe_min = 1
    warmup = 12000       # 21 sessions of at most 555 one-minute bars (20 for the norm + today), plus margin
    rules = SessionRules(entry_start_after_open_min=15, entry_end_before_close_min=30, flatten_before_close_min=10)
    params = {
        "box_min": 120,
        "ratio_max": 0.8,
        "baseline_sessions": 20,
        "breakout_ticks": 1,
        "min_minutes_to_close_at_signal": 75,
        "stop_b": 1.0,
        "trail_b": 1.0,
        "hold_min": 60,
        "direction": "fade",
    }

    def __init__(self, calendar=None) -> None:
        super().__init__(calendar)
        self._trade: dict | None = None      # {"side", "b", "since"} of the entry this instance sent

    def indicators(self, df):
        p = self.params
        tick = self.market.tick_size
        n_box = int(round(p["box_min"] / self.timeframe_min))
        day = pd.factorize(df["local_date"])[0]
        high, low, close = (df[c].to_numpy(dtype=float) for c in ("high", "low", "close"))
        g = lambda x: pd.Series(x).groupby(day)                                          # noqa: E731
        hi = g(high).transform(lambda z: z.shift(1).rolling(n_box, min_periods=n_box).max()).to_numpy()
        lo = g(low).transform(lambda z: z.shift(1).rolling(n_box, min_periods=n_box).min()).to_numpy()
        prev_c = g(close).shift(1).to_numpy()
        r = (hi - lo) / prev_c
        norm = _same_minute_stat(r, day, df["minute_of_day"].to_numpy(), "median", p["baseline_sessions"])
        ratio = r / norm
        mtc = df["minutes_to_close"].to_numpy(dtype=float)
        ok = (ratio <= p["ratio_max"] + EPS) & (mtc >= p["min_minutes_to_close_at_signal"] - EPS)
        k = p["breakout_ticks"] * tick
        up = ok & (close >= hi + k - EPS)
        dn = ok & (close <= lo - k + EPS)
        d = up.astype(int) - dn.astype(int)
        df["bf_side"] = -d if p["direction"] == "fade" else d
        half = (hi - lo) / 2.0
        df["bf_b"] = np.where(np.isfinite(half), np.maximum(np.ceil(half / tick - 1e-9) * tick, tick), np.nan)
        return df

    # The live engine's entry point: the management needs the bars since the entry, not only the last row.
    def signal(self, bars, position):
        frame = self.prepare(bars_to_frame(bars))
        sig = self.decide_frame(frame, position)
        return sig

    def decide(self, row, position):          # entries only (the research backtester's path; no management there)
        if position is None:
            return self._entry(row)
        return Signal(HOLD)

    def _entry(self, row):
        side, b = int(row.bf_side), float(row.bf_b)
        if side == 0 or not math.isfinite(b):
            return Signal(HOLD)
        c = float(row.close)
        since = row.time + timedelta(minutes=self.timeframe_min)          # the signal bar's close = the fill time
        self._trade = {"side": side, "b": b, "since": since}
        if side > 0:
            return Signal(ENTER_LONG, stop_price=c - self.params["stop_b"] * b, reason="box_fade_long")
        return Signal(ENTER_SHORT, stop_price=c + self.params["stop_b"] * b, reason="box_fade_short")

    def _recover(self, frame, side):
        """After a restart: the latest signal of this side today (B and its close time)."""
        today = frame["local_date"].iloc[-1]
        before = frame.iloc[:-1]                                            # the current bar cannot be the entry
        f = before[(before["local_date"] == today) & (before["bf_side"] == side)]
        if not len(f):
            return None
        r = f.iloc[-1]
        return {"side": side, "b": float(r["bf_b"]), "since": r["time"] + timedelta(minutes=self.timeframe_min)}

    def decide_frame(self, frame, position):
        row = next(frame.tail(1).itertuples(index=False, name="Row"))
        if position is None or not position.volume:
            self._trade = None
            return self._entry(row)
        side = 1 if position.volume > 0 else -1
        tr = self._trade if self._trade and self._trade["side"] == side else self._recover(frame, side)
        if tr is None:
            return Signal(HOLD, reason="open position without a known signal: server stop and engine flatten only")
        self._trade = tr
        tf = timedelta(minutes=self.timeframe_min)
        bar_close = row.time + tf
        if bar_close >= tr["since"] + timedelta(minutes=self.params["hold_min"]):
            return Signal(EXIT, reason="time_exit_60_min")
        held = frame[frame["time"] >= tr["since"]]                          # bars from the entry minute on
        if not len(held):
            return Signal(HOLD)
        e, b, trail = float(position.entry_price), tr["b"], self.params["trail_b"] * tr["b"]
        if side > 0:
            level = max(e, float(held["high"].max())) - trail
            level = max(level, e - self.params["stop_b"] * b)
            if float(row.close) <= level:
                return Signal(EXIT, reason="trail_through")
            cur = position.stop_loss
            if cur is None or level > cur + EPS:
                return Signal(MOVE_STOP, stop_price=float(level), reason="breakeven_trailing")
        else:
            level = min(e, float(held["low"].min())) + trail
            level = min(level, e + self.params["stop_b"] * b)
            if float(row.close) >= level:
                return Signal(EXIT, reason="trail_through")
            cur = position.stop_loss
            if cur is None or level < cur - EPS:
                return Signal(MOVE_STOP, stop_price=float(level), reason="breakeven_trailing")
        return Signal(HOLD)
