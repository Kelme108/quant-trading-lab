"""Conveyor batch B-129 (agent, 2026-11-24). Indicator/structure ideas not yet screened: Heikin-Ashi flip, fractal swing
break, Fibonacci leg retracement, Hull MA turn, clock-relative quiet box, TSI extreme cross, Aroon oscillator,
CCI thrust, MFI re-entry, wedge compression break."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _sig(long, short):
    return np.asarray(long, bool).astype(int) - np.asarray(short, bool).astype(int)


def _ffill_day(ctx, x):
    return pd.Series(x).groupby(ctx.day).ffill().to_numpy()


def _bars_since(ctx, x, n, kind):
    """Bars since the max/min of x over the last n+1 bars of the session (0 = current); NaN early in the session."""
    w = n + 1
    pad = np.concatenate([np.full(w - 1, x[0]), x])
    win = np.lib.stride_tricks.sliding_window_view(pad, w)
    idx = win.argmax(axis=1) if kind == "max" else win.argmin(axis=1)
    out = (w - 1 - idx).astype(float)
    out[ctx.bar_in_day < w - 1] = np.nan
    return out


# ---------------------------------------------------------------- E-1288 Heikin-Ashi flip after a run
def _ha_flip(ctx, p):
    k = int(p["run_bars"])

    def build():
        hac = (ctx.o + ctx.h + ctx.l + ctx.c) / 4.0
        hao = np.empty(ctx.n)
        for i in range(ctx.n):
            if i == 0 or ctx.day[i] != ctx.day[i - 1]:
                hao[i] = (ctx.o[i] + ctx.c[i]) / 2.0
            else:
                hao[i] = (hao[i - 1] + hac[i - 1]) / 2.0
        return hac, hao
    hac, hao = ctx.cached("ha", build)
    green = (hac > hao).astype(float)
    red = (hac < hao).astype(float)
    was_red = ctx.roll(red, k, "sum", include_current=False) == k
    was_green = ctx.roll(green, k, "sum", include_current=False) == k
    return _sig(was_red & (green == 1), was_green & (red == 1))


# ---------------------------------------------------------------- E-1289 fractal swing break
def _fractal_break(ctx, p):
    k = int(p["side_bars"])
    w = 2 * k + 1
    hmax = ctx.roll(ctx.h, w, "max")
    lmin = ctx.roll(ctx.l, w, "min")
    hk, lk = ctx.prev(ctx.h, k), ctx.prev(ctx.l, k)
    sh = _ffill_day(ctx, np.where(hk >= hmax, hk, np.nan))
    sl = _ffill_day(ctx, np.where(lk <= lmin, lk, np.nan))
    return _sig(ctx.cross(ctx.c > sh), ctx.cross(ctx.c < sl))


# ---------------------------------------------------------------- E-1290 Fibonacci retracement resume
def _fib_resume(ctx, p):
    f = p["retrace"]
    n = ctx.bars(p["leg_min"])
    hi = ctx.roll(ctx.h, n, "max")
    lo = ctx.roll(ctx.l, n, "min")
    avg = ctx.roll(ctx.h - ctx.l, n, "mean")
    ah = ctx.cached(("ah", n), lambda: _bars_since(ctx, ctx.h, n, "max"))
    al = ctx.cached(("al", n), lambda: _bars_since(ctx, ctx.l, n, "min"))
    leg = hi - lo
    big = leg >= 6.0 * avg
    up_lvl = hi - f * leg
    dn_lvl = lo + f * leg
    touched_up = ctx.roll(ctx.l, 3, "min") <= up_lvl
    touched_dn = ctx.roll(ctx.h, 3, "max") >= dn_lvl
    long = big & (ah < al) & touched_up & (ctx.c > up_lvl) & (ctx.prev(ctx.c, 1) <= up_lvl) & (ctx.c < hi)
    short = big & (al < ah) & touched_dn & (ctx.c < dn_lvl) & (ctx.prev(ctx.c, 1) >= dn_lvl) & (ctx.c > lo)
    return _sig(long, short)


# ---------------------------------------------------------------- E-1291 Hull MA turn
def _wma(x, n):
    w = np.arange(1, n + 1, dtype=float)
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        out[n - 1:] = np.convolve(x, w[::-1], mode="valid") / w.sum()
    return out


def _hma_turn(ctx, p):
    n = int(p["length"])
    half, root = max(2, n // 2), max(2, int(round(np.sqrt(n))))

    def build():
        raw = 2.0 * _wma(ctx.c, half) - _wma(ctx.c, n)
        h = _wma(np.nan_to_num(raw, nan=0.0), root)
        h[ctx.bar_in_day < n + root + 1] = np.nan
        return h
    hm = ctx.cached(("hma", n), build)
    d1 = hm - np.concatenate([[np.nan], hm[:-1]])
    d2 = np.concatenate([[np.nan], d1[:-1]])
    long = (d1 > 0) & (d2 <= 0)
    short = (d1 < 0) & (d2 >= 0)
    return _sig(long, short)


# ---------------------------------------------------------------- E-1292 clock-relative quiet box break
def _quiet_box(ctx, p):
    q, m = p["quiet_ratio"], int(p["box_bars"])
    rng = ctx.h - ctx.l
    typ = ctx.cached("rng_med", lambda: ctx.same_minute(rng, "median"))
    quiet = (rng < q * typ).astype(float)
    all_quiet = ctx.roll(quiet, m, "sum", include_current=False) == m
    bh = ctx.roll(ctx.h, m, "max", include_current=False)
    bl = ctx.roll(ctx.l, m, "min", include_current=False)
    return _sig(ctx.cross(all_quiet & (ctx.c > bh)), ctx.cross(all_quiet & (ctx.c < bl)))


# ---------------------------------------------------------------- E-1293 TSI cross from the extreme side
def _tsi_cross(ctx, p):
    r, th = int(p["slow"]), p["zone"]
    s = max(2, r // 2)
    mom = ctx.c - ctx.prev(ctx.c, 1)
    num = ctx.cached(("tsin", r, s), lambda: ctx.ema(ctx.ema(np.nan_to_num(mom), r), s))
    den = ctx.cached(("tsid", r, s), lambda: ctx.ema(ctx.ema(np.abs(np.nan_to_num(mom)), r), s))
    with np.errstate(divide="ignore", invalid="ignore"):
        tsi = 100.0 * num / den
    sg = ctx.ema(np.nan_to_num(tsi), 7)
    long = ctx.cross(tsi > sg) & (tsi < -th)
    short = ctx.cross(tsi < sg) & (tsi > th)
    return _sig(long, short)


# ---------------------------------------------------------------- E-1294 Aroon oscillator cross
def _aroon(ctx, p):
    n, th = int(p["length"]), p["level"]
    bh = ctx.cached(("ah", n), lambda: _bars_since(ctx, ctx.h, n, "max"))
    bl = ctx.cached(("al", n), lambda: _bars_since(ctx, ctx.l, n, "min"))
    osc = 100.0 * ((n - bh) - (n - bl)) / n
    return _sig(ctx.cross(osc >= th), ctx.cross(osc <= -th))


# ---------------------------------------------------------------- E-1295 CCI thrust
def _cci_series(ctx, n):
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    pad = np.concatenate([np.full(n - 1, tp[0]), tp])
    win = np.lib.stride_tricks.sliding_window_view(pad, n)
    out = np.empty(ctx.n)
    step = 100000
    for a in range(0, ctx.n, step):
        w = win[a:a + step]
        mu = w.mean(axis=1)
        md = np.abs(w - mu[:, None]).mean(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            out[a:a + step] = (tp[a:a + step] - mu) / (0.015 * md)
    out[ctx.bar_in_day < n - 1] = np.nan
    return out


def _cci_thrust(ctx, p):
    n, th = int(p["length"]), p["level"]
    cci = ctx.cached(("cci", n), lambda: _cci_series(ctx, n))
    return _sig(ctx.cross(cci > th), ctx.cross(cci < -th))


# ---------------------------------------------------------------- E-1296 MFI re-entry fade
def _mfi_reentry(ctx, p):
    n, lo = int(p["length"]), p["level"]
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    up = tp > ctx.prev(tp, 1)
    flow = tp * ctx.v
    pos = ctx.roll(np.where(up, flow, 0.0), n, "sum")
    tot = ctx.roll(flow, n, "sum")
    with np.errstate(divide="ignore", invalid="ignore"):
        mfi = 100.0 * pos / tot
    pm = ctx.prev(mfi, 1)
    long = (pm < lo) & (mfi >= lo)
    short = (pm > 100 - lo) & (mfi <= 100 - lo)
    return _sig(long, short)


# ---------------------------------------------------------------- E-1297 wedge compression break
def _wedge_break(ctx, p):
    half = max(2, ctx.bars(p["window_min"]) // 2)
    ratio = p["ratio"]
    hi2 = ctx.roll(ctx.h, half, "max", include_current=False)
    lo2 = ctx.roll(ctx.l, half, "min", include_current=False)
    r2 = hi2 - lo2
    r1 = ctx.prev(r2, half)
    squeezed = (r1 > 0) & (r2 < ratio * r1)
    return _sig(ctx.cross(squeezed & (ctx.c > hi2)), ctx.cross(squeezed & (ctx.c < lo2)))


FAMILIES = [
    Family("E-1288", "Heikin-Ashi colour flip after a run",
           "A run of same-coloured smoothed candles ends when one side's pressure is exhausted; the first opposite "
           "Heikin-Ashi candle shows the other side taking over, so follow the flip.",
           {"run_bars": [3, 5, 8]}, _ha_flip, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1289", "Fractal swing break",
           "Confirmed swing highs/lows hold resting stops; a close through the latest confirmed swing triggers them "
           "and the move extends.",
           {"side_bars": [2, 3, 5]}, _fractal_break, markets=("WIN",), source="assistant reasoning (Williams fractals)",
           author="agent"),
    Family("E-1290", "Fibonacci leg retracement resume",
           "After a large leg, a pullback to a common retracement level that holds attracts dip buyers (or rally "
           "sellers) who watch that level; follow the resumption.",
           {"retrace": [0.382, 0.5, 0.618], "leg_min": [30, 60, 90]}, _fib_resume, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1291", "Hull moving average turn",
           "The Hull MA reacts with little lag; its slope changing sign marks the start of a new short swing that "
           "slower traders only join later.",
           {"length": [16, 25, 36]}, _hma_turn, markets=("WIN",), source="assistant reasoning (Hull MA)", author="agent"),
    Family("E-1292", "Clock-relative quiet box break",
           "Bars much smaller than usual for the time of day mean resting liquidity is being left alone; the first "
           "close beyond that box releases the pent-up direction.",
           {"quiet_ratio": [0.5, 0.7, 0.9], "box_bars": [3, 5]}, _quiet_box, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1293", "TSI signal cross from the extreme side",
           "The double-smoothed true strength index crossing its signal line while far on one side of zero marks "
           "the end of a push; trade the turn back toward the centre.",
           {"slow": [10, 15, 25], "zone": [0, 10, 20]}, _tsi_cross, markets=("WIN",), source="assistant reasoning (TSI)",
           author="agent"),
    Family("E-1294", "Aroon oscillator cross",
           "When the newest highs are much more recent than the newest lows, buyers are steadily making progress; "
           "the oscillator crossing a high level flags a young trend.",
           {"length": [14, 25, 50], "level": [50, 70]}, _aroon, markets=("WIN",), source="assistant reasoning (Aroon)",
           author="agent"),
    Family("E-1295", "CCI thrust break",
           "A commodity channel index beyond +/-100 means price is far above its typical-price mean in units of "
           "usual deviation: a thrust that tends to carry momentum traders along.",
           {"length": [14, 20, 30], "level": [100, 150]}, _cci_thrust, markets=("WIN",), source="assistant reasoning (CCI)",
           author="agent"),
    Family("E-1296", "Money-flow index re-entry fade",
           "Volume-weighted buying or selling pressure at an extreme is exhausted when the MFI comes back inside; "
           "the late pushers are trapped and price reverts.",
           {"length": [10, 14, 20], "level": [10, 20, 30]}, _mfi_reentry, markets=("WIN",),
           source="assistant reasoning (Money Flow Index)", author="agent"),
    Family("E-1297", "Wedge compression break",
           "When the recent half of a window trades in a much smaller range than the earlier half, the market is "
           "coiling; a close outside the tight range starts the next swing.",
           {"window_min": [20, 40, 60], "ratio": [0.5, 0.7]}, _wedge_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
