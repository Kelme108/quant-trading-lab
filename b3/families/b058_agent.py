"""Conveyor batch B-058 (agent, 2026-11-21). Context-filtered micro-break fades and short-run exhaustion shapes on WIN."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _fade_break(ctx, nb, up_ok=None, dn_ok=None, mask=None):
    """Fade the first bar that pokes beyond the prior nb-bar high/low (short above, long below)."""
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    up = ctx.h > hi
    dn = ctx.l < lo
    if up_ok is not None:
        up = up & up_ok
    if dn_ok is not None:
        dn = dn & dn_ok
    if mask is not None:
        up = up & mask
        dn = dn & mask
    return ctx.cross(dn).astype(int) - ctx.cross(up).astype(int)


def _thin_break(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    thin = ctx.v < k * med
    return _fade_break(ctx, nb, thin, thin)


def _tweezer(ctx, p):
    run, tol = int(p["run"]), p["tol"]
    scale = ctx.roll(ctx.h - ctx.l, 10, "mean", include_current=False)
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    o1, c1 = ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1)
    base_c, far_c = ctx.prev(ctx.c, 2), ctx.prev(ctx.c, 2 + run)
    short = (base_c > far_c) & (c1 > o1) & (ctx.c < ctx.o) & (np.abs(ctx.h - h1) <= tol * scale)
    long = (base_c < far_c) & (c1 < o1) & (ctx.c > ctx.o) & (np.abs(ctx.l - l1) <= tol * scale)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _staircase_stall(ctx, p):
    n, k = int(p["n"]), p["k"]
    scale = ctx.roll(ctx.h - ctx.l, 10, "mean", include_current=False)
    up_stairs = np.ones(ctx.n, dtype=bool)
    dn_stairs = np.ones(ctx.n, dtype=bool)
    for i in range(1, n + 1):
        up_stairs &= (ctx.prev(ctx.h, i) > ctx.prev(ctx.h, i + 1)) & (ctx.prev(ctx.l, i) > ctx.prev(ctx.l, i + 1))
        dn_stairs &= (ctx.prev(ctx.h, i) < ctx.prev(ctx.h, i + 1)) & (ctx.prev(ctx.l, i) < ctx.prev(ctx.l, i + 1))
    adv = ctx.prev(ctx.c, 1) - ctx.prev(ctx.c, n + 1)
    short = up_stairs & (adv >= k * scale) & (ctx.h <= ctx.prev(ctx.h, 1)) & (ctx.c < ctx.prev(ctx.c, 1))
    long = dn_stairs & (-adv >= k * scale) & (ctx.l >= ctx.prev(ctx.l, 1)) & (ctx.c > ctx.prev(ctx.c, 1))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _open_chop_break(ctx, p):
    n, nb = int(p["crosses"]), ctx.bars(p["win_min"])
    sgn = np.sign(ctx.c - ctx.day_open)
    ps = ctx.prev(sgn, 1)
    chg = ((sgn != ps) & ~np.isnan(ps)).astype(float)
    cnt = ctx.roll(chg, ctx.bars(90), "sum")
    return _fade_break(ctx, nb, mask=(cnt >= n))


def _afternoon_break(ctx, p):
    nb = ctx.bars(p["win_min"])
    mask = (ctx.minute >= p["start_min"]) & (ctx.minute < 17 * 60)
    return _fade_break(ctx, nb, mask=mask)


def _clv_saturation(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    rng = ctx.h - ctx.l
    clv = np.where(rng > 0, (2 * ctx.c - ctx.h - ctx.l) / np.where(rng > 0, rng, 1.0), 0.0)
    m = ctx.roll(clv, nb, "mean")
    short = ctx.cross(m >= th)
    long = ctx.cross(m <= -th)
    return long.astype(int) - short.astype(int)


def _narrow_poke(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    r = ctx.roll(ctx.h - ctx.l, 20, "mean", include_current=False)
    narrow = (ctx.h - ctx.l) < k * r
    return _fade_break(ctx, nb, narrow, narrow)


def _up_share(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    upb = ctx.roll((ctx.c > ctx.o).astype(float), nb, "mean")
    dnb = ctx.roll((ctx.c < ctx.o).astype(float), nb, "mean")
    short = ctx.cross(upb >= th)
    long = ctx.cross(dnb >= th)
    return long.astype(int) - short.astype(int)


def _median_mad_fade(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]

    def _med():
        s = pd.Series(ctx.c)
        return s.groupby(ctx.day).transform(lambda z: z.rolling(n, min_periods=n).median()).to_numpy()

    med = ctx.cached(("median", n), _med)
    mad = ctx.roll(np.abs(ctx.c - med), n, "mean")
    z = np.where(mad > 0, (ctx.c - med) / np.where(mad > 0, mad, 1.0), 0.0)
    return ctx.cross(z <= -k).astype(int) - ctx.cross(z >= k).astype(int)


def _early_break(ctx, p):
    nb = ctx.bars(p["win_min"])
    mask = (ctx.minute >= 9 * 60 + 15) & (ctx.minute < p["end_min"])
    return _fade_break(ctx, nb, mask=mask)


FAMILIES = [
    Family("E-578", "Thin-volume micro-break fade",
           "A poke beyond the recent high/low made on volume below normal for the minute of day has no real "
           "participation behind it; liquidity takers are absent and the poke is rejected back into the range.",
           {"win_min": [10, 20, 30], "k": [0.5, 0.75, 1.0]}, _thin_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-579", "Tweezer reversal after a run",
           "Two adjacent bars of opposite colour stopping at the same extreme after a run show a level that two "
           "waves of aggressive orders both failed to pass; fade it.",
           {"run": [3, 5, 8], "tol": [0.1, 0.2, 0.3]}, _tweezer, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-580", "Staircase stall fade",
           "After a run of bars each making higher highs and higher lows, the first bar that fails to extend and "
           "closes down shows the late trend followers have run out of buyers.",
           {"n": [3, 4, 5], "k": [0.0, 1.0, 2.0]}, _staircase_stall, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-581", "Open-chop micro-break fade",
           "When price has repeatedly crossed the day's opening price in the last 90 minutes the market is "
           "rotating around a fair value; short-window breaks in that state are stop runs that revert.",
           {"crosses": [2, 3, 4], "win_min": [10, 20, 30]}, _open_chop_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-582", "Afternoon micro-break fade",
           "In the afternoon, after the day's information is priced and before the closing flow, short-window "
           "breaks lack follow-through and are faded by liquidity providers.",
           {"start_min": [840, 900, 960], "win_min": [10, 20, 30]}, _afternoon_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-583", "Close-location saturation fade",
           "When bars keep closing at one end of their range over a window, aggressors have been paying the spread "
           "for a while; that pressure is spent and the next move is back.",
           {"win_min": [15, 30, 60], "th": [0.3, 0.4, 0.5]}, _clv_saturation, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-584", "Narrow-poke break fade",
           "A break of the recent extreme made by a small-range bar is a creep rather than an impulse; a creep "
           "into resting orders gets absorbed instead of continuing.",
           {"win_min": [10, 20, 30], "k": [0.5, 0.75, 1.0]}, _narrow_poke, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-585", "One-colour bar share fade",
           "When nearly all bars in a window have the same colour, the move is one-sided enough that dip buyers "
           "or rally sellers are waiting; fade the saturation point.",
           {"win_min": [10, 15, 20], "th": [0.7, 0.8, 0.9]}, _up_share, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-586", "Local-median stretch fade",
           "A close far from its rolling median, scaled by the mean absolute deviation around that median, is a "
           "robust measure of overextension that single spikes do not distort; fade it.",
           {"win_min": [30, 60, 90], "k": [2.5, 3.0, 4.0]}, _median_mad_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-587", "Early-session micro-break fade",
           "Right after the open, quotes are wide and breaks of the first few minutes' extremes are often "
           "liquidity vacuums, which refill and revert.",
           {"end_min": [600, 630, 660], "win_min": [5, 10, 15]}, _early_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
