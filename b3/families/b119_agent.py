"""Conveyor batch B-119 (agent, 2026-11-24). Mixed themes: regime switch, seasonality, absorption, volatility expansion, volume climax, wick accumulation, acceleration, lunch box, persistence, aged-extreme stop runs."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _d(long, short, ctx):
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _autocorr_regime(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    num = ctx.roll(r * ctx.prev(r, 1), nb, "mean")
    den = ctx.roll(r * r, nb, "mean")
    rho = num / np.where(den > 0, den, np.nan)
    big = np.abs(r) > ctx.roll(np.abs(r), nb, "mean")
    mr = (rho < -th) & big
    tr = (rho > th) & big
    long = (mr & (r < 0)) | (tr & (r > 0))
    short = (mr & (r > 0)) | (tr & (r < 0))
    return _d(long, short, ctx)


def _clock_drift(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    fwd = (pd.Series(ctx.c).groupby(ctx.day).shift(-nb) / ctx.c - 1.0).to_numpy()
    m = ctx.same_minute(fwd, "mean")
    a = ctx.same_minute(np.abs(fwd), "mean")
    return _d(m > k * a, m < -k * a, ctx)


def _absorption(ctx, p):
    nb, vk = ctx.bars(p["move_min"]), p["vol_k"]
    rng = ctx.h - ctx.l
    vmed = ctx.same_minute(ctx.v, "median")
    rmed = ctx.same_minute(rng, "median")
    move = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    typ = ctx.cached(("absmove", nb), lambda: ctx.prev_sessions(np.abs(move), "mean"))
    absorb = (ctx.v >= vk * vmed) & (rng <= 0.7 * rmed)
    short = absorb & (move >= typ)
    long = absorb & (move <= -typ)
    return _d(long, short, ctx)


def _vol_expansion(ctx, p):
    k = p["k"]
    nf, ns = ctx.bars(p["fast_min"]), ctx.bars(60)
    rng = ctx.h - ctx.l
    fast = ctx.roll(rng, nf, "mean")
    slow = ctx.roll(rng, ns, "mean")
    on = fast > k * slow
    dirn = np.sign(ctx.c - ctx.prev(ctx.c, nf))
    return _d(on & (dirn > 0), on & (dirn < 0), ctx)


def _climax_fade(ctx, p):
    nb, mn = ctx.bars(p["lookback_min"]), ctx.bars(p["min_min"])
    pm = pd.Series(ctx.v).groupby(ctx.day).transform(lambda z: z.cummax().shift(1)).to_numpy()
    climax = (ctx.v > pm) & (ctx.bar_in_day >= mn)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    short = climax & (ctx.h > hi)
    long = climax & (ctx.l < lo)
    return long.astype(int) - short.astype(int)


def _wick_accum(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    rng = ctx.h - ctx.l
    up = ctx.h - np.maximum(ctx.o, ctx.c)
    lo = np.minimum(ctx.o, ctx.c) - ctx.l
    w = np.where(rng > 0, (lo - up) / np.where(rng > 0, rng, 1.0), 0.0)
    m = ctx.roll(w, nb, "mean")
    return _d(m > th, m < -th, ctx)


def _accel(ctx, p):
    nb, k = ctx.bars(p["move_min"]), p["k"]
    m1 = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    m0 = ctx.prev(ctx.c, nb) / ctx.prev(ctx.c, 2 * nb) - 1.0
    typ = ctx.cached(("absmove", nb), lambda: ctx.prev_sessions(np.abs(m1), "mean"))
    long = (m1 >= k * typ) & (m0 > 0) & (m1 > 2 * m0)
    short = (m1 <= -k * typ) & (m0 < 0) & (m1 < 2 * m0)
    return _d(long, short, ctx)


def _lunch_box(ctx, p):
    L = int(p["box_min"])
    start, end = 13 * 60 - L, 13 * 60
    inbox = (ctx.minute >= start) & (ctx.minute < end)
    g = pd.DataFrame({"d": ctx.day, "h": np.where(inbox, ctx.h, np.nan), "l": np.where(inbox, ctx.l, np.nan)})
    bh = g.groupby("d")["h"].transform("max").to_numpy()
    bl = g.groupby("d")["l"].transform("min").to_numpy()
    act = (ctx.minute >= end) & (ctx.minute < 15 * 60)
    return _d(act & (ctx.c > bh), act & (ctx.c < bl), ctx)


def _persistent_extremes(ctx, p):
    nb, m = ctx.bars(p["win_min"]), p["m"]
    nh = (ctx.h > ctx.session_high()).astype(float)
    nl = (ctx.l < ctx.session_low()).astype(float)
    ch = ctx.roll(nh, nb, "sum")
    cl = ctx.roll(nl, nb, "sum")
    return _d((ch >= m) & (cl == 0), (cl >= m) & (ch == 0), ctx)


def _aged_extreme_run(ctx, p):
    nb, age = ctx.bars(p["lookback_min"]), ctx.bars(p["age_min"])
    hi_old = ctx.prev(ctx.roll(ctx.h, nb, "max"), age)
    lo_old = ctx.prev(ctx.roll(ctx.l, nb, "min"), age)
    rec_h = ctx.roll(ctx.h, age, "max", include_current=False)
    rec_l = ctx.roll(ctx.l, age, "min", include_current=False)
    short = (ctx.h > hi_old) & (rec_h <= hi_old) & (ctx.c < hi_old)
    long = (ctx.l < lo_old) & (rec_l >= lo_old) & (ctx.c > lo_old)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-1188", "Autocorrelation regime switch",
           "When the rolling lag-1 return autocorrelation is strongly negative, bars are bid-ask bounce and a large bar is "
           "faded; when strongly positive, orders are being sliced into the market and a large bar is followed.",
           {"win_min": [30, 60, 90], "th": [0.15, 0.25, 0.35]}, _autocorr_regime,
           source="assistant reasoning", author="agent"),
    Family("E-1189", "Same-clock forward drift",
           "Some clock windows (macro releases, NY open, fund rebalancing) drift the same way in most recent sessions; "
           "trade in the direction of the average forward move that followed this minute in the last 20 sessions.",
           {"win_min": [15, 30, 60], "k": [0.2, 0.3, 0.4]}, _clock_drift,
           source="assistant reasoning (intraday time-of-day seasonality)", author="agent"),
    Family("E-1190", "Volume absorption after a move",
           "A high-volume bar with a tiny range after a run means passive limit orders absorbed the aggressors; "
           "the run is exhausted so fade it.",
           {"move_min": [10, 20, 30], "vol_k": [1.5, 2.0, 3.0]}, _absorption,
           source="assistant reasoning (effort versus result, volume-spread analysis)", author="agent"),
    Family("E-1191", "Fast/slow range expansion start",
           "When the short-term average bar range jumps above the one-hour average, a volatility regime begins "
           "and the move that triggered it tends to continue as stops and momentum orders arrive.",
           {"k": [1.5, 2.0, 2.5], "fast_min": [5, 10]}, _vol_expansion,
           source="assistant reasoning", author="agent"),
    Family("E-1192", "Session-volume-climax extreme fade",
           "The highest-volume bar of the session printing at a fresh local extreme is capitulation or "
           "blow-off; late participants are trapped, so fade the extreme.",
           {"lookback_min": [20, 40, 60], "min_min": [60, 90]}, _climax_fade,
           source="assistant reasoning (volume climax)", author="agent"),
    Family("E-1193", "Wick-imbalance accumulation",
           "Several recent bars with long lower wicks and short upper wicks show repeated rejection of lower prices by "
           "patient buyers; buy (and the mirror for sellers) when the rolling wick imbalance gets large.",
           {"win_min": [15, 30, 60], "th": [0.2, 0.3, 0.4]}, _wick_accum,
           source="assistant reasoning", author="agent"),
    Family("E-1194", "Momentum acceleration",
           "A move that is not only large but at least twice as fast as the preceding equal window shows urgency "
           "(forced flow), which continues for a few more bars.",
           {"move_min": [5, 10, 20], "k": [1.0, 1.5]}, _accel,
           source="assistant reasoning", author="agent"),
    Family("E-1195", "Lunch-box breakout",
           "The thin lunch period builds a box; the first close beyond it after 13:00 comes with returning "
           "liquidity and positioning for the afternoon, so follow it.",
           {"box_min": [30, 60, 90]}, _lunch_box,
           source="assistant reasoning (intraday liquidity cycle)", author="agent", markets=("WIN",)),
    Family("E-1196", "Persistent new-extreme making",
           "When many of the recent bars each set a new session high with no new low, buyers are lifting every offer "
           "in sequence; the persistent pressure carries on.",
           {"win_min": [30, 60, 90], "m": [3, 4, 5]}, _persistent_extremes,
           source="assistant reasoning", author="agent"),
    Family("E-1197", "Aged-extreme stop run (Turtle Soup)",
           "A swing extreme untouched for several bars collects resting stops beyond it; a poke through it that closes "
           "back inside is a stop run with no follow-through, so fade it.",
           {"lookback_min": [20, 30, 60], "age_min": [5, 10]}, _aged_extreme_run,
           source="Linda Raschke Turtle Soup (assistant reasoning)", author="agent"),
]
