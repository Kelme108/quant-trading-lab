"""Conveyor batch B-133 (agent, 2026-11-24). Mixed themes: regression channel, point-scale excursions, cross-market
anomalies, previous-day range regime, VWAP dwell, hour-level carry, Donchian midlines."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _sgn(long, short):
    return long.astype(int) - short.astype(int)


def _linreg_channel_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    n = float(nb)
    y = ctx.c - ctx.day_open
    x = ctx.bar_in_day.astype(float)
    with np.errstate(all="ignore"):
        sy, sx = ctx.roll(y, nb, "sum"), ctx.roll(x, nb, "sum")
        sxy, sxx, syy = ctx.roll(x * y, nb, "sum"), ctx.roll(x * x, nb, "sum"), ctx.roll(y * y, nb, "sum")
        varx = sxx / n - (sx / n) ** 2
        cov = sxy / n - (sx / n) * (sy / n)
        slope = cov / varx
        fit = sy / n + slope * (x - sx / n)
        resvar = np.maximum(syy / n - (sy / n) ** 2 - slope ** 2 * varx, 0.0)
        sd = np.sqrt(resvar)
        ok = (sd > 0) & (varx > 0)
        short = ok & (y > fit + k * sd)
        long = ok & (y < fit - k * sd)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _point_excursion_fade(ctx, p):
    nb, pts = ctx.bars(p["n_min"]), p["pts"]
    with np.errstate(all="ignore"):
        mv = ctx.c - ctx.prev(ctx.c, nb)
        short = (mv >= pts) & (ctx.c < ctx.o)
        long = (mv <= -pts) & (ctx.c > ctx.o)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _comove_anomaly(ctx, p):
    k = p["k"]
    oc = ctx.other_close()
    first = pd.Series(oc).groupby(ctx.day).transform("first").to_numpy()
    with np.errstate(all="ignore"):
        wdo = oc / first - 1.0
        win = ctx.c / ctx.day_open - 1.0
        late = ctx.bar_in_day >= ctx.bars(30)
        short = late & (win >= 2 * k) & (wdo >= k)
        long = late & (win <= -2 * k) & (wdo <= -k)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _post_narrow_break(ctx, p):
    nb, ratio = ctx.bars(p["lookback_min"]), p["ratio"]
    d = ctx.day
    top = int(d.max()) + 1
    dh = pd.Series(ctx.h).groupby(d).max().reindex(range(top))
    dl = pd.Series(ctx.l).groupby(d).min().reindex(range(top))
    rng = dh - dl
    typ = rng.shift(2).rolling(10, min_periods=10).mean()
    narrow = (rng.shift(1) < ratio * typ).fillna(False).to_numpy(bool)[d]
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    with np.errstate(all="ignore"):
        long = narrow & (ctx.c > hi)
        short = narrow & (ctx.c < lo)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _vwap_dwell_departure(ctx, p):
    b, nb = p["band"], ctx.bars(p["dwell_min"])
    vw = ctx.vwap()
    with np.errstate(all="ignore"):
        dev = (ctx.c - vw) / vw
        inb = (np.abs(dev) < b).astype(float)
        was = ctx.roll(inb, nb, "min", include_current=False) == 1
        long = was & (dev >= b)
        short = was & (dev <= -b)
    return _sgn(long, short)


def _counter_burst_in_day_trend(ctx, p):
    nb, k = ctx.bars(p["burst_min"]), p["k"]
    vw = ctx.vwap()
    with np.errstate(all="ignore"):
        move = ctx.c / ctx.prev(ctx.c, nb) - 1.0
        typ = ctx.cached(("absmove", nb), lambda: ctx.prev_sessions(np.abs(move), "mean"))
        start_c, start_v = ctx.prev(ctx.c, nb), ctx.prev(vw, nb)
        long = (move <= -k * typ) & (start_c > start_v) & (ctx.c >= ctx.day_open)
        short = (move >= k * typ) & (start_c < start_v) & (ctx.c <= ctx.day_open)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _alternating_chop_break(ctx, p):
    n = int(p["n_alt"])
    with np.errstate(all="ignore"):
        s = np.sign(ctx.c - ctx.prev(ctx.c, 1))
        alt = ((s * ctx.prev(s, 1)) < 0).astype(float)
        run = ctx.roll(alt, n, "min", include_current=False) == 1
        hi = ctx.roll(ctx.h, n + 1, "max", include_current=False)
        lo = ctx.roll(ctx.l, n + 1, "min", include_current=False)
        long = run & (ctx.c > hi)
        short = run & (ctx.c < lo)
    return _sgn(long, short)


def _index_in_dollar_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    oc = ctx.other_close()
    with np.errstate(all="ignore"):
        r = np.log(ctx.c) - np.log(np.where(oc > 0, oc, np.nan))
        m, s = ctx.roll(r, nb, "mean"), ctx.roll(r, nb, "std")
        z = (r - m) / s
        short = (s > 0) & (z >= k)
        long = (s > 0) & (z <= -k)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _prev_hour_close_carry(ctx, p):
    q = p["q"]
    hr = (ctx.minute // 60).astype(float)
    g = pd.DataFrame({"d": ctx.day, "hr": hr, "h": ctx.h, "l": ctx.l, "c": ctx.c}).groupby(["d", "hr"])
    hh = g["h"].transform("max").to_numpy()
    ll = g["l"].transform("min").to_numpy()
    cc = g["c"].transform("last").to_numpy()
    ph, pl, pc, phr = ctx.prev(hh, 1), ctx.prev(ll, 1), ctx.prev(cc, 1), ctx.prev(hr, 1)
    with np.errstate(all="ignore"):
        new_hour = np.isfinite(phr) & (hr != phr) & np.isfinite(ph) & (ph > pl)
        loc = (pc - pl) / (ph - pl)
        long = new_hour & (loc >= 1 - q)
        short = new_hour & (loc <= q)
    return _sgn(long, short)


def _donchian_mid_cross(ctx, p):
    f = ctx.bars(p["fast_min"])
    s = ctx.bars(p["fast_min"] * p["mult"])
    if s <= f:
        s = f + 1
    with np.errstate(all="ignore"):
        mf = (ctx.roll(ctx.h, f, "max") + ctx.roll(ctx.l, f, "min")) / 2
        ms = (ctx.roll(ctx.h, s, "max") + ctx.roll(ctx.l, s, "min")) / 2
        long, short = mf > ms, mf < ms
    return _sgn(ctx.cross(long), ctx.cross(short))


FAMILIES = [
    Family("E-1328", "Regression-channel edge fade",
           "Price far outside the rolling least-squares channel (fit +/- k residual sd) has outrun its own trend line; "
           "momentum chasers and stop orders are exhausted and liquidity providers revert it toward the fitted line.",
           {"win_min": [30, 60, 90], "k": [2.0, 2.5, 3.0]}, _linreg_channel_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1329", "Point-scale excursion fade",
           "A move of 150+ index points in minutes is as large as the trade stop/target scale; scalpers take profit and "
           "stops sit behind it, so a bar closing against the excursion starts a give-back.",
           {"pts": [150, 250, 350], "n_min": [10, 20, 30]}, _point_excursion_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1330", "Index-with-dollar co-move anomaly fade",
           "The index normally moves against the dollar; when both are up (or both down) from the open the index move "
           "is not backed by the usual currency channel and is fragile, so fade the index.",
           {"k": [0.001, 0.002, 0.003]}, _comove_anomaly, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1331", "Post-narrow-day range break",
           "After a session whose range was below average, volatility tends to expand the next day (range clustering); "
           "a close through the recent high/low on such a day is the start of that expansion, so follow it.",
           {"lookback_min": [30, 60, 90], "ratio": [0.8, 1.0]}, _post_narrow_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1332", "VWAP-band dwell departure",
           "Price glued to the session VWAP for a long time means two-sided benchmark trading in balance; the first "
           "close leaving the band is the side that has won initiative, so follow the departure.",
           {"band": [0.0005, 0.001, 0.0015], "dwell_min": [15, 30, 60]}, _vwap_dwell_departure, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1333", "Counter-burst in the day's trend",
           "On a day trading on one side of VWAP and the open, a sharp burst against the day's side is mostly "
           "stop-run and small-trader flow; trend holders absorb it, so trade back with the day's side.",
           {"burst_min": [5, 10, 15], "k": [1.5, 2.0, 3.0]}, _counter_burst_in_day_trend, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1334", "Alternating-colour chop break",
           "A run of bars alternating up and down is a rotation where each side's market orders cancel; the first close "
           "beyond the chop's range means one side ran out of orders, so follow the break.",
           {"n_alt": [3, 4, 5]}, _alternating_chop_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1335", "Index-in-dollar-terms z-score fade",
           "The index divided by the dollar (index in USD) is the foreign investor's price; when it stretches from its "
           "recent mean, arbitrage and relative-value desks trade it back, and the index leg reverts.",
           {"win_min": [60, 120], "k": [2.0, 2.5, 3.0]}, _index_in_dollar_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1336", "Previous-hour close-location carry",
           "Desks and algos that work parent orders by clock hour continue into the next hour when the last hour "
           "closed near its high (low); at each hour start follow that close location.",
           {"q": [0.2, 0.3, 0.4]}, _prev_hour_close_carry, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1337", "Donchian-midline cross",
           "The midpoint of the fast channel crossing the midpoint of a slower channel (Ichimoku tenkan/kijun logic) "
           "marks a shift of the trading range's centre that trend followers using it act on together; follow it.",
           {"fast_min": [10, 20, 30], "mult": [2, 3]}, _donchian_mid_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
