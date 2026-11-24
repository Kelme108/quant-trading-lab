"""Conveyor batch B-108 (agent, 2026-11-24). Mixed themes: seasonality, block levels, absorption, efficiency, robust stretch, breadth, relative volume, VWAP slope, late session."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _seasonal_drift(ctx, p):
    nb, k = ctx.bars(p["horizon_min"]), p["k"]
    ret = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    m = ctx.cached(("sd_m", nb), lambda: ctx.same_minute(ret, "mean"))
    s = ctx.cached(("sd_s", nb), lambda: ctx.same_minute(np.abs(ret), "mean"))
    z = np.where(s > 0, m / np.where(s > 0, s, 1.0), 0.0)
    return ctx.cross(z > k).astype(int) - ctx.cross(z < -k).astype(int)


def _prev_block_break(ctx, p):
    blk = int(p["block_min"])
    bid = (ctx.minute // blk).astype(int)
    df = pd.DataFrame({"d": ctx.day, "b": bid, "h": ctx.h, "l": ctx.l})
    agg = df.groupby(["d", "b"]).agg(hh=("h", "max"), ll=("l", "min")).reset_index()
    agg["ph"] = agg.groupby("d")["hh"].shift(1)
    agg["pl"] = agg.groupby("d")["ll"].shift(1)
    m = df[["d", "b"]].merge(agg[["d", "b", "ph", "pl"]], on=["d", "b"], how="left")
    ph, pl = m["ph"].to_numpy(float), m["pl"].to_numpy(float)
    up = ctx.cross(ctx.c > ph)
    dn = ctx.cross(ctx.c < pl)
    return up.astype(int) - dn.astype(int)


def _churn_fade(ctx, p):
    k, f = p["vol_k"], p["range_frac"]
    nb = ctx.bars(15)
    rng = ctx.h - ctx.l
    mv = ctx.cached("churn_v", lambda: ctx.same_minute(ctx.v, "median"))
    mr = ctx.cached("churn_r", lambda: ctx.same_minute(rng, "median"))
    churn = (ctx.v >= k * mv) & (rng <= f * mr) & (mr > 0)
    move = ctx.c - ctx.prev(ctx.c, nb)
    long = churn & (move < 0)
    short = churn & (move > 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _record_range_bar(ctx, p):
    nb, fr = ctx.bars(p["min_min"]), p["close_frac"]
    rng = ctx.h - ctx.l
    prior = pd.Series(rng).groupby(ctx.day).transform(lambda z: z.cummax().shift(1)).to_numpy()
    loc = np.where(rng > 0, (ctx.c - ctx.l) / np.where(rng > 0, rng, 1.0), 0.5)
    rec = (rng > prior) & (ctx.bar_in_day >= nb)
    long = rec & (loc >= fr)
    short = rec & (loc <= 1 - fr)
    return long.astype(int) - short.astype(int)


def _efficiency_surge(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["er"]
    step = np.abs(ctx.c - ctx.prev(ctx.c, 1))
    path = ctx.roll(step, nb, "sum")
    net = ctx.c - ctx.prev(ctx.c, nb)
    er = np.where(path > 0, np.abs(net) / np.where(path > 0, path, 1.0), 0.0)
    long = (er > th) & (net > 0)
    short = (er > th) & (net < 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _robust_stretch_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    s = pd.Series(ctx.c)
    med = s.groupby(ctx.day).transform(lambda z: z.rolling(nb, min_periods=nb).median()).to_numpy()
    dev = np.abs(ctx.c - med)
    mad = pd.Series(dev).groupby(ctx.day).transform(lambda z: z.rolling(nb, min_periods=nb).mean()).to_numpy()
    z = np.where(mad > 0, (ctx.c - med) / np.where(mad > 0, mad, 1.0), 0.0)
    return ctx.cross(z < -k).astype(int) - ctx.cross(z > k).astype(int)


def _upbar_breadth(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["share"]
    up = (ctx.c > ctx.prev(ctx.c, 1)).astype(float)
    up = np.where(np.isnan(ctx.prev(ctx.c, 1)), np.nan, up)
    fr = ctx.roll(up, nb, "mean")
    return ctx.cross(fr >= th).astype(int) - ctx.cross(fr <= 1 - th).astype(int)


def _relvol_day_side(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["rv"]
    rs = ctx.roll(ctx.v, nb, "sum")
    typ = ctx.cached(("rv_typ", nb), lambda: ctx.same_minute(rs, "median"))
    rv = np.where(typ > 0, rs / np.where(typ > 0, typ, 1.0), 0.0)
    heavy = rv >= k
    long = heavy & (ctx.c > ctx.day_open)
    short = heavy & (ctx.c < ctx.day_open)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _vwap_slope_touch(ctx, p):
    nb, k = ctx.bars(p["slope_min"]), p["slope_k"]
    vw = ctx.vwap()
    slope = vw / ctx.prev(vw, nb) - 1.0
    move = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    typ = ctx.cached(("vs_abs", nb), lambda: ctx.prev_sessions(np.abs(move), "mean"))
    long = (slope >= k * typ) & (ctx.l <= vw) & (ctx.c > vw)
    short = (slope <= -k * typ) & (ctx.h >= vw) & (ctx.c < vw)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _late_ema_vwap(ctx, p):
    n = ctx.bars(p["ema_min"])
    late = ctx.minute >= int(p["from_hour"]) * 60
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, max(2, n)))
    vw = ctx.vwap()
    long = ctx.cross((ctx.c > ema) & (ctx.c > vw)) & late
    short = ctx.cross((ctx.c < ema) & (ctx.c < vw)) & late
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-1078", "Seasonal same-minute drift follow",
           "Index flows (rebalancing, lunch, US open) repeat at the same clock minutes; when the 20-session average move "
           "at this minute is consistently one-signed, institutions on the other side are scheduled, so follow it.",
           {"horizon_min": [10, 20, 30], "k": [0.3, 0.5, 0.7]}, _seasonal_drift,
           source="assistant reasoning", author="assistant"),
    Family("E-1079", "Previous clock-block break follow",
           "A close beyond the high/low of the previous completed clock block (15/30/60 min) triggers stops resting "
           "just outside a level short-term traders watch; follow.",
           {"block_min": [15, 30, 60]}, _prev_block_break, markets=("WIN",),
           source="assistant reasoning", author="assistant"),
    Family("E-1080", "Churn-bar absorption fade",
           "A bar with heavy volume but a small range means passive limit orders absorbed the aggressors; the run "
           "before it is exhausted, fade it.",
           {"vol_k": [1.0, 1.5, 2.0], "range_frac": [0.5, 0.75, 1.0]}, _churn_fade, markets=("WIN",),
           source="assistant reasoning", author="assistant"),
    Family("E-1081", "Record-range bar follow",
           "A bar whose range is the largest of the session so far that also closes near its extreme shows an "
           "unusually committed buyer or seller; follow it.",
           {"min_min": [15, 30, 60], "close_frac": [0.6, 0.7, 0.8]}, _record_range_bar, markets=("WIN",),
           source="assistant reasoning", author="assistant"),
    Family("E-1082", "Efficiency-ratio surge follow",
           "When price covers most of its path in one direction (Kaufman efficiency ratio high) the move is "
           "one-sided flow rather than noise; follow the first bar where it crosses the threshold.",
           {"win_min": [15, 30, 45], "er": [0.5, 0.6, 0.7]}, _efficiency_surge, markets=("WIN",),
           source="Kaufman efficiency ratio, assistant reasoning", author="assistant"),
    Family("E-1083", "Median-deviation stretch fade",
           "Price far from its rolling median in units of mean absolute deviation is a liquidity-driven stretch "
           "that a robust centre (unlike the mean) is not dragged by; fade the return to it.",
           {"win_min": [30, 60, 90], "k": [2.0, 2.5, 3.0]}, _robust_stretch_fade, markets=("WIN",),
           source="assistant reasoning", author="assistant"),
    Family("E-1084", "Up-bar breadth extreme follow",
           "When 70-80% of recent bars close up (or down), many small orders are all leaning one way; follow when "
           "the share first reaches the threshold.",
           {"win_min": [20, 30, 45], "share": [0.7, 0.75, 0.8]}, _upbar_breadth, markets=("WIN",),
           source="assistant reasoning", author="assistant"),
    Family("E-1085", "Relative-volume heavy window with the day side",
           "A window with volume well above the same-clock norm, while price is on one side of the day's open, "
           "shows participation joining the day's winners; follow that side.",
           {"win_min": [15, 30], "rv": [1.25, 1.5, 2.0]}, _relvol_day_side,
           source="assistant reasoning", author="assistant"),
    Family("E-1086", "Sloping-VWAP touch continuation",
           "When session VWAP is rising (falling) faster than usual, institutional average-price buyers (sellers) "
           "defend it; the first touch that closes back on the trend side is a continuation entry.",
           {"slope_min": [20, 30, 60], "slope_k": [0.5, 1.0, 1.5]}, _vwap_slope_touch, markets=("WIN",),
           source="assistant reasoning", author="assistant"),
    Family("E-1087", "Late-session EMA cross with VWAP side",
           "Late in the session, position squaring follows the VWAP side; a cross of a short EMA in agreement "
           "with the VWAP side shows the closing flow starting.",
           {"from_hour": [14, 15, 16], "ema_min": [10, 20, 30]}, _late_ema_vwap, markets=("WIN",),
           source="assistant reasoning", author="assistant"),
]
