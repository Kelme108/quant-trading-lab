"""Conveyor batch B-057 (agent, 2026-11-21). Mixed themes: seasonality, anchors, regimes, volume-conditioned opens."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _sgn(long, short):
    return np.asarray(long, bool).astype(int) - np.asarray(short, bool).astype(int)


def _seasonal_path_fade(ctx, p):
    k, n = p["k"], int(p["sessions"])
    r = ctx.c / ctx.day_open - 1.0
    prof = ctx.cached(("prof", n), lambda: ctx.same_minute(r, "mean", n))
    typ = ctx.cached(("typ_abs", n), lambda: ctx.same_minute(np.abs(r), "mean", n))
    dev = r - prof
    short = dev > k * typ
    long = dev < -k * typ
    return _sgn(ctx.cross(long), ctx.cross(short))


def _day_open_cross(ctx, p):
    nb = ctx.bars(p["away_min"])
    below = (ctx.c < ctx.day_open).astype(float)
    above = (ctx.c > ctx.day_open).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    return _sgn(was_below & (ctx.c > ctx.day_open), was_above & (ctx.c < ctx.day_open))


def _autocorr_regime(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    ret = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    lag = ctx.prev(ret, 1)
    with np.errstate(all="ignore"):
        num = ctx.roll(ret * lag, nb, "mean")
        den = np.sqrt(ctx.roll(ret * ret, nb, "mean") * ctx.roll(lag * lag, nb, "mean"))
        ac = num / den
        sd = ctx.roll(ret, nb, "std")
        big = np.abs(ret) >= sd
        long = big & (((ac < -th) & (ret < 0)) | ((ac > th) & (ret > 0)))
        short = big & (((ac < -th) & (ret > 0)) | ((ac > th) & (ret < 0)))
    return _sgn(ctx.cross(long), ctx.cross(short))


def _us_open_anchor_follow(ctx, p):
    anchor, k = int(p["anchor_min"]), p["k"]
    a = pd.Series(np.where(ctx.minute == anchor, ctx.o, np.nan)).groupby(ctx.day).ffill().to_numpy()
    with np.errstate(all="ignore"):
        mv = ctx.c / a - 1.0
        typ = ctx.cached(("us_typ", anchor), lambda: ctx.same_minute(np.abs(mv), "mean"))
    end = ctx.minute + ctx.tf
    win = (end >= anchor + 10) & (end <= anchor + 70)
    long = win & (mv >= k * typ) & (mv > 0)
    short = win & (mv <= -k * typ) & (mv < 0)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _prior_mid_cross(ctx, p):
    nb = ctx.bars(p["away_min"])
    mid = (ctx.prev_session_value("high") + ctx.prev_session_value("low")) / 2.0
    below = (ctx.c < mid).astype(float)
    above = (ctx.c > mid).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    return _sgn(was_below & (ctx.c > mid), was_above & (ctx.c < mid))


def _same_minute_drift(ctx, p):
    n, th = int(p["sessions"]), p["th"]
    h = ctx.bars(30)
    fwd = (pd.Series(ctx.c).groupby(ctx.day).shift(-h) / pd.Series(ctx.c) - 1.0).to_numpy()
    m1 = ctx.cached(("fm1", n, h), lambda: ctx.same_minute(fwd, "mean", n))
    m2 = ctx.cached(("fm2", n, h), lambda: ctx.same_minute(fwd * fwd, "mean", n))
    with np.errstate(all="ignore"):
        t = m1 / np.sqrt(np.maximum(m2 - m1 * m1, 1e-18)) * np.sqrt(n)
    return _sgn(ctx.cross(t > th), ctx.cross(t < -th))


def _body_through_vwap(ctx, p):
    k = p["k"]
    vw = ctx.vwap()
    body = np.abs(ctx.c - ctx.o)
    typ = ctx.cached("body_typ", lambda: ctx.prev_sessions(body, "mean"))
    big = body >= k * typ
    return _sgn(big & (ctx.o < vw) & (ctx.c > vw), big & (ctx.o > vw) & (ctx.c < vw))


def _clean_side_break(ctx, p):
    nb, m, bb = ctx.bars(p["win_min"]), int(p["m"]), ctx.bars(p["brk_min"])
    vw = ctx.vwap()
    side = np.sign(ctx.c - vw)
    ps_ = ctx.prev(side, 1)
    flip = np.where(np.isnan(ps_), 0.0, (side != ps_).astype(float))
    cnt = ctx.roll(flip, nb, "sum")
    clean = cnt <= m
    hi = ctx.roll(ctx.h, bb, "max", include_current=False)
    lo = ctx.roll(ctx.l, bb, "min", include_current=False)
    long = clean & (ctx.c > vw) & (ctx.c > hi)
    short = clean & (ctx.c < vw) & (ctx.c < lo)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _heavy_open_break(ctx, p):
    nb, k = ctx.bars(p["open_min"]), p["k"]
    first = ctx.bar_in_day < nb
    d = ctx.day
    v0 = pd.Series(np.where(first, ctx.v, 0.0)).groupby(d).sum()
    typ = v0.shift(1).rolling(20, min_periods=10).mean().to_numpy()[d]
    vol0 = v0.to_numpy()[d]
    g = pd.DataFrame({"d": d, "h": np.where(first, ctx.h, np.nan), "l": np.where(first, ctx.l, np.nan)})
    orh = g.groupby("d")["h"].transform("max").to_numpy()
    orl = g.groupby("d")["l"].transform("min").to_numpy()
    done = ~first
    with np.errstate(all="ignore"):
        heavy = done & (vol0 >= k * typ)
        up = heavy & (ctx.c > orh)
        dn = heavy & (ctx.c < orl)
    return _sgn(ctx.cross(up), ctx.cross(dn))


def _colour_imbalance_absorb(ctx, p):
    nb, q = ctx.bars(p["win_min"]), p["q"]
    up = (ctx.c > ctx.o).astype(float)
    share = ctx.roll(up, nb, "mean")
    net = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    typ = ctx.cached(("net_typ", nb), lambda: ctx.prev_sessions(np.abs(net), "mean"))
    stuck = np.abs(net) <= 0.5 * typ
    short = stuck & (share >= q)
    long = stuck & (share <= 1.0 - q)
    return _sgn(ctx.cross(long), ctx.cross(short))


FAMILIES = [
    Family("E-568", "Seasonal-path deviation fade",
           "Price tends to follow an average intraday path (same minute, last sessions); when the day's move strays "
           "from that path by more than its usual size, the stray is liquidity-driven and reverts toward the path.",
           {"k": [0.75, 1.0, 1.5], "sessions": [10, 20]}, _seasonal_path_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-569", "Day-open cross follow",
           "After staying on one side of the session open for a while, a close across it shows the morning's "
           "positioning has been overturned; trapped traders add fuel to the move.",
           {"away_min": [15, 30, 45]}, _day_open_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-570", "Autocorrelation regime bar trade",
           "When recent one-bar returns are negatively autocorrelated the tape is mean-reverting (fade the large bar); "
           "when positively, it is trending (follow it).",
           {"win_min": [30, 60, 90], "th": [0.1, 0.2, 0.3]}, _autocorr_regime, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-571", "US-cash-open anchor follow",
           "From the US cash open, order flow from S&P-linked investors moves WIN; a move from the anchor that is "
           "larger than usual for the clock time is information-driven and keeps going.",
           {"anchor_min": [630, 690], "k": [1.0, 1.5, 2.0]}, _us_open_anchor_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-572", "Clean-side micro-trend break follow",
           "If the price has stayed almost entirely on one side of VWAP (few side flips), institutions are working an "
           "order on that side; a break of the last few minutes' extreme in that direction continues.",
           {"win_min": [60, 90], "m": [0, 1, 2], "brk_min": [10, 20]}, _clean_side_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-573", "Prior-day midpoint cross follow",
           "The previous session's range midpoint is a fair-value reference; a close across it after a spell on the "
           "other side shifts acceptance and follows through.",
           {"away_min": [15, 30, 60]}, _prior_mid_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-574", "Same-minute drift persistence",
           "Recurring flows (rebalancing, hedging, US data windows) push price the same way at the same clock "
           "time; trade the sign of the average forward 30-minute return when it is statistically distinct.",
           {"sessions": [10, 15, 20], "th": [1.0, 1.5, 2.0]}, _same_minute_drift, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-575", "Body-through-VWAP bar follow",
           "A single large-bodied bar that opens on one side of VWAP and closes on the other is an aggressive "
           "repricing through the benchmark algos trade against; follow it.",
           {"k": [0.5, 1.0, 1.5]}, _body_through_vwap, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-576", "Heavy-open-volume range break follow",
           "A heavy first window of volume relative to recent sessions signals large participants with a view; "
           "a break of that window's range afterward follows the aggressor.",
           {"open_min": [15, 30], "k": [0.8, 1.0, 1.2]}, _heavy_open_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-577", "Bar-colour imbalance without progress fade",
           "Many bars of one colour but little net displacement means the aggressive side is being absorbed by "
           "passive limit orders; fade the colour majority.",
           {"win_min": [20, 30, 45], "q": [0.6, 0.65, 0.7]}, _colour_imbalance_absorb, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
