"""Conveyor batch B-144 (agent, 2026-11-24). Mixed themes: VWAP stretch, volatility expansion, cross-market lead-lag, clock-hour open, day-open, volume dry-up."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _atr(ctx, minutes):
    nb = ctx.bars(minutes)
    return ctx.cached(("atr", nb), lambda: ctx.roll(ctx.h - ctx.l, nb, "mean"))


def _vwap_stretch(ctx, p):
    k = p["k"]
    vw = ctx.vwap()
    dist = (ctx.c - vw) / _atr(ctx, 60)
    short = dist > k
    long = dist < -k
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _atr_expansion(ctx, p):
    k = p["k"]
    ratio = _atr(ctx, 10) / _atr(ctx, 60)
    sign = np.sign(ctx.c - ctx.o)
    on = ctx.cross(ratio > k)
    return np.where(on, sign, 0).astype(int)


def _rets(ctx, p):
    nb = ctx.bars(p["lag_min"])
    oc = ctx.other_close()
    ro = np.nan_to_num(oc / ctx.prev(oc, nb) - 1.0)
    rw = np.nan_to_num(ctx.c / ctx.prev(ctx.c, nb) - 1.0)
    typ = ctx.prev_sessions(np.abs(ro), "mean")
    return ro, rw, typ


def _usd_lag(ctx, p):
    k = p["k"]
    ro, rw, typ = _rets(ctx, p)
    short = (ro >= k * typ) & (typ > 0) & (rw >= 0)
    long = (ro <= -k * typ) & (typ > 0) & (rw <= 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _comove_fade(ctx, p):
    k = p["k"]
    ro, rw, typ = _rets(ctx, p)
    typw = ctx.prev_sessions(np.abs(rw), "mean")
    both_up = (ro >= k * typ) & (rw >= k * typw) & (typ > 0) & (typw > 0)
    both_dn = (ro <= -k * typ) & (rw <= -k * typw) & (typ > 0) & (typw > 0)
    return ctx.cross(both_dn).astype(int) - ctx.cross(both_up).astype(int)


def _day_open_reclaim(ctx, p):
    nb = ctx.bars(p["away_min"])
    below = (ctx.c < ctx.day_open).astype(float)
    above = (ctx.c > ctx.day_open).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    up = was_below & (ctx.c > ctx.day_open)
    dn = was_above & (ctx.c < ctx.day_open)
    return up.astype(int) - dn.astype(int)


def _expanding_run(ctx, p):
    f = p["body_frac"]
    rng = ctx.h - ctx.l
    body = ctx.c - ctx.o
    strong_up = (body > 0) & (body >= f * rng)
    strong_dn = (body < 0) & (-body >= f * rng)
    r1, r2 = ctx.prev(rng, 1), ctx.prev(rng, 2)
    wide = (rng > r1) & (r1 > r2)
    up = wide & strong_up & (ctx.prev(strong_up.astype(float), 1) == 1) & (ctx.prev(strong_up.astype(float), 2) == 1)
    dn = wide & strong_dn & (ctx.prev(strong_dn.astype(float), 1) == 1) & (ctx.prev(strong_dn.astype(float), 2) == 1)
    return up.astype(int) - dn.astype(int)


def _hour_open_fade(ctx, p):
    k = p["k"]
    at_hour = (ctx.minute % 60) < ctx.tf
    ho = pd.Series(np.where(at_hour, ctx.o, np.nan)).groupby(ctx.day).ffill().to_numpy()
    dev = (ctx.c - ho) / _atr(ctx, 60)
    long = dev < -k
    short = dev > k
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _upbar_share(ctx, p):
    nb = ctx.bars(p["win_min"])
    q = p["q"]
    share = ctx.roll((ctx.c > ctx.o).astype(float), nb, "mean")
    dshare = ctx.roll((ctx.c < ctx.o).astype(float), nb, "mean")
    return ctx.cross(share >= q).astype(int) - ctx.cross(dshare >= q).astype(int)


def _dryup_expansion(ctx, p):
    m, k = int(p["dry_bars"]), p["k"]
    nb = ctx.bars(20)
    vm = ctx.roll(ctx.v, nb, "mean", include_current=False)
    small = (ctx.v < 0.7 * vm).astype(float)
    dry = ctx.roll(small, m, "min", include_current=False) == 1
    trig = dry & (ctx.v > k * vm)
    sign = np.sign(ctx.c - ctx.o)
    return np.where(trig, sign, 0).astype(int)


def _late_open_stretch(ctx, p):
    k, start = p["k"], p["start_hour"]
    r = ctx.c / ctx.day_open - 1.0
    typical = ctx.cached("abs_ret_same_minute", lambda: ctx.same_minute(np.abs(r), "mean"))
    late = ctx.minute >= int(start * 60)
    short = late & (r >= k * typical) & (typical > 0)
    long = late & (r <= -k * typical) & (typical > 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


FAMILIES = [
    Family("E-1438", "VWAP stretch fade in ATR units",
           "A close several average bar-ranges away from session VWAP is an over-extension by impatient aggressors; "
           "liquidity providers and VWAP-benchmarked algos pull price back, so fade the first bar of the stretch.",
           {"k": [3, 5, 7]}, _vwap_stretch, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1439", "Short/long ATR expansion follow",
           "When the 10-minute average range jumps relative to the 60-minute one, a new information flow has arrived "
           "and the first expansion bar's direction tends to persist while slower participants catch up.",
           {"k": [1.5, 2.0, 2.5]}, _atr_expansion, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1440", "Dollar-leads, index-lags inverse",
           "WIN and WDO are normally inversely related; when the dollar makes an unusual move and the index has not "
           "yet reacted, index arbitrageurs/hedgers move WIN the opposite way a few minutes later.",
           {"lag_min": [5, 10, 15], "k": [1.0, 1.5, 2.0]}, _usd_lag, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1441", "Day-open reclaim after a stay",
           "After price spends a while on one side of the session open, a close back through it shows the earlier "
           "side's positions are under water; follow the cross.",
           {"away_min": [15, 30, 60]}, _day_open_reclaim, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1442", "Three expanding strong bars follow",
           "Three same-direction bodies with widening ranges show escalating urgency of one side; follow the third.",
           {"body_frac": [0.5, 0.6, 0.7]}, _expanding_run, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1443", "Clock-hour open magnet fade",
           "Hourly opens are anchors for desks that mark intraday P&L by the hour; a large drift away from the "
           "current hour's open tends to partly revert.",
           {"k": [3, 4, 5]}, _hour_open_fade, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1444", "Up-bar share persistence",
           "When nearly all recent bars close in one colour, a persistent one-sided order flow (e.g. a large "
           "parent order sliced over time) is being worked; follow its onset.",
           {"win_min": [20, 30, 45], "q": [0.7, 0.8]}, _upbar_share, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-1445", "Volume dry-up then expansion follow",
           "After several low-volume bars, a sudden volume burst marks the end of balance; the burst bar's colour "
           "gives the direction of the new initiative.",
           {"dry_bars": [3, 5], "k": [1.5, 2.0, 3.0]}, _dryup_expansion, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1446", "Index and dollar moving together fade",
           "WIN and WDO usually move in opposite directions; when both make a large move the same way it is "
           "usually a transient dislocation (one leg is a flow-driven error) and WIN reverts.",
           {"lag_min": [10, 20], "k": [1.0, 1.5, 2.0]}, _comove_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1447", "Late-session open-stretch fade",
           "Late in the session, day-traders who held a large open-to-now move square up before the close, so an "
           "unusually stretched price (vs the same-minute typical) reverts toward the open.",
           {"k": [1.0, 1.5, 2.0], "start_hour": [14, 15, 16]}, _late_open_stretch, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
