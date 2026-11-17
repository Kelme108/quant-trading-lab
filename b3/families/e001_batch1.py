"""Conveyor families, batch 1 (assistant, 2026-11-17). Simple intraday ideas NOT among the 16 families of the
pattern search (pattern_search_b3.json) nor the agents' rules P-008..P-031. Each fires on a crossing so one
setup gives one signal. Signals use only the bar's close and earlier bars (checked by b3.esteira)."""

from __future__ import annotations

import numpy as np

from b3.esteira import Family


def _vwap_reclaim(ctx, p):
    n = int(p["away_min"])
    nb = ctx.bars(n)
    vw = ctx.vwap()
    below = (ctx.c < vw).astype(float)
    above = (ctx.c > vw).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1      # every one of the n bars before
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    up = was_below & (ctx.c > vw)
    dn = was_above & (ctx.c < vw)
    return up.astype(int) - dn.astype(int)


def _pd_level_reject(ctx, p):
    b = p["buffer_frac"]
    pdh, pdl = ctx.prev_session_value("high"), ctx.prev_session_value("low")
    short = (ctx.h > pdh * (1 + b)) & (ctx.c < pdh)
    long = (ctx.l < pdl * (1 - b)) & (ctx.c > pdl)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _pd_level_break(ctx, p):
    b = p["buffer_frac"]
    pdh, pdl = ctx.prev_session_value("high"), ctx.prev_session_value("low")
    up = ctx.cross(ctx.c > pdh * (1 + b))
    dn = ctx.cross(ctx.c < pdl * (1 - b))
    return up.astype(int) - dn.astype(int)


def _trend_pullback(ctx, p):
    k, n = p["k"], int(p["ema_bars"])
    r = ctx.c / ctx.day_open - 1.0
    typical = ctx.cached("abs_ret_same_minute", lambda: ctx.same_minute(np.abs(r), "mean"))
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    long = (r >= k * typical) & (ctx.l <= ema) & (ctx.c > ema)
    short = (r <= -k * typical) & (ctx.h >= ema) & (ctx.c < ema)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _inside_break(ctx, p):
    ratio = p["max_ratio"]
    rng = ctx.h - ctx.l
    h1, l1, r1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1), ctx.prev(rng, 1)
    h2, l2, r2 = ctx.prev(ctx.h, 2), ctx.prev(ctx.l, 2), ctx.prev(rng, 2)
    inside = (h1 <= h2) & (l1 >= l2) & (r1 <= ratio * r2) & (r2 > 0)
    return np.where(inside & (ctx.c > h1), 1, 0) - np.where(inside & (ctx.c < l1), 1, 0)


def _or_failure(ctx, p):
    nb = ctx.bars(p["range_min"])
    first = ctx.bar_in_day < nb
    import pandas as pd
    g = pd.DataFrame({"d": ctx.day, "h": np.where(first, ctx.h, np.nan), "l": np.where(first, ctx.l, np.nan)})
    orh = g.groupby("d")["h"].transform("max").to_numpy()
    orl = g.groupby("d")["l"].transform("min").to_numpy()
    done = ~first
    broke_up = ctx.session_high(include_current=True) > orh
    broke_dn = ctx.session_low(include_current=True) < orl
    short = done & broke_up & (ctx.c < orh) & (ctx.prev(ctx.c, 1) >= orh)
    long = done & broke_dn & (ctx.c > orl) & (ctx.prev(ctx.c, 1) <= orl)
    return long.astype(int) - short.astype(int)


def _quiet_continuation(ctx, p):
    nb, k = ctx.bars(p["move_min"]), p["vol_k"]
    move = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    typical = ctx.cached(("abs_move", nb), lambda: ctx.prev_sessions(np.abs(move), "mean"))
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    quiet = ctx.v < k * med
    bar = np.sign(ctx.c - ctx.o)
    long = (move >= 1.5 * typical) & quiet & (bar > 0)
    short = (move <= -1.5 * typical) & quiet & (bar < 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _midday_extreme_fade(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    mid = (ctx.minute >= 12 * 60) & (ctx.minute < 14 * 60 + 30)
    short = mid & (ctx.h > hi) & (ctx.c < hi)
    long = mid & (ctx.l < lo) & (ctx.c > lo)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-001", "VWAP reclaim",
           "After the price stays on one side of the session VWAP for a while, the first close back across it marks "
           "a change of control; follow the cross.",
           {"away_min": [10, 20, 30, 45]}, _vwap_reclaim, source="practitioner intraday VWAP use", author="assistant"),
    Family("E-002", "Previous-day high/low rejection",
           "Trading beyond the previous session's high/low and closing back inside it is a failed auction at a "
           "level many participants watch; fade it.",
           {"buffer_frac": [0.0, 0.0005, 0.001]}, _pd_level_reject, source="auction market theory", author="assistant"),
    Family("E-003", "Previous-day high/low breakout",
           "A close beyond the previous session's high/low triggers stops and breakout orders; follow it.",
           {"buffer_frac": [0.0, 0.0005, 0.001]}, _pd_level_break, source="auction market theory", author="assistant"),
    Family("E-004", "Trend-day pullback to the EMA",
           "On a day already moving more than usual for the time of day, the first pullback to a short EMA that "
           "closes back on the trend side is a continuation entry.",
           {"k": [0.75, 1.0, 1.5], "ema_bars": [10, 20, 30]}, _trend_pullback, source="practitioner trend-day playbooks",
           author="assistant"),
    Family("E-005", "Inside-bar breakout",
           "A bar inside the previous one compresses the range; a close beyond it releases it in that direction.",
           {"max_ratio": [0.5, 0.7, 0.9]}, _inside_break, source="price-action literature", author="assistant"),
    Family("E-006", "Opening-range failure",
           "When the price breaks the opening range and then closes back inside it, the breakout traders are "
           "trapped; fade back into the range.",
           {"range_min": [15, 30, 60]}, _or_failure, source="opening range literature (failure variant)", author="assistant"),
    Family("E-007", "Quiet continuation",
           "After a large move, a bar in the move's direction on LOW volume means nobody is pushing back; follow.",
           {"move_min": [10, 20, 30], "vol_k": [0.6, 0.8, 1.0]}, _quiet_continuation, source="volume-price analysis",
           author="assistant"),
    Family("E-008", "Midday extreme fade",
           "Between 12:00 and 14:30 liquidity is thinner and breaks of the recent high/low tend to fail; fade a bar "
           "that pokes beyond and closes back inside.",
           {"lookback_min": [20, 30, 45, 60]}, _midday_extreme_fade, source="intraday seasonality of liquidity",
           author="assistant"),
]
