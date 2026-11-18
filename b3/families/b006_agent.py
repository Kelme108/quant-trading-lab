"""Conveyor batch B-006 (agent, 2026-11-18). Mixed WIN themes: volume time, retail-setup stops, volume profile, clock marks, exact-tick levels, trend strength."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.esteira import Family


def _dryup_ignition(ctx, p):
    nb, k = ctx.bars(p["quiet_min"]), p["k"]
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    rv = ctx.v / np.where(med > 0, med, np.nan)
    quiet = ctx.roll(rv, nb, "mean", include_current=False) < 0.7
    ign = quiet & (rv >= k)
    long = ign & (ctx.c > ctx.o)
    short = ign & (ctx.c < ctx.o)
    return long.astype(int) - short.astype(int)


def _setup91_fail(ctx, p):
    span, exp = int(p["ema"]), ctx.bars(p["expire_min"])
    e = ctx.ema(ctx.c, span)
    e1, e2 = ctx.prev(e, 1), ctx.prev(e, 2)
    tu = ((e > e1) & (e1 <= e2)).tolist()
    td = ((e < e1) & (e1 >= e2)).tolist()
    h, l, c, day = ctx.h.tolist(), ctx.l.tolist(), ctx.c.tolist(), ctx.day.tolist()
    buy = np.zeros(ctx.n, dtype=bool)
    sell = np.zeros(ctx.n, dtype=bool)
    cur, L, S = None, None, None
    for i in range(ctx.n):
        if day[i] != cur:
            cur, L, S = day[i], None, None
        if L is not None:                       # long 9.1 setup: [turn bar, its high, its low, triggered]
            if i - L[0] > exp:
                L = None
            elif not L[3]:
                if c[i] > L[1]:
                    L[3] = True
            elif c[i] < L[2]:
                sell[i] = True
                L = None
        if S is not None:                       # short 9.1 setup: [turn bar, its low, its high, triggered]
            if i - S[0] > exp:
                S = None
            elif not S[3]:
                if c[i] < S[1]:
                    S[3] = True
            elif c[i] > S[2]:
                buy[i] = True
                S = None
        if tu[i]:
            L = [i, h[i], l[i], False]
        if td[i]:
            S = [i, l[i], h[i], False]
    return buy.astype(int) - sell.astype(int)


def _outside_fade(ctx, p):
    k, q = p["k"], p["q"]
    rng = ctx.h - ctx.l
    avg = ctx.roll(rng, 20, "mean", include_current=False)
    outside = (ctx.h > ctx.prev(ctx.h, 1)) & (ctx.l < ctx.prev(ctx.l, 1)) & (rng >= k * avg) & (rng > 0)
    clv = (ctx.c - ctx.l) / np.where(rng > 0, rng, np.nan)
    short = outside & (clv >= 1 - q)
    long = outside & (clv <= q)
    return long.astype(int) - short.astype(int)


def _poc_shift(ctx, p):
    m, jump = float(p["m"]), int(p["jump"])
    rng = ctx.h - ctx.l
    typ = ctx.cached("rng_prev_mean", lambda: ctx.prev_sessions(rng, "mean")).tolist()
    tp = ((ctx.h + ctx.l + ctx.c) / 3.0).tolist()
    v, day, bid = ctx.v.tolist(), ctx.day.tolist(), ctx.bar_in_day.tolist()
    start = ctx.bars(30)
    out = np.zeros(ctx.n, dtype=int)
    cur, prof, poc, best = None, {}, None, 0.0
    for i in range(ctx.n):
        if day[i] != cur:
            cur, prof, poc, best = day[i], {}, None, 0.0
        w = m * typ[i]
        if not (w > 0):
            continue
        b = int(math.floor(tp[i] / w))
        vol = prof.get(b, 0.0) + v[i]
        prof[b] = vol
        if poc is None:
            poc, best = b, vol
            continue
        if vol > best:
            old = poc
            poc, best = b, vol
            if b != old and bid[i] >= start:
                if b - old >= jump:
                    out[i] = 1
                elif old - b >= jump:
                    out[i] = -1
    return out


def _hourly_or_break(ctx, p):
    om = int(p["or_min"])
    mh = ctx.minute % 60
    key = ctx.day.astype(np.int64) * 100 + ctx.minute // 60
    first = mh < om
    df = pd.DataFrame({"k": key, "h": np.where(first, ctx.h, np.nan), "l": np.where(first, ctx.l, np.nan)})
    orh = df.groupby("k")["h"].transform("max").to_numpy()
    orl = df.groupby("k")["l"].transform("min").to_numpy()
    done = (~first) & np.isfinite(orh) & np.isfinite(orl)
    up = done & (ctx.c > orh)
    dn = done & (ctx.c < orl)
    cu = pd.Series(up.astype(int)).groupby(key).cumsum().to_numpy()
    cd = pd.Series(dn.astype(int)).groupby(key).cumsum().to_numpy()
    return (up & (cu == 1)).astype(int) - (dn & (cd == 1)).astype(int)


def _iceberg_break(ctx, p):
    nb, t = ctx.bars(p["lookback_min"]), int(p["touches"])
    mx = ctx.roll(ctx.h, nb, "max", include_current=False)
    mn = ctx.roll(ctx.l, nb, "min", include_current=False)
    cu = np.zeros(ctx.n)
    cd = np.zeros(ctx.n)
    for j in range(1, nb + 1):
        cu += ctx.prev(ctx.h, j) == mx
        cd += ctx.prev(ctx.l, j) == mn
    up = (cu >= t) & (ctx.c > mx)
    dn = (cd >= t) & (ctx.c < mn)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _volume_clock(ctx, p):
    nbe, k = ctx.bars(p["bucket_min"]), p["k"]
    vbar = ctx.cached("v_prev_mean", lambda: ctx.prev_sessions(ctx.v, "mean"))
    size = vbar * nbe
    cumv = pd.Series(ctx.v).groupby(ctx.day).cumsum().to_numpy()
    b = np.floor(cumv / np.where(size > 0, size, np.nan))
    change = b > ctx.prev(b, 1)
    pe = np.where(change, ctx.c, np.nan)
    last = pd.Series(pe).groupby(ctx.day).ffill().to_numpy()
    last_prev = ctx.prev(last, 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        ret = np.where(change, np.log(ctx.c / last_prev), np.nan)
    typ = ctx.prev_sessions(np.abs(ret), "mean")
    big = change & (np.abs(ret) > k * typ)
    return (big & (ret > 0)).astype(int) - (big & (ret < 0)).astype(int)


def _clock_mark_fade(ctx, p):
    every, k = int(p["every_min"]), p["k"]
    rng = ctx.h - ctx.l
    med = ctx.cached("rng_med", lambda: ctx.same_minute(rng, "median"))
    body = ctx.c - ctx.o
    mark = ((ctx.minute % every) == 0) & (ctx.bar_in_day > 0)
    big = mark & (rng >= k * med) & (np.abs(body) >= 0.5 * rng) & (rng > 0)
    return (big & (body < 0)).astype(int) - (big & (body > 0)).astype(int)


def _decel_fade(ctx, p):
    N, k = int(p["run"]), p["k"]
    body = ctx.c - ctx.o
    typ = ctx.roll(np.abs(body), 20, "mean", include_current=False)
    up = np.ones(ctx.n, dtype=bool)
    dn = np.ones(ctx.n, dtype=bool)
    for j in range(1, N + 1):
        bj = ctx.prev(body, j)
        up &= bj > 0
        dn &= bj < 0
    for j in range(1, N):
        bj, bj1 = ctx.prev(body, j), ctx.prev(body, j + 1)
        cj, cj1 = ctx.prev(ctx.c, j), ctx.prev(ctx.c, j + 1)
        up &= (bj < bj1) & (cj > cj1)
        dn &= (bj > bj1) & (cj < cj1)
    first = np.abs(ctx.prev(body, N))
    big = first >= k * ctx.prev(typ, N - 1) if N > 1 else first >= k * typ
    c1 = ctx.prev(ctx.c, 1)
    short = up & big & (body < 0) & (ctx.c < c1)
    long = dn & big & (body > 0) & (ctx.c > c1)
    return long.astype(int) - short.astype(int)


def _adx_start(ctx, p):
    n, th = int(p["n"]), p["th"]
    span = 2 * n - 1
    ph, pl, pc = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1), ctx.prev(ctx.c, 1)
    upm, dnm = ctx.h - ph, pl - ctx.l
    pdm = np.where((upm > dnm) & (upm > 0), upm, 0.0)
    mdm = np.where((dnm > upm) & (dnm > 0), dnm, 0.0)
    tr = np.nanmax(np.vstack([ctx.h - ctx.l, np.abs(ctx.h - pc), np.abs(ctx.l - pc)]), axis=0)
    atr = ctx.ema(tr, span)
    with np.errstate(invalid="ignore", divide="ignore"):
        pdi = ctx.ema(pdm, span) / atr
        mdi = ctx.ema(mdm, span) / atr
        dx = 100.0 * np.abs(pdi - mdi) / (pdi + mdi)
    dx = np.where(np.isfinite(dx), dx, np.nan)
    adx = ctx.ema(dx, span)
    on = ctx.cross(adx > th)
    return (on & (pdi > mdi)).astype(int) - (on & (pdi < mdi)).astype(int)


FAMILIES = [
    Family("E-049", "Volume ignition after a dry-up",
           "After a stretch where volume runs well below its normal level for the time of day, nobody informed is "
           "trading; the first bar with volume several times normal is new information arriving (not churn), and "
           "the passive side quoting the quiet market is run over, so follow the ignition bar's direction.",
           {"quiet_min": [10, 20, 30], "k": [1.5, 2.0, 3.0]}, _dryup_ignition,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-050", "Setup 9.1 failure stop run",
           "Brazilian retail day traders widely run Larry Williams' setup 9.1 on WIN: buy above the high of the bar "
           "that turns the 9 EMA up, stop below that bar's low. When the setup triggers and price then closes back "
           "below the turn bar's low, those clustered retail stops are hit together and the trapped longs' exits push "
           "the move on; follow the failure (mirror for the sell setup).",
           {"ema": [7, 9, 12], "expire_min": [20, 40, 60]}, _setup91_fail, markets=("WIN",),
           source="Setup 9.1, 9.2 e 9.3 de Larry Williams (Awake Trader) "
                  "https://www.awaketrader.com/pt/educacao/setup-9-1-9-2-9-3-larry-williams", author="agent"),
    Family("E-051", "Wide outside-bar fade",
           "A wide bar that takes out both the previous bar's high and low has swept the stops on both sides; when it "
           "closes at one extreme, that last sweep was forced stop and chase orders rather than new interest, and with "
           "both stop pools spent liquidity providers lean against it; fade the close side.",
           {"k": [1.0, 1.5, 2.0], "q": [0.2, 0.3, 0.4]}, _outside_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-052", "Developing POC migration",
           "The developing point of control (the price bin with the most volume today) is where the session has "
           "accepted value; when it jumps to a higher bin, buyers have moved the bulk of trade up and responsive "
           "sellers failed to hold value lower, so initiative flow continues that way; follow the shift.",
           {"m": [1.0, 2.0, 3.0], "jump": [1, 2]}, _poc_shift, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-053", "Hourly opening-range break",
           "Execution desks and algos restart schedules at each clock hour, and the first minutes of the hour set a "
           "local range many short-term traders mark; the first close beyond it within the hour shows which side the "
           "new hour's flow is on, so follow the first break of each hour.",
           {"or_min": [5, 10, 15]}, _hourly_or_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-054", "Exact-tick repeated level break",
           "Several recent bars topping at exactly the same tick show a refreshed resting order (an iceberg) defending "
           "it; once a bar closes beyond it the absorber is filled or gone, the stops behind the level fire and the "
           "traders who leaned on it cover; follow the break.",
           {"lookback_min": [15, 30, 60], "touches": [2, 3]}, _iceberg_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-055", "Volume-clock bucket momentum",
           "Measured in volume time (equal-volume buckets) price moves track information flow rather than the clock; "
           "a bucket whose return is large next to typical buckets carries a parent order still being worked, so the "
           "next bucket tends to move the same way; follow the large bucket's sign.",
           {"bucket_min": [5, 10, 20], "k": [1.0, 1.5, 2.0]}, _volume_clock, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-056", "Clock-mark bar impulse fade",
           "At the :00/:15/:30 marks scheduled orders (time-sliced algos, timed stops, alerts) hit the book together, "
           "so a mark bar that is large for its minute and closes decisively is a mechanical burst, not new "
           "information; once it is done liquidity returns and price reverts; fade the mark bar.",
           {"every_min": [15, 30, 60], "k": [1.0, 1.5, 2.0]}, _clock_mark_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-057", "Decelerating run reversal",
           "A run of same-direction bars whose bodies shrink bar after bar shows each push finding fewer aggressive "
           "takers; when the next bar closes against the run, the late chasers of the weakest push are under water "
           "and the momentum side has stopped paying up; fade the run.",
           {"run": [2, 3, 4], "k": [0.5, 1.0, 1.5]}, _decel_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-058", "ADX trend-start follow",
           "Wilder's ADX is on most retail platforms and a cross above its threshold is a common 'trend has started' "
           "trigger; when it crosses, directional movement has become one-sided and DI-based trend followers join in "
           "the leading DI's direction, extending the move; follow the cross.",
           {"n": [7, 10, 14], "th": [20, 25, 30]}, _adx_start, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
