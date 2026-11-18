"""Conveyor batch B-005 (agent, 2026-11-18). Mixed WIN ideas: gap retests, clock-hour and open-relative levels,
pre-flatten time-of-day fade, weak-volume pushes, burst exhaustion, trapped chasers, wick order-flow, wedges.
All levels are relative (the history is back-adjusted, so absolute round numbers are not used)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _typ(ctx):
    """Typical bar range at this minute of day (median over the 20 sessions before)."""
    return ctx.cached("b5_typ_rng", lambda: ctx.same_minute(ctx.h - ctx.l, "median"))


def _pm(long, short):
    long = np.asarray(long, bool)
    short = np.asarray(short, bool)
    return long.astype(int) - short.astype(int)


# E-039 -------------------------------------------------------------------------------------------
def _fvg_hold(ctx, p):
    g = float(p["gap_k"])
    nb = ctx.bars(p["window_min"])
    typ = _typ(ctx)
    h, l, c = ctx.h, ctx.l, ctx.c
    long = np.zeros(ctx.n, bool)
    short = np.zeros(ctx.n, bool)
    run_lo = np.full(ctx.n, np.inf)      # lowest low of the bars between the gap bar and now
    run_hi = np.full(ctx.n, -np.inf)
    for L in range(1, nb + 1):
        if L >= 2:
            run_lo = np.fmin(run_lo, ctx.prev(l, L - 1))
            run_hi = np.fmax(run_hi, ctx.prev(h, L - 1))
        t_l = ctx.prev(typ, L)
        # bullish gap at bar t-L: low(t-L) > high(t-L-2); zone [high(t-L-2), low(t-L)]
        top_b, bot_b = ctx.prev(l, L), ctx.prev(h, L + 2)
        bull = (top_b > bot_b) & (top_b - bot_b >= g * t_l)
        long |= bull & (run_lo > top_b) & (l <= top_b) & (l >= bot_b) & (c > top_b)
        # bearish gap at bar t-L: high(t-L) < low(t-L-2); zone [high(t-L), low(t-L-2)]
        lo_s, hi_s = ctx.prev(h, L), ctx.prev(l, L + 2)
        bear = (hi_s > lo_s) & (hi_s - lo_s >= g * t_l)
        short |= bear & (run_hi < lo_s) & (h >= lo_s) & (h <= hi_s) & (c < lo_s)
    return _pm(long & ~short, short & ~long)


# E-040 -------------------------------------------------------------------------------------------
def _hour_open_defence(ctx, p):
    k = float(p["k"])
    key = ctx.day.astype(np.int64) * 100 + (np.asarray(ctx.minute) // 60).astype(np.int64)
    s = pd.DataFrame({"k": key, "o": ctx.o, "h": ctx.h, "l": ctx.l})
    g = s.groupby("k", sort=False)
    ho = g["o"].transform("first").to_numpy()
    hh_prev = g["h"].cummax().groupby(s["k"]).shift(1).to_numpy()
    ll_prev = g["l"].cummin().groupby(s["k"]).shift(1).to_numpy()
    typ = _typ(ctx)
    pc = ctx.prev(ctx.c, 1)
    long = (hh_prev - ho >= k * typ) & (ctx.l <= ho) & (ctx.c > ho) & (pc > ho)
    short = (ho - ll_prev >= k * typ) & (ctx.h >= ho) & (ctx.c < ho) & (pc < ho)
    return _pm(ctx.cross(long), ctx.cross(short))


# E-041 -------------------------------------------------------------------------------------------
def _preflatten_fade(ctx, p):
    w, k = float(p["window_min"]), float(p["k"])
    r = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("b5_abs_r_same_minute", lambda: ctx.same_minute(np.abs(r), "mean"))
    win = ctx.minutes_to_close <= w
    long = win & (r <= -k * typ) & (ctx.c > ctx.prev(ctx.h, 1))
    short = win & (r >= k * typ) & (ctx.c < ctx.prev(ctx.l, 1))
    return _pm(ctx.cross(long), ctx.cross(short))


# E-042 -------------------------------------------------------------------------------------------
def _weak_push_fade(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    ratio = float(p["ratio"])
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    up = ctx.h > hi
    dn = ctx.l < lo
    bid = np.asarray(ctx.bar_in_day, float)
    day = pd.Series(ctx.day)

    def last(mask, x):
        sr = pd.Series(np.where(mask, x, np.nan))
        return sr.groupby(day).ffill().groupby(day).shift(1).to_numpy()

    vu, iu = last(up, ctx.v), last(up, bid)
    vd, idn = last(dn, ctx.v), last(dn, bid)
    mid = (ctx.h + ctx.l) / 2.0
    short = up & (ctx.v < ratio * vu) & (bid - iu <= nb) & (ctx.c < mid)
    long = dn & (ctx.v < ratio * vd) & (bid - idn <= nb) & (ctx.c > mid)
    return _pm(long & ~short, short & ~long)


# E-043 -------------------------------------------------------------------------------------------
def _burst_exhaustion(ctx, p):
    m, k = int(p["bars"]), float(p["k"])
    rng = ctx.h - ctx.l
    typ = _typ(ctx)
    bull = np.ones(ctx.n, bool)
    bear = np.ones(ctx.n, bool)
    accel = np.ones(ctx.n, bool)
    for i in range(1, m + 1):
        oi, ci = ctx.prev(ctx.o, i), ctx.prev(ctx.c, i)
        bull &= ci > oi
        bear &= ci < oi
        if i < m:
            accel &= ctx.prev(rng, i) > ctx.prev(rng, i + 1)
    big = ctx.prev(rng, 1) >= k * ctx.prev(typ, 1)
    short = bull & accel & big & (ctx.h <= ctx.prev(ctx.h, 1)) & (ctx.c < ctx.o)
    long = bear & accel & big & (ctx.l >= ctx.prev(ctx.l, 1)) & (ctx.c > ctx.o)
    return _pm(long, short)


# E-044 -------------------------------------------------------------------------------------------
def _failed_strong_close(ctx, p):
    k = float(p["k"])
    rng = ctx.h - ctx.l
    h1, l1, o1, c1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1), ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1)
    r1, t1 = ctx.prev(rng, 1), ctx.prev(_typ(ctx), 1)
    big = (r1 > 0) & (r1 >= k * t1)
    strong_up = big & (c1 - o1 >= 0.7 * r1) & (h1 - c1 <= 0.15 * r1)
    strong_dn = big & (o1 - c1 >= 0.7 * r1) & (c1 - l1 <= 0.15 * r1)
    mid1 = (h1 + l1) / 2.0
    return _pm(strong_dn & (ctx.c > mid1), strong_up & (ctx.c < mid1))


# E-045 -------------------------------------------------------------------------------------------
def _wick_imbalance_break(ctx, p):
    nb = ctx.bars(p["win_min"])
    th = float(p["th"])
    lw = np.minimum(ctx.o, ctx.c) - ctx.l
    uw = ctx.h - np.maximum(ctx.o, ctx.c)
    num = ctx.roll(lw - uw, nb, "sum")
    den = ctx.roll(ctx.h - ctx.l, nb, "sum")
    imb = np.where(den > 0, num / np.where(den > 0, den, 1.0), 0.0)
    imb = ctx.prev(imb, 1)                       # imbalance of the bars BEFORE the break bar
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    long = (imb >= th) & (ctx.c > hi)
    short = (imb <= -th) & (ctx.c < lo)
    return _pm(ctx.cross(long), ctx.cross(short))


# E-046 -------------------------------------------------------------------------------------------
def _adr_level_fade(ctx, p):
    f = float(p["frac"])

    def _adr():
        s = pd.DataFrame({"d": ctx.day, "h": ctx.h, "l": ctx.l})
        dr = (s.groupby("d")["h"].transform("max") - s.groupby("d")["l"].transform("min")).to_numpy()
        return ctx.prev_sessions(dr, "mean")      # previous 20 sessions only

    adr = ctx.cached("b5_adr", _adr)
    step = f * adr
    ok = np.isfinite(step) & (step > 0)
    step = np.where(ok, step, np.nan)
    o0 = ctx.day_open
    pc = ctx.prev(ctx.c, 1)
    ju = np.floor((ctx.h - o0) / step)
    lu = o0 + ju * step
    short = ok & (ju >= 1) & (pc < lu) & (ctx.c < lu)
    jd = np.ceil((ctx.l - o0) / step)
    ld = o0 + jd * step
    long = ok & (jd <= -1) & (pc > ld) & (ctx.c > ld)
    return _pm(long & ~short, short & ~long)


# E-047 -------------------------------------------------------------------------------------------
def _three_push_fade(ctx, p):
    m = ctx.bars(p["window_min"])
    nh = ctx.bars(p["nh_min"])
    hi = ctx.roll(ctx.h, nh, "max", include_current=False)
    lo = ctx.roll(ctx.l, nh, "min", include_current=False)
    up = ctx.h > hi
    dn = ctx.l < lo
    up_start = up & ~(ctx.prev(up.astype(float), 1) == 1)    # a new push after at least one pause bar
    dn_start = dn & ~(ctx.prev(dn.astype(float), 1) == 1)
    cu = ctx.roll(up_start.astype(float), m, "sum")
    cd = ctx.roll(dn_start.astype(float), m, "sum")
    rec_up = ctx.roll(up.astype(float), 3, "max") == 1
    rec_dn = ctx.roll(dn.astype(float), 3, "max") == 1
    short = (cu >= 3) & rec_up & ~up & (ctx.c < ctx.prev(ctx.l, 1))
    long = (cd >= 3) & rec_dn & ~dn & (ctx.c > ctx.prev(ctx.h, 1))
    return _pm(ctx.cross(long & ~short), ctx.cross(short & ~long))


# E-048 -------------------------------------------------------------------------------------------
def _close_vwap_level(ctx, p):
    w = float(p["window_min"])

    def _lvl():
        tp = (ctx.h + ctx.l + ctx.c) / 3.0
        last = ctx.minutes_to_close <= w
        s = pd.DataFrame({"d": ctx.day, "pv": np.where(last, tp * ctx.v, 0.0), "vv": np.where(last, ctx.v, 0.0)})
        agg = s.groupby("d")[["pv", "vv"]].sum()
        lv = agg["pv"] / agg["vv"].where(agg["vv"] > 0)
        lv = lv.reindex(range(int(ctx.day.max()) + 1)).shift(1)   # the PREVIOUS session's value
        return lv.to_numpy()[ctx.day]

    lv = ctx.cached(("b5_close_vwap", w), _lvl)
    pc = ctx.prev(ctx.c, 1)
    short = (pc < lv) & (ctx.h >= lv) & (ctx.c < lv)
    long = (pc > lv) & (ctx.l <= lv) & (ctx.c > lv)
    return _pm(long, short)


FAMILIES = [
    Family("E-039", "Fair-value-gap retest hold",
           "A three-bar gap (bar low above the high two bars earlier) marks a burst of one-sided market orders that "
           "left no two-sided trade in the zone; when price first comes back into the zone and closes back out on the "
           "impulse side, the impulse side's remaining resting orders absorbed the late counter-traders; follow it.",
           {"gap_k": [0.25, 0.5, 1.0], "window_min": [15, 30, 60]}, _fvg_hold,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-040", "Clock-hour open defence",
           "Hourly candles are the frame many desks and chart traders read; after the hour ran well away from its open, "
           "a return to the hour's open that closes back on the excursion side shows the side ahead for the hour "
           "defending a green (red) candle, and the retest-sellers are trapped; trade back toward the excursion.",
           {"k": [2, 3, 4]}, _hour_open_defence,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-041", "Pre-flatten day-move fade",
           "In the last hour or two the day traders who rode the day's move (and retail accounts facing broker "
           "auto-flatten) must close, which is order flow against the day's direction; on a day already moved more "
           "than usual for the minute, a bar closing beyond the previous bar against the move starts that unwind; fade.",
           {"window_min": [60, 90, 120], "k": [0.5, 1.0, 1.5]}, _preflatten_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-042", "Weak-volume new-extreme push fade",
           "A new recent high made on clearly less volume than the previous push to a high, and closing in the lower "
           "half of its bar, means fewer aggressive buyers answer each new price while sellers stay; the push is the "
           "last buyers' exhaustion, so fade it (mirror for lows).",
           {"lookback_min": [15, 30, 60], "ratio": [0.5, 0.7, 0.9]}, _weak_push_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-043", "Accelerating-burst exhaustion fade",
           "Consecutive same-direction bars with each range larger than the last, ending in an unusually large bar, are "
           "a stop/momentum-ignition cascade; once the next bar fails to extend and closes against it, the forced "
           "orders are spent and liquidity providers pull price back; fade.",
           {"bars": [2, 3, 4], "k": [1.5, 2.0, 3.0]}, _burst_exhaustion,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-044", "Failed strong-close bar fade",
           "A large bar that closes at its extreme attracts chasers at the close; when the very next bar closes back "
           "beyond that bar's midpoint, the chasers are under water at once and their stops sit just behind, so their "
           "exits push the reversal; fade the strong bar.",
           {"k": [0.75, 1.0, 1.5]}, _failed_strong_close,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-045", "Wick-imbalance range break",
           "When the recent bars carry much longer lower wicks than upper wicks, dips keep being bought by passive "
           "buyers while offers are lifted without rejection; a close through the window's high then confirms the "
           "absorbing side has won; follow the break in the direction of the wick imbalance.",
           {"win_min": [10, 20, 30], "th": [0.1, 0.2, 0.3]}, _wick_imbalance_break,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-046", "ADR-fraction level fade from the open",
           "Day traders set targets as fractions of the average daily range measured from the session open; at each "
           "open +/- j x frac x ADR take-profit orders rest, so a bar that reaches such a level from the open side and "
           "closes back shows the targets absorbing the push; fade back toward the open.",
           {"frac": [0.2, 0.25, 0.3]}, _adr_level_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-047", "Three-push wedge fade",
           "Three separate pushes to new short-term highs inside one window (a wedge) show each leg being sold into "
           "again; when the bar after the third push closes below the prior bar's low, the late buyers of the third "
           "push are trapped and the move reverts; fade (mirror for lows).",
           {"window_min": [30, 45, 60], "nh_min": [5, 10, 15]}, _three_push_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-048", "Prior-session closing VWAP rejection",
           "The volume-weighted price of yesterday's closing window is where index funds and institutions executed "
           "their close-benchmarked orders; they defend or re-enter near it, so a bar that reaches it from one side "
           "and closes back on that side meets their resting orders; trade away from the level.",
           {"window_min": [30, 60, 90]}, _close_vwap_level,
           markets=("WIN",), source="assistant reasoning", author="agent"),
]
