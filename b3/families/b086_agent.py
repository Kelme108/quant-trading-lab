"""Conveyor batch B-086 (agent, 2026-11-23). Mixed indicator-state ideas: VWAP bands, squeeze, MACD, channel mid, dollar lag, ribbon, late drift, CCI, DI, OR midpoint."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _ratio(a, b):
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(b > 0, a / b, np.nan)


def _sig(ctx, long, short):
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _vwap_band_fade(ctx, p):
    nb = ctx.bars(p["win_min"])
    dev = ctx.c - ctx.vwap()
    sd = ctx.roll(dev, nb, "std")
    z = _ratio(dev, sd)
    return _sig(ctx, z <= -p["k"], z >= p["k"])


def _squeeze_break(ctx, p):
    nb = ctx.bars(p["win_min"])
    m = ctx.roll(ctx.c, nb, "mean")
    s = ctx.roll(ctx.c, nb, "std")
    width = _ratio(s, m)
    typ = ctx.cached(("sqw", nb), lambda: ctx.same_minute(np.nan_to_num(width), "median"))
    sq = (width < p["k"] * typ) & (typ > 0)
    prev_sq = ctx.prev(sq.astype(float), 1) == 1
    long = prev_sq & (ctx.c > m + 2 * s)
    short = prev_sq & (ctx.c < m - 2 * s)
    return long.astype(int) - short.astype(int)


def _macd_cross(ctx, p):
    f = int(p["fast"])
    macd = ctx.ema(ctx.c, f) - ctx.ema(ctx.c, 2 * f)
    hist = macd - ctx.ema(macd, f)
    return _sig(ctx, hist > 0, hist < 0)


def _donchian_mid(ctx, p):
    nb = ctx.bars(p["win_min"])
    hi, lo = ctx.roll(ctx.h, nb, "max"), ctx.roll(ctx.l, nb, "min")
    mid = (hi + lo) / 2
    pm = ctx.prev(mid, ctx.bars(10))
    return _sig(ctx, (ctx.c > mid) & (mid > pm), (ctx.c < mid) & (mid < pm))


def _dollar_lag(ctx, p):
    nb = ctx.bars(p["ret_min"])
    oc = ctx.other_close()
    ri = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    rw = oc / ctx.prev(oc, nb) - 1.0
    ti = ctx.cached(("ti", nb), lambda: ctx.prev_sessions(np.nan_to_num(np.abs(ri)), "mean"))
    tw = ctx.cached(("tw", nb), lambda: ctx.prev_sessions(np.nan_to_num(np.abs(rw)), "mean"))
    s = _ratio(ri, ti) + _ratio(rw, tw)
    return _sig(ctx, s <= -p["k"], s >= p["k"])


def _ema_ribbon(ctx, p):
    n = int(p["n"])
    e1 = ctx.ema(ctx.c, n)
    e2 = ctx.ema(ctx.c, 2 * n)
    e3 = ctx.ema(ctx.c, 4 * n)
    return _sig(ctx, (ctx.c > e1) & (e1 > e2) & (e2 > e3), (ctx.c < e1) & (e1 < e2) & (e2 < e3))


def _late_vwap_drift(ctx, p):
    rng = ctx.session_high(True) - ctx.session_low(True)
    frac = _ratio(ctx.c - ctx.vwap(), rng)
    win = (ctx.minutes_to_close <= p["start"]) & (ctx.minutes_to_close >= 10)
    return _sig(ctx, win & (frac <= -p["f"]), win & (frac >= p["f"]))


def _cci_reentry(ctx, p):
    nb = ctx.bars(p["win_min"])
    tp = (ctx.h + ctx.l + ctx.c) / 3
    sma = ctx.roll(tp, nb, "mean")
    md = ctx.roll(np.abs(tp - sma), nb, "mean")
    cci = _ratio(tp - sma, 0.015 * md)
    pc = ctx.prev(cci, 1)
    th = p["th"]
    short = (pc > th) & (cci <= th)
    long = (pc < -th) & (cci >= -th)
    return long.astype(int) - short.astype(int)


def _di_cross(ctx, p):
    nb = ctx.bars(p["win_min"])
    up = ctx.h - ctx.prev(ctx.h, 1)
    dn = ctx.prev(ctx.l, 1) - ctx.l
    plus = np.where((up > dn) & (up > 0), up, 0.0)
    minus = np.where((dn > up) & (dn > 0), dn, 0.0)
    pc = ctx.prev(ctx.c, 1)
    tr = np.maximum(ctx.h - ctx.l, np.maximum(np.abs(ctx.h - pc), np.abs(ctx.l - pc)))
    tr = np.where(np.isnan(pc), np.nan, tr)
    plus = np.where(np.isnan(pc), np.nan, plus)
    minus = np.where(np.isnan(pc), np.nan, minus)
    st = ctx.roll(tr, nb, "sum")
    dip = _ratio(ctx.roll(plus, nb, "sum"), st)
    dim = _ratio(ctx.roll(minus, nb, "sum"), st)
    dx = _ratio(np.abs(dip - dim), dip + dim)
    adx = ctx.roll(dx, nb, "mean")
    ok = adx >= p["adx_min"]
    long = ctx.cross(dip > dim) & ok
    short = ctx.cross(dim > dip) & ok
    return long.astype(int) - short.astype(int)


def _or_mid_cross(ctx, p):
    nb = ctx.bars(p["range_min"])
    first = ctx.bar_in_day < nb
    g = pd.DataFrame({"d": ctx.day, "h": np.where(first, ctx.h, np.nan), "l": np.where(first, ctx.l, np.nan)})
    mid = (g.groupby("d")["h"].transform("max").to_numpy() + g.groupby("d")["l"].transform("min").to_numpy()) / 2
    done = ~first
    return _sig(ctx, done & (ctx.c > mid), done & (ctx.c < mid))


FAMILIES = [
    Family("E-858", "VWAP deviation z-score band fade",
           "Price stretched several standard deviations from VWAP (measured on its own recent deviation) is pushed by "
           "impatient flow; liquidity providers fade it back toward VWAP.",
           {"win_min": [60, 120], "k": [2.0, 2.5, 3.0]}, _vwap_band_fade,
           source="assistant reasoning", author="agent"),
    Family("E-859", "Bollinger squeeze expansion break",
           "When band width is far below its usual level for the time of day, volatility is compressed; the first "
           "close outside the band signals the release direction.",
           {"win_min": [20, 40], "k": [0.6, 0.8, 1.0]}, _squeeze_break,
           source="assistant reasoning", author="agent"),
    Family("E-860", "MACD histogram sign flip",
           "A flip of the MACD histogram marks momentum changing hands between short and long horizon traders; "
           "follow the new sign.",
           {"fast": [6, 9, 12]}, _macd_cross, source="assistant reasoning", author="agent"),
    Family("E-861", "Donchian midpoint cross with rising mid",
           "A close crossing the middle of the N-minute high/low channel while the channel midpoint already drifts "
           "the same way shows value migrating; follow it.",
           {"win_min": [30, 60, 120]}, _donchian_mid, source="assistant reasoning", author="agent",),
    Family("E-862", "Dollar lead, index lag",
           "WIN and the dollar are inversely linked; when the dollar has moved much more than the index implies, "
           "index traders lag arbitrageurs and WIN catches up.",
           {"ret_min": [5, 15, 30], "k": [1.5, 2.0, 2.5]}, _dollar_lag, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-863", "EMA ribbon alignment onset",
           "Close above a stack of rising-order EMAs (n, 2n, 4n) means all horizons agree; the first bar of "
           "alignment starts a trend leg.",
           {"n": [5, 8, 12]}, _ema_ribbon, source="assistant reasoning", author="agent"),
    Family("E-864", "Late-session stretch back to VWAP",
           "Near the close, day traders and funds flatten books; a large stretch from VWAP relative to the day's "
           "range tends to be pulled back as positions are squared.",
           {"f": [0.25, 0.35, 0.5], "start": [45, 90]}, _late_vwap_drift,
           source="assistant reasoning", author="agent"),
    Family("E-865", "CCI extreme re-entry fade",
           "When CCI falls back inside +-threshold after an extreme, the stretch has stopped extending and "
           "late momentum chasers are trapped; fade.",
           {"win_min": [30, 60, 120], "th": [100, 150, 200]}, _cci_reentry,
           source="assistant reasoning", author="agent"),
    Family("E-866", "DI cross with trend-strength filter",
           "A +DI/-DI cross while directional movement is already strong (high ADX-like reading) indicates that "
           "the stronger side keeps control.",
           {"win_min": [30, 60], "adx_min": [0.15, 0.25, 0.35]}, _di_cross,
           source="assistant reasoning", author="agent"),
    Family("E-867", "Opening-range midpoint cross",
           "After the opening range ends, the range midpoint is the balance point; a close crossing it shows the "
           "opening auction's winner and drives the day's side.",
           {"range_min": [15, 30, 60]}, _or_mid_cross, source="assistant reasoning", author="agent"),
]
