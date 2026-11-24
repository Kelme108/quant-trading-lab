"""Conveyor batch B-141 (agent, 2026-11-24). Mixed bag: round numbers, squeezes, dollar lead, autocorrelation regime, bar gaps, volume ramps."""
from __future__ import annotations

import numpy as np
from b3.esteira import Family


def _round_number_fade(ctx, p):
    step = float(p["step"])
    pc = ctx.prev(ctx.c, 1)
    up_lvl = np.ceil(pc / step) * step
    dn_lvl = np.floor(pc / step) * step
    short = (ctx.h >= up_lvl) & (ctx.c < up_lvl) & (pc < up_lvl)
    long = (ctx.l <= dn_lvl) & (ctx.c > dn_lvl) & (pc > dn_lvl)
    return long.astype(int) - short.astype(int)


def _squeeze_release(ctx, p):
    nb = ctx.bars(p["win_min"])
    k = p["k"]
    w = ctx.roll(ctx.c, nb, "std") / ctx.c
    typ = ctx.cached(("w_typ", nb), lambda: ctx.same_minute(w, "median"))
    sq = (w < k * typ).astype(float)
    sq_prev = ctx.prev(sq, 1) == 1
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    up = sq_prev & (ctx.c > hi)
    dn = sq_prev & (ctx.c < lo)
    return up.astype(int) - dn.astype(int)


def _dollar_lead(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    oc = ctx.other_close()
    mx = ctx.roll(oc, nb, "max", include_current=False)
    mn = ctx.roll(oc, nb, "min", include_current=False)
    dollar_up = ctx.cross(oc > mx)
    dollar_dn = ctx.cross(oc < mn)
    return dollar_dn.astype(int) - dollar_up.astype(int)


def _widest_bar_follow(ctx, p):
    nb = max(ctx.bars(p["lookback_min"]), 5)
    rng = ctx.h - ctx.l
    mx = ctx.roll(rng, nb, "max", include_current=False)
    wide = rng > mx
    strong_up = (ctx.c - ctx.l) >= 0.75 * rng
    strong_dn = (ctx.h - ctx.c) >= 0.75 * rng
    return (wide & strong_up).astype(int) - (wide & strong_dn).astype(int)


def _bar_gap_fade(ctx, p):
    g = p["gap_frac"]
    pc = ctx.prev(ctx.c, 1)
    gap = ctx.o / pc - 1.0
    short = gap >= g
    long = gap <= -g
    return long.astype(int) - short.astype(int)


def _range_mid_cross(ctx, p):
    nb = ctx.bars(p["win_min"])
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    mid = (hi + lo) / 2.0
    wide = (hi - lo) > p["min_width_frac"] * ctx.c
    up = ctx.cross((ctx.c > mid) & wide)
    dn = ctx.cross((ctx.c < mid) & wide)
    return up.astype(int) - dn.astype(int)


def _volume_ramp(ctx, p):
    m, k = int(p["m"]), p["vol_k"]
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    up = np.ones(ctx.n, bool)
    dn = np.ones(ctx.n, bool)
    for i in range(m):
        ci, cp = ctx.prev(ctx.c, i), ctx.prev(ctx.c, i + 1)
        vi, vp = ctx.prev(ctx.v, i), ctx.prev(ctx.v, i + 1)
        up &= (ci > cp) & (vi > vp)
        dn &= (ci < cp) & (vi > vp)
    big = ctx.v >= k * med
    return ctx.cross(up & big).astype(int) - ctx.cross(dn & big).astype(int)


def _autocorr_regime(ctx, p):
    nb = ctx.bars(p["win_min"])
    thr = p["thr"]
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    r1 = ctx.prev(r, 1)
    ac = ctx.roll(r * r1, nb, "mean") / ctx.roll(r * r, nb, "mean")
    big = np.abs(r) > ctx.roll(np.abs(r), nb, "mean")
    sgn = np.sign(r)
    follow = (ac > thr) & big
    fade = (ac < -thr) & big
    long = (follow & (sgn > 0)) | (fade & (sgn < 0))
    short = (follow & (sgn < 0)) | (fade & (sgn > 0))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _prev_close_hold(ctx, p):
    nb = ctx.bars(p["away_min"])
    pcl = ctx.prev_session_value("close")
    below = (ctx.c < pcl).astype(float)
    above = (ctx.c > pcl).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    up = was_below & (ctx.c > pcl)
    dn = was_above & (ctx.c < pcl)
    return up.astype(int) - dn.astype(int)


def _volume_shock_fade(ctx, p):
    k = p["vol_k"]
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    rng = ctx.h - ctx.l
    typ = ctx.cached("rng_typ", lambda: ctx.same_minute(rng, "median"))
    shock = (ctx.v >= k * med) & (rng >= typ) & (rng > 0)
    body_up = (ctx.c - ctx.o) >= 0.6 * rng
    body_dn = (ctx.o - ctx.c) >= 0.6 * rng
    short = shock & body_up
    long = shock & body_dn
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-1408", "Round-number poke rejection",
           "Index points ending in round hundreds attract resting orders; a bar that pokes through the next round level and closes back is a failed push through a crowded level, fade it.",
           {"step": [250, 500, 1000]}, _round_number_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1409", "Volatility squeeze release",
           "When recent close dispersion is far below its usual level for the time of day, energy is stored; the first close beyond the window's extreme releases it in that direction.",
           {"win_min": [20, 30, 45], "k": [0.5, 0.7, 0.9]}, _squeeze_release,
           source="assistant reasoning (Bollinger squeeze idea)", author="agent"),
    Family("E-1410", "Dollar new-extreme lead (inverse)",
           "WIN trades inversely to the dollar; when WDO makes a new rolling high/low, hedgers and macro desks reprice the index a moment later; trade WIN the other way.",
           {"lookback_min": [15, 30, 60]}, _dollar_lead, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1411", "Widest-bar close-strength follow",
           "A bar whose range exceeds every range of the last window and closes in its extreme quarter shows an aggressive side overwhelming the book; follow it.",
           {"lookback_min": [15, 30, 60]}, _widest_bar_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1412", "Bar-open gap fade",
           "A bar opening away from the prior close reflects a burst of market orders sweeping the book; the book refills and price tends to drift back to the prior close.",
           {"gap_frac": [0.0003, 0.0005, 0.0008]}, _bar_gap_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1413", "Rolling range midpoint cross",
           "The midpoint of the recent range is the fair-value line of the window; a close crossing it in a range of meaningful width signals a shift of balance toward that side.",
           {"win_min": [30, 60, 120], "min_width_frac": [0.002, 0.004]}, _range_mid_cross, markets=("WIN",),
           source="assistant reasoning (Donchian midline)", author="agent"),
    Family("E-1414", "Volume-confirmed bar run",
           "Consecutive bars closing in one direction while each bar's volume exceeds the last show participation building into the move; follow it (down-moves on rising volume are sold).",
           {"m": [2, 3, 4], "vol_k": [0.8, 1.0, 1.3]}, _volume_ramp, markets=("WIN",),
           source="volume-price analysis (assistant reasoning)", author="agent"),
    Family("E-1415", "Autocorrelation regime switch",
           "Short-term return autocorrelation flips sign between trending and bid-ask-bounce regimes; follow a large bar when it is positive, fade it when negative.",
           {"win_min": [20, 40, 60], "thr": [0.15, 0.3]}, _autocorr_regime,
           source="assistant reasoning (serial correlation regimes)", author="agent"),
    Family("E-1416", "Prior-close hold-and-cross",
           "The previous session's close is the reference for overnight positions; after the price stays on one side of it for a while, a close across it marks overnight holders capitulating; follow.",
           {"away_min": [15, 30, 60]}, _prev_close_hold,
           source="assistant reasoning", author="agent"),
    Family("E-1417", "Volume-shock body fade",
           "A bar with volume far above normal and a wide, one-sided body is often a market-order sweep (stop run or panic); liquidity providers who absorbed it are paid as price retraces.",
           {"vol_k": [2.0, 3.0, 4.0]}, _volume_shock_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
