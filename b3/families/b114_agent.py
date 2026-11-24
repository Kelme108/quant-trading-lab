"""Conveyor batch B-114 (agent, 2026-11-24). Mixed themes: round numbers, cross-market lag, session midpoint, prior close, staircases, lunch range, absorption, EMA ribbon, window-midpoint recovery."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _sgn(long, short):
    return long.astype(int) - short.astype(int)


def _round_number(ctx, p):
    step = float(p["step"])
    lc = np.floor(ctx.c / step)
    lp = ctx.prev(lc, 1)
    up = (lc > lp) & (ctx.c > ctx.o)
    dn = (lc < lp) & (ctx.c < ctx.o)
    return _sgn(up, dn)


def _lag_signal(ctx, p, sign):
    nb, k = ctx.bars(p["n_min"]), p["k"]
    oc = ctx.other_close()
    ro = oc / ctx.prev(oc, nb) - 1.0
    rs = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    to = ctx.cached(("t_other", nb), lambda: ctx.prev_sessions(np.abs(ro), "mean"))
    ts = ctx.cached(("t_self", nb), lambda: ctx.prev_sessions(np.abs(rs), "mean"))
    # sign=+1: other asset rising -> this asset expected to rise; sign=-1: inverse relation
    other_up = ro >= k * to
    other_dn = ro <= -k * to
    if sign > 0:
        long = other_up & (rs <= 0.25 * ts)
        short = other_dn & (rs >= -0.25 * ts)
    else:
        long = other_dn & (rs <= 0.25 * ts)
        short = other_up & (rs >= -0.25 * ts)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _dollar_lead_win(ctx, p):
    return _lag_signal(ctx, p, -1)      # dollar up -> index down


def _index_lead_wdo(ctx, p):
    return _lag_signal(ctx, p, -1)      # index up -> dollar down (same inverse relation)


def _session_mid_cross(ctx, p):
    frac = p["range_frac"]
    sh = ctx.session_high(include_current=True)
    sl = ctx.session_low(include_current=True)
    mid = (sh + sl) / 2.0
    pr = ctx.prev_session_value("high") - ctx.prev_session_value("low")
    wide = (sh - sl) >= frac * pr
    up = wide & (ctx.c > mid) & (ctx.prev(ctx.c, 1) <= ctx.prev(mid, 1))
    dn = wide & (ctx.c < mid) & (ctx.prev(ctx.c, 1) >= ctx.prev(mid, 1))
    return _sgn(up, dn)


def _prior_close_cross(ctx, p):
    nb = ctx.bars(p["hold_min"])
    pc = ctx.prev_session_value("close")
    below = (ctx.c < pc).astype(float)
    above = (ctx.c > pc).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    return _sgn(was_below & (ctx.c > pc), was_above & (ctx.c < pc))


def _staircase(ctx, p):
    n = int(p["n_bars"])
    ph, pl = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    stair_up = ((ctx.h > ph) & (ctx.l > pl)).astype(float)
    stair_dn = ((ctx.h < ph) & (ctx.l < pl)).astype(float)
    up = ctx.roll(stair_up, n, "min") == 1
    dn = ctx.roll(stair_dn, n, "min") == 1
    return _sgn(ctx.cross(up), ctx.cross(dn))


def _lunch_break(ctx, p):
    rm = float(p["range_min"])
    m = (ctx.minute >= 13 * 60 - rm) & (ctx.minute < 13 * 60)
    g = pd.DataFrame({"d": ctx.day, "h": np.where(m, ctx.h, np.nan), "l": np.where(m, ctx.l, np.nan)})
    hi = g.groupby("d")["h"].transform("max").to_numpy()
    lo = g.groupby("d")["l"].transform("min").to_numpy()
    after = ctx.minute >= 13 * 60
    up = after & (ctx.c > hi)
    dn = after & (ctx.c < lo)
    return _sgn(ctx.cross(up), ctx.cross(dn))


def _absorption(ctx, p):
    k, nb = p["vol_k"], ctx.bars(p["move_min"])
    rng = ctx.h - ctx.l
    med = ctx.cached("v_med", lambda: ctx.same_minute(ctx.v, "median"))
    typ = ctx.cached("rng_mean", lambda: ctx.same_minute(rng, "mean"))
    move = ctx.prev(ctx.c, 1) / ctx.prev(ctx.c, nb + 1) - 1.0
    tm = ctx.cached(("absmv", nb), lambda: ctx.prev_sessions(np.abs(move), "mean"))
    absorb = (ctx.v >= k * med) & (rng <= 0.8 * typ)
    long = absorb & (move <= -1.0 * tm)
    short = absorb & (move >= 1.0 * tm)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _ribbon(ctx, p):
    b = int(p["base"])
    e1 = ctx.cached(("ema", b), lambda: ctx.ema(ctx.c, b))
    e2 = ctx.cached(("ema", 2 * b), lambda: ctx.ema(ctx.c, 2 * b))
    e3 = ctx.cached(("ema", 4 * b), lambda: ctx.ema(ctx.c, 4 * b))
    up = (e1 > e2) & (e2 > e3) & (ctx.c > e1)
    dn = (e1 < e2) & (e2 < e3) & (ctx.c < e1)
    return _sgn(ctx.cross(up), ctx.cross(dn))


def _window_mid_recovery(ctx, p):
    nb = ctx.bars(p["look_min"])
    q = max(1, nb // 3)
    hi = ctx.roll(ctx.h, nb, "max")
    lo = ctx.roll(ctx.l, nb, "min")
    hq = ctx.roll(ctx.h, q, "max")
    lq = ctx.roll(ctx.l, q, "min")
    mid = (hi + lo) / 2.0
    low_recent = ctx.prev(lq, 1) == ctx.prev(lo, 1)
    high_recent = ctx.prev(hq, 1) == ctx.prev(hi, 1)
    up = low_recent & (ctx.c > mid) & (ctx.prev(ctx.c, 1) <= ctx.prev(mid, 1))
    dn = high_recent & (ctx.c < mid) & (ctx.prev(ctx.c, 1) >= ctx.prev(mid, 1))
    return _sgn(up, dn)


FAMILIES = [
    Family("E-1138", "Round-number crossing follow",
           "Index levels at multiples of 250/500/1000 points attract resting stops and breakout orders; a bar that "
           "closes through one in its own direction triggers them and the move should continue briefly.",
           {"step": [250, 500, 1000]}, _round_number, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1139", "Dollar-leads-index lag",
           "Index and dollar move inversely; when the mini dollar makes an outsized move and the index has not yet "
           "responded, slower index participants catch up in the opposite direction.",
           {"n_min": [5, 10, 15], "k": [1.0, 1.5, 2.0]}, _dollar_lead_win, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1140", "Session-midpoint cross follow",
           "Once the day's range is wide relative to yesterday's, a close crossing the range midpoint shifts the "
           "balance of the auction toward the new side; follow it.",
           {"range_frac": [0.5, 0.75, 1.0]}, _session_mid_cross, markets=("WIN",),
           source="assistant reasoning (auction market theory)", author="agent"),
    Family("E-1141", "Prior-close cross after a hold",
           "The prior settlement is the reference for the day's winners and losers; after trading on one side for a "
           "while, a close across it flips positioning and traders chase.",
           {"hold_min": [10, 20, 30]}, _prior_close_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1142", "Staircase bars follow",
           "Several consecutive bars with both higher highs and higher lows (or lower/lower) show persistent one-sided "
           "order flow; the sequence onset is followed.",
           {"n_bars": [3, 4, 5]}, _staircase, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1143", "Lunch-range break",
           "Liquidity thins into the midday lull and reopens with New York around 13:00; a close beyond the lunch "
           "range marks the afternoon's direction as sidelined participants return.",
           {"range_min": [30, 60, 90]}, _lunch_break, markets=("WIN",),
           source="assistant reasoning (intraday liquidity cycle)", author="agent"),
    Family("E-1144", "Absorption bar reversal",
           "A high-volume bar with a small range after a sharp move means aggressive orders were absorbed by passive "
           "size; the move that preceded it tends to reverse.",
           {"vol_k": [1.5, 2.0, 3.0], "move_min": [10, 20, 30]}, _absorption, markets=("WIN",),
           source="assistant reasoning (effort versus result, volume-price analysis)", author="agent"),
    Family("E-1145", "EMA ribbon alignment onset",
           "When fast, medium and slow EMAs line up in order with price beyond the fast one, short- and medium-term "
           "holders agree on direction; the first alignment bar starts a continuation.",
           {"base": [3, 5, 8]}, _ribbon, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1146", "Index-leads-dollar lag",
           "The mini dollar often reacts to index moves with a delay; after an outsized index move with the dollar "
           "still unmoved, the dollar follows inversely.",
           {"n_min": [5, 10, 15], "k": [1.0, 1.5, 2.0]}, _index_lead_wdo, markets=("WDO",),
           source="assistant reasoning", author="agent"),
    Family("E-1147", "Window-extreme recovery through the midpoint",
           "After a rolling window's low (high) was set recently, a close back through the window midpoint shows buyers "
           "(sellers) recovered half the range and continuing is favoured.",
           {"look_min": [30, 60, 90]}, _window_mid_recovery, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
