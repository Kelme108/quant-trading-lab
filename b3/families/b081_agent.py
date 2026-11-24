"""Conveyor batch B-081 (agent, 2026-11-23). Mixed themes: lunch range, chop breaks, envelopes, trailing levels, bar-body quality, profile gaps, thrust."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _ffill_day(x, day):
    return pd.Series(x).groupby(day).ffill().to_numpy()


def _lunch_break(ctx, p):
    start = int(p["start_min"])
    end = start + 60
    win = (ctx.minute >= start) & (ctx.minute < end)
    g_h = pd.Series(np.where(win, ctx.h, np.nan)).groupby(ctx.day).cummax().to_numpy()
    g_l = pd.Series(np.where(win, ctx.l, np.nan)).groupby(ctx.day).cummin().to_numpy()
    hi, lo = _ffill_day(g_h, ctx.day), _ffill_day(g_l, ctx.day)
    live = (ctx.minute >= end) & (ctx.minute < end + int(p["after_min"]))
    up = live & (ctx.c > hi)
    dn = live & (ctx.c < lo)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _alt_chop_break(ctx, p):
    n = int(p["n"])
    col = np.sign(ctx.c - ctx.o)
    alt = ((col * ctx.prev(col, 1)) == -1).astype(float)
    chop = ctx.roll(alt, n, "sum") == n
    hi = ctx.roll(ctx.h, n + 1, "max")
    lo = ctx.roll(ctx.l, n + 1, "min")
    cp = np.nan_to_num(ctx.prev(chop.astype(float), 1)) == 1
    up = cp & (ctx.c > ctx.prev(hi, 1))
    dn = cp & (ctx.c < ctx.prev(lo, 1))
    return up.astype(int) - dn.astype(int)


def _keltner_fade(ctx, p):
    n, k = int(p["ema_bars"]), p["k"]
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    rg = ctx.cached(("rg", n), lambda: ctx.roll(ctx.h - ctx.l, n, "mean"))
    dist = (ctx.c - ema) / np.where(rg > 0, rg, np.nan)
    d1 = ctx.prev(dist, 1)
    short = (d1 > k) & (dist <= k)
    long = (d1 < -k) & (dist >= -k)
    return long.astype(int) - short.astype(int)


def _chandelier_recover(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    hh = ctx.roll(ctx.h, nb, "max")
    ll = ctx.roll(ctx.l, nb, "min")
    atr = ctx.roll(ctx.h - ctx.l, nb, "mean")
    long = ctx.c > hh - k * atr
    short = ctx.c < ll + k * atr
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _body_persistence(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    rng = ctx.h - ctx.l
    br = np.where(rng > 0, np.abs(ctx.c - ctx.o) / np.where(rng > 0, rng, 1.0), 0.0)
    m = ctx.roll(br, nb, "mean")
    net = ctx.c - ctx.prev(ctx.c, nb)
    cond = m >= th
    return ctx.cross(cond & (net > 0)).astype(int) - ctx.cross(cond & (net < 0)).astype(int)


def _pdc_reclaim(ctx, p):
    nb = ctx.bars(p["away_min"])
    pc = ctx.prev_session_value("close")
    below = (ctx.c < pc).astype(float)
    above = (ctx.c > pc).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    up = was_below & (ctx.c > pc)
    dn = was_above & (ctx.c < pc)
    return up.astype(int) - dn.astype(int)


def _line_break_flip(ctx, p):
    n = int(p["n"])
    hi = ctx.prev(ctx.roll(ctx.c, n, "max"), 1)
    lo = ctx.prev(ctx.roll(ctx.c, n, "min"), 1)
    s = np.where(ctx.c > hi, 1.0, np.where(ctx.c < lo, -1.0, np.nan))
    st = _ffill_day(s, ctx.day)
    prev_st = ctx.prev(st, 1)
    up = (st == 1) & (prev_st == -1)
    dn = (st == -1) & (prev_st == 1)
    return up.astype(int) - dn.astype(int)


def _vol_onset(ctx, p):
    nf, ratio = ctx.bars(p["fast_min"]), p["ratio"]
    ns = ctx.bars(60)
    r = np.abs(ctx.c / ctx.prev(ctx.c, 1) - 1.0)
    fast = ctx.roll(r, nf, "mean")
    slow = ctx.roll(r, max(ns, nf + 1), "mean")
    cond = (fast > ratio * slow) & (slow > 0)
    d = ctx.c - ctx.prev(ctx.c, nf)
    return ctx.cross(cond & (d > 0)).astype(int) - ctx.cross(cond & (d < 0)).astype(int)


def _thin_node(ctx, p):
    step, k = float(p["bin"]), p["k"]
    out = np.zeros(ctx.n)
    hist: dict = {}
    tot = 0.0
    prev_b = None
    cur_day = -1
    for i in range(ctx.n):
        if ctx.day[i] != cur_day:
            cur_day, hist, tot, prev_b = ctx.day[i], {}, 0.0, None
        b = int(np.floor(ctx.c[i] / step))
        if prev_b is not None and b != prev_b and len(hist) >= 3:
            avg = tot / len(hist)
            if avg > 0 and hist.get(b, 0.0) < k * avg:
                out[i] = 1 if b > prev_b else -1
        hist[b] = hist.get(b, 0.0) + ctx.v[i]
        tot += ctx.v[i]
        prev_b = b
    return out.astype(int)


def _thrust_bar(ctx, p):
    k = p["k"]
    pr = ctx.prev(ctx.h - ctx.l, 1)
    dc = ctx.c - ctx.prev(ctx.c, 1)
    up = (pr > 0) & (dc > k * pr)
    dn = (pr > 0) & (dc < -k * pr)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


FAMILIES = [
    Family("E-808", "Lunch-range breakout",
           "The thin midday hour builds a range of resting orders; a close beyond it after lunch shows the "
           "afternoon participants choosing a side, and stops beyond the range add fuel.",
           {"start_min": [690, 720, 750], "after_min": [90, 150]}, _lunch_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-809", "Alternating-colour chop break",
           "A string of alternating bar colours is two-sided balance; the first close beyond the whole chop "
           "range ends the balance and follows through.",
           {"n": [3, 4, 5]}, _alt_chop_break, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-810", "Keltner-envelope snapback",
           "A close far outside an EMA envelope scaled by the average bar range is an overextension; the first "
           "bar back inside the envelope shows buyers/sellers of the extreme giving up.",
           {"ema_bars": [20, 40], "k": [2.0, 3.0, 4.0]}, _keltner_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-811", "Chandelier-level recovery follow",
           "After a pullback deeper than k average ranges from the window extreme, a close back above that "
           "trailing level means trend holders have defended it; follow the recovery.",
           {"win_min": [30, 60], "k": [2.0, 3.0, 4.0]}, _chandelier_recover, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-812", "Persistent-body trend onset",
           "When most of each bar's range is body over a window, moves are one-sided with little two-way "
           "trade; the onset of that state in the net direction continues.",
           {"win_min": [15, 30, 60], "th": [0.5, 0.6]}, _body_persistence, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-813", "Previous-close reclaim",
           "The previous settlement-like close is a reference for overnight positions; after a spell on one "
           "side, a close back across it shifts the day's bias.",
           {"away_min": [10, 20, 40]}, _pdc_reclaim, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-814", "Close-line-break flip",
           "A close beyond the extreme close of the last n bars flips a line-break trend state; the first flip "
           "shows the other side taking control.",
           {"n": [3, 5, 8]}, _line_break_flip, markets=("WIN",), source="Japanese three-line break charting",
           author="agent"),
    Family("E-815", "Volatility-onset direction follow",
           "When recent average bar movement jumps above the hour's norm, new information is being priced; "
           "the direction of the burst keeps going while liquidity is being consumed.",
           {"fast_min": [5, 10], "ratio": [1.5, 2.0, 2.5]}, _vol_onset, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-816", "Thin volume-node crossing",
           "Price entering a price bin where little volume traded today has few resting counterparties, so it "
           "tends to slide through to the next accepted area; follow the entry direction.",
           {"bin": [100, 200, 300], "k": [0.25, 0.5]}, _thin_node, markets=("WIN",),
           source="auction market theory (low-volume nodes)", author="agent"),
    Family("E-817", "Range-multiple thrust bar",
           "A close that moves more than the previous bar's whole range beyond its close is a thrust that "
           "overwhelms the prior bar's liquidity; follow.",
           {"k": [1.0, 1.5, 2.0]}, _thrust_bar, markets=("WIN",), source="assistant reasoning", author="agent"),
]
