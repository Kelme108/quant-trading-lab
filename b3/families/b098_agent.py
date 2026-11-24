"""Conveyor batch B-098 (agent, 2026-11-24). Regression slope, opening-range midpoint, typical-path deviation, V-shapes,
semivariance, US-open window, multi-session mean, previous block midpoint, level stack, last-hour band re-entry."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _linreg_t(ctx, p):
    n = max(4, ctx.bars(p["win_min"]))
    th = p["t"]
    x = ctx.bar_in_day.astype(float)
    y = (ctx.c / ctx.day_open - 1.0) * 1e4
    sx, sy = ctx.roll(x, n, "sum"), ctx.roll(y, n, "sum")
    sxy, sxx, syy = ctx.roll(x * y, n, "sum"), ctx.roll(x * x, n, "sum"), ctx.roll(y * y, n, "sum")
    with np.errstate(all="ignore"):
        cov = sxy / n - sx / n * sy / n
        vx = sxx / n - (sx / n) ** 2
        vy = syy / n - (sy / n) ** 2
        r = np.clip(cov / np.sqrt(vx * vy), -0.9999, 0.9999)
        t = r * np.sqrt((n - 2) / (1.0 - r * r))
    t = np.nan_to_num(t, nan=0.0)
    return ctx.cross(t > th).astype(int) - ctx.cross(t < -th).astype(int)


def _or_mid_cross(ctx, p):
    nb = ctx.bars(p["range_min"])
    buf = p["buf"]
    first = ctx.bar_in_day < nb
    g = pd.DataFrame({"d": ctx.day, "h": np.where(first, ctx.h, np.nan), "l": np.where(first, ctx.l, np.nan)})
    orh = g.groupby("d")["h"].transform("max").to_numpy()
    orl = g.groupby("d")["l"].transform("min").to_numpy()
    mid, w = (orh + orl) / 2.0, orh - orl
    ok = ctx.bar_in_day > nb
    up = ctx.cross(ctx.c > mid + buf * w) & ok
    dn = ctx.cross(ctx.c < mid - buf * w) & ok
    return up.astype(int) - dn.astype(int)


def _path_dev_fade(ctx, p):
    k, n = p["k"], int(p["n"])
    r = ctx.c / ctx.day_open - 1.0
    path = ctx.cached(("path", n), lambda: ctx.same_minute(r, "mean", n))
    s = ctx.cached(("pathabs", n), lambda: ctx.same_minute(np.abs(r), "mean", n))
    dev = r - path
    short = ctx.cross(dev > k * s)
    long = ctx.cross(dev < -k * s)
    return long.astype(int) - short.astype(int)


def _v_complete(ctx, p):
    m = ctx.bars(p["m_min"])
    k = p["k"]
    L = 2 * m
    a = ctx.prev(ctx.c, L)
    mn = ctx.roll(ctx.l, L, "min")
    mx = ctx.roll(ctx.h, L, "max")
    typ = ctx.cached(("vtyp", L), lambda: ctx.prev_sessions(np.abs(ctx.c / ctx.prev(ctx.c, L) - 1.0), "mean"))
    with np.errstate(all="ignore"):
        up = ((a - mn) / a >= k * typ) & (ctx.c >= a)
        dn = ((mx - a) / a >= k * typ) & (ctx.c <= a)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _semivar_follow(ctx, p):
    n, th = ctx.bars(p["win_min"]), p["th"]
    r1 = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    su = ctx.roll(np.where(r1 > 0, r1 * r1, 0.0), n, "sum")
    sd = ctx.roll(np.where(r1 < 0, r1 * r1, 0.0), n, "sum")
    ratio = (su + 1e-14) / (sd + 1e-14)
    up = np.nan_to_num(ratio, nan=1.0) >= th
    dn = np.nan_to_num(ratio, nan=1.0) <= 1.0 / th
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _us_open_drift(ctx, p):
    w, k = p["w_min"], p["k"]
    nb = ctx.bars(w)
    move = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    typ = ctx.cached(("usabs", nb), lambda: ctx.prev_sessions(np.abs(move), "mean"))
    at = np.zeros(ctx.n, dtype=bool)
    for om in (630, 690):
        at |= (ctx.minute + ctx.tf) == (om + w)
    big = np.abs(move) >= k * typ
    with np.errstate(all="ignore"):
        up = at & big & (move > 0)
        dn = at & big & (move < 0)
    return up.astype(int) - dn.astype(int)


def _multi_mean_cross(ctx, p):
    n, buf = int(p["n"]), p["buf"]
    m = ctx.cached(("mm", n), lambda: ctx.prev_sessions(ctx.c, "mean", n))
    up = ctx.cross(ctx.c > m * (1 + buf))
    dn = ctx.cross(ctx.c < m * (1 - buf))
    return up.astype(int) - dn.astype(int)


def _prev_block_mid(ctx, p):
    blk, buf = int(p["block_min"]), p["buf"]
    key = ctx.day.astype(np.int64) * 10000 + (ctx.minute // blk).astype(np.int64)
    codes, _ = pd.factorize(key)
    g = pd.DataFrame({"k": codes, "h": ctx.h, "l": ctx.l, "d": ctx.day})
    agg = g.groupby("k").agg(h=("h", "max"), l=("l", "min"), d=("d", "first"))
    ph, pl = agg["h"].shift(1), agg["l"].shift(1)
    same = (agg["d"].shift(1) == agg["d"])
    ph, pl = ph.where(same).to_numpy()[codes], pl.where(same).to_numpy()[codes]
    mid, w = (ph + pl) / 2.0, ph - pl
    up = ctx.cross(ctx.c > mid + buf * w)
    dn = ctx.cross(ctx.c < mid - buf * w)
    return up.astype(int) - dn.astype(int)


def _level_stack(ctx, p):
    nb = ctx.bars(p["hold_min"])
    pc = ctx.prev_session_value("close")
    top = np.maximum(np.maximum(ctx.day_open, ctx.vwap()), pc)
    bot = np.minimum(np.minimum(ctx.day_open, ctx.vwap()), pc)
    up = (ctx.c > top).astype(float)
    dn = (ctx.c < bot).astype(float)
    upn = ctx.roll(up, nb, "min") == 1
    dnn = ctx.roll(dn, nb, "min") == 1
    return ctx.cross(upn).astype(int) - ctx.cross(dnn).astype(int)


def _last_hour_band(ctx, p):
    L, buf = p["last_min"], p["buf"]
    last = ctx.minutes_to_close <= L
    nd = int(ctx.day.max()) + 1
    hi = pd.Series(np.where(last, ctx.h, np.nan)).groupby(ctx.day).max().reindex(range(nd)).shift(1).to_numpy()[ctx.day]
    lo = pd.Series(np.where(last, ctx.l, np.nan)).groupby(ctx.day).min().reindex(range(nd)).shift(1).to_numpy()[ctx.day]
    prev_c = ctx.prev(ctx.c, 1)
    with np.errstate(all="ignore"):
        short = (ctx.c < hi * (1 - buf)) & (prev_c >= hi)
        long = (ctx.c > lo * (1 + buf)) & (prev_c <= lo)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-978", "Regression-slope t-stat follow",
           "A statistically significant linear drift of the day's return over a window means a persistent flow is "
           "working an order; the first bar where the slope t-stat exceeds the threshold is early in that flow.",
           {"win_min": [30, 60, 90], "t": [3.0, 4.0]}, _linreg_t, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-979", "Opening-range midpoint cross follow",
           "After the opening range is formed its midpoint is the balance point; a close that moves clear of it to "
           "one side shows the opening auction resolving that way.",
           {"range_min": [15, 30, 60], "buf": [0.0, 0.1, 0.25]}, _or_mid_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-980", "Typical-path deviation fade",
           "Intraday flow has a recurring time-of-day shape (average return path from the open over recent sessions); "
           "a stretch far from that path is a one-off imbalance that tends to mean-revert toward it.",
           {"k": [0.5, 1.0, 1.5], "n": [10, 20]}, _path_dev_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-981", "V-shape completion follow",
           "When price drops (or spikes) by an unusual amount and then recovers to the level where the move began, "
           "the sellers/buyers who pushed it are trapped and the recovery continues.",
           {"m_min": [5, 10, 15], "k": [1.0, 1.5, 2.0]}, _v_complete, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-982", "Realized semivariance dominance follow",
           "When squared up-moves dominate squared down-moves over a window, buyers are the ones moving price in "
           "jumps; the asymmetry of realized variance is a persistent-pressure marker.",
           {"win_min": [30, 60, 90], "th": [1.5, 2.0, 3.0]}, _semivar_follow, markets=("WIN",),
           source="assistant reasoning (realized semivariance literature)", author="agent"),
    Family("E-983", "US-open window drift follow",
           "The US cash open (10:30 or 11:30 Sao Paulo depending on DST) brings foreign flow into the index; the "
           "direction of the first minutes after it tends to carry.",
           {"w_min": [10, 15, 30], "k": [0.0, 0.5, 1.0]}, _us_open_drift, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-984", "Multi-session mean-price cross follow",
           "The average price of the last several sessions is the multi-day fair value that swing holders anchor on; "
           "a close through it shifts inventory control for the day.",
           {"n": [5, 10, 20], "buf": [0.0, 0.001]}, _multi_mean_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-985", "Previous-block midpoint cross follow",
           "The midpoint of the previous clock block's range is where the last block balanced; clearing it by a "
           "fraction of that range signals the new block's direction.",
           {"block_min": [30, 60, 120], "buf": [0.0, 0.25]}, _prev_block_mid, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-986", "Level-stack alignment onset",
           "When price holds above (or below) the day open, the session VWAP and the previous close together, every "
           "reference group of participants is on one side, so no one is defending against the move.",
           {"hold_min": [5, 10, 20, 30]}, _level_stack, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-987", "Prior last-hour band re-entry",
           "The previous session's last hour is where its final inventory was set; price coming back into that band "
           "from outside is the market accepting the old closing value and tends to keep going through it.",
           {"last_min": [30, 60, 90], "buf": [0.0, 0.0005]}, _last_hour_band, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
