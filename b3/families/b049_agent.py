"""Conveyor batch B-049 (agent, 2026-11-21). Mixed themes: multi-day levels, opening-range midpoint, VWAP chop,
bar-streak exhaustion, record-range bars, historical VWAP deviation, price-volume correlation, volatility burst,
bar-colour dominance, central pivot."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _chan_poke(ctx, p):
    n, tol = int(p["n_sessions"]), p["tol"]
    nd = int(ctx.day.max()) + 1
    hi_d = pd.Series(ctx.h).groupby(ctx.day).max().reindex(range(nd)).rolling(n, min_periods=n).max().shift(1)
    lo_d = pd.Series(ctx.l).groupby(ctx.day).min().reindex(range(nd)).rolling(n, min_periods=n).min().shift(1)
    chh, chl = hi_d.to_numpy()[ctx.day], lo_d.to_numpy()[ctx.day]
    rng = ctx.h - ctx.l
    uw = ctx.h - np.maximum(ctx.o, ctx.c)
    lw = np.minimum(ctx.o, ctx.c) - ctx.l
    with np.errstate(invalid="ignore"):
        short = (ctx.h >= chh * (1 - tol)) & (rng > 0) & (uw >= 0.5 * rng) & (ctx.c < ctx.o)
        long = (ctx.l <= chl * (1 + tol)) & (rng > 0) & (lw >= 0.5 * rng) & (ctx.c > ctx.o)
    return long.astype(int) - short.astype(int)


def _or_mid_cross(ctx, p):
    nb = ctx.bars(p["or_min"])
    first = ctx.bar_in_day < nb
    g = pd.DataFrame({"d": ctx.day, "h": np.where(first, ctx.h, np.nan), "l": np.where(first, ctx.l, np.nan)})
    orh = g.groupby("d")["h"].transform("max").to_numpy()
    orl = g.groupby("d")["l"].transform("min").to_numpy()
    mid = (orh + orl) / 2.0
    vw = ctx.vwap()
    done = ~first
    up = done & (ctx.c > mid) & (ctx.c > vw)
    dn = done & (ctx.c < mid) & (ctx.c < vw)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _vwap_chop_fade(ctx, p):
    nb, m = ctx.bars(p["win_min"]), int(p["m"])
    vw = ctx.vwap()
    side = np.sign(ctx.c - vw)
    ps_ = np.nan_to_num(ctx.prev(side, 1))
    crossed = (side != ps_) & (side != 0) & (ps_ != 0)
    cnt = ctx.roll(crossed.astype(float), nb, "sum", include_current=False)
    chop = cnt >= m
    short = crossed & (side > 0) & chop
    long = crossed & (side < 0) & chop
    return long.astype(int) - short.astype(int)


def _hh_streak_end(ctx, p):
    n = int(p["n"])
    ph, pl = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    with np.errstate(invalid="ignore"):
        hh = (ctx.h > ph).astype(float)
        ll = (ctx.l < pl).astype(float)
        up_streak = ctx.roll(hh, n, "sum", include_current=False) == n
        dn_streak = ctx.roll(ll, n, "sum", include_current=False) == n
        short = up_streak & (ctx.h <= ph) & (ctx.c < ctx.o)
        long = dn_streak & (ctx.l >= pl) & (ctx.c > ctx.o)
    return long.astype(int) - short.astype(int)


def _record_range_bar(ctx, p):
    q, nb = p["q"], ctx.bars(p["warm_min"])
    rng = ctx.h - ctx.l
    prior = pd.Series(rng).groupby(ctx.day).transform(lambda z: z.cummax().shift(1)).to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        clv = (ctx.c - ctx.l) / rng
        rec = (rng > prior) & (ctx.bar_in_day >= nb) & (rng > 0)
        long = rec & (clv >= 1 - q)
        short = rec & (clv <= q)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _vwap_dev_hist_fade(ctx, p):
    k, nb = p["k"], ctx.bars(p["after_min"])
    vw = ctx.vwap()
    dev = (ctx.c - vw) / vw
    sd = ctx.cached("vwapdev_sd", lambda: ctx.prev_sessions(dev, "sd"))
    ok = ctx.bar_in_day >= nb
    with np.errstate(invalid="ignore"):
        short = ok & (dev > k * sd)
        long = ok & (dev < -k * sd)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _pv_corr_follow(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    x = ctx.c - ctx.prev(ctx.c, 1)
    y = ctx.v
    mx, my = ctx.roll(x, nb, "mean"), ctx.roll(y, nb, "mean")
    mxy, mxx, myy = ctx.roll(x * y, nb, "mean"), ctx.roll(x * x, nb, "mean"), ctx.roll(y * y, nb, "mean")
    with np.errstate(invalid="ignore", divide="ignore"):
        corr = (mxy - mx * my) / np.sqrt(np.maximum(mxx - mx * mx, 0) * np.maximum(myy - my * my, 0))
        up = corr >= th
        dn = corr <= -th
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _vol_burst_follow(ctx, p):
    k, nf, ns = p["k"], ctx.bars(p["fast_min"]), ctx.bars(60)
    rng = ctx.h - ctx.l
    fast, slow = ctx.roll(rng, nf, "mean"), ctx.roll(rng, ns, "mean")
    hi = ctx.roll(ctx.h, nf, "max", include_current=False)
    lo = ctx.roll(ctx.l, nf, "min", include_current=False)
    with np.errstate(invalid="ignore", divide="ignore"):
        burst = fast >= k * slow
        up = burst & (ctx.c > hi)
        dn = burst & (ctx.c < lo)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _colour_dominance(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    upb = (ctx.c > ctx.o).astype(float)
    dnb = (ctx.c < ctx.o).astype(float)
    us, ds = ctx.roll(upb, nb, "mean"), ctx.roll(dnb, nb, "mean")
    pc = ctx.prev(ctx.c, nb)
    with np.errstate(invalid="ignore"):
        up = (us >= th) & (ctx.c > pc)
        dn = (ds >= th) & (ctx.c < pc)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _pivot_cross(ctx, p):
    m, buf = int(p["hold_bars"]), p["buf"]
    piv = (ctx.prev_session_value("high") + ctx.prev_session_value("low") + ctx.prev_session_value("close")) / 3.0
    lo_c = ctx.roll(ctx.c, m, "min")
    hi_c = ctx.roll(ctx.c, m, "max")
    with np.errstate(invalid="ignore"):
        up = lo_c > piv * (1 + buf)
        dn = hi_c < piv * (1 - buf)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


FAMILIES = [
    Family("E-488", "Multi-day channel wick poke rejection",
           "Swing traders rest orders at the high/low of the last 5-20 sessions; a bar that reaches that edge, prints a "
           "long wick and closes against it has met that size, so fade back from the edge.",
           {"n_sessions": [5, 10, 20], "tol": [0.0005, 0.001, 0.002]}, _chan_poke,
           source="assistant reasoning", author="agent"),
    Family("E-489", "Opening-range midpoint cross with VWAP",
           "The midpoint of the opening range is the opening auction's balance; once the range is complete, a close "
           "that crosses it on the VWAP side shows the day's participants leaning that way, so follow.",
           {"or_min": [15, 30, 60]}, _or_mid_cross, source="assistant reasoning", author="agent"),
    Family("E-490", "VWAP cross-count chop fade",
           "When price has already crossed the VWAP several times in the last window, VWAP acts as a magnet inside a "
           "two-sided rotation; the next cross is noise that rotational traders lean against, so fade it.",
           {"win_min": [30, 60, 90], "m": [2, 3, 4]}, _vwap_chop_fade, source="assistant reasoning", author="agent"),
    Family("E-491", "Higher-high streak end fade",
           "After several bars in a row printing higher highs (lower lows), a bar that fails to extend and closes "
           "against the streak shows the chasing buyers (sellers) are exhausted; fade it.",
           {"n": [3, 4, 5]}, _hh_streak_end, source="assistant reasoning", author="agent"),
    Family("E-492", "Record-range bar closing at its extreme follow",
           "A bar with the widest range of the session so far that closes in the top (bottom) of its range is "
           "an unusually aggressive one-sided order flow that the book could not absorb; follow it.",
           {"q": [0.2, 0.25, 0.33], "warm_min": [30, 60, 90]}, _record_range_bar,
           source="assistant reasoning", author="agent"),
    Family("E-493", "Historical VWAP-deviation extreme fade",
           "Measured against the distribution of VWAP distances seen in the previous 20 sessions, a close several "
           "standard deviations from today's VWAP is a stretch intraday traders have repeatedly sold (bought); fade.",
           {"k": [2.0, 2.5, 3.0], "after_min": [15, 30, 60]}, _vwap_dev_hist_fade,
           source="assistant reasoning", author="agent"),
    Family("E-494", "Price-volume correlation follow",
           "When bar price changes correlate positively with volume, up moves are traded heavily and down moves "
           "lightly: aggressive buyers dominate; follow the sign when the correlation turns strongly one way.",
           {"win_min": [30, 60, 90], "th": [0.2, 0.3, 0.4]}, _pv_corr_follow,
           source="assistant reasoning", author="agent"),
    Family("E-495", "Volatility-burst extreme break follow",
           "When the average range of the last few minutes jumps well above the last hour's, new information or "
           "a large parent order is moving the market; a close beyond the burst window's extreme is followed.",
           {"k": [1.5, 2.0, 2.5], "fast_min": [10, 15, 20]}, _vol_burst_follow,
           source="assistant reasoning", author="agent"),
    Family("E-496", "Bar-colour dominance follow",
           "When most bars of the last window close up (down) and the net move agrees, a steady stream of small "
           "marketable orders is lifting offers (hitting bids) rather than one big print; follow it.",
           {"win_min": [20, 30, 45], "th": [0.65, 0.7, 0.75]}, _colour_dominance,
           source="assistant reasoning", author="agent"),
    Family("E-497", "Prior-session central pivot hold-cross follow",
           "The prior session's central pivot (H+L+C)/3 is a reference many desks publish; a run of closes "
           "that stays beyond it means the day accepted the new side, so follow the first such confirmed cross.",
           {"hold_bars": [1, 2, 3], "buf": [0.0, 0.0005, 0.001]}, _pivot_cross,
           source="assistant reasoning", author="agent"),
]
