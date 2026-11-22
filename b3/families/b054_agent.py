"""Conveyor batch B-054 (agent, 2026-11-21). Reference-price holds, time-of-day anchors, volume troughs and bar-share extremes on WIN."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _ls(long, short):
    return long.astype(int) - short.astype(int)


def _open_revisit(ctx, p):
    nb = ctx.bars(p["away_min"])
    do = ctx.day_open
    was_above = ctx.roll((ctx.c > do).astype(float), nb, "min", include_current=False) == 1
    was_below = ctx.roll((ctx.c < do).astype(float), nb, "min", include_current=False) == 1
    long = was_above & (ctx.l <= do) & (ctx.c > do)
    short = was_below & (ctx.h >= do) & (ctx.c < do)
    return _ls(ctx.cross(long), ctx.cross(short))


def _prior_open_reject(ctx, p):
    nb = ctx.bars(p["away_min"])
    po = ctx.prev_session_value("open")
    was_below = ctx.roll((ctx.c < po).astype(float), nb, "min", include_current=False) == 1
    was_above = ctx.roll((ctx.c > po).astype(float), nb, "min", include_current=False) == 1
    short = was_below & (ctx.h >= po) & (ctx.c < po)
    long = was_above & (ctx.l <= po) & (ctx.c > po)
    return _ls(ctx.cross(long), ctx.cross(short))


def _vwap_z_fade(ctx, p):
    k = p["k"]
    vw = ctx.vwap()
    d = (ctx.c - vw) / vw
    typ = ctx.cached("vwap_absdev", lambda: ctx.same_minute(np.abs(d), "mean"))
    short = (d > k * typ) & (ctx.c < ctx.o)
    long = (d < -k * typ) & (ctx.c > ctx.o)
    return _ls(ctx.cross(long), ctx.cross(short))


def _upshare_fade(ctx, p):
    nb, q = ctx.bars(p["win_min"]), p["q"]
    share = ctx.roll((ctx.c > ctx.o).astype(float), nb, "mean")
    dn = ctx.roll((ctx.c < ctx.o).astype(float), nb, "mean")
    short = share >= q
    long = dn >= q
    return _ls(ctx.cross(long), ctx.cross(short))


def _vol_surge_follow(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    ar = np.abs(ctx.c / ctx.prev(ctx.c, 1) - 1.0)
    fast = ctx.roll(ar, nb, "mean")
    typ = ctx.cached(("fast_typ", nb), lambda: ctx.same_minute(fast, "mean"))
    surge = ctx.cross(fast > k * typ)
    mv = ctx.c - ctx.prev(ctx.c, nb)
    return np.where(surge & (mv > 0), 1, 0) - np.where(surge & (mv < 0), 1, 0)


def _noon_cross(ctx, p):
    anchor, nbh = p["anchor"], ctx.bars(p["hold_min"])
    pm = ctx.prev(ctx.minute.astype(float), 1)
    mask = (ctx.minute >= anchor) & (pm < anchor)
    ref = pd.Series(np.where(mask, ctx.c, np.nan)).groupby(ctx.day).ffill().to_numpy()
    live = (ctx.minute >= anchor + p["hold_min"]) & (ctx.minutes_to_close > 20)
    up = ctx.roll((ctx.c > ref).astype(float), nbh, "min") == 1
    dn = ctx.roll((ctx.c < ref).astype(float), nbh, "min") == 1
    return _ls(ctx.cross(live & up), ctx.cross(live & dn))


def _or_levels(ctx, nb):
    first = ctx.bar_in_day < nb
    g = pd.DataFrame({"d": ctx.day, "h": np.where(first, ctx.h, np.nan), "l": np.where(first, ctx.l, np.nan)})
    orh = g.groupby("d")["h"].transform("max").to_numpy()
    orl = g.groupby("d")["l"].transform("min").to_numpy()
    return first, orh, orl


def _or_mid_hold(ctx, p):
    nb, hb = ctx.bars(p["or_min"]), ctx.bars(p["hold_min"])
    first, orh, orl = _or_levels(ctx, nb)
    mid = (orh + orl) / 2.0
    done = ~first
    up = ctx.roll((ctx.c > mid).astype(float), hb, "min") == 1
    dn = ctx.roll((ctx.c < mid).astype(float), hb, "min") == 1
    live = done & (ctx.minutes_to_close > 20)
    return _ls(ctx.cross(live & up), ctx.cross(live & dn))


def _vol_trough_break(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    vmin = ctx.cached(("vmin", nb), lambda: ctx.roll(ctx.v, nb, "min"))
    v1 = ctx.prev(ctx.v, 1)
    trough = (v1 <= ctx.prev(vmin, 1)) & (v1 < k * ctx.prev(med, 1))
    long = trough & (ctx.c > ctx.prev(ctx.h, 1))
    short = trough & (ctx.c < ctx.prev(ctx.l, 1))
    return _ls(long, short)


def _or_volume_break(ctx, p):
    nb, k = ctx.bars(p["or_min"]), p["k"]
    first, orh, orl = _or_levels(ctx, nb)
    per = pd.Series(np.where(first, ctx.v, 0.0)).groupby(ctx.day).sum()
    ref = per.rolling(5, min_periods=3).mean().shift(1)
    idx = ctx.day.astype(int)
    today = per.reindex(range(int(ctx.day.max()) + 1)).to_numpy()[idx]
    refb = ref.reindex(range(int(ctx.day.max()) + 1)).to_numpy()[idx]
    live = (~first) & (ctx.minutes_to_close > 30) & (today > k * refb)
    return _ls(ctx.cross(live & (ctx.c > orh)), ctx.cross(live & (ctx.c < orl)))


def _roc_hook(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    mv = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    typ = ctx.cached(("roc_typ", nb), lambda: ctx.prev_sessions(np.abs(mv), "mean"))
    lo = ctx.roll(mv, 2 * nb, "min")
    hi = ctx.roll(mv, 2 * nb, "max")
    long = ctx.cross(mv > 0) & (lo < -k * typ)
    short = ctx.cross(mv < 0) & (hi > k * typ)
    return _ls(long, short)


FAMILIES = [
    Family("E-538", "Day-open revisit hold",
           "After trading on one side of the session open for a while, a bar that dips back to the open and closes on the "
           "original side shows the open price defended by that side's buyers/sellers; follow the original side.",
           {"away_min": [10, 20, 30]}, _open_revisit, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-539", "Prior-session open rejection",
           "The previous session's opening print is a reference few systems track; a poke into it from one side that "
           "closes back is rejected supply/demand; fade it.",
           {"away_min": [10, 20, 30]}, _prior_open_reject, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-540", "VWAP-deviation time-of-day z fade",
           "A distance from VWAP large compared with what this minute of the day usually shows is a stretch that "
           "mean-reverting liquidity providers fade once the bar turns.",
           {"k": [1.5, 2.0, 3.0]}, _vwap_z_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-541", "Bar-colour share extreme fade",
           "When nearly all recent bars have closed the same colour, aggressive flow is spent and the first bar count "
           "reaching the extreme share marks a point where the move is crowded; fade it.",
           {"win_min": [10, 20, 30], "q": [0.7, 0.8, 0.9]}, _upshare_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-542", "Realized-volatility surge direction follow",
           "A jump in short-window realized volatility above this time of day's norm signals new information arriving; "
           "informed flow keeps pushing in the direction of the move that caused it.",
           {"win_min": [5, 10, 15], "k": [1.5, 2.0, 3.0]}, _vol_surge_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-543", "Midday-price cross follow",
           "The price at a fixed midday clock mark is where the morning's positions are balanced; a held close beyond it "
           "in the afternoon shifts the balance and the new side keeps control.",
           {"anchor": [720, 780, 840], "hold_min": [10, 20, 30]}, _noon_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-544", "Opening-range midpoint hold",
           "The midpoint of the opening range is the opening auction's fair value; sustained closes beyond it after the "
           "range completes show which side won the opening and tend to continue.",
           {"or_min": [15, 30, 60], "hold_min": [3, 5, 10]}, _or_mid_hold, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-545", "Volume-trough bar break",
           "A bar with the lowest volume in a while means resting liquidity thinned out; the next bar that breaks its "
           "high or low finds little opposition and follows through.",
           {"win_min": [10, 20, 30], "k": [0.3, 0.5, 0.7]}, _vol_trough_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-546", "Opening-volume-backed range break",
           "A session whose opening range traded much more volume than recent opening ranges has strong participation; "
           "a break of that range is backed by real flow and continues.",
           {"or_min": [15, 30], "k": [1.2, 1.5, 2.0]}, _or_volume_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-547", "Momentum hook after an extreme",
           "After an outsized counter move, momentum turning back through zero marks forced liquidations ending; "
           "trade the turn.",
           {"win_min": [10, 20, 30], "k": [1.0, 1.5, 2.0]}, _roc_hook, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
