"""Conveyor batch B-053 (agent, 2026-11-21). Mixed micro-structure ideas: pokes, volume sequences, levels, VWAP side."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _d(long, short):
    return np.asarray(long, bool).astype(int) - np.asarray(short, bool).astype(int)


def _poke_fade(ctx, p):
    q = p["q"]
    h1, l1, c1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1), ctx.prev(ctx.c, 1)
    r1 = h1 - l1
    short = (ctx.h > h1) & (ctx.h <= h1 + q * r1) & (ctx.c < c1) & (r1 > 0)
    long = (ctx.l < l1) & (ctx.l >= l1 - q * r1) & (ctx.c > c1) & (r1 > 0)
    return _d(long, short)


def _prior_open_recross(ctx, p):
    nb = ctx.bars(p["away_min"])
    po = ctx.prev_session_value("open")
    below = (ctx.c < po).astype(float)
    above = (ctx.c > po).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    return _d(was_below & (ctx.c > po), was_above & (ctx.c < po))


def _fading_volume_run(ctx, p):
    n = int(p["run"])
    c1, v1 = ctx.prev(ctx.c, 1), ctx.prev(ctx.v, 1)
    up = ((ctx.c > c1) & (ctx.v < v1)).astype(float)
    dn = ((ctx.c < c1) & (ctx.v < v1)).astype(float)
    up_run = ctx.roll(up, n, "min") == 1
    dn_run = ctx.roll(dn, n, "min") == 1
    return _d(ctx.cross(dn_run), ctx.cross(up_run))


def _signed_volume_share(ctx, p):
    k = p["k"]
    sv = np.sign(ctx.c - ctx.o) * ctx.v
    g = pd.DataFrame({"d": ctx.day, "sv": sv, "v": ctx.v})
    cum = g.groupby("d")["sv"].cumsum().to_numpy()
    cumv = g.groupby("d")["v"].cumsum().to_numpy()
    share = np.where(cumv > 0, cum / np.where(cumv > 0, cumv, 1.0), 0.0)
    ok = ctx.bar_in_day >= ctx.bars(30)
    return _d(ctx.cross((share > k) & ok), ctx.cross((share < -k) & ok))


def _event_minute_bar(ctx, p):
    k = p["k"]
    med = ctx.cached("vol_med_same", lambda: ctx.same_minute(ctx.v, "median"))
    heavy = (med > 0) & (ctx.v > k * med)
    c1 = ctx.prev(ctx.c, 1)
    long = heavy & (ctx.c > ctx.o) & (ctx.c > c1)
    short = heavy & (ctx.c < ctx.o) & (ctx.c < c1)
    return _d(long, short)


def _closing_vwap_side(ctx, p):
    nb = ctx.bars(p["side_min"])
    vw = ctx.vwap()
    above = ctx.roll((ctx.c > vw).astype(float), nb, "min") == 1
    below = ctx.roll((ctx.c < vw).astype(float), nb, "min") == 1
    nb2 = ctx.bars(10)
    hi = ctx.roll(ctx.h, nb2, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb2, "min", include_current=False)
    late = ctx.minutes_to_close <= 150
    long = late & above & (ctx.c > hi)
    short = late & below & (ctx.c < lo)
    return _d(ctx.cross(long), ctx.cross(short))


def _elder_ray_hook(ctx, p):
    n = int(p["ema_bars"])
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    rising = ema > ctx.prev(ema, 3)
    falling = ema < ctx.prev(ema, 3)
    bear = ctx.l - ema
    bull = ctx.h - ema
    bear1 = ctx.prev(bear, 1)
    bull1 = ctx.prev(bull, 1)
    bear_min = ctx.prev(ctx.roll(bear, 5, "min"), 1)
    bull_max = ctx.prev(ctx.roll(bull, 5, "max"), 1)
    long = rising & (bear1 < 0) & (bear1 <= bear_min) & (bear > bear1) & (ctx.c > ctx.o)
    short = falling & (bull1 > 0) & (bull1 >= bull_max) & (bull < bull1) & (ctx.c < ctx.o)
    return _d(long, short)


def _counter_run_vwap(ctx, p):
    n = int(p["run"])
    vw = ctx.vwap()
    c1 = ctx.prev(ctx.c, 1)
    dn = (ctx.c < c1).astype(float)
    up = (ctx.c > c1).astype(float)
    ab = (ctx.c > vw).astype(float)
    be = (ctx.c < vw).astype(float)
    dn_run = ctx.roll(dn, n, "min", include_current=False) == 1
    up_run = ctx.roll(up, n, "min", include_current=False) == 1
    ab_run = ctx.roll(ab, n, "min", include_current=False) == 1
    be_run = ctx.roll(be, n, "min", include_current=False) == 1
    long = dn_run & ab_run & (ctx.c > c1) & (ctx.c > ctx.o) & (ctx.c > vw)
    short = up_run & be_run & (ctx.c < c1) & (ctx.c < ctx.o) & (ctx.c < vw)
    return _d(long, short)


def _no_supply(ctx, p):
    n, r = int(p["ema_bars"]), p["r"]
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    rng = ctx.h - ctx.l
    avg = ctx.cached("avg_rng20", lambda: ctx.roll(rng, 20, "mean"))
    c1 = ctx.prev(ctx.c, 1)
    vmin = np.minimum(ctx.prev(ctx.v, 1), ctx.prev(ctx.v, 2))
    narrow = rng < r * avg
    thin = ctx.v < vmin
    long = narrow & thin & (ctx.c < c1) & (ctx.c > ema)
    short = narrow & thin & (ctx.c > c1) & (ctx.c < ema)
    return _d(long, short)


def _thrust_fade(ctx, p):
    n, th = int(p["n_bars"]), p["th"]
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    union = np.maximum(ctx.h, h1) - np.minimum(ctx.l, l1)
    inter = np.minimum(ctx.h, h1) - np.maximum(ctx.l, l1)
    ov = np.where(union > 0, np.clip(inter, 0, None) / np.where(union > 0, union, 1.0), np.nan)
    mov = ctx.roll(ov, n, "mean")
    net = ctx.c - ctx.prev(ctx.c, n)
    thrust = mov < th
    up = thrust & (net > 0) & (ctx.c > ctx.o)
    dn = thrust & (net < 0) & (ctx.c < ctx.o)
    return _d(ctx.cross(dn), ctx.cross(up))


W = ("WIN",)

FAMILIES = [
    Family("E-528", "One-sliver poke fade",
           "A bar that pokes only a sliver beyond the previous bar's extreme and closes back against the prior close "
           "shows stop orders just beyond the extreme found no follow-through; fade the poke.",
           {"q": [0.1, 0.25, 0.5]}, _poke_fade, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-529", "Prior-session open recross follow",
           "The previous session's opening price is a reference many participants remember; a close back across it "
           "after a long stay on one side flips the sentiment of yesterday's openers, follow the cross.",
           {"away_min": [15, 30, 60]}, _prior_open_recross, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-530", "Fading-volume run fade",
           "A run of closes in one direction while each bar trades less volume than the last means the push lacks "
           "participation; liquidity providers fade it.",
           {"run": [2, 3, 4]}, _fading_volume_run, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-531", "Session signed-volume share cross follow",
           "The share of the session's volume traded in up bars minus down bars summarises who has been the "
           "aggressor all day; when it crosses a threshold the day's inventory holders are on one side, follow.",
           {"k": [0.05, 0.1, 0.2]}, _signed_volume_share, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-532", "Event-minute heavy bar follow",
           "A bar with volume far above its usual same-minute level is a scheduled-or-news event; the informed "
           "flow behind it keeps pushing in the bar's direction.",
           {"k": [2.0, 3.0, 4.0]}, _event_minute_bar, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-533", "Closing-hours VWAP-side breakout follow",
           "In the last hours, a market that has stayed on one side of VWAP and makes a fresh short-term extreme "
           "has benchmark (VWAP) buyers or sellers still to execute before the close; follow.",
           {"side_min": [30, 60, 90]}, _closing_vwap_side, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-534", "Elder-Ray power hook in an EMA trend",
           "In a rising EMA trend, bear power (low minus EMA) turning up from its recent low marks sellers losing "
           "the pullback; buy the hook, sell the mirror in a falling trend.",
           {"ema_bars": [13, 21, 34]}, _elder_ray_hook, markets=W,
           source="Elder, Come Into My Trading Room (Elder-Ray); assistant reasoning", author="agent"),
    Family("E-535", "Counter-colour run on the VWAP side resumption",
           "Several counter-trend closes that never lose the VWAP are a shallow pullback inside the side that "
           "institutions defend; the first bar back with the trend resumes it.",
           {"run": [2, 3, 4]}, _counter_run_vwap, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-536", "Wyckoff no-supply / no-demand test",
           "A narrow, low-volume down bar inside an uptrend (no supply) shows sellers have dried up; the mirror "
           "no-demand bar in a downtrend; trade with the trend.",
           {"ema_bars": [20, 40, 60], "r": [0.5, 0.7, 0.9]}, _no_supply, markets=W,
           source="Wyckoff method (no supply / no demand bars), assistant reasoning", author="agent"),
    Family("E-537", "Low-overlap thrust fade",
           "Consecutive bars barely overlapping mean one side took liquidity aggressively; such thrusts overshoot "
           "and partly revert once the urgent flow is done.",
           {"n_bars": [3, 4, 5], "th": [0.3, 0.4, 0.5]}, _thrust_fade, markets=W,
           source="assistant reasoning", author="agent"),
]
