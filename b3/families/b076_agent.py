"""Conveyor batch B-076 (agent, 2026-11-23). Indicator-state onsets and session-structure ideas not yet screened."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _d(long, short):
    return long.astype(int) - short.astype(int)


def _median_cross(ctx, p):
    n = ctx.bars(p["win_min"])
    med = pd.Series(ctx.c).groupby(ctx.day).transform(lambda z: z.rolling(n, min_periods=n).median()).to_numpy()
    slope = med - ctx.prev(med, 1)
    long = (ctx.c > med) & (slope > 0)
    short = (ctx.c < med) & (slope < 0)
    return _d(ctx.cross(long), ctx.cross(short))


def _vwap_chop_break(ctx, p):
    nb = ctx.bars(p["win_min"])
    vw = ctx.vwap()
    side = np.sign(ctx.c - vw)
    ps_ = ctx.prev(side, 1)
    flips = ((side != ps_) & (ps_ != 0) & (side != 0)).astype(float)
    cnt = ctx.roll(flips, nb, "sum")
    atr = ctx.roll(ctx.h - ctx.l, ctx.bars(30), "mean")
    chop = cnt >= p["flips"]
    long = chop & (ctx.c - vw > p["k"] * atr)
    short = chop & (vw - ctx.c > p["k"] * atr)
    return _d(ctx.cross(long), ctx.cross(short))


def _er_onset(ctx, p):
    nb = ctx.bars(p["win_min"])
    step = np.abs(ctx.c - ctx.prev(ctx.c, 1))
    path = ctx.roll(step, nb, "sum")
    move = ctx.c - ctx.prev(ctx.c, nb)
    er = np.abs(move) / np.where(path > 0, path, np.nan)
    ok = er >= p["th"]
    return _d(ctx.cross(ok & (move > 0)), ctx.cross(ok & (move < 0)))


def _widest_bar(ctx, p):
    rng = ctx.h - ctx.l
    prior_max = pd.Series(rng).groupby(ctx.day).transform(lambda z: z.cummax().shift(1)).to_numpy()
    late = ctx.bar_in_day >= ctx.bars(p["min_min"])
    wide = late & (rng > prior_max) & (rng > 0)
    loc = (ctx.c - ctx.l) / np.where(rng > 0, rng, np.nan)
    long = wide & (loc >= p["frac"]) & (ctx.c > ctx.o)
    short = wide & (loc <= 1 - p["frac"]) & (ctx.c < ctx.o)
    return _d(long, short)


def _burst_count(ctx, p):
    m = ctx.bars(p["win_min"])
    atr = ctx.roll(ctx.h - ctx.l, ctx.bars(60), "mean")
    body = ctx.c - ctx.o
    up = ctx.roll((body > p["k"] * atr).astype(float), m, "sum")
    dn = ctx.roll((body < -p["k"] * atr).astype(float), m, "sum")
    need = p["need"]
    long = (up >= need) & (dn == 0)
    short = (dn >= need) & (up == 0)
    return _d(ctx.cross(long), ctx.cross(short))


def _early_bias_vwap(ctx, p):
    nb = ctx.bars(p["win_min"])
    first = ctx.bar_in_day < nb
    g = pd.DataFrame({"d": ctx.day, "u": np.where(first, (ctx.c > ctx.o).astype(float), 0.0),
                      "f": first.astype(float)})
    share = (g.groupby("d")["u"].transform("sum") / g.groupby("d")["f"].transform("sum")).to_numpy()
    done = ~first
    vw = ctx.vwap()
    long = done & (share >= p["th"]) & (ctx.c > vw)
    short = done & (share <= 1 - p["th"]) & (ctx.c < vw)
    return _d(ctx.cross(long), ctx.cross(short))


def _macd_turn(ctx, p):
    f = int(p["fast"])
    s = 2 * f + 2
    macd = ctx.ema(ctx.c, f) - ctx.ema(ctx.c, s)
    hist = macd - pd.Series(macd).groupby(ctx.day).transform(
        lambda z: z.ewm(span=max(2, int(0.75 * f)), adjust=False).mean()).to_numpy()
    h1, h2 = ctx.prev(hist, 1), ctx.prev(hist, 2)
    long = (hist < 0) & (hist > h1) & (h1 > h2)
    short = (hist > 0) & (hist < h1) & (h1 < h2)
    if int(p["need"]) >= 3:
        h3 = ctx.prev(hist, 3)
        long = long & (h2 > h3)
        short = short & (h2 < h3)
    return _d(ctx.cross(long), ctx.cross(short))


def _cci_fade(ctx, p):
    n = int(p["n"])
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    sma = ctx.roll(tp, n, "mean")
    md = ctx.roll(np.abs(tp - sma), n, "mean")
    cci = (tp - sma) / (0.015 * np.where(md > 0, md, np.nan))
    th = p["th"]
    prv = ctx.prev(cci, 1)
    short = (prv > th) & (cci <= th)
    long = (prv < -th) & (cci >= -th)
    return _d(long, short)


def _chop_onset(ctx, p):
    n = int(p["n"])
    tr = ctx.h - ctx.l
    s = ctx.roll(tr, n, "sum")
    hh = ctx.roll(ctx.h, n, "max")
    ll = ctx.roll(ctx.l, n, "min")
    width = hh - ll
    ci = 100.0 * np.log10(s / np.where(width > 0, width, np.nan)) / np.log10(n)
    move = ctx.c - ctx.prev(ctx.c, n)
    ok = ci < p["th"]
    return _d(ctx.cross(ok & (move > 0)), ctx.cross(ok & (move < 0)))


def _force_thrust(ctx, p):
    n = int(p["n"])
    f = (ctx.c - ctx.prev(ctx.c, 1)) * ctx.v
    fi = pd.Series(f).groupby(ctx.day).transform(lambda z: z.ewm(span=n, adjust=False).mean()).to_numpy()
    scale = ctx.roll(np.abs(f), ctx.bars(60), "mean")
    k = p["k"]
    return _d(ctx.cross(fi > k * scale), ctx.cross(fi < -k * scale))


def _er_dummy(ctx, p):
    return np.zeros(ctx.n, dtype=int)


FAMILIES = [
    Family("E-758", "Rolling-median cross with rising median",
           "The median of recent closes ignores spikes; a close crossing a sloping median means the typical price "
           "level is migrating, so stop-based traders chase the direction.",
           {"win_min": [15, 30, 60]}, _median_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-759", "VWAP chop then break",
           "Many crossings of the VWAP mean balanced trade; a close far from VWAP after the chop signals the "
           "balance resolving and trapped counter-traders adding to the move.",
           {"win_min": [30, 60], "flips": [3, 4], "k": [0.5, 1.0, 1.5]}, _vwap_chop_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-760", "Efficiency-ratio trend onset",
           "When net movement becomes a large share of the path travelled, flow is one-sided; follow the first bar "
           "where the Kaufman efficiency ratio crosses the threshold.",
           {"win_min": [15, 30, 45], "th": [0.5, 0.6, 0.7]}, _er_onset, markets=("WIN",),
           source="Kaufman efficiency ratio, assistant reasoning", author="agent"),
    Family("E-761", "Widest bar of the session so far",
           "A bar wider than every earlier bar of the day, closing at its extreme in its own colour, shows the "
           "strongest aggression of the session; the other side is forced to cover.",
           {"min_min": [30, 60, 90], "frac": [0.6, 0.7, 0.8]}, _widest_bar, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-762", "Same-colour big-body burst count",
           "Several large same-direction bodies in a short window with none against show persistent institutional "
           "execution that slices orders; follow the burst.",
           {"win_min": [10, 15, 20], "k": [0.75, 1.0], "need": [2, 3]}, _burst_count, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-763", "Early-bias VWAP side follow",
           "A session whose first bars were mostly one colour has a directional bias; after the opening window, "
           "the first close on the bias side of VWAP is a dip-buy/rally-sell by trend participants.",
           {"win_min": [30, 45], "th": [0.55, 0.6, 0.65]}, _early_bias_vwap, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-764", "MACD histogram early turn",
           "A histogram that rises for several bars while still below zero shows selling momentum fading before "
           "the lines cross; the early turn catches the reversal ahead of lagging followers.",
           {"fast": [6, 9, 12], "need": [2, 3]}, _macd_turn, markets=("WIN",),
           source="Appel MACD histogram, assistant reasoning", author="agent"),
    Family("E-765", "CCI re-entry fade",
           "A Commodity Channel Index excursion beyond a large threshold followed by a return inside it marks "
           "exhausted extension; fade back toward the mean.",
           {"n": [14, 20, 30], "th": [100, 150, 200]}, _cci_fade, markets=("WIN",),
           source="Lambert CCI, assistant reasoning", author="agent"),
    Family("E-766", "Choppiness-index trend onset",
           "A fall of the choppiness index below its trending threshold means ranges stop overlapping; follow the "
           "net direction of the window.",
           {"n": [14, 20, 30], "th": [38.2, 45.0, 50.0]}, _chop_onset, markets=("WIN",),
           source="Dreiss choppiness index, assistant reasoning", author="agent"),
    Family("E-767", "Force-index thrust",
           "Price change times volume, smoothed, beyond a typical-size threshold shows volume-backed pressure; "
           "follow the first bar where it exceeds that size.",
           {"n": [5, 10, 15], "k": [0.25, 0.5, 0.75]}, _force_thrust, markets=("WIN",),
           source="Elder force index, assistant reasoning", author="agent"),
]
