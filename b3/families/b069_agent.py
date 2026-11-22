"""Conveyor batch B-069 (agent, 2026-11-22). Mixed themes: autocorrelation regime, wick pressure, absorption, shocks, regression snap, midpoint, thrust, late-day VWAP, prior-range thrust, measured move."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _autocorr_regime(ctx, p):
    nb = ctx.bars(p["win_min"])
    thr = p["thr"]
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    r1 = ctx.prev(r, 1)
    num = ctx.roll(r * r1, nb, "mean")
    den = ctx.roll(r * r, nb, "mean")
    with np.errstate(all="ignore"):
        ac = num / den
    long = ctx.cross((ac > thr) & (r > 0)) | ctx.cross((ac < -thr) & (r < 0))
    short = ctx.cross((ac > thr) & (r < 0)) | ctx.cross((ac < -thr) & (r > 0))
    return long.astype(int) - short.astype(int)


def _wick_pressure(ctx, p):
    nb = ctx.bars(p["win_min"])
    k = p["k"]
    rng = ctx.h - ctx.l
    with np.errstate(all="ignore"):
        lw = np.where(rng > 0, (np.minimum(ctx.o, ctx.c) - ctx.l) / rng, 0.0)
        uw = np.where(rng > 0, (ctx.h - np.maximum(ctx.o, ctx.c)) / rng, 0.0)
    s = ctx.roll(lw - uw, nb, "mean")
    return ctx.cross(s > k).astype(int) - ctx.cross(s < -k).astype(int)


def _absorption_break(ctx, p):
    k, frac = p["vol_k"], p["range_frac"]
    rng = ctx.h - ctx.l
    vmed = ctx.cached("vmed_b69", lambda: ctx.same_minute(ctx.v, "median"))
    rmed = ctx.cached("rmed_b69", lambda: ctx.same_minute(rng, "median"))
    absorb = (ctx.v > k * vmed) & (rng < frac * rmed)
    pa = ctx.prev(absorb.astype(float), 1) == 1
    ph, pl = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    long = pa & (ctx.c > ph)
    short = pa & (ctx.c < pl)
    return long.astype(int) - short.astype(int)


def _shock_fade(ctx, p):
    k, vcap = p["k"], p["vol_cap"]
    r = ctx.c / ctx.o - 1.0
    typ = ctx.cached("absr_b69", lambda: ctx.same_minute(np.abs(r), "mean"))
    vmed = ctx.cached("vmed_b69", lambda: ctx.same_minute(ctx.v, "median"))
    with np.errstate(all="ignore"):
        z = r / typ
        vr = ctx.v / vmed
    long = (z < -k) & (vr < vcap)
    short = (z > k) & (vr < vcap)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _regression_snap(ctx, p):
    nb = ctx.bars(p["win_min"])
    k = p["k"]
    x = ctx.bar_in_day.astype(float)
    y = ctx.c
    mx, my = ctx.roll(x, nb, "mean"), ctx.roll(y, nb, "mean")
    mxy, mxx, myy = ctx.roll(x * y, nb, "mean"), ctx.roll(x * x, nb, "mean"), ctx.roll(y * y, nb, "mean")
    with np.errstate(all="ignore"):
        vx = mxx - mx * mx
        slope = (mxy - mx * my) / vx
        fit = my + slope * (x - mx)
        res_var = (myy - my * my) - slope * slope * vx
        sd = np.sqrt(np.maximum(res_var, 0.0))
        z = np.where(sd > 0, (y - fit) / sd, 0.0)
    return ctx.cross(z < -k).astype(int) - ctx.cross(z > k).astype(int)


def _midpoint_cross(ctx, p):
    wait, f = p["wait_min"], p["frac"]
    sh, sl = ctx.session_high(False), ctx.session_low(False)
    mid, rg = (sh + sl) / 2.0, sh - sl
    late = ctx.bar_in_day * ctx.tf >= wait
    up = late & (ctx.c > mid + f * rg)
    dn = late & (ctx.c < mid - f * rg)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _range_thrust(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["ratio"]
    hi, lo = ctx.roll(ctx.h, nb, "max"), ctx.roll(ctx.l, nb, "min")
    rng = hi - lo
    prior = ctx.prev(rng, nb)
    with np.errstate(all="ignore"):
        loc = np.where(rng > 0, (ctx.c - lo) / rng, 0.5)
        big = rng > k * prior
    long = big & (loc >= 0.8)
    short = big & (loc <= 0.2)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _late_vwap_magnet(ctx, p):
    win, k = p["win_min"], p["k"]
    vw = ctx.vwap()
    dev = ctx.c / vw - 1.0
    typ = ctx.cached("vwapdev_b69", lambda: ctx.prev_sessions(np.abs(dev), "mean"))
    late = ctx.minutes_to_close <= win
    short = late & (dev > k * typ)
    long = late & (dev < -k * typ)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _prior_range_thrust(ctx, p):
    nb, frac = ctx.bars(p["horizon_min"]), p["frac"]
    pr = ctx.prev_session_value("high") - ctx.prev_session_value("low")
    move = ctx.c - ctx.prev(ctx.c, nb)
    return ctx.cross(move > frac * pr).astype(int) - ctx.cross(move < -frac * pr).astype(int)


def _measured_move_fade(ctx, p):
    nb, mult = ctx.bars(p["range_min"]), p["mult"]
    first = ctx.bar_in_day < nb
    g = pd.DataFrame({"d": ctx.day, "h": np.where(first, ctx.h, np.nan), "l": np.where(first, ctx.l, np.nan)})
    orh = g.groupby("d")["h"].transform("max").to_numpy()
    orl = g.groupby("d")["l"].transform("min").to_numpy()
    ht = orh - orl
    done = ~first
    short = done & (ctx.c > orh + mult * ht)
    long = done & (ctx.c < orl - mult * ht)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


FAMILIES = [
    Family("E-688", "Autocorrelation regime switch",
           "When recent bar-to-bar returns are positively autocorrelated the last bar's direction tends to persist (trend regime, "
           "stop-chasing flow); when negatively autocorrelated it bounces (inventory-driven chop); follow or fade accordingly.",
           {"win_min": [30, 60, 90], "thr": [0.1, 0.2, 0.3]}, _autocorr_regime,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-689", "Accumulated wick pressure",
           "Repeated long lower wicks over a window show passive buyers absorbing sell orders (and upper wicks the reverse); "
           "when the average wick imbalance crosses a threshold, trade with the absorbers.",
           {"win_min": [20, 40, 60], "k": [0.1, 0.2, 0.3]}, _wick_pressure,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-690", "Absorption bar break",
           "A high-volume, tiny-range bar means aggressive flow met a large passive order; the next close beyond that bar "
           "shows which side gave up, and the move follows.",
           {"vol_k": [1.5, 2.0, 3.0], "range_frac": [0.5, 0.7, 1.0]}, _absorption_break,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-691", "Low-volume shock fade",
           "A bar move many times larger than usual for the time of day but on ordinary volume is likely a thin-book "
           "air pocket or a single sweep; liquidity returns and the move retraces.",
           {"k": [2.0, 3.0, 4.0], "vol_cap": [1.0, 1.5, 2.0]}, _shock_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-692", "Regression-channel snap-back",
           "Price stretching more than k residual deviations from a rolling least-squares line is an overshoot against the "
           "local trend; liquidity providers fade it back toward the line.",
           {"win_min": [30, 60, 90], "k": [2.0, 2.5, 3.0]}, _regression_snap,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-693", "Session-midpoint cross follow",
           "After the early session, a close that crosses from one half of the day's range to the other signals the "
           "balance of the day shifting; follow the cross.",
           {"wait_min": [60, 120, 180], "frac": [0.0, 0.05, 0.1]}, _midpoint_cross,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-694", "Range-expansion thrust",
           "When the last n minutes' range is a multiple of the preceding n minutes' range and the close sits at the extreme, "
           "volatility has switched on with a directional push and stops feed it.",
           {"win_min": [10, 20, 30], "ratio": [1.5, 2.0, 3.0]}, _range_thrust,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-695", "Late-day VWAP magnet",
           "Into the final stretch, institutions benchmarked to VWAP and day traders closing positions pull a stretched "
           "price back toward the session VWAP; fade the stretch.",
           {"win_min": [90, 150, 240], "k": [1.5, 2.0, 3.0]}, _late_vwap_magnet,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-696", "Prior-range-scaled thrust",
           "A move over the last minutes that is a set fraction of yesterday's whole range is large in a way participants "
           "anchored on yesterday's levels notice; chasing flow extends it.",
           {"horizon_min": [15, 30, 60], "frac": [0.1, 0.15, 0.2]}, _prior_range_thrust,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-697", "Opening-range measured-move fade",
           "Technical traders project the opening range height beyond its edge as a profit target; price reaching that "
           "projection meets take-profit orders and fades.",
           {"range_min": [15, 30, 60], "mult": [0.5, 1.0, 1.5]}, _measured_move_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
]
