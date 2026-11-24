"""Conveyor batch B-134 (agent, 2026-11-24). Mixed themes: return skew, Heikin-Ashi, opening drive, volume pace,
regression slope, TWAP-vs-VWAP, Aroon, clock-hour volume pace, plus two WIN-only timing/level ideas."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _out(long, short):
    return np.asarray(long, bool).astype(int) - np.asarray(short, bool).astype(int)


def _skew_fade(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    m = ctx.roll(r, n, "mean")
    s = ctx.roll(r, n, "std")
    m3 = ctx.roll(r ** 3, n, "mean")
    with np.errstate(all="ignore"):
        sk = (m3 - 3 * m * s ** 2 - m ** 3) / s ** 3
    return _out(ctx.cross(sk < -k), ctx.cross(sk > k))


def _ha_flip(ctx, p):
    nrun = int(p["run"])
    hac = (ctx.o + ctx.h + ctx.l + ctx.c) / 4.0
    hao = ctx.prev(ctx.ema(hac, 3), 1)
    up = hac > hao
    dn = hac < hao
    was_dn = ctx.roll(dn.astype(float), nrun, "min", include_current=False) == 1
    was_up = ctx.roll(up.astype(float), nrun, "min", include_current=False) == 1
    return _out(up & was_dn, dn & was_up)


def _open_drive_fade(ctx, p):
    k = p["k"]
    early = (ctx.bar_in_day < ctx.bars(p["win_min"])) & (ctx.bar_in_day >= ctx.bars(10))
    r = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("abs_r_same_minute", lambda: ctx.same_minute(np.abs(r), "mean"))
    short = early & (r >= k * typ) & (typ > 0) & (ctx.c < ctx.o)
    long = early & (r <= -k * typ) & (typ > 0) & (ctx.c > ctx.o)
    return _out(ctx.cross(long), ctx.cross(short))


def _volume_pace(ctx, p):
    k = p["k"]
    cv = ctx.cached("cumvol", lambda: pd.Series(ctx.v).groupby(ctx.day).cumsum().to_numpy())
    ref = ctx.cached("cumvol_ref", lambda: ctx.same_minute(cv, "mean"))
    with np.errstate(all="ignore"):
        pace = cv / ref
    ok = ctx.bar_in_day >= ctx.bars(p["min_min"])
    vw = ctx.vwap()
    long = ok & (pace >= k) & (ctx.c > vw) & (ctx.c > ctx.day_open)
    short = ok & (pace >= k) & (ctx.c < vw) & (ctx.c < ctx.day_open)
    return _out(ctx.cross(long), ctx.cross(short))


def _slope_onset(ctx, p):
    n, k = max(3, ctx.bars(p["win_min"])), p["k"]
    w = np.arange(n) - (n - 1) / 2.0
    num = np.convolve(ctx.c, w[::-1])[: ctx.n] / np.sum(w ** 2)
    rng = ctx.roll(ctx.h - ctx.l, n, "mean")
    with np.errstate(all="ignore"):
        s = num / rng
    s = np.where(ctx.bar_in_day >= n - 1, s, np.nan)
    return _out(ctx.cross(s > k), ctx.cross(s < -k))


def _twap_vwap(ctx, p):
    k = p["k"]
    cnt = pd.Series(np.ones(ctx.n)).groupby(ctx.day).cumsum().to_numpy()
    twap = pd.Series(ctx.c).groupby(ctx.day).cumsum().to_numpy() / cnt
    d = (ctx.vwap() - twap) / ctx.c
    ok = ctx.bar_in_day >= ctx.bars(p["min_min"])
    return _out(ctx.cross(ok & (d > k)), ctx.cross(ok & (d < -k)))


def _aroon(ctx, p):
    n, th = ctx.bars(p["win_min"]), p["th"]
    hh = np.concatenate([np.full(n, -np.inf, np.float32), ctx.h.astype(np.float32)])
    ll = np.concatenate([np.full(n, np.inf, np.float32), ctx.l.astype(np.float32)])
    sw = np.lib.stride_tricks.sliding_window_view
    up = 100.0 * sw(hh, n + 1).argmax(axis=1) / n
    dn = 100.0 * sw(ll, n + 1).argmin(axis=1) / n
    osc = up - dn
    ok = ctx.bar_in_day >= n
    return _out(ctx.cross(ok & (osc > th)), ctx.cross(ok & (osc < -th)))


def _hour_volume(ctx, p):
    k, em = p["k"], p["elapsed_min"]
    blk = (ctx.minute // 60).astype(int)
    df = pd.DataFrame({"d": ctx.day, "b": blk, "v": ctx.v, "o": ctx.o})
    g = df.groupby(["d", "b"])
    cum = g["v"].cumsum().to_numpy()
    hopen = g["o"].transform("first").to_numpy()
    tot = g["v"].sum()
    prev_tot = tot.groupby(level=0).shift(1)
    pt = prev_tot.reindex(pd.MultiIndex.from_arrays([ctx.day, blk])).to_numpy()
    elapsed = (ctx.minute % 60) + ctx.tf
    with np.errstate(all="ignore"):
        ratio = cum / (pt * elapsed / 60.0)
    ok = (elapsed >= em) & (elapsed <= 45)
    long = ok & (ratio >= k) & (ctx.c > hopen)
    short = ok & (ratio >= k) & (ctx.c < hopen)
    return _out(ctx.cross(long), ctx.cross(short))


def _tight_close_pair(ctx, p):
    n, q = ctx.bars(p["lookback_min"]), p["q"]
    hi = ctx.roll(ctx.h, n, "max", include_current=False)
    lo = ctx.roll(ctx.l, n, "min", include_current=False)
    rng = ctx.h - ctx.l
    with np.errstate(all="ignore"):
        loc = (ctx.c - ctx.l) / rng
    c1, loc1 = ctx.prev(ctx.c, 1), ctx.prev(loc, 1)
    up = (ctx.c > hi) & (loc >= 1 - q) & (loc1 >= 1 - q) & (c1 <= hi)
    dn = (ctx.c < lo) & (loc <= q) & (loc1 <= q) & (c1 >= lo)
    return _out(up, dn)


def _range_edge_zone(ctx, p):
    f, k = p["frac"], p["k"]
    hi, lo = ctx.session_high(True), ctx.session_low(True)
    rng = hi - lo
    typ = ctx.cached("rng_same_minute", lambda: ctx.same_minute(rng, "mean"))
    with np.errstate(all="ignore"):
        pos = (ctx.c - lo) / rng
    ok = (rng >= k * typ) & (typ > 0) & (ctx.bar_in_day >= ctx.bars(30))
    return _out(ctx.cross(ok & (pos >= f)), ctx.cross(ok & (pos <= 1 - f)))


FAMILIES = [
    Family("E-1338", "Return-skew extreme fade",
           "A rolling window whose returns are strongly skewed means one-sided spikes (stop runs, thin-book jumps) "
           "dominated; liquidity takers who chased the spike are offside and price drifts back. Fade the skew sign.",
           {"win_min": [60, 90, 120], "k": [1.0, 1.5, 2.0]}, _skew_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1339", "Heikin-Ashi colour flip after a run",
           "Smoothed candles that change colour after a run of the other colour mark the end of a persistent order "
           "flow; slower participants rebalancing keep pushing the new way. Follow the first flipped candle.",
           {"run": [2, 3, 4]}, _ha_flip, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1340", "Opening-drive fade",
           "In the first 30-60 minutes an outsized move from the open, with the current bar closing against it, is "
           "often overnight/news order flow exhausting; fade it back.",
           {"k": [1.5, 2.0, 3.0], "win_min": [30, 45, 60]}, _open_drive_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1341", "Cumulative volume pace follow",
           "When the day's cumulative volume runs well ahead of its usual pace for the clock, informed or "
           "institutional flow is in the market; follow the side of VWAP and day open the price is on.",
           {"k": [1.2, 1.5, 2.0], "min_min": [60, 120]}, _volume_pace, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1342", "Regression-slope onset",
           "A fitted slope of recent closes that becomes large relative to the average bar range marks a trend that "
           "is orderly rather than noisy; follow the cross of the normalised slope.",
           {"win_min": [20, 40, 60], "k": [0.1, 0.2, 0.3]}, _slope_onset, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1343", "TWAP-VWAP spread flip",
           "When VWAP rises above the plain time-average price, more volume traded at higher prices than time spent "
           "there: aggressive buyers. Follow the sign change of the spread (and the opposite for sellers).",
           {"k": [0.0001, 0.0002, 0.0004], "min_min": [30, 60]}, _twap_vwap, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1344", "Aroon oscillator cross",
           "When the most recent high is much fresher than the most recent low in the window, buyers are still "
           "making progress and sellers are not; follow the oscillator crossing a strong threshold.",
           {"win_min": [15, 30, 45], "th": [50, 80]}, _aroon, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1345", "Clock-hour volume pace follow",
           "Within a clock hour, volume running well above the previous hour's pace shows a participant arriving "
           "at the hour's start; follow the side of the hour's open the price is on.",
           {"k": [1.5, 2.0, 3.0], "elapsed_min": [15, 30]}, _hour_volume, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1346", "Two strong closes through the range edge",
           "Two successive bars closing at the extreme of their own range while the second breaks the recent "
           "high/low means aggressive one-sided taking with no pushback; follow it.",
           {"lookback_min": [10, 20, 30], "q": [0.2, 0.3]}, _tight_close_pair, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1347", "Session-range edge-zone entry",
           "Once the day's range is meaningful for the clock, closing in the top (bottom) part of it means the "
           "auction is accepting prices at the edge; follow the move into that zone.",
           {"frac": [0.8, 0.9], "k": [0.75, 1.0, 1.25]}, _range_edge_zone, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
