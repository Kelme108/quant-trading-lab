"""Conveyor batch B-122 (agent, 2026-11-24). Mixed themes: dollar lead, day-open retest, up-bar share, gap bar,
VWAP slope pullback, stretch z-score, midday box break, staircase follow, volume-surge breakout."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family

W = ("WIN",)


def _dollar_lead(ctx, p):
    nb, k = ctx.bars(p["move_min"]), p["k"]
    ow = ctx.other_close()
    rd = ow / ctx.prev(ow, nb) - 1.0
    rw = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    td = ctx.cached(("td", nb), lambda: ctx.prev_sessions(np.abs(rd), "mean"))
    tw = ctx.cached(("tw", nb), lambda: ctx.prev_sessions(np.abs(rw), "mean"))
    # dollar falls hard while the index has not yet moved up -> buy the index (and the mirror)
    long = (rd <= -k * td) & (rw <= 0.5 * tw)
    short = (rd >= k * td) & (rw >= -0.5 * tw)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _day_open_retest(ctx, p):
    k = p["k"]
    r = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("abs_r_sm", lambda: ctx.same_minute(np.abs(r), "mean"))
    hi = pd.Series(r).groupby(ctx.day).cummax().to_numpy()
    lo = pd.Series(r).groupby(ctx.day).cummin().to_numpy()
    hi1, lo1 = ctx.prev(hi, 1), ctx.prev(lo, 1)
    long = (hi1 >= k * typ) & (ctx.l <= ctx.day_open) & (ctx.c > ctx.day_open)
    short = (lo1 <= -k * typ) & (ctx.h >= ctx.day_open) & (ctx.c < ctx.day_open)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _upbar_share(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    up = np.where(ctx.c > ctx.o, 1.0, np.where(ctx.c < ctx.o, 0.0, 0.5))
    share = ctx.roll(up, nb, "mean")
    short = share >= th
    long = share <= 1 - th
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _gap_bar_fill(ctx, p):
    k, nb = p["k"], ctx.bars(p["avg_min"])
    pc = ctx.prev(ctx.c, 1)
    rng = ctx.h - ctx.l
    avg = ctx.prev(ctx.roll(rng, nb, "mean"), 1)
    gap = ctx.o - pc
    short = (gap >= k * avg) & (avg > 0) & (ctx.c < pc)
    long = (-gap >= k * avg) & (avg > 0) & (ctx.c > pc)
    return long.astype(int) - short.astype(int)


def _vwap_slope_pullback(ctx, p):
    nb, k = ctx.bars(p["slope_min"]), p["k"]
    vw = ctx.vwap()
    s = vw / ctx.prev(vw, nb) - 1.0
    typ = ctx.cached(("vs", nb), lambda: ctx.prev_sessions(np.abs(s), "mean"))
    long = (s >= k * typ) & (ctx.l <= vw) & (ctx.c > vw)
    short = (s <= -k * typ) & (ctx.h >= vw) & (ctx.c < vw)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _stretch_z_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    m = ctx.roll(ctx.c, nb, "mean")
    sd = ctx.roll(ctx.c, nb, "std")
    z = np.where(sd > 0, (ctx.c - m) / np.where(sd > 0, sd, 1.0), 0.0)
    return ctx.cross(z <= -k).astype(int) - ctx.cross(z >= k).astype(int)


def _midday_box_break(ctx, p):
    start, width = int(p["start_min"]), int(p["width_min"])
    end = start + width
    inbox = (ctx.minute >= start) & (ctx.minute < end)
    g = pd.DataFrame({"d": ctx.day, "h": np.where(inbox, ctx.h, np.nan), "l": np.where(inbox, ctx.l, np.nan)})
    bh = g.groupby("d")["h"].transform("max").to_numpy()
    bl = g.groupby("d")["l"].transform("min").to_numpy()
    live = (ctx.minute >= end) & (ctx.minute < 15 * 60 + 30)
    up = live & (ctx.c > bh)
    dn = live & (ctx.c < bl)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _staircase(ctx, p):
    m = int(p["steps"])
    up = np.ones(ctx.n, bool)
    dn = np.ones(ctx.n, bool)
    for j in range(m):
        hj, hj1 = ctx.prev(ctx.h, j), ctx.prev(ctx.h, j + 1)
        lj, lj1 = ctx.prev(ctx.l, j), ctx.prev(ctx.l, j + 1)
        up &= (hj > hj1) & (lj > lj1)
        dn &= (hj < hj1) & (lj < lj1)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _volume_surge_break(ctx, p):
    nb, k = ctx.bars(p["lookback_min"]), p["vol_k"]
    med = ctx.cached("vol_med2", lambda: ctx.same_minute(ctx.v, "median"))
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    heavy = ctx.v >= k * med
    return (heavy & (ctx.c > hi)).astype(int) - (heavy & (ctx.c < lo)).astype(int)


def _range_close_streak(ctx, p):
    # narrow-range bar closing at its extreme after a wide opposite bar: absorption of the last push
    k, q = p["k"], p["q"]
    rng = ctx.h - ctx.l
    typ = ctx.cached("rng_sm", lambda: ctx.same_minute(rng, "median"))
    pr = ctx.prev(rng, 1)
    pb = ctx.prev(ctx.c, 1) - ctx.prev(ctx.o, 1)
    pos = np.where(rng > 0, (ctx.c - ctx.l) / np.where(rng > 0, rng, 1.0), 0.5)
    wide_dn = (pb < 0) & (pr >= k * typ)
    wide_up = (pb > 0) & (pr >= k * typ)
    long = wide_dn & (pos >= 1 - q) & (rng < pr) & (ctx.c > ctx.prev(ctx.o, 1))
    short = wide_up & (pos <= q) & (rng < pr) & (ctx.c < ctx.prev(ctx.o, 1))
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-1218", "Dollar lead on the index",
           "WIN and the dollar are negatively linked and WDO often reprices first; when the dollar moves sharply and "
           "the index has not yet moved, the index catches up in the opposite direction.",
           {"move_min": [5, 10, 20], "k": [1.5, 2.0, 3.0]}, _dollar_lead, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1219", "Day-open retest bounce",
           "After the day has drifted well away from its open, a return to the opening price that closes back on the "
           "trend side shows the day's early buyers/sellers still defend it; follow the original direction.",
           {"k": [0.5, 1.0, 1.5]}, _day_open_retest, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1220", "Up-bar share extreme fade",
           "When nearly every recent bar closes the same way the move is crowded and the next marginal buyer/seller "
           "is exhausted; fade the first bar the share reaches the extreme.",
           {"win_min": [10, 20, 30], "th": [0.7, 0.8, 0.9]}, _upbar_share, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1221", "Gap-bar fill",
           "A bar that opens with a gap from the previous close that is large for the recent range and then closes "
           "back through the previous close shows the gap was an overreaction; follow the fill.",
           {"k": [0.5, 1.0, 1.5], "avg_min": [10, 20]}, _gap_bar_fill, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1222", "Sloped-VWAP pullback",
           "When the session VWAP itself is rising or falling faster than usual, the day's average cost is trending; "
           "a dip to VWAP that closes back on the trend side is where trend traders add.",
           {"slope_min": [30, 60], "k": [1.0, 1.5, 2.0]}, _vwap_slope_pullback, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1223", "Rolling z-score stretch fade",
           "A close several standard deviations from its own rolling mean is a liquidity-driven stretch that "
           "mean-reverts within minutes; fade the first bar to get there.",
           {"win_min": [30, 60, 90], "k": [2.0, 2.5, 3.0]}, _stretch_z_fade, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1224", "Midday box break follow",
           "The thin midday hour builds a box of resting orders; the first close outside it after the box ends "
           "signals the return of the afternoon's directional flow (US open); follow it.",
           {"start_min": [690, 720, 750], "width_min": [30, 60]}, _midday_box_break, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1225", "Staircase of higher highs and higher lows",
           "A short run of bars each making both a higher high and a higher low (or lower/lower) is orderly "
           "one-sided flow rather than noise; follow when the staircase completes.",
           {"steps": [3, 4, 5]}, _staircase, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1226", "Volume-surge range break",
           "A close beyond the recent range on volume well above the usual for that minute of day means real "
           "participation, not a thin poke; follow it.",
           {"lookback_min": [10, 20, 30], "vol_k": [1.5, 2.0, 3.0]}, _volume_surge_break, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1227", "Absorption after a wide bar",
           "A wide bar followed by a smaller bar that closes at its far extreme and back over the wide bar's open "
           "means the push was absorbed by the other side; trade the reversal.",
           {"k": [1.5, 2.0, 3.0], "q": [0.25, 0.4]}, _range_close_streak, markets=W,
           source="assistant reasoning", author="agent"),
]
