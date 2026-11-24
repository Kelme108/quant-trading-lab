"""Conveyor batch B-077 (agent, 2026-11-23). Mixed themes: time-of-day drift, day-open, volume dryness, impulse retrace, VWAP slope, stairs."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _tod_drift(ctx, p):
    z = p["z"]
    nxt = np.zeros(ctx.n)
    same = ctx.day[1:] == ctx.day[:-1]
    nxt[:-1] = np.where(same, ctx.c[1:] / ctx.c[:-1] - 1.0, 0.0)
    m = ctx.cached("tod_m", lambda: ctx.same_minute(nxt, "mean"))
    m2 = ctx.cached("tod_m2", lambda: ctx.same_minute(nxt ** 2, "mean"))
    sd = np.sqrt(np.maximum(m2 - m ** 2, 1e-18))
    t = m / (sd / np.sqrt(20.0))
    return ctx.cross(t > z).astype(int) - ctx.cross(t < -z).astype(int)


def _open_recross(ctx, p):
    nb = ctx.bars(p["away_min"])
    below = (ctx.c < ctx.day_open).astype(float)
    above = (ctx.c > ctx.day_open).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    up = was_below & (ctx.c > ctx.day_open)
    dn = was_above & (ctx.c < ctx.day_open)
    return up.astype(int) - dn.astype(int)


def _dry_extreme(ctx, p):
    k = p["vol_k"]
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    dry = ctx.v < k * med
    newhi = ctx.h > ctx.session_high(False)
    newlo = ctx.l < ctx.session_low(False)
    short = newhi & dry & ~newlo
    long = newlo & dry & ~newhi
    return long.astype(int) - short.astype(int)


def _impulse_half_retrace(ctx, p):
    k = p["k"]
    rng = ctx.h - ctx.l
    typical = ctx.cached("rng_typ", lambda: ctx.prev_sessions(rng, "mean"))
    o1, c1 = ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1)
    body = c1 - o1
    mid = (o1 + c1) / 2.0
    big = np.abs(body) >= k * typical
    long = big & (body > 0) & (ctx.l <= mid) & (ctx.c > mid)
    short = big & (body < 0) & (ctx.h >= mid) & (ctx.c < mid)
    return long.astype(int) - short.astype(int)


def _vwap_slope_pullback(ctx, p):
    nb = ctx.bars(p["slope_min"])
    k = p["k"]
    vw = ctx.vwap()
    slope = vw - ctx.prev(vw, nb)
    mv = np.abs(ctx.c - ctx.prev(ctx.c, nb))
    typical = ctx.cached(("abs_mv", nb), lambda: ctx.prev_sessions(mv, "mean"))
    long = (slope >= k * typical) & (ctx.l <= vw) & (ctx.c > vw)
    short = (slope <= -k * typical) & (ctx.h >= vw) & (ctx.c < vw)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _accel_bodies(ctx, p):
    n, g = int(p["n"]), p["growth"]
    body = ctx.c - ctx.o
    ok_up = body > 0
    ok_dn = body < 0
    for i in range(1, n):
        bi, bj = ctx.prev(body, i - 1) if i > 1 else body, ctx.prev(body, i)
        ok_up = ok_up & (bi > 0) & (bj > 0) & (np.abs(bi) >= g * np.abs(bj))
        ok_dn = ok_dn & (bi < 0) & (bj < 0) & (np.abs(bi) >= g * np.abs(bj))
    return ctx.cross(ok_up).astype(int) - ctx.cross(ok_dn).astype(int)


def _prev_close_bias(ctx, p):
    q = p["q"]
    ph, pl, pc = ctx.prev_session_value("high"), ctx.prev_session_value("low"), ctx.prev_session_value("close")
    pos = (pc - pl) / np.where(ph > pl, ph - pl, np.nan)
    early = ctx.minute < 12 * 60
    long = (pos >= 1 - q) & early & (ctx.c > pc)
    short = (pos <= q) & early & (ctx.c < pc)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _hour_range_break(ctx, p):
    rm = p["rng_min"]
    hid = ctx.day.astype(np.int64) * 24 + (ctx.minute // 60)
    first = (ctx.minute % 60) < rm
    g = pd.DataFrame({"k": hid, "h": np.where(first, ctx.h, np.nan), "l": np.where(first, ctx.l, np.nan)})
    hh = g.groupby("k")["h"].transform("max").to_numpy()
    ll = g.groupby("k")["l"].transform("min").to_numpy()
    after = ~first
    up = after & (ctx.c > hh)
    dn = after & (ctx.c < ll)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _stall_after_run(ctx, p):
    nb = ctx.bars(p["move_min"])
    f = p["stall"]
    rng = ctx.h - ctx.l
    run = ctx.prev(ctx.c, 1) - ctx.prev(ctx.c, nb + 1)
    typical = ctx.cached(("run_typ", nb), lambda: ctx.prev_sessions(np.abs(ctx.c - ctx.prev(ctx.c, nb)), "mean"))
    avg = ctx.roll(rng, nb, "mean", include_current=False)
    stall = (rng <= f * avg) & (avg > 0)
    short = stall & (run >= typical)
    long = stall & (run <= -typical)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _stairs(ctx, p):
    n = int(p["n"])
    up = np.ones(ctx.n, bool)
    dn = np.ones(ctx.n, bool)
    for i in range(n):
        hi_a = ctx.h if i == 0 else ctx.prev(ctx.h, i)
        lo_a = ctx.l if i == 0 else ctx.prev(ctx.l, i)
        hi_b, lo_b = ctx.prev(ctx.h, i + 1), ctx.prev(ctx.l, i + 1)
        up = up & (hi_a > hi_b) & (lo_a > lo_b)
        dn = dn & (hi_a < hi_b) & (lo_a < lo_b)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


FAMILIES = [
    Family("E-768", "Time-of-day drift persistence",
           "At a given minute of the day the next bar has leaned the same way on most of the last 20 sessions "
           "(scheduled flows: fixings, futures-roll hedges, foreign desks); trade the lean when its t-stat is high.",
           {"z": [1.5, 2.0, 2.5]}, _tod_drift, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-769", "Day-open recross follow",
           "After the price spends a while on one side of the session open, a close back across it flips the "
           "day's winners and losers; follow the cross.",
           {"away_min": [15, 30, 60]}, _open_recross, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-770", "Dry-volume new extreme fade",
           "A new session high/low printed on well below usual volume has no real participation behind it; fade it.",
           {"vol_k": [0.5, 0.75, 1.0]}, _dry_extreme, markets=("WIN",), source="volume-price analysis (assistant reasoning)",
           author="agent"),
    Family("E-771", "Impulse bar half-retrace resume",
           "After an unusually large bar, a pullback to its midpoint that closes back past it shows the impulse "
           "holders are still in control; resume in the impulse direction.",
           {"k": [1.5, 2.0, 3.0]}, _impulse_half_retrace, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-772", "Sloping-VWAP pullback",
           "When the session VWAP itself is clearly rising or falling, institutional average-price buyers/sellers "
           "defend it; the first touch that closes back on the trend side is a continuation entry.",
           {"slope_min": [15, 30], "k": [0.5, 1.0]}, _vwap_slope_pullback, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-773", "Accelerating-body momentum",
           "Consecutive same-colour bars with growing bodies show urgency that has not yet been met by "
           "opposing flow; follow the acceleration.",
           {"n": [3, 4], "growth": [1.0, 1.2]}, _accel_bodies, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-774", "Prior-close location bias",
           "A day that closed in the top (bottom) of its range leaves overnight/opening bias in that direction; in "
           "the morning, a cross of the prior close in that direction is followed.",
           {"q": [0.2, 0.25, 0.33]}, _prev_close_bias, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-775", "Hourly opening-range break",
           "Order flow resets on the hour (scheduled data, desk shifts); a close beyond the first minutes' range "
           "of the hour is followed.",
           {"rng_min": [10, 15, 20]}, _hour_range_break, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-776", "Stall bar after a run fade",
           "After a run, a bar with a much smaller range than the recent average shows the aggressive side has "
           "run out of fuel; fade the run.",
           {"move_min": [15, 30], "stall": [0.4, 0.6, 0.8]}, _stall_after_run, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-777", "Higher-high higher-low staircase",
           "A staircase of N bars each making both a higher high and a higher low (or lower/lower) is an orderly "
           "trend with no overlap for counter-traders; follow it.",
           {"n": [3, 4, 5]}, _stairs, markets=("WIN",), source="assistant reasoning", author="agent"),
]
