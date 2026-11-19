"""Conveyor batch B-028 (agent, 2026-11-19). New measures (today's volume-at-price, high-low spread estimator,
round-number stop cascades, opening-auction weight, chart constructions) across fade, follow, level and range ideas."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


# ------------------------------------------------------------------------------------------------ helpers

def _breaks(ctx, nb):
    def f():
        hi = ctx.roll(ctx.h, nb, "max", include_current=False)
        lo = ctx.roll(ctx.l, nb, "min", include_current=False)
        return ctx.cross(ctx.c > hi), ctx.cross(ctx.c < lo)
    return ctx.cached(("b028_breaks", nb), f)


def _session_bounds(ctx):
    starts = np.r_[0, np.flatnonzero(np.diff(ctx.day)) + 1]
    ends = np.r_[starts[1:], ctx.n]
    return starts, ends


# ------------------------------------------------------------------------------------------------ E-278

def _profile_share(ctx, nb, band_frac):
    """Share of the session's earlier volume (bars older than the break window) traded within band of the close."""
    def f():
        tp = (ctx.h + ctx.l + ctx.c) / 3.0
        out = np.full(ctx.n, np.nan)
        starts, ends = _session_bounds(ctx)
        for a, b in zip(starts, ends):
            m = b - a
            c, t, v = ctx.c[a:b], tp[a:b], ctx.v[a:b]
            near = np.abs(t[None, :] - c[:, None]) <= band_frac * c[:, None]
            near &= np.tri(m, m, -(nb + 1), dtype=bool)
            num = near.astype(float) @ v
            cum = np.cumsum(v)
            den = np.full(m, 0.0)
            if m > nb + 1:
                den[nb + 1:] = cum[:m - nb - 1]
            with np.errstate(invalid="ignore", divide="ignore"):
                out[a:b] = np.where(den > 0, num / den, np.nan)
        return out
    return ctx.cached(("b028_profile", nb, band_frac), f)


def _dense_profile_fade(ctx, p):
    nb = ctx.bars(p["win_min"])
    up, dn = _breaks(ctx, nb)
    share = _profile_share(ctx, nb, 0.001)
    dense = share >= p["q"]
    return (dn & dense).astype(int) - (up & dense).astype(int)


# ------------------------------------------------------------------------------------------------ E-279

def _round_cross_follow(ctx, p):
    c = ctx.c
    big = c > 20000                                     # WIN prices ~1e5, WDO ~5e3
    win_step = {1: 250.0, 2: 500.0, 3: 1000.0}[int(p["step_rank"])]
    wdo_step = {1: 5.0, 2: 10.0, 3: 50.0}[int(p["step_rank"])]
    step = np.where(big, win_step, wdo_step)
    buf = p["buf_ticks"] * np.where(big, 5.0, 0.5)
    cp = ctx.prev(c, 1)
    with np.errstate(invalid="ignore"):
        up = np.floor((c - buf) / step) > np.floor((cp - buf) / step)
        dn = np.ceil((c + buf) / step) < np.ceil((cp + buf) / step)
    return up.astype(int) - dn.astype(int)


# ------------------------------------------------------------------------------------------------ E-280

def _cs_spread(ctx):
    def f():
        with np.errstate(invalid="ignore", divide="ignore"):
            lh = np.log(ctx.h / ctx.l)
            beta = lh ** 2 + ctx.prev(lh, 1) ** 2
            h2 = np.maximum(ctx.h, ctx.prev(ctx.h, 1))
            l2 = np.minimum(ctx.l, ctx.prev(ctx.l, 1))
            gamma = np.log(h2 / l2) ** 2
            den = 3.0 - 2.0 * np.sqrt(2.0)
            alpha = (np.sqrt(2.0 * beta) - np.sqrt(beta)) / den - np.sqrt(gamma / den)
            s = 2.0 * (np.exp(alpha) - 1.0) / (1.0 + np.exp(alpha))
        return np.where(np.isnan(s), np.nan, np.maximum(s, 0.0))
    return ctx.cached("b028_cs", f)


def _spread_regime_fade(ctx, p):
    s = _cs_spread(ctx)
    nb = ctx.bars(p["win_min"])
    sm = ctx.roll(s, nb, "mean")
    norm = ctx.cached("b028_cs_norm", lambda: ctx.prev_sessions(s, "mean"))
    wide = sm > p["k"] * norm
    up, dn = _breaks(ctx, ctx.bars(10))
    return (dn & wide).astype(int) - (up & wide).astype(int)


# ------------------------------------------------------------------------------------------------ E-281

def _expanding_run_follow(ctx, p):
    run, k = int(p["run"]), p["k"]
    rng = ctx.h - ctx.l
    body = ctx.c - ctx.o
    typ = ctx.cached("b028_rng_med", lambda: ctx.same_minute(rng, "median"))
    up = np.ones(ctx.n, bool)
    dn = np.ones(ctx.n, bool)
    for i in range(run):
        r_i = rng if i == 0 else ctx.prev(rng, i)
        b_i = body if i == 0 else ctx.prev(body, i)
        r_prev = ctx.prev(rng, i + 1)
        grow = r_i > r_prev
        up &= grow & (b_i > 0)
        dn &= grow & (b_i < 0)
    big = rng >= k * typ
    return ctx.cross(up & big).astype(int) - ctx.cross(dn & big).astype(int)


# ------------------------------------------------------------------------------------------------ E-282

def _hs_neck(piv, s, tol):
    ext = [(x * s, i) for kind, x, i in piv if kind == s]
    if len(ext) < 3:
        return np.nan, -1
    (a, ia), (b, ib), (cc, ic) = ext[-3:]
    tr1 = [x * s for kind, x, i in piv if kind == -s and ia < i < ib]
    tr2 = [x * s for kind, x, i in piv if kind == -s and ib < i < ic]
    if not tr1 or not tr2 or not (b > a and b > cc):
        return np.nan, -1
    t1, t2 = min(tr1), min(tr2)
    if abs(a - cc) > tol * (b - min(t1, t2)):
        return np.nan, -1
    return t2 * s, ic


def _head_shoulders(ctx, p):
    w, tol = int(p["w"]), p["tol"]
    span = 2 * w + 1
    hmax = ctx.roll(ctx.h, span, "max")
    lmin = ctx.roll(ctx.l, span, "min")
    hw, lw = ctx.prev(ctx.h, w), ctx.prev(ctx.l, w)
    with np.errstate(invalid="ignore"):
        ph = hw >= hmax
        pl = lw <= lmin
    c, day = ctx.c, ctx.day
    out = np.zeros(ctx.n, int)
    piv = []
    sn, ln, s_id, l_id, s_done, l_done = np.nan, np.nan, -1, -1, -1, -1
    for t in range(ctx.n):
        new_day = t == 0 or day[t] != day[t - 1]
        if new_day:
            piv = []
            sn, ln, s_id, l_id, s_done, l_done = np.nan, np.nan, -1, -1, -1, -1
        changed = False
        if ph[t]:
            piv.append((1, hw[t], t - w))
            changed = True
        if pl[t]:
            piv.append((-1, lw[t], t - w))
            changed = True
        if changed:
            sn, s_id = _hs_neck(piv, 1, tol)
            ln, l_id = _hs_neck(piv, -1, tol)
        if new_day:
            continue
        if sn == sn and s_id != s_done and c[t] < sn <= c[t - 1]:
            out[t] = -1
            s_done = s_id
        elif ln == ln and l_id != l_done and c[t] > ln >= c[t - 1]:
            out[t] = 1
            l_done = l_id
    return out


# ------------------------------------------------------------------------------------------------ E-283

def _multi_session_trend_follow(ctx, p):
    ns = int(p["n_sessions"])
    mean_n = ctx.cached(("b028_msmean", ns), lambda: ctx.prev_sessions(ctx.c, "mean", ns))
    pc = ctx.prev_session_value("close")
    trend_up = pc > mean_n
    trend_dn = pc < mean_n
    up, dn = _breaks(ctx, ctx.bars(p["win_min"]))
    return (up & trend_up).astype(int) - (dn & trend_dn).astype(int)


# ------------------------------------------------------------------------------------------------ E-284

def _gap_midpoint_fade(ctx, p):
    pc = ctx.prev_session_value("close")
    op = ctx.day_open
    lvl = (pc + op) / 2.0
    gap = op - pc
    big = np.abs(gap) >= p["k"] * 0.001 * pc
    long = big & (gap > 0) & (ctx.l <= lvl) & (ctx.c > lvl)
    short = big & (gap < 0) & (ctx.h >= lvl) & (ctx.c < lvl)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# ------------------------------------------------------------------------------------------------ E-285

def _camarilla(ctx, p):
    m = p["mult"]
    pc, ph, pl = ctx.prev_session_value("close"), ctx.prev_session_value("high"), ctx.prev_session_value("low")
    r = ph - pl
    h3, l3 = pc + r * m / 4.0, pc - r * m / 4.0
    h4, l4 = pc + r * m / 2.0, pc - r * m / 2.0
    fade_s = ctx.cross((ctx.h >= h3) & (ctx.c < h3))
    fade_l = ctx.cross((ctx.l <= l3) & (ctx.c > l3))
    brk_l = ctx.cross(ctx.c > h4)
    brk_s = ctx.cross(ctx.c < l4)
    return (fade_l | brk_l).astype(int) - (fade_s | brk_s).astype(int)


# ------------------------------------------------------------------------------------------------ E-286

def _heavy_auction_fade(ctx, p):
    def ratio():
        sm = ctx.same_minute(ctx.v, "median")
        g = pd.Series(ctx.v).groupby(ctx.day).transform("first").to_numpy()
        t = pd.Series(sm).groupby(ctx.day).transform("first").to_numpy()
        with np.errstate(invalid="ignore", divide="ignore"):
            return g / t
    rt = ctx.cached("b028_auction_ratio", ratio)
    heavy = (rt >= p["k"]) & (ctx.bar_in_day >= ctx.bars(30))
    up, dn = _breaks(ctx, ctx.bars(p["win_min"]))
    return (dn & heavy).astype(int) - (up & heavy).astype(int)


# ------------------------------------------------------------------------------------------------ E-287

def _three_line_break(ctx, p):
    n = int(p["lines"])
    c, day = ctx.c, ctx.day
    out = np.zeros(ctx.n, int)
    ref, streak, d = 0.0, [], 0
    for t in range(ctx.n):
        x = c[t]
        if t == 0 or day[t] != day[t - 1]:
            ref, streak, d = x, [], 0
            continue
        if x != x:
            continue
        if d == 0:
            if x > ref:
                streak, d = [(ref, x)], 1
            elif x < ref:
                streak, d = [(x, ref)], -1
            continue
        lo, hi = streak[-1]
        if d == 1:
            if x > hi:
                streak.append((hi, x))
            elif x < min(s[0] for s in streak[-n:]):
                if len(streak) >= n:
                    out[t] = -1
                streak, d = [(x, lo)], -1
        else:
            if x < lo:
                streak.append((x, lo))
            elif x > max(s[1] for s in streak[-n:]):
                if len(streak) >= n:
                    out[t] = 1
                streak, d = [(hi, x)], 1
    return out


# ------------------------------------------------------------------------------------------------ families

FAMILIES = [
    Family("E-278", "Dense-profile micro-break fade",
           "A close beyond the recent high/low that lands in a price zone where a large share of today's earlier volume "
           "already traded is breaking into accepted inventory: the holders from that zone (and the passive orders that "
           "made it a high-volume node) sell into the up-break and buy the down-break, so the small breaker is faded.",
           {"win_min": [10, 15, 30], "q": [0.1, 0.2, 0.3]}, _dense_profile_fade, markets=("WIN",),
           source="NexusFi: Volume Profile Nodes https://nexusfi.com/a/concepts/volume-profile-nodes", author="agent"),
    Family("E-279", "Round-number cross follow (stop cascade)",
           "Stop-loss buy orders cluster just above round numbers and stop-loss sells just below; a close through a "
           "round level triggers that cluster, and the executed stops are market orders that push the price further "
           "(Osler's price cascades), so follow the close through the round number.",
           {"step_rank": [1, 2, 3], "buf_ticks": [0, 2, 4]}, _round_cross_follow,
           source="Osler, Stop-loss orders and price cascades, FRBNY staff report 150 "
                  "https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf", author="agent"),
    Family("E-280", "High-low spread-regime micro-break fade",
           "When the Corwin-Schultz high-low spread estimate over the last window runs well above its 20-session norm, "
           "bar ranges are made mostly of bid-ask bouncing between liquidity providers rather than of information; "
           "a 10-minute high/low break then is the bounce reaching the far quote, which the providers lean back, so fade.",
           {"win_min": [15, 30, 60], "k": [1.0, 1.25, 1.5]}, _spread_regime_fade, markets=("WIN",),
           source="Corwin & Schultz, A Simple Way to Estimate Bid-Ask Spreads from Daily High and Low Prices "
                  "https://projects.nber.org/confer/2009/mms09/Corwin_Schultz.pdf", author="agent"),
    Family("E-281", "Expanding-range run follow",
           "Consecutive same-colour bars whose ranges grow each bar, ending with a bar of at least normal range for the "
           "minute, show an aggressive parent order accelerating while market makers widen and pull quotes; the urgency "
           "is not spent at the bar close, so follow the run's direction.",
           {"run": [2, 3, 4], "k": [0.75, 1.0, 1.5]}, _expanding_run_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-282", "Intraday head-and-shoulders neckline break follow",
           "Three swing highs with a higher middle and roughly level shoulders mean the last push failed below the head; "
           "chart traders who see the pattern sell the close through the neckline and the longs from the right shoulder "
           "have stops just under it, so the neckline break is followed (inverse pattern for longs).",
           {"w": [2, 3, 5], "tol": [0.25, 0.5, 1.0]}, _head_shoulders, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-283", "Multi-session-trend micro-break follow",
           "When yesterday closed above the average price of the last several sessions, swing holders are long and "
           "positioned to add; intraday breaks in that direction are joined by their adds and by short covering, while "
           "breaks against it meet their dip-buying, so follow only breaks aligned with the multi-session trend.",
           {"n_sessions": [5, 10, 20], "win_min": [10, 20, 30]}, _multi_session_trend_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-284", "Half-gap level hold",
           "On a meaningful opening gap, gap-fade traders take profit at the half-gap (midpoint of yesterday's close and "
           "today's open) and gap-continuation traders buy it; a bar that reaches the half-gap and closes back on the "
           "gap side shows that interest absorbing the fill, so trade back toward the open.",
           {"k": [1, 2, 4]}, _gap_midpoint_fade, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-285", "Camarilla H3/L3 fade, H4/L4 break",
           "Camarilla levels (yesterday's close +/- 1.1 x range / 4 and / 2) are a published day-trader map: users "
           "sell the first touch of H3 that closes back below and buy L3, but chase a close beyond H4/L4; their shared "
           "orders make those reactions self-fulfilling at the level.",
           {"mult": [1.0, 1.1, 1.2]}, _camarilla, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-286", "Heavy-opening-auction day micro-break fade",
           "A session whose opening bar trades much more than its usual volume priced the overnight information in the "
           "auction itself; the rest of the day has no informed parent order left to work and is run by responsive "
           "liquidity providers, so after the first half hour short-term breaks are faded.",
           {"k": [1.5, 2.0, 3.0], "win_min": [10, 15, 30]}, _heavy_auction_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-287", "Three-line-break reversal follow",
           "On a three-line-break chart a reversal needs a close beyond the extreme of the last N same-colour lines, "
           "i.e. the whole recent leg is undone on closing prices; the leg's late entrants are then under water and "
           "exit while the chart's users enter the new direction, so follow the reversal after a leg of at least N lines.",
           {"lines": [2, 3, 4]}, _three_line_break, markets=("WIN",), source="assistant reasoning", author="agent"),
]
