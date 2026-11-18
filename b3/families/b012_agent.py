"""Conveyor batch B-012 (agent, 2026-11-18). New state variables: return skewness, zigzag swing geometry (AB=CD,
pullback speed), Mass Index range bulge, negative-volume index, triangle geometry, cross-market calm/lead, bar-body
asymmetry and close-vs-midpoint divergence."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _typ(ctx):
    # typical bar range of the 20 sessions before (constant inside a session)
    return ctx.cached("b012_typ", lambda: ctx.prev_sessions(ctx.h - ctx.l, "mean"))


def _logret(ctx, nb):
    return np.log(ctx.c / ctx.prev(ctx.c, nb))


# E-109 ---------------------------------------------------------------------------------------
def _skew_reversal(ctx, p):
    nb = max(ctx.bars(p["win_min"]), 12)
    th = p["th"]
    r = _logret(ctx, 1)
    m1 = ctx.roll(r, nb, "mean", include_current=False)
    m2 = ctx.roll(r * r, nb, "mean", include_current=False)
    m3 = ctx.roll(r * r * r, nb, "mean", include_current=False)
    var = m2 - m1 * m1
    mu3 = m3 - 3.0 * m1 * m2 + 2.0 * m1 ** 3
    ok = np.isfinite(var) & (var > 0)
    sk = np.full(ctx.n, np.nan)
    sk[ok] = mu3[ok] / var[ok] ** 1.5
    pc = ctx.prev(ctx.c, 1)
    short = (sk > th) & (ctx.c < pc)
    long = (sk < -th) & (ctx.c > pc)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-110 ---------------------------------------------------------------------------------------
def _abcd(ctx, p):
    R = (p["k"] * _typ(ctx)).tolist()
    h, l, c, day = ctx.h.tolist(), ctx.l.tolist(), ctx.c.tolist(), ctx.day.tolist()
    out = np.zeros(ctx.n, dtype=int)
    cur = None
    r = dirn = 0
    hi = lo = ext = 0.0
    piv, fired = [], False
    for i in range(ctx.n):
        if day[i] != cur:
            cur, r, dirn, hi, lo, piv, fired = day[i], R[i], 0, h[i], l[i], [], False
            continue
        if not (r > 0):
            continue
        hh, ll = h[i], l[i]
        if dirn == 0:
            hi, lo = max(hi, hh), min(lo, ll)
            if hi - lo >= r:
                if c[i] - lo >= hi - c[i]:
                    dirn, ext = 1, hi
                    piv.append(lo)
                else:
                    dirn, ext = -1, lo
                    piv.append(hi)
            continue
        if dirn == 1:
            ext = max(ext, hh)
            if not fired and len(piv) >= 3:
                a, b, cc = piv[-3], piv[-2], piv[-1]
                leg = b - a
                if leg > 0 and cc > a and 0.382 <= (b - cc) / leg <= 0.886 and hh >= cc + leg:
                    out[i], fired = -1, True
            if ext - ll >= r:
                piv.append(ext)
                dirn, ext, fired = -1, ll, False
        else:
            ext = min(ext, ll)
            if not fired and len(piv) >= 3:
                a, b, cc = piv[-3], piv[-2], piv[-1]
                leg = a - b
                if leg > 0 and cc < a and 0.382 <= (cc - b) / leg <= 0.886 and ll <= cc - leg:
                    out[i], fired = 1, True
            if hh - ext >= r:
                piv.append(ext)
                dirn, ext, fired = 1, hh, False
    return out


# E-111 ---------------------------------------------------------------------------------------
def _mass_bulge(ctx, p):
    th = p["th"]
    e1 = ctx.cached("b012_mi_e1", lambda: ctx.ema(ctx.h - ctx.l, 9))
    e2 = ctx.cached("b012_mi_e2", lambda: ctx.ema(e1, 9))
    ok = np.isfinite(e2) & (e2 > 0)
    ratio = np.full(ctx.n, np.nan)
    ratio[ok] = e1[ok] / e2[ok]
    mi = ctx.cached("b012_mi", lambda: ctx.roll(ratio, 25, "sum"))
    was_above = ctx.prev(ctx.roll((mi > th).astype(float), 25, "max"), 1) == 1
    trig = ctx.cross(mi < th - 0.5) & was_above
    e9 = ctx.cached("b012_e9", lambda: ctx.ema(ctx.c, 9))
    slope = e9 - ctx.prev(e9, 3)
    return (trig & (slope < 0)).astype(int) - (trig & (slope > 0)).astype(int)


# E-112 ---------------------------------------------------------------------------------------
def _nvi_cross(ctx, p):
    nb, k = ctx.bars(p["span_min"]), p["k"]
    r = _logret(ctx, 1)
    quiet = ctx.v < ctx.prev(ctx.v, 1)
    step = np.where(quiet & np.isfinite(r), r, 0.0)
    nvi = ctx.cached("b012_nvi", lambda: pd.Series(step).groupby(ctx.day).cumsum().to_numpy())
    dev = nvi - ctx.ema(nvi, nb)
    typ = ctx.cached("b012_absr", lambda: ctx.prev_sessions(np.nan_to_num(np.abs(r)), "mean"))
    return ctx.cross(dev > k * typ).astype(int) - ctx.cross(dev < -k * typ).astype(int)


# E-113 ---------------------------------------------------------------------------------------
def _triangle(ctx, p):
    nb = max(ctx.bars(p["win_min"]), 6)
    half, k = nb // 2, p["k"]
    typ = _typ(ctx)
    H2 = ctx.roll(ctx.h, half, "max", include_current=False)
    L2 = ctx.roll(ctx.l, half, "min", include_current=False)
    H1, L1 = ctx.prev(H2, half), ctx.prev(L2, half)
    top, bot = np.maximum(H1, H2), np.minimum(L1, L2)
    asc = (np.abs(H2 - H1) <= 0.5 * typ) & (L2 - L1 >= k * typ)
    desc = (np.abs(L2 - L1) <= 0.5 * typ) & (H1 - H2 >= k * typ)
    return ctx.cross(asc & (ctx.c > top)).astype(int) - ctx.cross(desc & (ctx.c < bot)).astype(int)


# E-114 ---------------------------------------------------------------------------------------
def _calm_dollar_fade(ctx, p):
    nb, q = ctx.bars(p["win_min"]), p["q"]
    w = ctx.other_close()
    nw = ctx.bars(30)
    wm = np.abs(np.log(w / ctx.prev(w, nw)))
    typ_w = ctx.cached(("b012_wm", nw), lambda: ctx.prev_sessions(np.nan_to_num(wm), "mean"))
    calm = wm < q * typ_w
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    return ctx.cross(calm & (ctx.c < lo)).astype(int) - ctx.cross(calm & (ctx.c > hi)).astype(int)


# E-115 ---------------------------------------------------------------------------------------
def _win_led_dollar(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    x = ctx.other_close()                      # WIN close when this frame is WDO
    xr = np.log(x / ctx.prev(x, nb))
    r = _logret(ctx, nb)
    tx = ctx.cached(("b012_tx", nb), lambda: ctx.prev_sessions(np.nan_to_num(np.abs(xr)), "mean"))
    tr = ctx.cached(("b012_tr", nb), lambda: ctx.prev_sessions(np.nan_to_num(np.abs(r)), "mean"))
    short = (xr > k * tx) & (r > -0.5 * tr)     # equities jumped, the dollar has not fallen yet
    long = (xr < -k * tx) & (r < 0.5 * tr)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-116 ---------------------------------------------------------------------------------------
def _body_asymmetry(ctx, p):
    nb, ratio = ctx.bars(p["win_min"]), p["ratio"]
    nb = max(nb, 8)
    body = ctx.c - ctx.o
    up, dn = body > 0, body < 0
    su = ctx.roll(np.where(up, body, 0.0), nb, "sum")
    sd = ctx.roll(np.where(dn, -body, 0.0), nb, "sum")
    nu = ctx.roll(up.astype(float), nb, "sum")
    nd = ctx.roll(dn.astype(float), nb, "sum")
    ok = (nu >= 3) & (nd >= 3) & (su > 0) & (sd > 0)
    mu = np.where(ok, su / np.where(nu > 0, nu, 1), np.nan)
    md = np.where(ok, sd / np.where(nd > 0, nd, 1), np.nan)
    mean_c = ctx.roll(ctx.c, nb, "mean")
    long = (mu >= ratio * md) & (ctx.c > mean_c)
    short = (md >= ratio * mu) & (ctx.c < mean_c)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-117 ---------------------------------------------------------------------------------------
def _slow_pullback(ctx, p):
    R = (p["k"] * _typ(ctx)).tolist()
    q = p["q"]
    h, l, c, day = ctx.h.tolist(), ctx.l.tolist(), ctx.c.tolist(), ctx.day.tolist()
    out = np.zeros(ctx.n, dtype=int)
    cur = None
    r = dirn = 0
    hi = lo = ext = 0.0
    hi_t = lo_t = ext_t = 0
    piv, pt, fired = [], [], False
    for i in range(ctx.n):
        if day[i] != cur:
            cur, r, dirn, piv, pt, fired = day[i], R[i], 0, [], [], False
            hi, lo, hi_t, lo_t = h[i], l[i], i, i
            continue
        if not (r > 0):
            continue
        hh, ll = h[i], l[i]
        if dirn == 0:
            if hh > hi:
                hi, hi_t = hh, i
            if ll < lo:
                lo, lo_t = ll, i
            if hi - lo >= r:
                if c[i] - lo >= hi - c[i]:
                    piv.append(lo); pt.append(lo_t)
                    dirn, ext, ext_t = 1, hi, hi_t
                else:
                    piv.append(hi); pt.append(hi_t)
                    dirn, ext, ext_t = -1, lo, lo_t
            continue
        if dirn == -1:                         # pulling back after an up leg A(low) -> B(high)
            if ll < ext:
                ext, ext_t = ll, i
            if not fired and len(piv) >= 2:
                b, a, tb, ta = piv[-1], piv[-2], pt[-1], pt[-2]
                imp, depth, dur = b - a, b - ext, i - tb
                if imp > 0 and dur >= 2 and depth <= 0.62 * imp and c[i] > h[i - 1] and \
                        depth / dur < q * imp / max(tb - ta, 1):
                    out[i], fired = 1, True
            if hh - ext >= r:
                piv.append(ext); pt.append(ext_t)
                dirn, ext, ext_t, fired = 1, hh, i, False
        else:                                  # bouncing after a down leg A(high) -> B(low)
            if hh > ext:
                ext, ext_t = hh, i
            if not fired and len(piv) >= 2:
                b, a, tb, ta = piv[-1], piv[-2], pt[-1], pt[-2]
                imp, depth, dur = a - b, ext - b, i - tb
                if imp > 0 and dur >= 2 and depth <= 0.62 * imp and c[i] < l[i - 1] and \
                        depth / dur < q * imp / max(tb - ta, 1):
                    out[i], fired = -1, True
            if ext - ll >= r:
                piv.append(ext); pt.append(ext_t)
                dirn, ext, ext_t, fired = -1, ll, i, False
    return out


# E-118 ---------------------------------------------------------------------------------------
def _close_mid_divergence(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    typ = _typ(ctx)
    mid = 0.5 * (ctx.h + ctx.l)
    dc = ctx.c - ctx.prev(ctx.c, nb)
    dm = mid - ctx.prev(mid, nb)
    short = (dc >= k * typ) & (dm <= 0.25 * dc)      # closes pushed up, the bars' bulk did not follow
    long = (dc <= -k * typ) & (dm >= 0.25 * dc)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


FAMILIES = [
    Family("E-109", "Realized-skewness reversal",
           "A window of 1-bar returns with strong positive skew means the rise came from a few large up bars (chasers "
           "and stop bursts) while most bars drifted down; like lottery-like assets, the spiky side is overpaid and "
           "liquidity providers lean against it, so the first down bar while skew is high starts the reversal (mirror).",
           {"win_min": [60, 120, 180], "th": [0.5, 1.0, 1.5]}, _skew_reversal,
           markets=("WIN",), source="assistant reasoning (realized-skewness predictability, Amaya et al.)", author="agent"),
    Family("E-110", "AB=CD measured-move completion fade",
           "Swing traders project the second leg equal to the first (AB=CD) and park take-profits and harmonic "
           "counter-entries at D; when a zigzag leg after a 38-89% pullback reaches D, that resting liquidity absorbs "
           "the push and the leg's late buyers are the exit, so fade at D (mirror).",
           {"k": [3, 5, 8]}, _abcd, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-111", "Mass Index reversal bulge",
           "Dorsey's Mass Index sums the EMA ratio of bar ranges; a bulge above ~27 that falls back means a range "
           "expansion has run its course, which tends to end the prevailing swing; trade against the 9-EMA slope at "
           "the moment the bulge completes.",
           {"th": [26.5, 27.0, 27.5]}, _mass_bulge, markets=("WIN",),
           source="Mass index (Wikipedia) https://en.wikipedia.org/wiki/Mass_index", author="agent"),
    Family("E-112", "Negative Volume Index cross follow",
           "Fosback's NVI accumulates price change only on bars where volume falls, the bars traded by patient "
           "participants rather than the crowd; when that quiet-bar price path breaks clearly away from its own EMA, "
           "the patient side is moving price without noise traders, so follow it.",
           {"span_min": [20, 40, 60], "k": [1.0, 2.0, 3.0]}, _nvi_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-113", "Converging-triangle break follow",
           "Flat highs with rising lows (ascending triangle) show a fixed seller being met by buyers raising their "
           "bids every dip; once that seller is filled and price closes above the flat top, the stops above and the "
           "impatient bidders lift it, so follow the break (mirror for a descending triangle).",
           {"win_min": [20, 40, 60], "k": [0.5, 1.0, 2.0]}, _triangle, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-114", "Calm-dollar WIN extreme fade",
           "Foreign and macro flow into Brazil moves the dollar and the index together; when WDO has barely moved in "
           "the last 30 minutes, a WIN close beyond its recent high/low is local flow without macro backing, which "
           "market makers fade back into the range.",
           {"win_min": [10, 20, 30], "q": [0.3, 0.5, 0.7]}, _calm_dollar_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-115", "WIN-led dollar catch-up",
           "Equity risk news reaches the index future first (S&P arbitrage, foreign equity desks); FX dealers re-price "
           "the dollar a little later, so a sharp WIN move not yet mirrored by WDO predicts the dollar moving the "
           "opposite way; trade WDO against the WIN jump.",
           {"win_min": [5, 10, 15], "k": [1.5, 2.0, 3.0]}, _win_led_dollar, markets=("WDO",),
           source="assistant reasoning", author="agent"),
    Family("E-116", "Impulsive-vs-corrective body asymmetry follow",
           "When up bars have much larger bodies than down bars over a window, rises are made by initiative market "
           "orders while dips are mere drift (corrective); the impulsive side controls the tape, so follow it when "
           "the asymmetry appears with price above its window mean (mirror).",
           {"win_min": [20, 40, 60], "ratio": [1.5, 2.0, 2.5]}, _body_asymmetry, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-117", "Slow-pullback resumption",
           "After a fast impulse leg, a pullback that travels much slower than the impulse is passive profit-taking, "
           "not new supply; the first bar closing above the previous bar's high shows the impulse side returning "
           "before the pullback gains speed, so follow it (mirror).",
           {"k": [3, 5, 8], "q": [0.25, 0.5, 0.75]}, _slow_pullback, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-118", "Close-vs-midpoint divergence fade",
           "When closes rise over a window but bar midpoints do not, the gains are printed in the last seconds of each "
           "bar (closing pushes) while most trading stays where it was; the push is cosmetic and reverts once the "
           "pushers stop, so fade it (mirror).",
           {"win_min": [10, 20, 30], "k": [1.0, 2.0, 3.0]}, _close_mid_divergence, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
