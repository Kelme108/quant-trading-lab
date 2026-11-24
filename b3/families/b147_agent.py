"""Conveyor batch B-147 (agent, 2026-11-24). Volume-profile POC, volume-clock, median and range-structure ideas."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _poc(ctx, bf):
    """Running point of control (price bin with most volume so far in the session), using bars < t.
    Returns (poc_before_bar, prior_session_final_poc)."""
    def build():
        tp = (ctx.h + ctx.l + ctx.c) / 3.0
        day = ctx.day
        out = np.full(ctx.n, np.nan)
        finals = {}
        cur = None
        counts: dict = {}
        best, bestv, width = None, -1.0, 1.0
        for i in range(ctx.n):
            d = day[i]
            if d != cur:
                if cur is not None and best is not None:
                    finals[cur] = best * width
                cur = d
                counts = {}
                best, bestv = None, -1.0
                width = max(float(ctx.day_open[i]) * bf, 1e-9)
            if best is not None:
                out[i] = best * width
            if np.isfinite(tp[i]):
                b = int(round(tp[i] / width))
                counts[b] = counts.get(b, 0.0) + float(ctx.v[i])
                if counts[b] > bestv:
                    bestv, best = counts[b], b
        if cur is not None and best is not None:
            finals[cur] = best * width
        prior = np.array([finals.get(int(d) - 1, np.nan) for d in day], float)
        return out, prior
    return ctx.cached(("poc", bf), build)


def _poc_cross(ctx, p):
    poc, _ = _poc(ctx, p["bin_frac"])
    age = ctx.bar_in_day >= ctx.bars(p["age_min"])
    up = ctx.cross((ctx.c > poc) & age)
    dn = ctx.cross((ctx.c < poc) & age)
    return up.astype(int) - dn.astype(int)


def _volume_clock(ctx, p):
    wb, k = ctx.bars(p["win_min"]), p["k"]
    day = ctx.day
    pc = ctx.prev(ctx.c, 1)
    step = np.where(np.isnan(pc), 0.0, ctx.c - pc)
    typ = ctx.cached("vc_typ", lambda: ctx.prev_sessions(np.abs(step), "mean"))
    mv = ctx.cached("vc_mv", lambda: ctx.prev_sessions(ctx.v, "mean"))
    z = np.full(ctx.n, np.nan)
    starts = np.r_[0, np.flatnonzero(np.diff(day)) + 1]
    ends = np.r_[starts[1:], ctx.n]
    for s, e in zip(starts, ends):
        cv = np.cumsum(ctx.v[s:e])
        target = cv - wb * mv[s:e]
        ok = np.isfinite(target) & (target >= cv[0])
        tsafe = np.where(ok, target, cv[0])
        j = np.searchsorted(cv, tsafe, side="left")
        j = np.minimum(j, np.arange(e - s))
        ret = ctx.c[s:e] - ctx.c[s:e][j]
        den = typ[s:e] * np.sqrt(wb)
        with np.errstate(divide="ignore", invalid="ignore"):
            zz = ret / den
        z[s:e] = np.where(ok, zz, np.nan)
    up = ctx.cross(z >= k)
    dn = ctx.cross(z <= -k)
    return up.astype(int) - dn.astype(int)


def _median_cross(ctx, p):
    n = ctx.bars(p["win_min"])
    med = ctx.cached(("med", n), lambda: pd.Series(ctx.c).groupby(ctx.day).transform(
        lambda z: z.rolling(n, min_periods=n).median()).to_numpy())
    slope_up = med > ctx.prev(med, 3)
    slope_dn = med < ctx.prev(med, 3)
    up = ctx.cross(ctx.c > med) & slope_up
    dn = ctx.cross(ctx.c < med) & slope_dn
    return up.astype(int) - dn.astype(int)


def _vwap_peak_turn(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    atr = ctx.cached("atr20", lambda: ctx.roll(ctx.h - ctx.l, 20, "mean"))
    dev = (ctx.c - ctx.vwap()) / atr
    mx = ctx.roll(dev, n, "max")
    mn = ctx.roll(dev, n, "min")
    d1 = ctx.prev(dev, 1)
    short = (d1 >= k) & (d1 >= ctx.prev(mx, 1) - 1e-12) & (dev < d1) & (ctx.c < ctx.prev(ctx.c, 1))
    long = (d1 <= -k) & (d1 <= ctx.prev(mn, 1) + 1e-12) & (dev > d1) & (ctx.c > ctx.prev(ctx.c, 1))
    return long.astype(int) - short.astype(int)


def _prior_thirds(ctx, p):
    f = p["frac"]
    pdh, pdl = ctx.prev_session_value("high"), ctx.prev_session_value("low")
    rng = pdh - pdl
    upper = pdl + (1 - f) * rng
    lower = pdl + f * rng
    up = ctx.cross(ctx.c > upper)
    dn = ctx.cross(ctx.c < lower)
    return up.astype(int) - dn.astype(int)


def _quartile_cross(ctx, p):
    q = p["q"]
    age = ctx.bar_in_day >= ctx.bars(p["age_min"])
    hi = ctx.session_high(include_current=False)
    lo = ctx.session_low(include_current=False)
    rng = hi - lo
    with np.errstate(divide="ignore", invalid="ignore"):
        pos = (ctx.c - lo) / rng
    up = ctx.cross((pos >= q) & (pos <= 1.0) & age)
    dn = ctx.cross((pos <= 1 - q) & (pos >= 0.0) & age)
    return up.astype(int) - dn.astype(int)


def _hikkake(ctx, p):
    k = p["k"]
    atr = ctx.cached("atr20", lambda: ctx.roll(ctx.h - ctx.l, 20, "mean"))
    h1, l1, c1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1), ctx.prev(ctx.c, 1)
    h2, l2 = ctx.prev(ctx.h, 2), ctx.prev(ctx.l, 2)
    h3, l3 = ctx.prev(ctx.h, 3), ctx.prev(ctx.l, 3)
    inside = (h2 <= h3) & (l2 >= l3) & ((h3 - l3) >= k * ctx.prev(atr, 3))
    long = inside & (l1 < l2) & (c1 < l2) & (ctx.c > h2)
    short = inside & (h1 > h2) & (c1 > h2) & (ctx.c < l2)
    return long.astype(int) - short.astype(int)


def _prior_poc_cross(ctx, p):
    _, prior = _poc(ctx, p["bin_frac"])
    up = ctx.cross(ctx.c > prior)
    dn = ctx.cross(ctx.c < prior)
    return up.astype(int) - dn.astype(int)


def _early_extreme_flip(ctx, p):
    early = p["early_min"]
    vw = ctx.vwap()
    shi = ctx.session_high(include_current=True)
    slo = ctx.session_low(include_current=True)
    hi_bar = pd.Series(np.where(ctx.h >= shi, ctx.bar_in_day, -1)).groupby(ctx.day).cummax().to_numpy()
    lo_bar = pd.Series(np.where(ctx.l <= slo, ctx.bar_in_day, -1)).groupby(ctx.day).cummax().to_numpy()
    early_hi = hi_bar * ctx.tf <= early
    early_lo = lo_bar * ctx.tf <= early
    late = ctx.minute >= p["start_min"]
    short = ctx.cross((ctx.c < vw) & early_hi & ~early_lo & late)
    long = ctx.cross((ctx.c > vw) & early_lo & ~early_hi & late)
    return long.astype(int) - short.astype(int)


def _poc_touch(ctx, p):
    poc, _ = _poc(ctx, p["bin_frac"])
    age = ctx.bar_in_day >= ctx.bars(p["age_min"])
    long = age & (ctx.o > poc) & (ctx.l <= poc) & (ctx.c > poc) & (ctx.c > ctx.o)
    short = age & (ctx.o < poc) & (ctx.h >= poc) & (ctx.c < poc) & (ctx.c < ctx.o)
    return long.astype(int) - short.astype(int)


W = ("WIN",)

FAMILIES = [
    Family("E-1468", "Running point-of-control cross follow",
           "The price bin with most session volume is where most participants hold positions; a close through it "
           "shifts them in or out of the money, so follow the side the price moves to.",
           {"bin_frac": [0.0003, 0.0005, 0.001], "age_min": [30, 60]}, _poc_cross, markets=W,
           source="assistant reasoning (market profile point of control)", author="agent"),
    Family("E-1469", "Volume-clock momentum follow",
           "Measuring the move over a fixed amount of traded volume instead of fixed time finds bursts where "
           "informed flow pushes price; follow a volume-time move that is large for its volume.",
           {"win_min": [15, 30, 60], "k": [1.5, 2.0]}, _volume_clock, markets=W,
           source="assistant reasoning (volume-clock sampling)", author="agent"),
    Family("E-1470", "Rolling-median cross with slope follow",
           "A rolling median ignores single spikes; a close crossing a median that already slopes the same way "
           "is a trend change not caused by one outlier bar.",
           {"win_min": [20, 40, 60]}, _median_cross, markets=W,
           source="assistant reasoning (robust moving average)", author="agent"),
    Family("E-1471", "VWAP deviation peak turn fade",
           "Institutional VWAP benchmarks pull price back; when the stretch from VWAP in ATR units has peaked "
           "within the window and the bar turns, trade back toward VWAP.",
           {"win_min": [10, 20, 30], "k": [1.5, 2.0, 3.0]}, _vwap_peak_turn, markets=W,
           source="assistant reasoning (VWAP benchmark reversion)", author="agent"),
    Family("E-1472", "Prior-range outer-zone entry follow",
           "Yesterday's range split in zones: moving from the middle into the upper or lower zone means accepting "
           "prices near the old extremes; follow the move.",
           {"frac": [0.25, 0.33, 0.4]}, _prior_thirds, markets=W,
           source="assistant reasoning (prior-day range zones)", author="agent"),
    Family("E-1473", "Session-range quartile entry follow",
           "Once the session range is established, a close that enters the top or bottom quartile from inside "
           "shows the market pushing toward the extreme where stops rest; follow it.",
           {"q": [0.7, 0.8, 0.9], "age_min": [60, 120]}, _quartile_cross, markets=W,
           source="assistant reasoning (range position)", author="agent"),
    Family("E-1474", "Hikkake false break reversal",
           "A break of an inside bar that fails and closes back past the opposite side traps breakout traders; "
           "their stops fuel the move the other way.",
           {"k": [0.5, 1.0, 1.5]}, _hikkake, markets=W,
           source="assistant reasoning (hikkake pattern)", author="agent"),
    Family("E-1475", "Prior-session POC cross follow",
           "Yesterday's most-traded price is a reference level watched by next-day participants; a close through "
           "it signals acceptance away from yesterday's value.",
           {"bin_frac": [0.0003, 0.0005, 0.001]}, _prior_poc_cross, markets=W,
           source="assistant reasoning (prior-day point of control)", author="agent"),
    Family("E-1476", "Early-extreme side flip",
           "When one session extreme was set early and the other was not, the morning's side lost control; a "
           "later close crossing VWAP toward the open-side confirms the day's drift.",
           {"early_min": [60, 90, 120], "start_min": [660, 690, 720]}, _early_extreme_flip, markets=W,
           source="assistant reasoning (time of session extremes)", author="agent"),
    Family("E-1477", "POC touch bounce",
           "A bar that dips to the session's most-traded price and closes back on its original side shows "
           "volume-defended value; trade the bounce.",
           {"bin_frac": [0.0003, 0.0005, 0.001], "age_min": [30, 60, 120]}, _poc_touch, markets=W,
           source="assistant reasoning (value area defence)", author="agent"),
]
