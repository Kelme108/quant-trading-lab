"""Conveyor batch B-085 (agent, 2026-11-23). Mixed themes: lunch box, bar-colour breadth, open recross, cross-market same-direction, relative volume, bar jumps, range-position swing, body growth, drift excess, confluence."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _lunch_box_break(ctx, p):
    nb_min = p["box_min"]
    m = ctx.minute
    inbox = (m >= 780 - nb_min) & (m < 780)
    g = pd.DataFrame({"d": ctx.day, "h": np.where(inbox, ctx.h, np.nan), "l": np.where(inbox, ctx.l, np.nan)})
    bh = g.groupby("d")["h"].transform("max").to_numpy()
    bl = g.groupby("d")["l"].transform("min").to_numpy()
    win = (m >= 780) & (m < 870)
    up = win & (ctx.c > bh)
    dn = win & (ctx.c < bl)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _upbar_breadth_fade(ctx, p):
    nb, th = ctx.bars(p["window_min"]), p["th"]
    up = (ctx.c > ctx.o).astype(float)
    dn = (ctx.c < ctx.o).astype(float)
    fu = ctx.roll(up, nb, "mean")
    fd = ctx.roll(dn, nb, "mean")
    short = fu >= th
    long = fd >= th
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _open_recross(ctx, p):
    k, nb = p["k"], ctx.bars(p["lookback_min"])
    r = ctx.c / ctx.day_open - 1.0
    typical = ctx.cached("abs_r_sm", lambda: ctx.same_minute(np.abs(r), "mean"))
    hi = ctx.roll(r, nb, "max", include_current=False)
    lo = ctx.roll(r, nb, "min", include_current=False)
    short = (hi >= k * typical) & (r < 0)
    long = (lo <= -k * typical) & (r > 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _same_dir_fade(ctx, p):
    nb, k = ctx.bars(p["move_min"]), p["k"]
    oc = ctx.other_close()
    rs = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    ro = oc / ctx.prev(oc, nb) - 1.0
    ts = ctx.cached(("ts", nb), lambda: ctx.prev_sessions(np.abs(rs), "mean"))
    to = ctx.cached(("to", nb), lambda: ctx.prev_sessions(np.abs(ro), "mean"))
    both_up = (rs >= k * ts) & (ro >= k * to)
    both_dn = (rs <= -k * ts) & (ro <= -k * to)
    return ctx.cross(both_dn).astype(int) - ctx.cross(both_up).astype(int)


def _relvol_trend(ctx, p):
    k, nb = p["k"], ctx.bars(p["win_min"])
    cumv = pd.Series(ctx.v).groupby(ctx.day).cumsum().to_numpy()
    typical = ctx.cached("cumv_sm", lambda: ctx.same_minute(cumv, "mean"))
    heavy = cumv >= k * typical
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    vw = ctx.vwap()
    long = heavy & (ctx.c > vw) & (ctx.c > hi)
    short = heavy & (ctx.c < vw) & (ctx.c < lo)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _bar_jump_fill(ctx, p):
    k = p["k"]
    gap = ctx.o - ctx.prev(ctx.c, 1)
    typical = ctx.cached("abs_gap", lambda: ctx.prev_sessions(np.abs(gap), "mean"))
    big = (np.abs(gap) >= k * typical) & (typical > 0)
    short = big & (gap > 0) & (ctx.c < ctx.o)
    long = big & (gap < 0) & (ctx.c > ctx.o)
    return long.astype(int) - short.astype(int)


def _range_pos_swing(ctx, p):
    nb, lo_th = ctx.bars(p["lookback_min"]), p["lo"]
    sh, sl = ctx.session_high(include_current=True), ctx.session_low(include_current=True)
    rng = sh - sl
    pos = np.where(rng > 0, (ctx.c - sl) / np.where(rng > 0, rng, 1.0), np.nan)
    pmin = ctx.roll(pos, nb, "min", include_current=False)
    pmax = ctx.roll(pos, nb, "max", include_current=False)
    long = (pmin <= lo_th) & (pos > 0.5)
    short = (pmax >= 1 - lo_th) & (pos < 0.5)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _growing_bodies(ctx, p):
    n, k = int(p["n"]), p["k"]
    body = ctx.c - ctx.o
    ab = np.abs(body)
    avg = ctx.cached("avg_body20", lambda: ctx.roll(ab, 20, "mean"))
    up = body > 0
    dn = body < 0
    grow = ab > 0
    for i in range(1, n):
        bi, bj = ctx.prev(body, i), ctx.prev(body, i - 1)
        up = up & (bi > 0)
        dn = dn & (bi < 0)
        grow = grow & (np.abs(bj) > np.abs(bi))
    big = ab >= k * avg
    return ctx.cross(up & grow & big).astype(int) - ctx.cross(dn & grow & big).astype(int)


def _drift_excess(ctx, p):
    k = p["k"]
    r = ctx.c / ctx.day_open - 1.0
    drift = ctx.cached("drift_sm", lambda: ctx.same_minute(r, "mean"))
    sd = ctx.cached("abs_r_sm2", lambda: ctx.same_minute(np.abs(r), "mean"))
    ex = r - drift
    return ctx.cross(ex >= k * sd).astype(int) - ctx.cross(ex <= -k * sd).astype(int)


def _confluence_cross(ctx, p):
    b = p["buffer_frac"]
    pdc = ctx.prev_session_value("close")
    vw = ctx.vwap()
    up = (ctx.c > vw * (1 + b)) & (ctx.c > pdc * (1 + b))
    dn = (ctx.c < vw * (1 - b)) & (ctx.c < pdc * (1 - b))
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


FAMILIES = [
    Family("E-848", "Lunch-box break follow",
           "The thin 12:00-13:00 box coils resting orders; the first close beyond it after 13:00 (until 14:30) releases "
           "stops and follows with the returning liquidity.",
           {"box_min": [45, 60, 90]}, _lunch_box_break, source="assistant reasoning", author="agent"),
    Family("E-849", "Bar-colour breadth fade",
           "When nearly all recent bars share one colour, the move is crowded and one-sided; the first threshold "
           "cross is a stretched sample and tends to revert.",
           {"window_min": [20, 30, 45], "th": [0.7, 0.75, 0.8]}, _upbar_breadth_fade, source="assistant reasoning",
           author="agent"),
    Family("E-850", "Open-price recross after a drive",
           "After the day pushed away from its open by more than usual, a close back through the open price shows the "
           "drive's buyers or sellers are trapped; follow the recross.",
           {"k": [0.5, 1.0, 1.5], "lookback_min": [60, 120, 240]}, _open_recross, source="assistant reasoning",
           author="agent"),
    Family("E-851", "Index and dollar moving the same way",
           "WIN and WDO usually move inversely; a large same-direction move in both is a risk-off/on anomaly or liquidity "
           "squeeze in one leg, and tends to snap back.",
           {"move_min": [15, 30], "k": [1.0, 1.5, 2.0]}, _same_dir_fade, source="assistant reasoning", author="agent"),
    Family("E-852", "Heavy-day breakout on the VWAP side",
           "On a session whose cumulative volume runs above its usual pace, a new range extreme on the VWAP side comes "
           "with participation and continues.",
           {"k": [1.2, 1.5], "win_min": [30, 60, 90]}, _relvol_trend, source="assistant reasoning", author="agent"),
    Family("E-853", "Bar-open jump fill",
           "An unusual jump between one close and the next open is noise from thin books; a bar that trades back "
           "against the jump is a gap fill in progress.",
           {"k": [2.0, 3.0, 4.0]}, _bar_jump_fill, source="assistant reasoning", author="agent"),
    Family("E-854", "Range-position swing follow",
           "A close that travels from the bottom (top) edge of the session range through its midpoint shows control "
           "changing sides; follow the crossing.",
           {"lookback_min": [30, 60, 90], "lo": [0.15, 0.25, 0.35]}, _range_pos_swing, source="assistant reasoning",
           author="agent"),
    Family("E-855", "Growing-body candle run",
           "Same-colour bars with strictly growing bodies show escalating aggression that the other side has not yet "
           "absorbed; follow it.",
           {"n": [3, 4], "k": [0.5, 1.0, 1.5]}, _growing_bodies, source="assistant reasoning", author="agent"),
    Family("E-856", "Drift-excess follow",
           "Return from the open in excess of the usual path for this time of day, measured against typical size, "
           "marks flow beyond the habitual drift; follow it.",
           {"k": [0.5, 1.0, 1.5]}, _drift_excess, source="assistant reasoning", author="agent"),
    Family("E-857", "VWAP and prior-close confluence cross",
           "Price clearing both the session VWAP and yesterday's close puts day-traders and swing holders on the same "
           "side; follow the first close past both.",
           {"buffer_frac": [0.0, 0.0003, 0.0006]}, _confluence_cross, source="assistant reasoning", author="agent"),
]
