"""Conveyor batch B-007 (agent, 2026-11-18). Mixed WIN themes: volume leading price, quiet pullbacks, range traverse, retail counts and patterns, impulse-bar levels."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _typ_range(ctx):
    return ctx.cached("rng_prev_mean", lambda: ctx.prev_sessions(ctx.h - ctx.l, "mean"))


def _vol_med(ctx):
    return ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))


def _obv_lead(ctx, p):
    nb = ctx.bars(p["win_min"])
    dc = ctx.c - ctx.prev(ctx.c, 1)
    sv = np.nan_to_num(np.sign(dc) * ctx.v, nan=0.0)
    obv = pd.Series(sv).groupby(ctx.day).cumsum().to_numpy()
    ohi = ctx.roll(obv, nb, "max", include_current=False)
    olo = ctx.roll(obv, nb, "min", include_current=False)
    phi = ctx.roll(ctx.h, nb, "max", include_current=False)
    plo = ctx.roll(ctx.l, nb, "min", include_current=False)
    long = (obv > ohi) & (ctx.c < phi) & (ctx.c > plo)
    short = (obv < olo) & (ctx.c > plo) & (ctx.c < phi)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _dry_pullback(ctx, p):
    pb, k = int(p["pb"]), float(p["k"])
    med = _vol_med(ctx)
    quiet = ctx.v < k * med
    c1 = ctx.prev(ctx.c, 1)
    dn = ((ctx.c < c1) & quiet).astype(float)
    up = ((ctx.c > c1) & quiet).astype(float)
    was_dn = ctx.roll(dn, pb, "min", include_current=False) == 1
    was_up = ctx.roll(up, pb, "min", include_current=False) == 1
    vw = ctx.vwap()
    vw_l = ctx.prev(vw, ctx.bars(30))
    upt = (ctx.c > vw) & (vw > vw_l)
    dnt = (ctx.c < vw) & (vw < vw_l)
    long = upt & was_dn & (ctx.c > ctx.prev(ctx.h, 1))
    short = dnt & was_up & (ctx.c < ctx.prev(ctx.l, 1))
    return long.astype(int) - short.astype(int)


def _traverse(ctx, p):
    nb, q = ctx.bars(p["win_min"]), float(p["q"])
    sh = ctx.session_high(include_current=True)
    sl = ctx.session_low(include_current=True)
    R = sh - sl
    yr = ctx.prev_session_value("high") - ctx.prev_session_value("low")
    ok = (ctx.bar_in_day >= ctx.bars(30)) & (R >= 0.3 * yr)
    pos = (ctx.c - sl) / np.where(R > 0, R, np.nan)
    lo_recent = ctx.roll(pos, nb, "min", include_current=False) <= q
    hi_recent = ctx.roll(pos, nb, "max", include_current=False) >= 1 - q
    long = ok & lo_recent & (pos >= 1 - q)
    short = ok & hi_recent & (pos <= q)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _rising_volume_run(ctx, p):
    r, k = int(p["run"]), float(p["k"])
    c1, v1 = ctx.prev(ctx.c, 1), ctx.prev(ctx.v, 1)
    med = _vol_med(ctx)
    upc = ((ctx.c > c1) & (ctx.v > v1)).astype(float)
    dnc = ((ctx.c < c1) & (ctx.v > v1)).astype(float)
    runu = ctx.roll(upc, r, "min") == 1
    rund = ctx.roll(dnc, r, "min") == 1
    heavy = ctx.v >= k * med
    long = ctx.cross(runu) & heavy
    short = ctx.cross(rund) & heavy
    return long.astype(int) - short.astype(int)


def _impulse_half(ctx, p):
    k, W = float(p["k"]), ctx.bars(p["window_min"])
    rng = ctx.h - ctx.l
    typ = _typ_range(ctx)
    body = ctx.c - ctx.o
    big = rng >= k * typ
    up_imp = (big & (body >= 0.6 * rng)).tolist()
    dn_imp = (big & (-body >= 0.6 * rng)).tolist()
    h, l, c, day = ctx.h.tolist(), ctx.l.tolist(), ctx.c.tolist(), ctx.day.tolist()
    out = np.zeros(ctx.n, dtype=int)
    cur, U, D = None, None, None
    for i in range(ctx.n):
        if day[i] != cur:
            cur, U, D = day[i], None, None
        s = 0
        if U is not None:
            if i - U[0] > W:
                U = None
            elif l[i] <= U[1]:
                if c[i] > U[1]:
                    s += 1
                U = None
        if D is not None:
            if i - D[0] > W:
                D = None
            elif h[i] >= D[1]:
                if c[i] < D[1]:
                    s -= 1
                D = None
        out[i] = s
        if up_imp[i]:
            U = (i, (h[i] + l[i]) / 2.0)
        if dn_imp[i]:
            D = (i, (h[i] + l[i]) / 2.0)
    return out


def _hikkake(ctx, p):
    m = int(p["m"])
    h, l, c, day = ctx.h.tolist(), ctx.l.tolist(), ctx.c.tolist(), ctx.day.tolist()
    out = np.zeros(ctx.n, dtype=int)
    cur, L, S = None, None, None
    for i in range(ctx.n):
        if day[i] != cur:
            cur, L, S = day[i], None, None
        s = 0
        if L is not None:
            if i > L[0]:
                L = None
            elif c[i] > L[1]:
                s += 1
                L = None
        if S is not None:
            if i > S[0]:
                S = None
            elif c[i] < S[1]:
                s -= 1
                S = None
        out[i] = s
        if i >= 2 and day[i - 2] == day[i]:
            inside = h[i - 1] < h[i - 2] and l[i - 1] > l[i - 2]
            if inside and l[i] < l[i - 1] and h[i] <= h[i - 1]:
                L = (i + m, h[i - 1])
            if inside and h[i] > h[i - 1] and l[i] >= l[i - 1]:
                S = (i + m, l[i - 1])
    return out


def _open_extreme(ctx, p):
    k = float(p["k"])
    rng = ctx.h - ctx.l
    typ = _typ_range(ctx)
    tol = 1e-6
    ok = (rng > 0) & (rng >= k * typ)
    long = ok & (np.abs(ctx.o - ctx.l) <= tol) & (ctx.c >= ctx.l + 0.5 * rng)
    short = ok & (np.abs(ctx.h - ctx.o) <= tol) & (ctx.c <= ctx.h - 0.5 * rng)
    return long.astype(int) - short.astype(int)


def _td_setup_fade(ctx, p):
    n = int(p["count"])
    c4 = ctx.prev(ctx.c, 4)
    up = (ctx.c > c4).astype(float)
    dn = (ctx.c < c4).astype(float)
    done_up = ctx.roll(up, n, "min") == 1
    done_dn = ctx.roll(dn, n, "min") == 1
    return ctx.cross(done_dn).astype(int) - ctx.cross(done_up).astype(int)


def _stoch_pop(ctx, p):
    n, th = int(p["n"]), float(p["th"])
    hh = ctx.roll(ctx.h, n, "max")
    ll = ctx.roll(ctx.l, n, "min")
    rr = hh - ll
    K = 100.0 * (ctx.c - ll) / np.where(rr > 0, rr, np.nan)
    vw = ctx.vwap()
    long = ctx.cross(K >= th) & (ctx.c > vw)
    short = ctx.cross(K <= 100.0 - th) & (ctx.c < vw)
    return long.astype(int) - short.astype(int)


def _volume_asymmetry(ctx, p):
    nb, r = ctx.bars(p["win_min"]), float(p["ratio"])
    isup = (ctx.c > ctx.o).astype(float)
    isdn = (ctx.c < ctx.o).astype(float)
    su = ctx.roll(ctx.v * isup, nb, "sum")
    sd = ctx.roll(ctx.v * isdn, nb, "sum")
    nu = ctx.roll(isup, nb, "sum")
    nd = ctx.roll(isdn, nb, "sum")
    mu = su / np.where(nu > 0, nu, np.nan)
    md = sd / np.where(nd > 0, nd, np.nan)
    net = ctx.c - ctx.prev(ctx.c, nb)
    short = (net > 0) & (md >= r * mu)
    long = (net < 0) & (mu >= r * md)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


FAMILIES = [
    Family("E-059", "OBV leads the price high",
           "When session on-balance volume makes a new high for the window while price is still below its window high, "
           "volume on up bars is outpacing volume on down bars before the price has moved (patient accumulation); the "
           "sellers capping the price are being worked through, so price follows the volume line (mirror for lows).",
           {"win_min": [15, 30, 60]}, _obv_lead, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-060", "Low-volume pullback resumption",
           "In a session trend (price on the rising side of a rising VWAP), a pullback of several bars each on below-normal "
           "volume for its minute shows no real supply, only profit-taking (a Wyckoff 'test'); the first close above the "
           "previous bar's high is the trend holders resuming, so follow it (mirror in a down trend).",
           {"pb": [2, 3, 4], "k": [0.6, 0.8, 1.0]}, _dry_pullback, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-061", "Session-range traverse follow",
           "Crossing from the bottom to the top part of the day's developed range within a short time is initiative "
           "activity by a longer-timeframe participant, not responsive rotation; such a participant keeps working the "
           "order, so the traverse continues past the far edge; follow it (mirror for a fast fall).",
           {"win_min": [10, 20, 30], "q": [0.15, 0.25, 0.35]}, _traverse, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-062", "Rising-volume run follow",
           "Consecutive higher closes each traded on more volume than the bar before show participation building into "
           "the move: more and more traders are paying up rather than a single burst; flow that keeps growing is a parent "
           "order being scaled up, so follow the bar that completes the run when its volume is at least normal.",
           {"run": [2, 3, 4], "k": [0.8, 1.0, 1.25]}, _rising_volume_run, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-063", "Impulse-bar midpoint hold",
           "A large near-full-body bar is a burst of one-sided market orders; its midpoint is the average fill of that "
           "burst. The first return to the midpoint that closes back on the impulse side shows the impulse side "
           "defending its average price while the counter-traders who faded it are trapped; follow the impulse.",
           {"k": [1.5, 2.0, 2.5], "window_min": [15, 30, 60]}, _impulse_half, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-064", "Hikkake inside-bar fakeout",
           "After an inside bar, a break of only one side of it draws breakout traders in that direction; if price then "
           "closes beyond the OTHER side of the inside bar within a few bars, those traders are trapped with stops just "
           "behind and the release of the compression goes the other way; follow the fakeout reversal.",
           {"m": [2, 3, 5]}, _hikkake, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-065", "Open-at-extreme bar follow",
           "A bar of at least typical range whose open is its low (no trade below the opening price for the whole bar) "
           "and that closes in its upper half shows buyers lifting offers from the first tick with no seller able to "
           "push below; demand that strong at the bar's start is a parent order still running, so follow it (mirror).",
           {"k": [0.75, 1.0, 1.5]}, _open_extreme, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-066", "TD setup count exhaustion fade",
           "DeMark's TD setup (N consecutive closes above the close four bars earlier) is plotted by many platforms and "
           "marks a move carried by late chasers; when the count completes, the trend followers are fully in and "
           "counters on many screens flag exhaustion at the same bar, so fade it (mirror for a down count).",
           {"count": [7, 9, 11]}, _td_setup_fade, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-067", "Stochastic pop with the VWAP side",
           "Bernstein-style 'stochastic pop': the fast stochastic reaching overbought is strength, not exhaustion, when "
           "price is on the buying side of the session VWAP; short-horizon momentum traders enter there and the "
           "oscillator faders' stops sit just above, so follow the pop (mirror for oversold below VWAP).",
           {"n": [9, 14, 21], "th": [70, 80, 90]}, _stoch_pop, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-068", "Up-on-light, down-on-heavy volume asymmetry fade",
           "When price has risen over the window but the average down bar trades much more volume than the average up "
           "bar, the rise is drifting on thin buying while sellers distribute size on every dip; once the asymmetry "
           "becomes large the distributing side controls the price, so fade the rise (mirror for a fall).",
           {"win_min": [15, 30, 60], "ratio": [1.25, 1.5, 2.0]}, _volume_asymmetry, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
