"""Conveyor batch B-061 (agent, 2026-11-22). Anchors and flow-shape ideas: cumulative wicks, mid/hour/prior-VWAP anchors,
volume-weighted close, Crabel narrow-range, afternoon fade, session volume climax, yesterday-same-minute, midday box."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _sig(long, short):
    return np.asarray(long, bool).astype(int) - np.asarray(short, bool).astype(int)


def _reclaim(ctx, level, nb):
    """First close back across `level` after nb consecutive closes on the other side."""
    below = (ctx.c < level).astype(float)
    above = (ctx.c > level).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    return _sig(was_below & (ctx.c > level), was_above & (ctx.c < level))


def _wick_pressure(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    upw = ctx.h - np.maximum(ctx.o, ctx.c)
    low = np.minimum(ctx.o, ctx.c) - ctx.l
    num = ctx.roll(low - upw, nb, "sum")
    den = ctx.roll(ctx.h - ctx.l, nb, "sum")
    with np.errstate(divide="ignore", invalid="ignore"):
        q = np.where(den > 0, num / den, np.nan)
    return _sig(ctx.cross(q > th), ctx.cross(q < -th))


def _mid_reclaim(ctx, p):
    mid = (ctx.session_high(include_current=True) + ctx.session_low(include_current=True)) / 2.0
    s = _reclaim(ctx, mid, ctx.bars(p["dwell_min"]))
    late = (ctx.bar_in_day * ctx.tf) >= p["after_min"]
    return np.where(late, s, 0)


def _hour_open(ctx, p):
    nb = ctx.bars(p["dwell_min"])
    key = ctx.day.astype(np.int64) * 100 + (ctx.minute // 60).astype(np.int64)
    ho = pd.Series(ctx.o).groupby(key).transform("first").to_numpy()
    s = _reclaim(ctx, ho, nb)
    return np.where((ctx.minute % 60) >= p["dwell_min"], s, 0)


def _vw_close(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    sv = ctx.roll(ctx.v, nb, "sum")
    scv = ctx.roll(ctx.c * ctx.v, nb, "sum")
    mn = ctx.roll(ctx.c, nb, "mean")
    sd = ctx.roll(ctx.c, nb, "std")
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where((sv > 0) & (sd > 0), (scv / sv - mn) / sd, np.nan)
    return _sig(ctx.cross(z > th), ctx.cross(z < -th))


def _narrow_range(ctx, p):
    n = int(p["n_bars"])
    rng = ctx.h - ctx.l
    nr = ((rng == ctx.roll(rng, n, "min")) & (rng > 0)).astype(float)
    pn = ctx.prev(nr, 1) == 1
    return _sig(pn & (ctx.c > ctx.prev(ctx.h, 1)), pn & (ctx.c < ctx.prev(ctx.l, 1)))


def _afternoon_fade(ctx, p):
    k, nb = p["k"], int(p["ema_min"])
    r = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("abs_ret_same_minute", lambda: ctx.same_minute(np.abs(r), "mean"))
    ema = ctx.cached(("ema_b061", nb, ctx.tf), lambda: ctx.ema(ctx.c, ctx.bars(nb)))
    aft = (ctx.minute >= 13 * 60 + 30) & (ctx.minute < 16 * 60 + 30)
    short = aft & (r >= k * typ) & ctx.cross(ctx.c < ema)
    long = aft & (r <= -k * typ) & ctx.cross(ctx.c > ema)
    return _sig(long, short)


def _volume_climax(ctx, p):
    k = p["k"]
    vmax = pd.Series(ctx.v).groupby(ctx.day).transform(lambda z: z.cummax().shift(1)).to_numpy()
    med = ctx.cached("vol_med_b061", lambda: ctx.same_minute(ctx.v, "median"))
    ok = (ctx.v > vmax) & (ctx.v >= k * med) & ((ctx.bar_in_day * ctx.tf) >= p["elapsed_min"])
    d = np.sign(ctx.c - ctx.o)
    return _sig(ok & (d < 0), ok & (d > 0))


def _prev_vwap_reclaim(ctx, p):
    last = pd.Series(ctx.vwap()).groupby(ctx.day).last()
    lvl = last.reindex(range(int(ctx.day.max()) + 1)).shift(1).to_numpy()[ctx.day]
    return _reclaim(ctx, lvl, ctx.bars(p["dwell_min"]))


def _yesterday_same_minute(ctx, p):
    k = p["k"]
    cur = pd.DataFrame({"day": ctx.day, "minute": ctx.minute})
    y = pd.DataFrame({"day": ctx.day + 1, "minute": ctx.minute, "yc": ctx.c})
    yc = cur.merge(y, on=["day", "minute"], how="left")["yc"].to_numpy(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = ctx.c / yc - 1.0
    typ = ctx.cached("yz_typ", lambda: ctx.prev_sessions(np.abs(z), "mean"))
    return _sig(ctx.cross(z > k * typ), ctx.cross(z < -k * typ))


def _midday_box(ctx, p):
    w = int(p["width_min"])
    inbox = (ctx.minute >= 720) & (ctx.minute < 720 + w)
    hi = pd.Series(np.where(inbox, ctx.h, np.nan)).groupby(ctx.day).transform("max").to_numpy()
    lo = pd.Series(np.where(inbox, ctx.l, np.nan)).groupby(ctx.day).transform("min").to_numpy()
    after = (ctx.minute >= 720 + w) & (ctx.minute < 16 * 60)
    return _sig(after & ctx.cross(ctx.c > hi), after & ctx.cross(ctx.c < lo))


FAMILIES = [
    Family("E-608", "Cumulative lower/upper wick pressure follow",
           "Over a window, lower wicks much larger than upper wicks mean dips were repeatedly bought by passive "
           "liquidity that keeps absorbing; follow that side when the net wick share crosses a threshold.",
           {"win_min": [15, 30, 60], "th": [0.2, 0.3, 0.4]}, _wick_pressure, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-609", "Session-midpoint dwell reclaim follow",
           "After the price spent a while on one side of the developing day-range midpoint, the first close back "
           "across it marks the balance area being re-accepted and rotation usually continues across; follow.",
           {"after_min": [60, 120], "dwell_min": [10, 20, 30]}, _mid_reclaim, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-610", "Clock-hour open dwell reclaim follow",
           "Hourly opens are anchors for desks that scale by the hour; after staying on one side of this hour's "
           "open, a close back across it shows flow from that hour's participants switching; follow.",
           {"dwell_min": [10, 15, 20]}, _hour_open, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-611", "Volume-weighted close vs mean close follow",
           "When the volume-weighted mean close of a window sits above its simple mean, contracts traded at the "
           "higher prices: informed size is buying up; follow when the standardised gap crosses a threshold.",
           {"win_min": [30, 60, 90], "th": [0.3, 0.5, 0.7]}, _vw_close, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-612", "Narrowest-range bar break (Crabel NR-n)",
           "A bar with the smallest range of the last n bars shows participants stepping aside; the next bar "
           "closing beyond its extreme releases stored energy in that direction; follow.",
           {"n_bars": [4, 7, 10]}, _narrow_range, markets=("WIN",), source="assistant reasoning (Crabel NR7 idea)",
           author="agent"),
    Family("E-613", "Afternoon trend-day EMA-cross fade",
           "After a morning that moved more than usual, afternoon liquidity is thin and trend followers have "
           "already positioned; a close back through a medium EMA against the day shows exhaustion; fade the day.",
           {"k": [1.0, 1.5, 2.0], "ema_min": [20, 30, 60]}, _afternoon_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-614", "Session volume-climax bar fade",
           "The largest-volume bar of the session so far, with volume well above normal for the minute, is where "
           "the impatient side exhausts itself; the next move reverts against that bar's colour.",
           {"elapsed_min": [30, 60, 90], "k": [2.0, 3.0]}, _volume_climax, markets=("WIN",),
           source="assistant reasoning (volume climax)", author="agent"),
    Family("E-615", "Prior-session VWAP reclaim follow",
           "Yesterday's final VWAP is the average price of the whole day's inventory; after trading on one side of "
           "it for a while, a close back across means yesterday's holders are in or out of the money again; follow.",
           {"dwell_min": [10, 20, 30]}, _prev_vwap_reclaim, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-616", "Return versus same minute yesterday follow",
           "Price versus its level at the same clock minute of the previous session measures the speed of the "
           "day-over-day drift that funds benchmark against; follow when the gap exceeds its usual size.",
           {"k": [0.5, 1.0, 1.5]}, _yesterday_same_minute, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-617", "Midday box break follow",
           "The 12:00 lunch window is a low-liquidity balance; the first close beyond its range after the box "
           "ends shows afternoon (US-open) flow taking control; follow the break.",
           {"width_min": [30, 60, 90]}, _midday_box, markets=("WIN",), source="assistant reasoning", author="agent"),
]
