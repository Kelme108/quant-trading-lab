"""Conveyor batch B-111 (agent, 2026-11-24). Mixed themes: volatility squeeze, band re-entry, anchors (day open, clock-hour open, prior close), autocorrelation regime, cross-market anomaly, bar gaps, seasonal drift, shock-bar failure."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _sig(long, short):
    return np.asarray(long, bool).astype(int) - np.asarray(short, bool).astype(int)


def _reclaim(ctx, anchor, nb):
    below = (ctx.c < anchor).astype(float)
    above = (ctx.c > anchor).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    return was_below & (ctx.c > anchor), was_above & (ctx.c < anchor)


def _squeeze_release(ctx, p):
    k, w = p["k"], p["lookback_min"]
    n = ctx.bars(20)
    with np.errstate(all="ignore"):
        m = ctx.roll(ctx.c, n, "mean")
        sd = ctx.roll(ctx.c, n, "std")
        bw = sd / m
        sq = (bw <= ctx.roll(bw, ctx.bars(w), "min")).astype(float)
        recent = ctx.roll(sq, ctx.bars(10), "max", include_current=False) == 1
        up = recent & (ctx.c > m + k * sd)
        dn = recent & (ctx.c < m - k * sd)
    return _sig(ctx.cross(up), ctx.cross(dn))


def _band_reentry(ctx, p):
    n, k = ctx.bars(p["n_min"]), p["k"]
    with np.errstate(all="ignore"):
        m = ctx.roll(ctx.c, n, "mean")
        sd = ctx.roll(ctx.c, n, "std")
        z = np.where(sd > 0, (ctx.c - m) / sd, 0.0)
        zp = ctx.prev(z, 1)
        short = (zp > k) & (z <= k)
        long = (zp < -k) & (z >= -k)
    return _sig(long, short)


def _day_open_reclaim(ctx, p):
    up, dn = _reclaim(ctx, ctx.day_open, ctx.bars(p["away_min"]))
    return _sig(up, dn)


def _hour_open_reclaim(ctx, p):
    a = p["away_min"]
    ho = pd.Series(ctx.o).groupby([ctx.day, ctx.minute // 60]).transform("first").to_numpy()
    up, dn = _reclaim(ctx, ho, ctx.bars(a))
    ok = (ctx.minute % 60) >= a
    return _sig(up & ok, dn & ok)


def _autocorr_regime(ctx, p):
    n, th = ctx.bars(p["n_min"]), p["th"]
    with np.errstate(all="ignore"):
        r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
        num = ctx.roll(r * ctx.prev(r, 1), n, "mean")
        den = ctx.roll(r * r, n, "mean")
        rho = np.where(den > 0, num / den, 0.0)
        s = np.sign(r)
        long = ((rho > th) & (s > 0)) | ((rho < -th) & (s < 0))
        short = ((rho > th) & (s < 0)) | ((rho < -th) & (s > 0))
    return _sig(ctx.cross(long), ctx.cross(short))


def _corr_break(ctx, p):
    nb, k = ctx.bars(p["move_min"]), p["k"]
    oc = ctx.other_close()
    with np.errstate(all="ignore"):
        rs = ctx.c / ctx.prev(ctx.c, nb) - 1.0
        ro = oc / ctx.prev(oc, nb) - 1.0
        ts = ctx.cached(("tsz", nb), lambda: ctx.prev_sessions(np.abs(rs), "mean"))
        to = ctx.cached(("toz", nb), lambda: ctx.prev_sessions(np.abs(ro), "mean"))
        anomaly = (rs * ro > 0) & (np.abs(rs) >= k * ts) & (np.abs(ro) >= k * to)
        long = anomaly & (rs < 0)
        short = anomaly & (rs > 0)
    return _sig(ctx.cross(long), ctx.cross(short))


def _bar_gap(ctx, p):
    k, nb = p["k"], ctx.bars(p["lookback_min"])
    with np.errstate(all="ignore"):
        rng = ctx.h - ctx.l
        avg = ctx.roll(rng, nb, "mean", include_current=False)
        pc = ctx.prev(ctx.c, 1)
        gap = ctx.o - pc
        long = (gap > k * avg) & (ctx.c > pc) & (ctx.c > ctx.o)
        short = (gap < -k * avg) & (ctx.c < pc) & (ctx.c < ctx.o)
    return _sig(long, short)


def _seasonal_drift(ctx, p):
    nb, k = ctx.bars(p["horizon_min"]), p["k"]
    fwd = ctx.cached(("fwd", nb), lambda: (pd.Series(ctx.c).groupby(ctx.day).shift(-nb) / ctx.c - 1.0).to_numpy())
    mu = ctx.cached(("fwd_mu", nb), lambda: ctx.same_minute(fwd, "mean"))
    ab = ctx.cached(("fwd_ab", nb), lambda: ctx.same_minute(np.abs(fwd), "mean"))
    with np.errstate(all="ignore"):
        edge = np.where(ab > 0, mu / ab, 0.0)
    return _sig(ctx.cross(edge > k), ctx.cross(edge < -k))


def _shock_failure(ctx, p):
    k = p["k"]
    with np.errstate(all="ignore"):
        rng = ctx.h - ctx.l
        med = ctx.cached("rng_med", lambda: ctx.same_minute(rng, "median"))
        shock = ctx.prev(rng, 1) >= k * ctx.prev(med, 1)
        d = np.sign(ctx.prev(ctx.c, 1) - ctx.prev(ctx.o, 1))
        mid = (ctx.prev(ctx.h, 1) + ctx.prev(ctx.l, 1)) / 2.0
        short = shock & (d > 0) & (ctx.c < mid)
        long = shock & (d < 0) & (ctx.c > mid)
    return _sig(long, short)


def _prior_close_reclaim(ctx, p):
    up, dn = _reclaim(ctx, ctx.prev_session_value("close"), ctx.bars(p["away_min"]))
    return _sig(up, dn)


def _range_ratio_turn(ctx, p):
    # fade a move when the last-N-minute net move is large versus the path travelled (clean one-way push)
    nb, k = ctx.bars(p["win_min"]), p["k"]
    with np.errstate(all="ignore"):
        net = ctx.c - ctx.prev(ctx.c, nb)
        path = ctx.roll(np.abs(ctx.c - ctx.prev(ctx.c, 1)), nb, "sum")
        eff = np.where(path > 0, np.abs(net) / path, 0.0)
        atr = ctx.roll(ctx.h - ctx.l, ctx.bars(60), "mean")
        big = np.abs(net) >= k * atr
        cond = (eff >= 0.7) & big
        # reversal trigger: current bar closes against the push
        short = cond & (net > 0) & (ctx.c < ctx.o)
        long = cond & (net < 0) & (ctx.c > ctx.o)
    return _sig(ctx.cross(long), ctx.cross(short))


FAMILIES = [
    Family("E-1108", "Bollinger squeeze release follow",
           "After bandwidth hits its lowest of the lookback, resting orders on both sides are stacked; the first close "
           "outside the band releases the compressed range in that direction.",
           {"k": [1.5, 2.0], "lookback_min": [60, 120, 180]}, _squeeze_release,
           source="assistant reasoning (Bollinger bandwidth squeeze)", author="agent"),
    Family("E-1109", "Bollinger band re-entry fade",
           "A close beyond k standard deviations is an overshoot by impatient flow; the first close back inside the band "
           "shows the push is spent, so trade back toward the mean.",
           {"n_min": [20, 40, 60], "k": [1.5, 2.0, 2.5]}, _band_reentry,
           source="assistant reasoning (band re-entry)", author="agent"),
    Family("E-1110", "Day-open reclaim",
           "The session open is the reference price for the day's participants; after trading on one side for a while, "
           "the first close back across it shifts the day's balance, so follow the cross.",
           {"away_min": [15, 30, 60]}, _day_open_reclaim,
           source="assistant reasoning (open price as anchor)", author="agent"),
    Family("E-1111", "Clock-hour open reclaim",
           "Hourly candles are watched by many desks; after trading below/above the current hour's open, a close back "
           "across it marks a shift in that hour's control, so follow it.",
           {"away_min": [10, 15, 20]}, _hour_open_reclaim,
           source="assistant reasoning (hourly candle anchor)", author="agent"),
    Family("E-1112", "Autocorrelation regime switch",
           "When the recent lag-1 return autocorrelation is strongly negative the market is bouncing (fade the last bar); "
           "when strongly positive it is trending in small steps (follow it).",
           {"n_min": [30, 60, 90], "th": [0.15, 0.25, 0.35]}, _autocorr_regime,
           source="assistant reasoning (serial correlation regimes)", author="agent"),
    Family("E-1113", "Index and dollar moving together: fade",
           "WIN and WDO normally move in opposite directions; a large simultaneous same-direction move is an anomaly "
           "driven by one-sided flow in a thin market and tends to be reversed.",
           {"move_min": [10, 20, 30], "k": [0.5, 1.0, 1.5]}, _corr_break,
           source="assistant reasoning (WIN/WDO inverse relation)", author="agent"),
    Family("E-1114", "Bar-gap continuation",
           "A bar opening far from the previous close, relative to the recent average range, shows an order burst between "
           "bars; if the bar then closes beyond the old close in the gap direction, follow.",
           {"k": [0.5, 1.0, 1.5], "lookback_min": [60, 120]}, _bar_gap,
           source="assistant reasoning (inter-bar gaps)", author="agent"),
    Family("E-1115", "Seasonal minute drift",
           "Some clock times show a recurring one-way drift (scheduled flows, index rebalancing, data releases); trade the "
           "sign of the average forward return from this minute over the previous 20 sessions when it is consistent.",
           {"horizon_min": [15, 30, 60], "k": [0.3, 0.5]}, _seasonal_drift,
           source="assistant reasoning (intraday seasonality)", author="agent"),
    Family("E-1116", "Shock-bar failure",
           "A bar with a range far above the norm for its minute of day is a burst of aggressive orders; if the next bar "
           "closes back through the shock bar's midpoint, the burst is being absorbed, so trade against it.",
           {"k": [1.5, 2.0, 3.0]}, _shock_failure,
           source="assistant reasoning (absorption after bursts)", author="agent"),
    Family("E-1117", "Prior-close reclaim",
           "The previous session's close is the settlement reference for overnight and gap positions; after trading on "
           "one side of it for a while, a close back across it signals gap holders giving up, so follow.",
           {"away_min": [15, 30, 60]}, _prior_close_reclaim,
           source="assistant reasoning (prior close anchor)", author="agent"),
]
