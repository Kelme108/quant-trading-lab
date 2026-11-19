"""Conveyor batch B-024 (agent, 2026-11-18). Mixed WIN ideas: multi-session calm and overlap regimes, previous-block
midpoints, stair-step break exhaustion, wicked break bars, filled opening gaps, outside hours, VWAP-contested
sessions, clock-hour range quotas and developing doji days."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


# ---------------------------------------------------------------------------------------------
# shared helpers (all causal, session-bounded; cross-session stats use completed sessions only)
# ---------------------------------------------------------------------------------------------

def _rng_med(ctx):
    return ctx.cached("b024_rng_med", lambda: ctx.same_minute(ctx.h - ctx.l, "median"))


def _micro(ctx, win_min):
    nb = ctx.bars(win_min)
    hi = ctx.cached(("b024_hi", nb), lambda: ctx.roll(ctx.h, nb, "max", include_current=False))
    lo = ctx.cached(("b024_lo", nb), lambda: ctx.roll(ctx.l, nb, "min", include_current=False))
    up = ctx.cross(ctx.c > hi)
    dn = ctx.cross(ctx.c < lo)
    return hi, lo, up, dn


def _sessions(ctx):
    """Per-session high, low, open, close (index = session number); the current session is never used for itself."""
    def build():
        df = pd.DataFrame({"d": ctx.day, "h": ctx.h, "l": ctx.l, "o": ctx.o, "c": ctx.c})
        g = df.groupby("d")
        per = pd.DataFrame({"h": g["h"].max(), "l": g["l"].min(), "o": g["o"].first(), "c": g["c"].last()})
        return per.reindex(range(int(ctx.day.max()) + 1))
    return ctx.cached("b024_sessions", build)


def _to_bars(ctx, per_session: pd.Series) -> np.ndarray:
    return per_session.to_numpy()[ctx.day]


def _prev_block(ctx, block_min):
    """High and low of the previous completed clock block (same session) on every bar."""
    def build():
        blk = (ctx.minute // int(block_min)).astype(int)
        df = pd.DataFrame({"d": ctx.day, "b": blk, "h": ctx.h, "l": ctx.l})
        agg = df.groupby(["d", "b"]).agg(hi=("h", "max"), lo=("l", "min"))
        prev = agg.groupby(level=0).shift(1)
        idx = pd.MultiIndex.from_arrays([ctx.day, blk])
        p = prev.reindex(idx)
        return p["hi"].to_numpy(float), p["lo"].to_numpy(float), blk
    return ctx.cached(("b024_prev_block", int(block_min)), build)


def _running_block(ctx, block_min):
    """Running high and low of the current clock block, including the current bar."""
    def build():
        blk = (ctx.minute // int(block_min)).astype(int)
        df = pd.DataFrame({"d": ctx.day, "b": blk, "h": ctx.h, "l": ctx.l})
        g = df.groupby(["d", "b"])
        return g["h"].cummax().to_numpy(float), g["l"].cummin().to_numpy(float), blk
    return ctx.cached(("b024_run_block", int(block_min)), build)


# ---------------------------------------------------------------------------------------------
# families
# ---------------------------------------------------------------------------------------------

def _calm_week_fade(ctx, p):
    per = _sessions(ctx)
    r = per["h"] - per["l"]
    short_m = r.shift(1).rolling(5, min_periods=5).mean()
    long_m = r.shift(1).rolling(20, min_periods=20).mean()
    ratio = _to_bars(ctx, short_m / long_m)
    calm = ratio < p["q"]
    _, _, up, dn = _micro(ctx, p["win_min"])
    return (dn & calm).astype(int) - (up & calm).astype(int)


def _prev_block_mid(ctx, p):
    B = int(p["block_min"])
    hi, lo, _ = _prev_block(ctx, B)
    mid = (hi + lo) / 2.0
    need = p["k"] * _rng_med(ctx) * np.sqrt(ctx.bars(B))
    wide = (hi - lo) >= need
    pc = ctx.prev(ctx.c, 1)
    long = wide & (pc > mid) & (ctx.l <= mid) & (ctx.c > mid)
    short = wide & (pc < mid) & (ctx.h >= mid) & (ctx.c < mid)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _stair_step_fade(ctx, p):
    nb = ctx.bars(p["win_min"])
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    bu = (ctx.c > hi)
    bd = (ctx.c < lo)
    W = ctx.bars(30)
    cu = ctx.roll(bu.astype(float), W, "sum")
    cd = ctx.roll(bd.astype(float), W, "sum")
    n = p["n"]
    short = ctx.cross((cu >= n) & (cd == 0)) & bu
    long = ctx.cross((cd >= n) & (cu == 0)) & bd
    return long.astype(int) - short.astype(int)


def _wicked_break_fade(ctx, p):
    _, _, up, dn = _micro(ctx, p["win_min"])
    rng = ctx.h - ctx.l
    ok = rng > 0
    w = p["wick"]
    short = up & ok & ((ctx.h - ctx.c) >= w * rng)
    long = dn & ok & ((ctx.c - ctx.l) >= w * rng)
    return long.astype(int) - short.astype(int)


def _overlap_balance_fade(ctx, p):
    per = _sessions(ctx)
    h1, l1 = per["h"].shift(1), per["l"].shift(1)
    h2, l2 = per["h"].shift(2), per["l"].shift(2)
    inter = np.minimum(h1, h2) - np.maximum(l1, l2)
    union = np.maximum(h1, h2) - np.minimum(l1, l2)
    ov = _to_bars(ctx, inter / union.where(union > 0))
    bal = ov >= p["th"]
    _, _, up, dn = _micro(ctx, p["win_min"])
    return (dn & bal).astype(int) - (up & bal).astype(int)


def _filled_gap_fade(ctx, p):
    per = _sessions(ctx)
    gap = per["o"] - per["c"].shift(1)
    typ = gap.abs().shift(1).rolling(15, min_periods=15).mean()
    g = _to_bars(ctx, gap)
    t = _to_bars(ctx, typ)
    pc = ctx.prev_session_value("close")
    big = np.abs(g) >= p["k"] * t
    lo_run = ctx.session_low(include_current=True)
    hi_run = ctx.session_high(include_current=True)
    filled = big & (((g > 0) & (lo_run <= pc)) | ((g < 0) & (hi_run >= pc)))
    _, _, up, dn = _micro(ctx, p["win_min"])
    return (dn & filled).astype(int) - (up & filled).astype(int)


def _outside_block_fade(ctx, p):
    B = int(p["block_min"])
    phi, plo, _ = _prev_block(ctx, B)
    chi, clo, _ = _running_block(ctx, B)
    outside = (chi > phi) & (clo < plo)
    _, _, up, dn = _micro(ctx, p["win_min"])
    return (dn & outside).astype(int) - (up & outside).astype(int)


def _contested_vwap_fade(ctx, p):
    vw = ctx.vwap()
    s = np.sign(ctx.c - vw)
    ps_ = ctx.prev(s, 1)
    crossed = (s != 0) & (ps_ != 0) & (s != ps_) & ~np.isnan(ps_)
    cnt = ctx.roll(crossed.astype(float), ctx.bars(120), "sum")
    contested = cnt >= p["n"]
    _, _, up, dn = _micro(ctx, p["win_min"])
    return (dn & contested).astype(int) - (up & contested).astype(int)


def _hour_quota_fade(ctx, p):
    chi, clo, hr = _running_block(ctx, 60)

    def typical():
        df = pd.DataFrame({"d": ctx.day, "b": hr, "h": ctx.h, "l": ctx.l})
        agg = df.groupby(["d", "b"]).agg(hi=("h", "max"), lo=("l", "min"))
        rng = (agg["hi"] - agg["lo"]).unstack(level=1)
        rng = rng.reindex(range(int(ctx.day.max()) + 1))
        typ = rng.shift(1).rolling(20, min_periods=10).mean()
        st = typ.stack()
        return st.reindex(pd.MultiIndex.from_arrays([ctx.day, hr])).to_numpy(float)

    typ = ctx.cached("b024_hour_typ", typical)
    reach = ctx.cross((chi - clo) >= p["k"] * typ)
    short = reach & (ctx.h >= chi)
    long = reach & (ctx.l <= clo)
    return long.astype(int) - short.astype(int)


def _doji_day_fade(ctx, p):
    first = pd.Series(ctx.minute).groupby(ctx.day).transform("first").to_numpy()
    elapsed = ctx.minute - first
    hi = ctx.session_high(include_current=True)
    lo = ctx.session_low(include_current=True)
    rng = hi - lo
    body = np.abs(ctx.c - ctx.day_open)
    doji = (elapsed >= 90) & (rng > 0) & (body <= p["th"] * rng)
    _, _, up, dn = _micro(ctx, p["win_min"])
    return (dn & doji).astype(int) - (up & doji).astype(int)


FAMILIES = [
    Family("E-238", "Calm-week micro-break fade",
           "When the last 5 sessions' average range is well below the 20-session average, the multi-day volatility "
           "regime is calm: dealers carry small inventories, no macro repositioning is under way and day traders cut "
           "their range expectations; a close beyond the recent high/low in such a week is a small push through "
           "quotes that liquidity providers lean back on, so fade it.",
           {"q": [0.7, 0.85, 1.0], "win_min": [10, 15, 30]}, _calm_week_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-239", "Previous-block midpoint rejection",
           "The 50% level of the last completed 15/30/60-minute candle is where chart traders reading that timeframe "
           "split the candle into buyers' and sellers' halves and rest their re-entries; a bar that comes back to it "
           "from one side and closes back on that side shows those orders absorbing the pullback, so trade away "
           "from the midpoint (only when the block was wide enough to matter).",
           {"block_min": [15, 30, 60], "k": [0.5, 1.0, 1.5]}, _prev_block_mid, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-240", "Stair-step break exhaustion fade",
           "Several closes above the short-term high within half an hour with no opposite break is a stair-step of "
           "small breakout entries; each step adds late buyers with stops just below, and once the count is high the "
           "breakout pool is used up and their stops sit close, so fade the bar where the count is reached (mirror).",
           {"n": [3, 4, 5], "win_min": [5, 10, 15]}, _stair_step_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-241", "Wicked break-bar fade",
           "A bar that closes above the recent high but leaves a large upper wick traded well beyond the level and was "
           "already sold back inside the same bar: sellers met the breakout at the new prices and the buyers who "
           "bought the bar's high are under water at once; fade the break (mirror for lows).",
           {"wick": [0.3, 0.45, 0.6], "win_min": [10, 15, 30]}, _wicked_break_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-242", "Multi-day overlap balance micro-break fade",
           "When yesterday's range overlapped most of the day before's, the market has accepted the same price zone "
           "for two sessions (multi-day balance): swing traders sell its top and buy its bottom and nobody initiates; "
           "today's short-term breaks inside that regime lack an initiator and are faded.",
           {"th": [0.4, 0.55, 0.7], "win_min": [10, 15, 30]}, _overlap_balance_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-243", "Gap-filled day micro-break fade",
           "Once an opening gap of meaningful size has been fully filled back to yesterday's close, local traders have "
           "reversed the overnight information and the session is run by responsive liquidity providers rather than "
           "by an overnight initiator; from then on short-term breaks are faded.",
           {"k": [0.0, 0.5, 1.0], "win_min": [10, 15, 30]}, _filled_gap_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-244", "Outside-block micro-break fade",
           "When the current clock block (30/60/120 minutes) has already traded beyond both the high and the low of "
           "the previous block, the stop pools on both sides of that candle are spent and the block is rotating "
           "two-way; a further short-term break inside such an outside block has no fresh stops to run and is faded.",
           {"block_min": [30, 60, 120], "win_min": [5, 10, 15]}, _outside_block_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-245", "VWAP-contested session micro-break fade",
           "Many closes crossing the session VWAP over the last two hours mean neither side can hold price away from "
           "the day's average cost: value is contested and both camps trade responsively around it; a short-term "
           "break in that state is absorbed by the other camp, so fade it.",
           {"n": [3, 5, 8], "win_min": [10, 15, 30]}, _contested_vwap_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-246", "Clock-hour range quota fade",
           "Short-term traders size targets on what a clock hour usually covers; when the current hour's range first "
           "reaches its 20-session typical range for that hour, the bar that set the new hour extreme is where their "
           "take-profits sit and the hour's directional flow is spent, so fade that bar.",
           {"k": [0.8, 1.0, 1.2]}, _hour_quota_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-247", "Developing doji-day micro-break fade",
           "After the first 90 minutes, a session whose price is back near its open despite a real range is drawing a "
           "doji on every daily chart: both sides tried and were rejected, and the day is being traded responsively; "
           "short-term breaks in that state lack an initiator and are faded.",
           {"th": [0.15, 0.25, 0.35], "win_min": [10, 15, 30]}, _doji_day_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
