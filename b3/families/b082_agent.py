"""Conveyor batch B-082 (agent, 2026-11-23). Mixed themes: return skew, new-high frequency, prior-close location,
gap bars, volume flips, chop regime, volume pulse, leg retracement, prior-range pace, intrabar vs between-bar flow."""
from __future__ import annotations

import numpy as np
import pandas as pd
from b3.esteira import Family

_E = np.errstate(all="ignore")


def _sig(long, short):
    return np.asarray(long, bool).astype(int) - np.asarray(short, bool).astype(int)


def _skew_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    with _E:
        r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
        m = ctx.roll(r, nb, "mean")
        m2 = ctx.roll(r ** 2, nb, "mean")
        m3 = ctx.roll(r ** 3, nb, "mean")
        s = np.sqrt(np.maximum(m2 - m ** 2, 0.0))
        sk = (m3 - 3 * m * m2 + 2 * m ** 3) / s ** 3
        up, dn = sk >= k, sk <= -k
        return _sig(ctx.cross(dn), ctx.cross(up))


def _new_high_share(ctx, p):
    w, f = ctx.bars(p["share_min"]), p["frac"]
    lb = ctx.bars(60)
    with _E:
        hi = ctx.roll(ctx.h, lb, "max", include_current=False)
        lo = ctx.roll(ctx.l, lb, "min", include_current=False)
        sh = ctx.roll((ctx.h > hi).astype(float), w, "mean")
        sl = ctx.roll((ctx.l < lo).astype(float), w, "mean")
        up = (sh >= f) & (sl == 0)
        dn = (sl >= f) & (sh == 0)
        return _sig(ctx.cross(up), ctx.cross(dn))


def _prior_loc_carry(ctx, p):
    t = p["loc"]
    with _E:
        pdh, pdl, pdc = ctx.prev_session_value("high"), ctx.prev_session_value("low"), ctx.prev_session_value("close")
        loc = (pdc - pdl) / (pdh - pdl)
        vw = ctx.vwap()
        long = (loc >= t) & (ctx.c > pdc)
        short = (loc <= 1 - t) & (ctx.c < pdc)
        return _sig(ctx.cross((ctx.c > vw) & long), ctx.cross((ctx.c < vw) & short))


def _gap_bar(ctx, p):
    k = p["k"]
    with _E:
        atr = ctx.roll(ctx.h - ctx.l, ctx.bars(30), "mean")
        ph, pl = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
        up = (ctx.l - ph) > k * atr
        dn = (pl - ctx.h) > k * atr
        return _sig(up & (ctx.c > ctx.o), dn & (ctx.c < ctx.o))


def _volume_flip(ctx, p):
    k = p["vol_k"]
    with _E:
        col = np.sign(ctx.c - ctx.o)
        pc = ctx.prev(col, 1)
        pc2 = ctx.prev(col, 2)
        pv = ctx.prev(ctx.v, 1)
        heavy = ctx.v >= k * pv
        long = (col > 0) & (pc < 0) & (pc2 < 0) & heavy
        short = (col < 0) & (pc > 0) & (pc2 > 0) & heavy
        return _sig(long, short)


def _chop_fade(ctx, p):
    nb, fl, z = ctx.bars(p["win_min"]), p["flips"], p["z"]
    with _E:
        col = np.sign(ctx.c - ctx.o)
        flip = ((col * ctx.prev(col, 1)) < 0).astype(float)
        flip[np.isnan(ctx.prev(col, 1))] = np.nan
        share = ctx.roll(flip, nb, "mean")
        mu = ctx.roll(ctx.c, nb, "mean")
        sd = ctx.roll(ctx.c, nb, "std")
        zz = (ctx.c - mu) / sd
        chop = share >= fl
        return _sig(ctx.cross(chop & (zz <= -z)), ctx.cross(chop & (zz >= z)))


def _volume_pulse(ctx, p):
    nb, k = ctx.bars(15), p["k"]
    with _E:
        vs = ctx.roll(ctx.v, nb, "sum")
        typ = ctx.cached(("vs_med", nb), lambda: ctx.same_minute(vs, "median"))
        ret = ctx.c - ctx.prev(ctx.c, nb)
        pulse = vs >= k * typ
        return _sig(ctx.cross(pulse & (ret > 0)), ctx.cross(pulse & (ret < 0)))


def _leg_retrace(ctx, p):
    nb, fr = ctx.bars(p["lookback_min"]), p["frac"]
    with _E:
        hi = ctx.roll(ctx.h, nb, "max")
        lo = ctx.roll(ctx.l, nb, "min")
        rng = hi - lo
        start = ctx.prev(ctx.c, nb - 1) if nb > 1 else ctx.c
        pos0 = (start - lo) / rng
        depth = (hi - ctx.c) / rng
        pd1 = ctx.prev(depth, 1)
        upleg = pos0 < 0.25
        dnleg = pos0 > 0.75
        long = upleg & (pd1 >= fr) & (pd1 < 0.75) & (ctx.c > ctx.o) & (ctx.c > ctx.prev(ctx.h, 1))
        pu = 1 - pd1
        short = dnleg & (pu >= fr) & (pu < 0.75) & (ctx.c < ctx.o) & (ctx.c < ctx.prev(ctx.l, 1))
        return _sig(ctx.cross(long), ctx.cross(short))


def _prior_range_pace(ctx, p):
    f = p["frac"]
    with _E:
        pr = ctx.prev_session_value("high") - ctx.prev_session_value("low")
        sh, sl = ctx.session_high(False), ctx.session_low(False)
        so = ctx.session_high(True) - ctx.session_low(True)
        big = so >= f * pr
        long = big & (ctx.h > sh) & (ctx.c > ctx.day_open)
        short = big & (ctx.l < sl) & (ctx.c < ctx.day_open)
        return _sig(ctx.cross(long), ctx.cross(short))


def _jump_vs_intrabar(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    with _E:
        jump = ctx.roll(ctx.o - ctx.prev(ctx.c, 1), nb, "sum")
        intra = ctx.roll(ctx.c - ctx.o, nb, "sum")
        tot = ctx.roll(ctx.h - ctx.l, nb, "sum")
        q = intra / tot
        long = (q >= k) & (jump < 0)
        short = (q <= -k) & (jump > 0)
        return _sig(ctx.cross(long), ctx.cross(short))


FAMILIES = [
    Family("E-818", "Return-skew spike fade",
           "A strongly skewed window of returns means one lottery-like bar did the work; liquidity takers there "
           "overpaid and the spike partly reverts.",
           {"win_min": [60, 90, 120], "k": [1.0, 1.5, 2.0]}, _skew_fade, source="assistant reasoning", author="assistant".replace("assistant", "agent")),
    Family("E-819", "New-high share thrust",
           "When a large share of recent bars each set a fresh 60-minute high with no fresh lows, persistent "
           "aggressive buying is in control and tends to continue (mirror for lows).",
           {"share_min": [15, 30, 45], "frac": [0.3, 0.4, 0.5]}, _new_high_share, source="assistant reasoning", author="agent"),
    Family("E-820", "Prior-close location carry on VWAP cross",
           "A session that closed near its high (low) leaves late buyers (sellers) positioned; next day a VWAP "
           "cross in that direction while above (below) the prior close is a continuation entry.",
           {"loc": [0.6, 0.7, 0.8]}, _prior_loc_carry, source="assistant reasoning", author="agent"),
    Family("E-821", "Non-overlapping gap bar follow",
           "A bar whose range lies entirely beyond the previous bar's range, in an ATR-sized jump, shows urgent "
           "one-sided orders and the next minutes follow.",
           {"k": [0.0, 0.1, 0.25, 0.5]}, _gap_bar, source="assistant reasoning", author="agent"),
    Family("E-822", "Volume-flip bar after two counter bars",
           "After two same-colour bars, an opposite bar on much heavier volume means the new side absorbed the "
           "earlier flow; follow the flip.",
           {"vol_k": [1.5, 2.0, 3.0]}, _volume_flip, source="assistant reasoning", author="agent"),
    Family("E-823", "Choppy-regime band fade",
           "When bar colours keep flipping the market is rotating, and a stretch beyond the window mean is "
           "likely to be pulled back.",
           {"win_min": [30, 60], "flips": [0.5, 0.6], "z": [1.5, 2.0]}, _chop_fade, source="assistant reasoning", author="agent"),
    Family("E-824", "Volume pulse ahead of schedule",
           "A 15-minute volume burst well above its same-clock median marks informed or forced flow; follow the "
           "direction of the burst.",
           {"k": [1.5, 2.0, 3.0]}, _volume_pulse, source="assistant reasoning", author="agent"),
    Family("E-825", "Leg retracement bounce",
           "After a leg from one end of the recent range, a partial retracement that turns with a bar through the "
           "prior high (low) attracts trend traders and resumes.",
           {"lookback_min": [30, 60, 90], "frac": [0.25, 0.382, 0.5]}, _leg_retrace, source="assistant reasoning", author="agent"),
    Family("E-826", "Prior-range pace extreme follow",
           "Once today's range has used a large share of yesterday's full range, a fresh extreme on the side of "
           "the day open signals an expanded-volatility trend day.",
           {"frac": [0.6, 0.8, 1.0]}, _prior_range_pace, source="assistant reasoning", author="agent"),
    Family("E-827", "Intrabar flow against between-bar jumps",
           "If bars close strongly in one direction but open gap the other way, passive liquidity is being "
           "absorbed by the intrabar side; follow the intrabar direction.",
           {"win_min": [15, 30, 60], "k": [0.2, 0.3, 0.4]}, _jump_vs_intrabar, source="assistant reasoning", author="agent"),
]
