"""Conveyor batch B-029 (agent, 2026-11-19). Geometry and bar-anatomy setups not screened yet: trendlines, order
blocks, higher-timeframe structure, Keltner walks, VWAP hugs, VIX-fix spikes, time symmetry, heavy takeovers,
close-location churn and a sleeping-Alligator fractal break. Every signal uses bars <= t, inside the session, with
20-session norms from prev_sessions/same_minute only."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _typ(ctx):
    """Typical bar range over every bar of the 20 sessions before."""
    return ctx.cached("b029_typ_rng", lambda: ctx.prev_sessions(ctx.h - ctx.l, "mean"))


# --- E-288 ------------------------------------------------------------------------------------
def _trendline_hold(ctx, p):
    w, tol = int(p["w"]), float(p["tol"])
    typ = _typ(ctx)
    lmin = ctx.roll(ctx.l, 2 * w + 1, "min")
    hmax = ctx.roll(ctx.h, 2 * w + 1, "max")
    pl, ph = ctx.prev(ctx.l, w), ctx.prev(ctx.h, w)
    sl = list(pl == lmin)
    sh = list(ph == hmax)
    pl, ph = list(pl), list(ph)
    L, H, C, T = list(ctx.l), list(ctx.h), list(ctx.c), list(typ)
    D = list(ctx.day)
    out = np.zeros(ctx.n, dtype=int)
    cur = None
    lows, highs = [], []
    was_up = was_dn = False
    for t in range(ctx.n):
        if D[t] != cur:
            cur, lows, highs, was_up, was_dn = D[t], [], [], False, False
        if sl[t]:
            lows = (lows + [(t - w, pl[t], t)])[-2:]
        if sh[t]:
            highs = (highs + [(t - w, ph[t], t)])[-2:]
        tt = T[t]
        up = dn = False
        if tt == tt and tt > 0:
            if len(lows) == 2 and lows[1][1] > lows[0][1] and t > lows[1][2]:
                (i1, p1, _), (i2, p2, _) = lows
                proj = p2 + (p2 - p1) / (i2 - i1) * (t - i2)
                if C[t] < proj - tol * tt:
                    lows = []
                else:
                    up = (L[t] <= proj + tol * tt) and (C[t] > proj)
            if len(highs) == 2 and highs[1][1] < highs[0][1] and t > highs[1][2]:
                (i1, p1, _), (i2, p2, _) = highs
                proj = p2 + (p2 - p1) / (i2 - i1) * (t - i2)
                if C[t] > proj + tol * tt:
                    highs = []
                else:
                    dn = (H[t] >= proj - tol * tt) and (C[t] < proj)
        if up and not was_up:
            out[t] += 1
        if dn and not was_dn:
            out[t] -= 1
        was_up, was_dn = up, dn
    return out


# --- E-289 ------------------------------------------------------------------------------------
def _vixfix(ctx, p):
    nb, k = ctx.bars(p["win_min"]), float(p["k"])
    hc = ctx.roll(ctx.c, nb, "max")
    lc = ctx.roll(ctx.c, nb, "min")
    fear = (hc - ctx.l) / hc
    greed = (ctx.h - lc) / lc
    fm = ctx.cached(("b029_fear_m", nb), lambda: ctx.prev_sessions(fear, "mean"))
    fs = ctx.cached(("b029_fear_s", nb), lambda: ctx.prev_sessions(fear, "sd"))
    gm = ctx.cached(("b029_greed_m", nb), lambda: ctx.prev_sessions(greed, "mean"))
    gs = ctx.cached(("b029_greed_s", nb), lambda: ctx.prev_sessions(greed, "sd"))
    f_spike = (fear > fm + k * fs).astype(float)
    g_spike = (greed > gm + k * gs).astype(float)
    f_recent = ctx.roll(f_spike, 3, "max", include_current=False) == 1
    g_recent = ctx.roll(g_spike, 3, "max", include_current=False) == 1
    ph, pl = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    long = f_recent & (f_spike == 0) & (ctx.c > ph)
    short = g_recent & (g_spike == 0) & (ctx.c < pl)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# --- E-290 ------------------------------------------------------------------------------------
def _time_symmetry(ctx, p):
    L, k = ctx.bars(p["leg_min"]), float(p["k"])
    P = max(1, L // 2)
    c = ctx.c
    mv = c - ctx.prev(c, L)
    typ = ctx.cached(("b029_absmv", L), lambda: ctx.prev_sessions(np.abs(mv), "mean"))
    leg = ctx.prev(mv, P)                                  # the L-bar move that ended P bars ago
    c_leg_end = ctx.prev(c, P)
    lo_pb = ctx.roll(ctx.l, P, "min", include_current=False)
    hi_pb = ctx.roll(ctx.h, P, "max", include_current=False)
    c1 = ctx.prev(c, 1)
    ph, pl = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    up_depth = (c_leg_end - lo_pb) / leg
    dn_depth = (hi_pb - c_leg_end) / (-leg)
    long = (leg >= k * typ) & (c1 < c_leg_end) & (up_depth > 0.2) & (up_depth < 0.8) & (c > ph)
    short = (leg <= -k * typ) & (c1 > c_leg_end) & (dn_depth > 0.2) & (dn_depth < 0.8) & (c < pl)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# --- E-291 ------------------------------------------------------------------------------------
def _keltner_walk(ctx, p):
    run, m = int(p["run"]), float(p["m"])
    mid = ctx.cached("b029_ema20", lambda: ctx.ema(ctx.c, 20))
    atr = ctx.cached("b029_atr20", lambda: ctx.ema(ctx.h - ctx.l, 20))
    up, lo = mid + m * atr, mid - m * atr
    above = (ctx.c > up).astype(float)
    below = (ctx.c < lo).astype(float)
    walked_up = ctx.roll(above, run, "min", include_current=False) == 1
    walked_dn = ctx.roll(below, run, "min", include_current=False) == 1
    short = walked_up & (ctx.c < up)
    long = walked_dn & (ctx.c > lo)
    return long.astype(int) - short.astype(int)


# --- E-292 ------------------------------------------------------------------------------------
def _vwap_hug_release(ctx, p):
    nb, k = ctx.bars(p["win_min"]), float(p["k"])
    vw = ctx.vwap()
    typ = _typ(ctx)
    hug = (np.abs(ctx.c - vw) <= k * typ).astype(float)
    hugged = ctx.roll(hug, nb, "min", include_current=False) == 1
    long = hugged & (ctx.c > vw + 2 * k * typ)
    short = hugged & (ctx.c < vw - 2 * k * typ)
    return long.astype(int) - short.astype(int)


# --- E-293 ------------------------------------------------------------------------------------
def _order_block(ctx, p):
    m, exp = float(p["m"]), ctx.bars(p["expire_min"])
    typ = _typ(ctx)
    body = ctx.c - ctx.o
    pc, po = ctx.prev(ctx.c, 1), ctx.prev(ctx.o, 1)
    bull = list((body >= m * typ) & (pc < po))
    bear = list((-body >= m * typ) & (pc > po))
    PH, PL = list(ctx.prev(ctx.h, 1)), list(ctx.prev(ctx.l, 1))
    O, H, L, C, D = list(ctx.o), list(ctx.h), list(ctx.l), list(ctx.c), list(ctx.day)
    out = np.zeros(ctx.n, dtype=int)
    cur, zb, zs = None, None, None
    for t in range(ctx.n):
        if D[t] != cur:
            cur, zb, zs = D[t], None, None
        if zb is not None:
            lo_z, hi_z, t0 = zb
            if t - t0 > exp or C[t] < lo_z:
                zb = None
            elif t - t0 >= 2 and L[t] <= hi_z and C[t] > hi_z and C[t] > O[t]:
                out[t] += 1
                zb = None
        if zs is not None:
            lo_z, hi_z, t0 = zs
            if t - t0 > exp or C[t] > hi_z:
                zs = None
            elif t - t0 >= 2 and H[t] >= lo_z and C[t] < lo_z and C[t] < O[t]:
                out[t] -= 1
                zs = None
        if bull[t]:
            zb = (PL[t], PH[t], t)
        if bear[t]:
            zs = (PL[t], PH[t], t)
    return out


# --- E-294 ------------------------------------------------------------------------------------
def _heavy_takeover(ctx, p):
    k = float(p["k"])
    med = ctx.cached("b029_vmed", lambda: ctx.same_minute(ctx.v, "median"))
    heavy = ctx.v > k * med
    h1 = ctx.prev(heavy.astype(float), 1) == 1
    v1 = ctx.prev(ctx.v, 1)
    o1, c1 = ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1)
    long = heavy & h1 & (ctx.v > v1) & (c1 < o1) & (ctx.c > ctx.o) & (ctx.c > o1)
    short = heavy & h1 & (ctx.v > v1) & (c1 > o1) & (ctx.c < ctx.o) & (ctx.c < o1)
    return long.astype(int) - short.astype(int)


# --- E-295 ------------------------------------------------------------------------------------
def _htf_structure_test(ctx, p):
    B, tol = int(p["block_min"]), float(p["tol"])
    key = ctx.day.astype(np.int64) * 10000 + (ctx.minute // B).astype(np.int64)
    s = pd.DataFrame({"k": key, "d": ctx.day, "h": ctx.h, "l": ctx.l})
    agg = s.groupby("k").agg(d=("d", "first"), h=("h", "max"), l=("l", "min"))
    g = agg.groupby("d")
    agg["h1"], agg["l1"] = g["h"].shift(1), g["l"].shift(1)
    agg["h2"], agg["l2"] = g["h"].shift(2), g["l"].shift(2)
    H1, L1 = agg["h1"].reindex(key).to_numpy(), agg["l1"].reindex(key).to_numpy()
    H2, L2 = agg["h2"].reindex(key).to_numpy(), agg["l2"].reindex(key).to_numpy()
    typ = _typ(ctx)
    up_struct = (H1 > H2) & (L1 > L2)
    dn_struct = (H1 < H2) & (L1 < L2)
    long = up_struct & (ctx.l <= L1 + tol * typ) & (ctx.c > L1) & (ctx.c > ctx.o)
    short = dn_struct & (ctx.h >= H1 - tol * typ) & (ctx.c < H1) & (ctx.c < ctx.o)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# --- E-296 ------------------------------------------------------------------------------------
def _close_churn(ctx, p):
    run, q = int(p["run"]), float(p["q"])
    rng = ctx.h - ctx.l
    clv = np.where(rng > 0, (ctx.c - ctx.l) / np.where(rng > 0, rng, 1.0), 0.5)
    typ = _typ(ctx)
    hi_c = ctx.roll((clv >= q).astype(float), run, "min") == 1
    lo_c = ctx.roll((clv <= 1 - q).astype(float), run, "min") == 1
    net = ctx.c - ctx.prev(ctx.c, run)
    stuck = np.abs(net) <= 0.5 * typ
    short = hi_c & stuck
    long = lo_c & stuck
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# --- E-297 ------------------------------------------------------------------------------------
def _sleeping_alligator_fractal(ctx, p):
    k, sc = float(p["k"]), int(p["scale"])
    med = (ctx.h + ctx.l) / 2.0

    def smma(n, shift):
        n, shift = n * sc, shift * sc
        return ctx.prev(ctx.cached(("b029_smma", n), lambda: ctx.ema(med, 2 * n - 1)), shift)

    jaw, teeth, lips = smma(13, 8), smma(8, 5), smma(5, 3)
    spread = np.maximum(np.maximum(jaw, teeth), lips) - np.minimum(np.minimum(jaw, teeth), lips)
    typ = _typ(ctx)
    asleep = spread <= k * typ
    ph2, pl2 = ctx.prev(ctx.h, 2), ctx.prev(ctx.l, 2)
    up_f = ph2 == ctx.roll(ctx.h, 5, "max")
    dn_f = pl2 == ctx.roll(ctx.l, 5, "min")
    s = pd.DataFrame({"d": ctx.day, "u": np.where(up_f, ph2, np.nan), "w": np.where(dn_f, pl2, np.nan)})
    up_lvl = s.groupby("d")["u"].ffill().to_numpy()
    dn_lvl = s.groupby("d")["w"].ffill().to_numpy()
    long = ctx.cross(ctx.c > up_lvl) & asleep
    short = ctx.cross(ctx.c < dn_lvl) & asleep
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-288", "Intraday trendline touch hold",
           "A rising line through the session's last two higher swing lows (falling line through two lower swing "
           "highs) is drawn by chart traders who rest buy (sell) orders on it; the first touch that closes back on "
           "the trend side shows those orders absorbing the pullback, so trade the hold; a close through the line "
           "voids it.",
           {"w": [2, 3, 4], "tol": [0.25, 0.5, 1.0]}, _trendline_hold, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-289", "Williams VIX-fix fear/greed spike reversal",
           "Larry Williams' synthetic VIX (drop of the low from the window's highest close) spiking far above its "
           "20-session norm marks forced, fearful selling; once the spike stops growing and a bar closes above the "
           "previous bar's high, the panic sellers are done and liquidity providers who bought from them lift the "
           "price (mirror: a greed spike from the lowest close).",
           {"win_min": [30, 60, 120], "k": [1.5, 2.0, 2.5]}, _vixfix, markets=("WIN",),
           source="Williams VIX Fix (LuxAlgo library) https://www.luxalgo.com/library/concept/williams-vix-fix/",
           author="agent"),
    Family("E-290", "Time-symmetric correction completion",
           "After a leg larger than usual, a pullback that has lasted about half the leg's duration and retraced "
           "20-80% of it without breaking down is a routine correction where the leg's holders did not exit; the "
           "first close beyond the previous bar's extreme at that time-symmetric point signals the correctors are "
           "done, so follow the leg.",
           {"leg_min": [15, 30, 60], "k": [1.0, 1.5, 2.0]}, _time_symmetry, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-291", "Keltner-band walk exhaustion",
           "Several consecutive closes outside an EMA +/- ATR Keltner band are a one-sided chase by late momentum "
           "traders; the first close back inside the band shows the chase has run out of new buyers (sellers) and "
           "their positions unwind toward the mean, so fade the re-entry.",
           {"run": [3, 5, 8], "m": [1.0, 1.5, 2.0]}, _keltner_walk, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-292", "VWAP-hug release follow",
           "When every close of a window stays within a small distance of the session VWAP, benchmark-tracking "
           "execution dominates and no side has an edge; a close far beyond that hug band means a participant "
           "stopped tracking the benchmark and is demanding liquidity, and the VWAP traders who were pinned there "
           "re-hedge in the same direction; follow the release.",
           {"win_min": [20, 30, 60], "k": [0.5, 1.0, 1.5]}, _vwap_hug_release, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-293", "Order-block retest hold",
           "The last opposite-colour bar before an impulse bar is where the impulsive participant started filling; "
           "when price first returns to that bar's range and closes back beyond it in the impulse direction, the "
           "unfilled remainder of that order defends the zone, so trade with the impulse; a close through the zone "
           "or a long wait voids it.",
           {"m": [1.5, 2.0, 3.0], "expire_min": [30, 60, 120]}, _order_block, markets=("WIN",),
           source="Bullish/bearish Order Block (LuxAlgo library) "
                  "https://www.luxalgo.com/library/concept/bullish-bearish-order-block/",
           author="agent"),
    Family("E-294", "Heavy-volume takeover bar",
           "Two consecutive bars both on abnormal volume for their minute, of opposite colour, where the second "
           "trades even more and closes beyond the first bar's open: the second side met the first side's heavy "
           "flow head-on and won; the losers of that contest exit over the next bars, so follow the second bar.",
           {"k": [1.5, 2.0, 3.0]}, _heavy_takeover, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-295", "Higher-timeframe structure low test",
           "When the last two completed 30-90 minute blocks of the session made a higher high and a higher low, "
           "swing traders reading that larger chart buy at the last block's low; a 1-5 minute bar that tests that "
           "low and closes up on the right side is their support holding, so trade with the larger structure "
           "(mirror for lower highs).",
           {"block_min": [30, 60, 90], "tol": [0.5, 1.0, 2.0]}, _htf_structure_test, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-296", "Close-location churn fade",
           "Several consecutive bars that all close near their highs while the price makes no net progress mean "
           "buyers lift every bar into its close but a larger passive seller sells each new bar back down; the "
           "aggressive side is spending effort for no result and gives up, so fade it (mirror for closes near the "
           "lows).",
           {"run": [3, 4, 5], "q": [0.6, 0.7, 0.8]}, _close_churn, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-297", "Fractal break while the Alligator sleeps",
           "Bill Williams' Alligator lines (smoothed medians 13/8/5, shifted) bunched together mean the market is "
           "asleep and stops cluster just beyond the last confirmed fractal high/low; the first close through a "
           "fractal while the lines are still tangled is the start of a new swing that wakes trend traders, so "
           "follow it only out of the sleeping state.",
           {"k": [0.5, 1.0, 1.5], "scale": [1, 2]}, _sleeping_alligator_fractal, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
