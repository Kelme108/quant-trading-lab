"""Conveyor batch B-071 (agent, 2026-11-22). Mixed themes: cross-market lead, levels, volatility regime, VWAP, channels."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _dollar_catchup(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    oc = ctx.other_close()
    rw = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    ro = oc / ctx.prev(oc, nb) - 1.0
    tw = ctx.cached(("aw", nb), lambda: ctx.prev_sessions(np.abs(rw), "mean"))
    to = ctx.cached(("ao", nb), lambda: ctx.prev_sessions(np.abs(ro), "mean"))
    wz = rw / (tw + 1e-12)
    dz = ro / (to + 1e-12)
    diff = -dz - wz
    long = (diff >= k) & (-dz > 0.5 * k)
    short = (-diff >= k) & (dz > 0.5 * k)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _open_retest(ctx, p):
    k = p["k"]
    ret = np.abs(ctx.c / ctx.day_open - 1.0)
    typ = ctx.cached("typ_open_dist", lambda: ctx.prev_sessions(ret, "mean"))
    thr = k * typ
    sh = ctx.session_high(False) / ctx.day_open - 1.0
    sl = 1.0 - ctx.session_low(False) / ctx.day_open
    long = (sh >= thr) & (ctx.l <= ctx.day_open) & (ctx.c > ctx.day_open)
    short = (sl >= thr) & (ctx.h >= ctx.day_open) & (ctx.c < ctx.day_open)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _squeeze_release(ctx, p):
    nb, ratio = ctx.bars(p["n_min"]), p["ratio"]
    bw = ctx.roll(ctx.c, nb, "std") / ctx.c
    typ = ctx.cached(("bw_typ", nb), lambda: ctx.prev_sessions(bw, "mean"))
    squeeze = bw < ratio * typ
    was = ctx.prev(squeeze.astype(float), 1) == 1
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    up = was & (ctx.c > hi)
    dn = was & (ctx.c < lo)
    return up.astype(int) - dn.astype(int)


def _afternoon_break(ctx, p):
    start = int(p["start_hour"]) * 60
    end = start + int(p["win_min"])
    form = (ctx.minute >= start) & (ctx.minute < end)
    after = (ctx.minute >= end) & (ctx.minutes_to_close >= 30)
    g = pd.DataFrame({"d": ctx.day, "h": np.where(form, ctx.h, np.nan), "l": np.where(form, ctx.l, np.nan)})
    hi = g.groupby("d")["h"].transform("max").to_numpy()
    lo = g.groupby("d")["l"].transform("min").to_numpy()
    up = after & (ctx.c > hi)
    dn = after & (ctx.c < lo)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _rolling_vwap_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    pv = ctx.roll(ctx.c * ctx.v, nb, "sum")
    vv = ctx.roll(ctx.v, nb, "sum")
    rv = pv / np.where(vv > 0, vv, np.nan)
    sd = ctx.roll(ctx.c, nb, "std")
    z = (ctx.c - rv) / np.where(sd > 0, sd, np.nan)
    return ctx.cross(z <= -k).astype(int) - ctx.cross(z >= k).astype(int)


def _range_thrust(ctx, p):
    nb, fb = ctx.bars(p["win_min"]), p["from_below"]
    hi = ctx.roll(ctx.h, nb, "max")
    lo = ctx.roll(ctx.l, nb, "min")
    rng = np.where(hi > lo, hi - lo, np.nan)
    pos = (ctx.c - lo) / rng
    nr = ctx.bars(10)
    pmin = ctx.roll(pos, nr, "min", include_current=False)
    pmax = ctx.roll(pos, nr, "max", include_current=False)
    long = (pos >= 0.9) & (pmin <= fb)
    short = (pos <= 0.1) & (pmax >= 1 - fb)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _ema_stretch_fade(ctx, p):
    k, n = p["k"], int(p["ema_bars"])
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    rng = ctx.h - ctx.l
    atr = ctx.cached(("atr", n), lambda: ctx.roll(rng, n, "mean"))
    z = (ctx.c - ema) / np.where(atr > 0, atr, np.nan)
    return ctx.cross(z <= -k).astype(int) - ctx.cross(z >= k).astype(int)


def _prior_close_cross(ctx, p):
    nb = ctx.bars(p["away_min"])
    pc = ctx.prev_session_value("close")
    below = (ctx.c < pc).astype(float)
    above = (ctx.c > pc).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    up = was_below & (ctx.c > pc)
    dn = was_above & (ctx.c < pc)
    return up.astype(int) - dn.astype(int)


def _autocorr_regime(ctx, p):
    nb, th, k = ctx.bars(p["win_min"]), p["th"], p["k"]
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    prod = r * ctx.prev(r, 1)
    ac = ctx.roll(prod, nb, "mean") / (ctx.roll(r * r, nb, "mean") + 1e-18)
    sd = np.sqrt(ctx.roll(r * r, nb, "mean"))
    big = np.abs(r) >= k * sd
    d = np.sign(r) * np.sign(ac)
    fire = big & (np.abs(ac) >= th)
    sig = np.where(fire, d, 0)
    sig = np.nan_to_num(sig).astype(int)
    return np.where(ctx.cross(sig != 0), sig, 0)


def _donchian_mid(ctx, p):
    nb = ctx.bars(p["n_min"])
    hi = ctx.roll(ctx.h, nb, "max")
    lo = ctx.roll(ctx.l, nb, "min")
    mid = (hi + lo) / 2
    return ctx.cross(ctx.c > mid).astype(int) - ctx.cross(ctx.c < mid).astype(int)


def _round_trip_spike(ctx, p):
    k, nb = p["k"], ctx.bars(p["win_min"])
    rng = ctx.h - ctx.l
    typ = ctx.cached(("rng_typ"), lambda: ctx.same_minute(rng, "median"))
    spike = rng >= k * typ
    ret = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    # spike bar closing against the preceding move: absorbed push
    up_prev = ret < 0
    long = spike & (ctx.c > ctx.o) & up_prev & (ctx.c > ctx.prev(ctx.h, 1))
    short = spike & (ctx.c < ctx.o) & ~up_prev & (ctx.c < ctx.prev(ctx.l, 1))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


FAMILIES = [
    Family("E-708", "Dollar-led catch-up",
           "WIN and the dollar are inversely linked intraday; when the dollar moves sharply and the index has not yet "
           "responded, slower index participants reprice and WIN catches up.",
           {"win_min": [10, 20, 30], "k": [1.0, 1.5, 2.0]}, _dollar_catchup, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-709", "Day-open retest hold",
           "After moving well away from the session open, a return to the open that closes back on the trend side "
           "shows the open acting as support/resistance for the day's inventory.",
           {"k": [1.0, 1.5, 2.0]}, _open_retest, source="assistant reasoning", author="agent"),
    Family("E-710", "Volatility squeeze release",
           "Realised volatility far below its 20-session norm means stored-up orders; the first break of the recent "
           "range after the squeeze starts a directional expansion.",
           {"n_min": [15, 30], "ratio": [0.5, 0.7, 0.9]}, _squeeze_release, source="assistant reasoning", author="agent"),
    Family("E-711", "Afternoon-window range break",
           "The range built in a late-morning or midday window holds resting orders at its edges; a close outside it "
           "later in the session triggers stops and follow-through.",
           {"start_hour": [10, 12, 14], "win_min": [30, 60]}, _afternoon_break, source="assistant reasoning", author="agent"),
    Family("E-712", "Rolling volume-weighted mean fade",
           "Price stretched far from the volume-weighted mean of the last hour has been pushed by few participants "
           "and tends to revert toward where most volume traded.",
           {"win_min": [30, 60, 90], "k": [1.5, 2.0, 2.5]}, _rolling_vwap_fade, source="assistant reasoning", author="agent"),
    Family("E-713", "Range thrust from the opposite side",
           "A fast move from the lower half of the recent range to its top (or reverse) within ten minutes shows "
           "aggressive one-sided flow that continues.",
           {"win_min": [30, 60, 90], "from_below": [0.3, 0.5]}, _range_thrust, source="assistant reasoning", author="agent"),
    Family("E-714", "ATR stretch from EMA fade",
           "A close several average ranges away from a short EMA is an extension that liquidity takers cannot "
           "sustain; fade it back.",
           {"k": [2.0, 3.0, 4.0], "ema_bars": [20, 30]}, _ema_stretch_fade, source="assistant reasoning", author="agent"),
    Family("E-715", "Prior-close cross after a stay",
           "The previous settlement-like close is a reference that market participants anchor to; a first close "
           "across it after a stay on one side signals the day's sentiment flipping.",
           {"away_min": [20, 40, 60]}, _prior_close_cross, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-716", "Autocorrelation-regime bar",
           "When the last hour's bar-to-bar returns are positively autocorrelated a big bar continues; when negatively "
           "autocorrelated it reverts. Trade the big bar according to the regime.",
           {"win_min": [30, 60, 90], "th": [0.1, 0.2], "k": [1.0, 1.5]}, _autocorr_regime, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-717", "Donchian midline cross",
           "The midpoint of the recent high-low channel separates buyer and seller control; a close crossing it "
           "marks a shift in control that persists.",
           {"n_min": [30, 60, 90]}, _donchian_mid, markets=("WIN",), source="assistant reasoning", author="agent"),
]
