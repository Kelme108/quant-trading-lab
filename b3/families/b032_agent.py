"""Conveyor batch B-032 (agent, 2026-11-19). Mixed themes: record pullbacks, cross-market climax and value flips,
new reference levels (yesterday's same-minute price, yesterday's VWAP, today's widest bar, the morning range),
participation and volume-price coupling regimes, and contained impulse bars."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _mins(ctx):
    return ctx.bar_in_day * ctx.tf


def _gb(ctx, x):
    return pd.Series(np.asarray(x, float)).groupby(ctx.day)


def _out(ctx, long, short):
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-318 -------------------------------------------------------------------------------------------
def _record_pullback(ctx, p):
    k, f = p["k"], p["f"]
    r = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("b032_absr_sm", lambda: ctx.same_minute(np.abs(r), "mean"))
    sh, sl = ctx.session_high(True), ctx.session_low(True)
    dd, du = sh - ctx.c, ctx.c - sl
    pdd = _gb(ctx, dd).transform(lambda z: z.cummax().shift(1)).to_numpy()
    pdu = _gb(ctx, du).transform(lambda z: z.cummax().shift(1)).to_numpy()
    late = _mins(ctx) >= 30
    long = late & (r >= k * typ) & (pdd > 0) & (dd > f * pdd)
    short = late & (r <= -k * typ) & (pdu > 0) & (du > f * pdu)
    return _out(ctx, long, short)


# E-319 -------------------------------------------------------------------------------------------
def _dollar_climax(ctx, p):
    nb, q = ctx.bars(p["win_min"]), p["q"]
    w = ctx.other_close()
    g = _gb(ctx, w)
    whi = g.transform(lambda z: z.cummax().ffill()).to_numpy()
    wlo = g.transform(lambda z: z.cummin().ffill()).to_numpy()
    span = whi - wlo
    pos = np.where(span > 0, (w - wlo) / np.where(span > 0, span, 1.0), np.nan)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    brk_up, brk_dn = ctx.cross(ctx.c > hi), ctx.cross(ctx.c < lo)
    late = _mins(ctx) >= 30
    long = brk_dn & late & (pos >= 1.0 - q)      # WIN breaks down while the dollar sits at its session high
    short = brk_up & late & (pos <= q)           # WIN breaks up while the dollar sits at its session low
    return long.astype(int) - short.astype(int)


# E-320 -------------------------------------------------------------------------------------------
def _yday_same_minute_close(ctx):
    df = pd.DataFrame({"d": ctx.day, "m": ctx.minute, "v": ctx.c})
    pv = df.pivot_table(index="d", columns="m", values="v", aggfunc="last", dropna=False)
    pv = pv.reindex(range(int(ctx.day.max()) + 1)).shift(1)
    col = {m: i for i, m in enumerate(pv.columns)}
    return pv.to_numpy()[np.asarray(ctx.day, int), np.array([col[m] for m in ctx.minute])]


def _yday_minute_poke(ctx, p):
    nb = ctx.bars(p["away_min"])
    L = ctx.cached("b032_yday_minute", lambda: _yday_same_minute_close(ctx))
    below = ctx.roll((ctx.c < L).astype(float), nb, "min", include_current=False) == 1
    above = ctx.roll((ctx.c > L).astype(float), nb, "min", include_current=False) == 1
    short = below & (ctx.h >= L) & (ctx.c < L)
    long = above & (ctx.l <= L) & (ctx.c > L)
    return _out(ctx, long, short)


# E-321 -------------------------------------------------------------------------------------------
def _falling_participation(ctx, p):
    nb, ratio = ctx.bars(p["win_min"]), p["ratio"]
    vs = ctx.roll(ctx.v, nb, "sum")
    vp = ctx.prev(vs, nb)
    fall = vs < ratio * vp
    b = ctx.bars(15)
    hi = ctx.roll(ctx.h, b, "max", include_current=False)
    lo = ctx.roll(ctx.l, b, "min", include_current=False)
    up, dn = ctx.cross(ctx.c > hi), ctx.cross(ctx.c < lo)
    return (dn & fall).astype(int) - (up & fall).astype(int)


# E-322 -------------------------------------------------------------------------------------------
def _widest_bar_poke(ctx, p):
    age_b = ctx.bars(p["min_age_min"])
    rng = ctx.h - ctx.l
    cm_prev = _gb(ctx, rng).transform(lambda z: z.cummax().shift(1)).to_numpy()
    is_rec = np.isnan(cm_prev) | (rng >= cm_prev)
    idx = np.arange(ctx.n, dtype=float)
    wh = _gb(ctx, np.where(is_rec, ctx.h, np.nan)).ffill().to_numpy()
    wl = _gb(ctx, np.where(is_rec, ctx.l, np.nan)).ffill().to_numpy()
    wi = _gb(ctx, np.where(is_rec, idx, np.nan)).ffill().to_numpy()
    whp, wlp, wip = ctx.prev(wh), ctx.prev(wl), ctx.prev(wi)
    old = (idx - wip) >= age_b
    c1 = ctx.prev(ctx.c)
    short = old & (c1 < whp) & (ctx.h > whp) & (ctx.c < whp)
    long = old & (c1 > wlp) & (ctx.l < wlp) & (ctx.c > wlp)
    return _out(ctx, long, short)


# E-323 -------------------------------------------------------------------------------------------
def _yday_vwap_level(ctx):
    per = pd.Series(ctx.vwap()).groupby(ctx.day).last()
    per = per.reindex(range(int(ctx.day.max()) + 1)).shift(1)
    return per.to_numpy()[np.asarray(ctx.day, int)]


def _yday_vwap_cross(ctx, p):
    nb = ctx.bars(p["away_min"])
    pv = ctx.cached("b032_yday_vwap", lambda: _yday_vwap_level(ctx))
    was_below = ctx.roll((ctx.c < pv).astype(float), nb, "min", include_current=False) == 1
    was_above = ctx.roll((ctx.c > pv).astype(float), nb, "min", include_current=False) == 1
    long = was_below & (ctx.c > pv)
    short = was_above & (ctx.c < pv)
    return long.astype(int) - short.astype(int)


# E-324 -------------------------------------------------------------------------------------------
def _vol_decoupled(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    x = np.abs(ctx.c - ctx.prev(ctx.c))
    y = ctx.v
    mx, my = ctx.roll(x, nb, "mean"), ctx.roll(y, nb, "mean")
    mxy = ctx.roll(x * y, nb, "mean")
    sx, sy = ctx.roll(x, nb, "std"), ctx.roll(y, nb, "std")
    den = sx * sy
    corr = np.where(den > 0, (mxy - mx * my) / np.where(den > 0, den, 1.0), np.nan)
    weak = corr < th
    b = ctx.bars(10)
    hi = ctx.roll(ctx.h, b, "max", include_current=False)
    lo = ctx.roll(ctx.l, b, "min", include_current=False)
    up, dn = ctx.cross(ctx.c > hi), ctx.cross(ctx.c < lo)
    return (dn & weak).astype(int) - (up & weak).astype(int)


# E-325 -------------------------------------------------------------------------------------------
def _dollar_twap_flip(ctx, p):
    nb = ctx.bars(p["away_min"])
    w = ctx.other_close()
    tw = _gb(ctx, w).transform(lambda z: z.expanding().mean()).to_numpy()
    above, below = w > tw, w < tw
    was_below = ctx.roll(below.astype(float), nb, "min", include_current=False) == 1
    was_above = ctx.roll(above.astype(float), nb, "min", include_current=False) == 1
    late = _mins(ctx) >= 30
    short = late & was_below & above        # dollar turns up through its session average: sell the index
    long = late & was_above & below
    return long.astype(int) - short.astype(int)


# E-326 -------------------------------------------------------------------------------------------
def _morning_range_fade(ctx, p):
    start = p["start_min"]
    morning = ctx.minute < 720
    mh = _gb(ctx, np.where(morning, ctx.h, np.nan)).transform(lambda z: z.cummax().ffill()).to_numpy()
    ml = _gb(ctx, np.where(morning, ctx.l, np.nan)).transform(lambda z: z.cummin().ffill()).to_numpy()
    aft = ctx.minute >= start
    short = ctx.cross(ctx.c > mh) & aft
    long = ctx.cross(ctx.c < ml) & aft
    return long.astype(int) - short.astype(int)


# E-327 -------------------------------------------------------------------------------------------
def _contained_impulse_fade(ctx, p):
    k = p["k"]
    rng = ctx.h - ctx.l
    med = ctx.cached("b032_rng_sm", lambda: ctx.same_minute(rng, "median"))
    body = ctx.c - ctx.o
    big = (rng >= k * med) & (med > 0) & (np.abs(body) >= 0.6 * rng)
    b = ctx.bars(30)
    hi = ctx.roll(ctx.h, b, "max", include_current=False)
    lo = ctx.roll(ctx.l, b, "min", include_current=False)
    inside = (ctx.h <= hi) & (ctx.l >= lo)
    long = big & inside & (body < 0)
    short = big & inside & (body > 0)
    return _out(ctx, long, short)


FAMILIES = [
    Family("E-318", "Record-pullback dip buy on a trend day",
           "On a day already moved more than usual from the open, a pullback that first becomes deeper than every "
           "earlier pullback of the session triggers the trailing stops of the day's holders all at once; that forced "
           "selling is absorbed by the participant still driving the day, so buy the record pullback (mirror on a down day).",
           {"k": [0.5, 1.0, 1.5], "f": [1.0, 1.25, 1.5]}, _record_pullback, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-319", "Dollar-at-extreme climax index break fade",
           "A WIN break to a new short-term low while WDO sits at its own session high means both legs of the "
           "risk-off trade are stretched at once: the foreign desks' hedges are already in, the last sellers are "
           "the late locals, and macro dealers stop adding at the dollar extreme; fade the WIN break (mirror).",
           {"win_min": [10, 15, 30], "q": [0.1, 0.2, 0.3]}, _dollar_climax, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-320", "Yesterday's same-minute price poke fade",
           "Day traders compare today's tape with where the market stood at the same time yesterday (overlay "
           "charts, intraday P&L versus a day ago); after price has stayed on one side of yesterday's same-minute "
           "price, a bar that pokes through it and closes back meets those anchored orders, so trade away from it.",
           {"away_min": [5, 15, 30]}, _yday_minute_poke, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-321", "Falling-participation micro-break fade",
           "When the volume of the last window is clearly below the volume of the window before it today, the "
           "participants who were trading are leaving; a 15-minute break in that fading tape has no new size behind "
           "it and liquidity providers lean it back, so fade it (today's own volume decay, not the seasonal clock).",
           {"win_min": [30, 60], "ratio": [0.7, 0.85, 1.0]}, _falling_participation, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-322", "Widest-bar extreme poke fade",
           "Today's widest bar is the session's biggest one-shot burst; its high and low are where that burst met "
           "the resting orders that stopped it. A later bar that pokes through that extreme and closes back meets "
           "the same untouched liquidity, so the poke buyers (sellers) are trapped; trade away from the level.",
           {"min_age_min": [10, 30, 60]}, _widest_bar_poke, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-323", "Yesterday's VWAP cross follow",
           "Yesterday's full-session VWAP is the average cost of yesterday's inventory; after price has stayed on "
           "one side of it for a while, a close across puts that whole cohort from in-profit to under water (or the "
           "reverse), and their exits plus swing traders' entries push price on; follow the cross.",
           {"away_min": [15, 30, 60]}, _yday_vwap_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-324", "Volume-decoupled tape micro-break fade",
           "Normally bigger price steps come with more volume (information moves price with size); when the recent "
           "correlation between absolute bar moves and bar volume is low, price steps are made by quote shifts, not "
           "by committed size, so a 10-minute break then is noise that liquidity providers fade.",
           {"win_min": [30, 60], "th": [0.2, 0.35, 0.5]}, _vol_decoupled, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-325", "Dollar session-average flip, index follows",
           "When the dollar, after trading on one side of its own session average price for a while, crosses back "
           "through it, the day's FX flow has turned (foreign money now leaving or entering); equity desks act on "
           "the same flow a little later, so trade WIN against the dollar's flip.",
           {"away_min": [15, 30, 60]}, _dollar_twap_flip, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-326", "Morning-range afternoon break fade",
           "The 09:00-12:00 range is where the cash session's institutions did the day's main trade; an afternoon "
           "close beyond it is usually carried by the thinner afternoon crowd, while the morning participants hold "
           "their orders at their own range edges; fade the afternoon break back into the morning range.",
           {"start_min": [780, 840, 900]}, _morning_range_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-327", "Contained impulse bar fade",
           "A bar much wider than usual for its minute and almost all body that still stays inside the last 30 "
           "minutes' range hit the book hard without reaching any level where stops or breakout orders rest; with "
           "nothing to cascade, the aggressor's push is the whole move and market makers re-centre; fade it.",
           {"k": [1.5, 2.0, 2.5]}, _contained_impulse_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
