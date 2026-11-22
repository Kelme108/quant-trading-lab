"""Conveyor batch B-050 (agent, 2026-11-21). Ten mixed ideas: z-score fade, US-open impulse, level crosses, volatility expansion, flow."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _dir(long, short):
    return np.asarray(long).astype(int) - np.asarray(short).astype(int)


def _ema_z_fade(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    ema = ctx.ema(ctx.c, n)
    dev = ctx.c - ema
    sd = ctx.roll(dev, n, "std")
    with np.errstate(all="ignore"):
        z = np.where(sd > 0, dev / sd, np.nan)
        return _dir(ctx.cross(z < -k), ctx.cross(z > k))


def _us_open_impulse(ctx, p):
    m = int(p["m"])
    out = np.zeros(ctx.n, dtype=int)
    for mark in (630, 690):
        mo = pd.Series(np.where(ctx.minute == mark, ctx.o, np.nan)).groupby(ctx.day).ffill().to_numpy()
        fire = ctx.minute == (mark + m - ctx.tf)
        with np.errstate(all="ignore"):
            d = np.sign(np.nan_to_num(ctx.c - mo))
        out = out + np.where(fire, d, 0).astype(int)
    return np.clip(out, -1, 1)


def _day_open_recross(ctx, p):
    k = p["k"]
    r = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("abs_r_sm", lambda: ctx.same_minute(np.abs(r), "mean"))
    hi = ctx.session_high(include_current=True) / ctx.day_open - 1.0
    lo = 1.0 - ctx.session_low(include_current=True) / ctx.day_open
    with np.errstate(all="ignore"):
        short = (hi >= k * typ) & (ctx.c < ctx.day_open) & (typ > 0)
        long = (lo >= k * typ) & (ctx.c > ctx.day_open) & (typ > 0)
        return _dir(ctx.cross(long), ctx.cross(short))


def _pd_mid_cross(ctx, p):
    b = p["buf"]
    mid = (ctx.prev_session_value("high") + ctx.prev_session_value("low")) / 2.0
    with np.errstate(all="ignore"):
        return _dir(ctx.cross(ctx.c > mid * (1 + b)), ctx.cross(ctx.c < mid * (1 - b)))


def _vol_expansion(ctx, p):
    ns, ratio = ctx.bars(p["short_min"]), p["ratio"]
    rng = ctx.h - ctx.l
    fast = ctx.roll(rng, ns, "mean")
    slow = ctx.roll(rng, ctx.bars(60), "mean")
    move = ctx.c - ctx.prev(ctx.c, ns)
    with np.errstate(all="ignore"):
        base = (fast > ratio * slow) & (slow > 0)
        return _dir(ctx.cross(base & (move > 0)), ctx.cross(base & (move < 0)))


def _ladder(ctx, p):
    n = int(p["n"])
    with np.errstate(all="ignore"):
        up = ((ctx.h > ctx.prev(ctx.h, 1)) & (ctx.l > ctx.prev(ctx.l, 1))).astype(float)
        dn = ((ctx.h < ctx.prev(ctx.h, 1)) & (ctx.l < ctx.prev(ctx.l, 1))).astype(float)
        u = ctx.roll(up, n, "sum") == n
        d = ctx.roll(dn, n, "sum") == n
    return _dir(ctx.cross(u), ctx.cross(d))


def _or_mid_cross(ctx, p):
    nb, b = ctx.bars(p["or_min"]), p["buf"]
    first = ctx.bar_in_day < nb
    g = pd.DataFrame({"d": ctx.day, "h": np.where(first, ctx.h, np.nan), "l": np.where(first, ctx.l, np.nan)})
    orh = g.groupby("d")["h"].transform("max").to_numpy()
    orl = g.groupby("d")["l"].transform("min").to_numpy()
    mid = (orh + orl) / 2.0
    done = ~first
    pc = ctx.prev(ctx.c, 1)
    with np.errstate(all="ignore"):
        up_lvl, dn_lvl = mid * (1 + b), mid * (1 - b)
        up = done & (pc <= up_lvl) & (ctx.c > up_lvl)
        dn = done & (pc >= dn_lvl) & (ctx.c < dn_lvl)
    return _dir(up, dn)


def _keltner_break(ctx, p):
    k = p["k"]
    n = ctx.bars(p["ema_min"])
    ema = ctx.ema(ctx.c, n)
    atr = ctx.roll(ctx.h - ctx.l, ctx.bars(10), "mean")
    with np.errstate(all="ignore"):
        return _dir(ctx.cross(ctx.c > ema + k * atr), ctx.cross(ctx.c < ema - k * atr))


def _seasonal_drift(ctx, p):
    th = p["th"]
    ret = (ctx.c - ctx.o) / ctx.o
    m = ctx.cached("sd_mean", lambda: ctx.same_minute(ret, "mean"))
    a = ctx.cached("sd_abs", lambda: ctx.same_minute(np.abs(ret), "mean"))
    with np.errstate(all="ignore"):
        ratio = np.where(a > 0, m / a, np.nan)
        return _dir(ctx.cross(ratio > th), ctx.cross(ratio < -th))


def _cmf_cross(ctx, p):
    n, th = ctx.bars(p["win_min"]), p["th"]
    rng = ctx.h - ctx.l
    with np.errstate(all="ignore"):
        clv = np.where(rng > 0, ((ctx.c - ctx.l) - (ctx.h - ctx.c)) / rng, 0.0)
        num = ctx.roll(clv * ctx.v, n, "sum")
        den = ctx.roll(ctx.v, n, "sum")
        cmf = np.where(den > 0, num / den, np.nan)
        return _dir(ctx.cross(cmf > th), ctx.cross(cmf < -th))


W = ("WIN",)
FAMILIES = [
    Family("E-498", "EMA z-score stretch fade",
           "A close several standard deviations from its own session EMA is a liquidity-driven stretch by an impatient "
           "taker; passive liquidity should pull it back toward the mean.",
           {"win_min": [30, 60, 120], "k": [2.0, 2.5, 3.0]}, _ema_z_fade, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-499", "US-cash-open impulse follow",
           "When US equities open (10:30 or 11:30 São Paulo depending on DST) foreign flow hits the index; the first "
           "minutes' direction should carry as hedgers and index arbitrageurs follow.",
           {"m": [5, 10, 15]}, _us_open_impulse, markets=W, source="assistant reasoning", author="agent"),
    Family("E-500", "Day-open recross after an excursion",
           "After an unusually large excursion from the session open, a close back through the open means the "
           "day's initiators lost; the other side takes control.",
           {"k": [1.0, 1.5, 2.0]}, _day_open_recross, markets=W, source="assistant reasoning", author="agent"),
    Family("E-501", "Prior-session midpoint cross follow",
           "The prior session's range midpoint splits yesterday's value in two; a close across it shifts the "
           "balance and the move should extend as range traders reposition.",
           {"buf": [0.0, 0.0003, 0.0006]}, _pd_mid_cross, markets=W, source="assistant reasoning", author="agent"),
    Family("E-502", "Volatility-expansion direction follow",
           "When recent bar ranges jump over the last hour's average, informed urgency has arrived; the net direction of "
           "that burst tends to carry while slower participants chase.",
           {"short_min": [5, 10, 15], "ratio": [1.5, 2.0, 2.5]}, _vol_expansion, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-503", "Higher-high higher-low ladder follow",
           "Consecutive bars each making higher highs and higher lows (or the reverse) show trapped counterparties "
           "covering step by step; follow the staircase.",
           {"n": [3, 4, 5]}, _ladder, markets=W, source="assistant reasoning", author="agent"),
    Family("E-504", "Opening-range midpoint cross follow",
           "After the opening range is set, the midpoint is where early buyers and sellers balance; a close "
           "across it signals the winning side and should extend.",
           {"or_min": [15, 30, 60], "buf": [0.0, 0.0002, 0.0005]}, _or_mid_cross, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-505", "Keltner channel break follow",
           "A close beyond EMA plus a multiple of average bar range signals a volatility-adjusted breakout; "
           "stop orders and momentum followers feed the move.",
           {"ema_min": [20, 40, 60], "k": [1.5, 2.0, 2.5]}, _keltner_break, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-506", "Same-minute seasonal drift follow",
           "Scheduled flows (funds, hedgers, index rebalance, data releases) recur at the same clock minute; if "
           "the last 20 sessions showed a consistent bar direction at this minute, join it.",
           {"th": [0.3, 0.4, 0.5]}, _seasonal_drift, markets=W, source="assistant reasoning", author="agent"),
    Family("E-507", "Chaikin money-flow zero-zone cross follow",
           "Where bars close inside their range, weighted by volume, reveals who is absorbing; a flip of this flow "
           "beyond a threshold shows a new aggressor.",
           {"win_min": [15, 30, 60], "th": [0.1, 0.2, 0.3]}, _cmf_cross, markets=W,
           source="assistant reasoning", author="agent"),
]
