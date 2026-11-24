"""Conveyor batch B-090 (agent, 2026-11-24). Mixed themes: median/prior-close/day-open levels, autocorrelation regime, absorption, force index, cross-market WIN->WDO."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _out(long, short):
    return np.asarray(long).astype(int) - np.asarray(short).astype(int)


def _median_cross(ctx, p):
    nb = ctx.bars(p["win_min"])
    med = pd.Series(ctx.c).groupby(ctx.day).transform(
        lambda z: z.rolling(nb, min_periods=nb).median()).to_numpy()
    return _out(ctx.cross(ctx.c > med), ctx.cross(ctx.c < med))


def _autocorr_fade(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    r0 = np.nan_to_num(r)
    typical = ctx.cached("ac_typ", lambda: ctx.prev_sessions(np.abs(r0), "mean"))
    num = ctx.roll(r0 * ctx.prev(r0, 1), nb, "mean", include_current=False)
    den = ctx.roll(r0 * r0, nb, "mean", include_current=False)
    ac = num / np.where(den > 0, den, np.nan)
    big = np.abs(r0) >= 1.0 * typical
    reg = (ac < -th) & big
    return _out(ctx.cross(reg & (r0 < 0)), ctx.cross(reg & (r0 > 0)))


def _staircase_fail(ctx, p):
    k = int(p["steps"])
    hh = (ctx.h > ctx.prev(ctx.h, 1)).astype(float)
    hl = (ctx.l > ctx.prev(ctx.l, 1)).astype(float)
    lh = (ctx.h < ctx.prev(ctx.h, 1)).astype(float)
    ll = (ctx.l < ctx.prev(ctx.l, 1)).astype(float)
    up = (ctx.roll(hh * hl, k, "min", include_current=False) == 1)
    dn = (ctx.roll(lh * ll, k, "min", include_current=False) == 1)
    short = up & (ctx.c < ctx.prev(ctx.l, 1))
    long = dn & (ctx.c > ctx.prev(ctx.h, 1))
    return _out(long, short)


def _prior_close_dwell(ctx, p):
    nb = ctx.bars(p["dwell_min"])
    pc = ctx.prev_session_value("close")
    below = (ctx.c < pc).astype(float)
    above = (ctx.c > pc).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    return _out(was_below & (ctx.c > pc), was_above & (ctx.c < pc))


def _open_recross(ctx, p):
    k = p["k"]
    r = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("oc_typ", lambda: ctx.prev_sessions(np.abs(np.nan_to_num(r)), "mean"))
    hi = ctx.session_high(include_current=False) / ctx.day_open - 1.0
    lo = ctx.session_low(include_current=False) / ctx.day_open - 1.0
    short = (hi >= k * typ) & (ctx.c < ctx.day_open)
    long = (lo <= -k * typ) & (ctx.c > ctx.day_open)
    return _out(ctx.cross(long), ctx.cross(short))


def _absorption_break(ctx, p):
    k = p["vol_k"]
    rng = ctx.h - ctx.l
    medv = ctx.cached("abs_medv", lambda: ctx.same_minute(ctx.v, "median"))
    medr = ctx.cached("abs_medr", lambda: ctx.same_minute(rng, "median"))
    absorb = ((ctx.v > k * medv) & (rng < 0.8 * medr)).astype(float)
    a1 = ctx.prev(absorb, 1) == 1
    long = a1 & (ctx.c > ctx.prev(ctx.h, 1))
    short = a1 & (ctx.c < ctx.prev(ctx.l, 1))
    return _out(long, short)


def _win_leads_wdo(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    oc = ctx.other_close()
    move = oc / ctx.prev(oc, nb) - 1.0
    typ = ctx.cached(("lw_typ", nb), lambda: ctx.prev_sessions(np.abs(np.nan_to_num(move)), "mean"))
    up = move >= k * typ
    dn = move <= -k * typ
    # index up sharply -> dollar tends to fall (and vice versa)
    return _out(ctx.cross(dn), ctx.cross(up))


def _force_index_cross(ctx, p):
    n = ctx.bars(p["span_min"])
    d = np.nan_to_num(ctx.c - ctx.prev(ctx.c, 1))
    fi = ctx.ema(d * ctx.v, n)
    return _out(ctx.cross(fi > 0), ctx.cross(fi < 0))


def _reversal_expansion(ctx, p):
    k, nb = p["k"], ctx.bars(p["lookback_min"])
    rng = ctx.h - ctx.l
    avg = ctx.roll(rng, nb, "mean", include_current=False)
    c1, cn = ctx.prev(ctx.c, 1), ctx.prev(ctx.c, nb)
    wide = (rng >= k * avg) & (avg > 0)
    long = wide & (c1 < cn) & (ctx.c - ctx.l >= 0.75 * rng) & (ctx.c > ctx.prev(ctx.h, 1))
    short = wide & (c1 > cn) & (ctx.h - ctx.c >= 0.75 * rng) & (ctx.c < ctx.prev(ctx.l, 1))
    return _out(long, short)


def _colour_saturation_fade(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    up = (ctx.c > ctx.o).astype(float)
    dn = (ctx.c < ctx.o).astype(float)
    fu = ctx.roll(up, nb, "mean")
    fd = ctx.roll(dn, nb, "mean")
    return _out(ctx.cross(fd >= th), ctx.cross(fu >= th))


FAMILIES = [
    Family("E-898", "Rolling-median cross follow",
           "The rolling median ignores single-bar spikes; a close crossing it marks a durable shift in where "
           "trades clear, which trend followers and stop orders then extend.",
           {"win_min": [30, 60, 90]}, _median_cross, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-899", "Negative-autocorrelation regime fade",
           "When recent bar returns alternate in sign (market making dominates), a large bar is mostly liquidity "
           "taking that gets reverted; fade it only in that regime.",
           {"win_min": [30, 60], "th": [0.1, 0.2, 0.3]}, _autocorr_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-900", "Staircase failure",
           "After several consecutive higher highs and higher lows, a close below the previous low shows the "
           "trend buyers stopped; late trend followers exit into it and the move extends.",
           {"steps": [3, 4, 5]}, _staircase_fail, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-901", "Prior-close dwell cross",
           "The previous session's close is the reference for overnight holders and gap traders; after dwelling on "
           "one side, a close across it signals a change of sentiment versus yesterday.",
           {"dwell_min": [20, 40, 60]}, _prior_close_dwell, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-902", "Day-open re-cross after an excursion",
           "After a stretch away from the open, a close back through it means the excursion was fully retraced and "
           "its late participants are trapped; follow the reversal.",
           {"k": [0.5, 0.75, 1.0]}, _open_recross, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-903", "Absorption bar break",
           "Heavy volume with a small range means one side absorbed the other's orders; the next bar's break of "
           "the absorption bar shows which side ran out.",
           {"vol_k": [1.5, 2.0, 3.0]}, _absorption_break, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-904", "Index surge, dollar fades (WDO)",
           "A sharp index move with dollar inversely correlated means foreign-flow hedgers lag; the dollar "
           "follows opposite to the index surge.",
           {"win_min": [10, 20, 30], "k": [1.5, 2.0, 3.0]}, _win_leads_wdo, markets=("WDO",),
           source="assistant reasoning", author="agent"),
    Family("E-905", "Force-index zero cross",
           "Price change times volume weights moves by participation; the smoothed series changing sign marks "
           "money flow switching side and momentum traders joining.",
           {"span_min": [15, 30, 60]}, _force_index_cross, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-906", "Reversal after range expansion",
           "A bar several times wider than recent bars that closes near its extreme against the prior drift is a "
           "capitulation of the trend side; trapped positions fuel the reversal.",
           {"k": [1.5, 2.0, 2.5], "lookback_min": [15, 30]}, _reversal_expansion, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-907", "One-sided bar-colour saturation fade",
           "When nearly every recent bar has the same colour the move is crowded and thinly supplied by "
           "the other side; the first saturated reading precedes a pause or pullback, so fade it.",
           {"win_min": [15, 30], "th": [0.75, 0.85]}, _colour_saturation_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
