"""Conveyor batch B-040 (agent, 2026-11-21). Mirror-of-open levels, Connors RSI, quarter-hour block fade, VWAP-TWAP gap, hourly floor pivots, first break after a quiet spell, Klinger hook, Laguerre RSI hook, two-horizon range-position mismatch and Ultimate Oscillator hook."""
from __future__ import annotations
import numpy as np
import pandas as pd
from b3.esteira import Family


# ----------------------------------------------------------------------------- shared helpers

def _gt(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    with np.errstate(invalid="ignore"):
        return np.where(np.isfinite(a) & np.isfinite(b), a > b, False)


def _lt(a, b):
    return _gt(b, a)


def _ge(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    with np.errstate(invalid="ignore"):
        return np.where(np.isfinite(a) & np.isfinite(b), a >= b, False)


def _le(a, b):
    return _ge(b, a)


def _out(long, short):
    long = np.nan_to_num(np.asarray(long, float), nan=0.0) > 0
    short = np.nan_to_num(np.asarray(short, float), nan=0.0) > 0
    both = long & short
    return (long & ~both).astype(int) - (short & ~both).astype(int)


def _typ_move(ctx, minutes):
    """Median |close - close `minutes` earlier| at the same minute over the 20 sessions before."""
    def f():
        nb = ctx.bars(minutes)
        return ctx.same_minute(np.abs(ctx.c - ctx.prev(ctx.c, nb)), "median")
    return ctx.cached(("b040_typmove", minutes), f)


def _ema(ctx, x, span, key):
    return ctx.cached(("b040_ema", key, span), lambda: ctx.ema(x, span))


def _rsi_of(ctx, x, n, key):
    """Session-reset Wilder-style RSI of any series x (smoothing span 2n-1)."""
    def f():
        d = np.nan_to_num(np.asarray(x, float) - ctx.prev(x), nan=0.0)
        span = max(2, 2 * n - 1)
        ag = ctx.ema(np.maximum(d, 0.0), span)
        al = ctx.ema(np.maximum(-d, 0.0), span)
        tot = ag + al
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(tot > 0, 100.0 * ag / np.where(tot > 0, tot, 1.0), 50.0) + 0 * tot
    return ctx.cached(("b040_rsi", key, n), f)


def _hook_up(ctx, x, th):
    """x rises back above th after being at or below it on the previous bar."""
    px = ctx.prev(x)
    return _gt(x, th) & _le(px, th)


def _hook_dn(ctx, x, th):
    px = ctx.prev(x)
    return _lt(x, th) & _ge(px, th)


def _breaks(ctx, win_min):
    def f():
        n = ctx.bars(win_min)
        hi = ctx.roll(ctx.h, n, "max", include_current=False)
        lo = ctx.roll(ctx.l, n, "min", include_current=False)
        return ctx.cross(_gt(ctx.c, hi)), ctx.cross(_lt(ctx.c, lo))
    return ctx.cached(("b040_breaks", win_min), f)


# ----------------------------------------------------------------------------- families

def _mirror_open_fade(ctx, p):
    sh = ctx.session_high(include_current=False)
    sl = ctx.session_low(include_current=False)
    o = ctx.day_open
    typ = _typ_move(ctx, 30)
    up_lvl = 2.0 * o - sl                       # the session low reflected above the open
    dn_lvl = 2.0 * o - sh                       # the session high reflected below the open
    deep_low = _gt(o - sl, p["k"] * typ)
    deep_high = _gt(sh - o, p["k"] * typ)
    ready = ctx.bar_in_day >= ctx.bars(15)
    short = deep_low & _ge(ctx.h, up_lvl) & _lt(ctx.c, up_lvl) & ready
    long = deep_high & _le(ctx.l, dn_lvl) & _gt(ctx.c, dn_lvl) & ready
    return _out(ctx.cross(long), ctx.cross(short))


def _connors_rsi_fade(ctx, p):
    def f():
        c = ctx.c
        r3 = _rsi_of(ctx, c, 3, "close")
        s = np.sign(np.nan_to_num(c - ctx.prev(c), nan=0.0))
        ss = pd.Series(s)
        ds = pd.Series(np.asarray(ctx.day))
        new_run = ss.ne(ss.shift()) | ds.ne(ds.shift())
        run = new_run.cumsum()
        cnt = pd.Series(np.ones(len(s))).groupby(run).cumsum().to_numpy()
        streak = s * cnt
        r2s = _rsi_of(ctx, streak, 2, "streak")
        ret = c - ctx.prev(c)
        m = 20
        cntr = np.zeros(len(c))
        for lag in range(1, m + 1):
            cntr += _gt(ret, ctx.prev(ret, lag))
        valid = np.isfinite(ctx.prev(ret, m)) & np.isfinite(ret)
        pr = np.where(valid, 100.0 * cntr / m, np.nan)
        return (r3 + r2s + pr) / 3.0
    crsi = ctx.cached("b040_crsi", f)
    lo = p["lo"]
    long = _lt(crsi, lo) & _ge(ctx.prev(crsi), lo)
    short = _gt(crsi, 100.0 - lo) & _le(ctx.prev(crsi), 100.0 - lo)
    return _out(long, short)


def _quarter_block_fade(ctx, p):
    b = int(p["block_min"])
    nb = ctx.bars(b)
    def f():
        ret = ctx.c - ctx.prev(ctx.c, nb)
        typ = ctx.same_minute(np.abs(ret), "median")
        bh = ctx.roll(ctx.h, nb, "max")
        bl = ctx.roll(ctx.l, nb, "min")
        rng = bh - bl
        loc = (ctx.c - bl) / np.where(rng > 0, rng, np.nan)
        return ret, typ, loc
    ret, typ, loc = ctx.cached(("b040_block", b), f)
    end = ((np.asarray(ctx.minute) + int(ctx.tf)) % b) == 0
    short = end & _gt(ret, p["k"] * typ) & _gt(loc, 0.75)
    long = end & _lt(ret, -p["k"] * typ) & _lt(loc, 0.25)
    return _out(long, short)


def _vwap_twap_gap_follow(ctx, p):
    def f():
        tp = (ctx.h + ctx.l + ctx.c) / 3.0
        twap = pd.Series(tp).groupby(np.asarray(ctx.day)).transform(lambda z: z.expanding().mean()).to_numpy()
        return ctx.vwap() - twap
    gap = ctx.cached("b040_vwap_twap", f)
    th = p["k"] * _typ_move(ctx, 30)
    ready = ctx.bar_in_day >= ctx.bars(30)
    pg = ctx.prev(gap)
    long = _gt(gap, th) & _le(pg, th) & ready
    short = _lt(gap, -th) & _ge(pg, -th) & ready
    return _out(long, short)


def _prev_hour_hlc(ctx):
    def f():
        hour = (np.asarray(ctx.minute) // 60).astype(np.int64)
        day = np.asarray(ctx.day).astype(np.int64)
        key = day * 100 + hour
        df = pd.DataFrame({"k": key, "d": day, "h": ctx.h, "l": ctx.l, "c": ctx.c})
        agg = df.groupby("k", sort=True).agg(d=("d", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"))
        prv = agg.shift(1)
        same = prv["d"].to_numpy() == agg["d"].to_numpy()
        H = np.where(same, prv["h"].to_numpy(float), np.nan)
        L = np.where(same, prv["l"].to_numpy(float), np.nan)
        C = np.where(same, prv["c"].to_numpy(float), np.nan)
        pos = agg.index.get_indexer(key)
        return H[pos], L[pos], C[pos]
    return ctx.cached("b040_prev_hour", f)


def _hourly_pivot_fade(ctx, p):
    H, L, C = _prev_hour_hlc(ctx)
    P = (H + L + C) / 3.0
    rng = H - L
    if int(p["level"]) == 1:
        R, S = 2.0 * P - L, 2.0 * P - H
    else:
        R, S = P + rng, P - rng
    band = p["band"] * rng
    short = _ge(ctx.h, R - band) & _lt(ctx.c, R - band)
    long = _le(ctx.l, S + band) & _gt(ctx.c, S + band)
    return _out(ctx.cross(long), ctx.cross(short))


def _quiet_spell_break_fade(ctx, p):
    up, dn = _breaks(ctx, p["win_min"])
    brk = up | dn
    idx = np.arange(ctx.n, dtype=float)
    last = pd.Series(np.where(brk, idx, np.nan)).groupby(np.asarray(ctx.day)).transform(
        lambda z: z.ffill().shift(1)).to_numpy()
    gap = np.where(np.isfinite(last), idx - last, np.asarray(ctx.bar_in_day, float))
    quiet = gap >= ctx.bars(p["quiet_min"])
    return _out(dn & quiet, up & quiet)


def _klinger_hook_fade(ctx, p):
    sc = int(p["scale"])
    fast, slow = 8 * sc, 13 * sc
    def f():
        tp = (ctx.h + ctx.l + ctx.c) / 3.0
        tr = np.sign(np.nan_to_num(tp - ctx.prev(tp), nan=0.0))
        vf = ctx.v * tr
        kvo = ctx.ema(vf, fast) - ctx.ema(vf, slow)
        norm = ctx.prev_sessions(np.abs(kvo), "mean")
        return kvo / np.where(norm > 0, norm, np.nan)
    z = ctx.cached(("b040_kvo", sc), f)
    k = p["k"]
    short = _hook_dn(ctx, z, k)
    long = _hook_up(ctx, z, -k)
    return _out(long, short)


def _laguerre_hook_fade(ctx, p):
    g = float(p["gamma"])
    def f():
        c = ctx.c
        day = np.asarray(ctx.day)
        n = len(c)
        out = np.full(n, np.nan)
        l0 = l1 = l2 = l3 = 0.0
        prev_day = None
        k_in = 0
        for i in range(n):
            x = c[i]
            if day[i] != prev_day:
                l0 = l1 = l2 = l3 = x
                prev_day = day[i]
                k_in = 0
            n0 = (1.0 - g) * x + g * l0
            n1 = -g * n0 + l0 + g * l1
            n2 = -g * n1 + l1 + g * l2
            n3 = -g * n2 + l2 + g * l3
            l0, l1, l2, l3 = n0, n1, n2, n3
            cu = max(l0 - l1, 0.0) + max(l1 - l2, 0.0) + max(l2 - l3, 0.0)
            cd = max(l1 - l0, 0.0) + max(l2 - l1, 0.0) + max(l3 - l2, 0.0)
            k_in += 1
            if k_in > 10 and cu + cd > 0:
                out[i] = cu / (cu + cd)
        return out
    lr = ctx.cached(("b040_lrsi", g), f)
    th = p["th"]
    long = _hook_up(ctx, lr, th)
    short = _hook_dn(ctx, lr, 1.0 - th)
    return _out(long, short)


def _range_position_mismatch(ctx, p):
    nb = ctx.bars(p["win_min"])
    sh = ctx.session_high(include_current=True)
    sl = ctx.session_low(include_current=True)
    srng = sh - sl
    pos_s = (ctx.c - sl) / np.where(srng > 0, srng, np.nan)
    wh = ctx.roll(ctx.h, nb, "max")
    wl = ctx.roll(ctx.l, nb, "min")
    wrng = wh - wl
    pos_w = (ctx.c - wl) / np.where(wrng > 0, wrng, np.nan)
    big = _gt(srng, _typ_move(ctx, 30))
    q = p["q"]
    short = _gt(pos_w, 0.85) & _lt(pos_s, q) & big
    long = _lt(pos_w, 0.15) & _gt(pos_s, 1.0 - q) & big
    return _out(ctx.cross(long), ctx.cross(short))


def _ultimate_hook_fade(ctx, p):
    sc = int(p["scale"])
    def f():
        pc = ctx.prev(ctx.c)
        lo = np.where(np.isfinite(pc), np.minimum(ctx.l, pc), np.nan)
        hi = np.where(np.isfinite(pc), np.maximum(ctx.h, pc), np.nan)
        bp = ctx.c - lo
        tr = hi - lo
        av = []
        for n in (7 * sc, 14 * sc, 28 * sc):
            sb = ctx.roll(bp, n, "sum")
            st = ctx.roll(tr, n, "sum")
            av.append(sb / np.where(st > 0, st, np.nan))
        return 100.0 * (4.0 * av[0] + 2.0 * av[1] + av[2]) / 7.0
    uo = ctx.cached(("b040_uo", sc), f)
    lo_th = p["lo"]
    long = _hook_up(ctx, uo, lo_th)
    short = _hook_dn(ctx, uo, 100.0 - lo_th)
    return _out(long, short)


SRC = "assistant reasoning"

FAMILIES = [
    Family("E-398", "Mirror-of-open swing fade",
           "Day traders anchor on the session open; once the day has dipped well below it, the price an equal distance above "
           "the open (the low mirrored through the open) is where those who bought the low book a symmetric profit and "
           "open-anchored sellers lean, so a bar that tags the mirror level and closes back below it is faded (and the "
           "reverse after a deep high).",
           {"k": [0.5, 1.0, 1.5]}, _mirror_open_fade,
           markets=("WIN",), source=SRC, author="agent"),
    Family("E-399", "Connors RSI extreme fade",
           "A composite of very short RSI, the RSI of the up/down close streak and the percentile of the last bar's return "
           "flags moments when one side has hit the tape several bars in a row with unusually large prints; liquidity "
           "providers absorb that one-sided flow and are paid when it pauses, so fade the moment the composite enters "
           "its extreme.",
           {"lo": [5, 10, 15]}, _connors_rsi_fade,
           markets=("WIN",), source=SRC, author="agent"),
    Family("E-400", "Quarter-hour block overreaction fade",
           "Execution algorithms slice parent orders on a fixed clock; a block of 10 to 20 minutes that moved much more "
           "than usual for its time and closed at its own extreme marks a slice that pushed through thin liquidity, and "
           "short-horizon returns tend to reverse at that horizon, so fade the block at its close.",
           {"block_min": [10, 15, 20], "k": [1.0, 1.5, 2.0]}, _quarter_block_fade,
           markets=("WIN",), source=SRC, author="agent"),
    Family("E-401", "VWAP-TWAP gap follow",
           "When the session's volume-weighted price moves clearly above its time-weighted price, contracts are changing "
           "hands mostly at the higher prices of the day, meaning buyers accepted them with size rather than the price "
           "merely drifting there; follow the side where the volume has been transacted.",
           {"k": [0.25, 0.5, 1.0]}, _vwap_twap_gap_follow,
           markets=("WIN",), source=SRC, author="agent"),
    Family("E-402", "Previous clock-hour floor-pivot fade",
           "Floor pivots built from the previous clock hour's high, low and close give R1/S1 (or R2/S2) levels that "
           "short-term desks quote and rest orders at; a bar that tags the level and closes back inside is met by those "
           "resting responsive orders, so fade it back toward the hour's pivot.",
           {"level": [1, 2], "band": [0.0, 0.1, 0.2]}, _hourly_pivot_fade,
           markets=("WIN",), source=SRC, author="agent"),
    Family("E-403", "First box break after a quiet spell fade",
           "When no close has escaped the rolling short-term box for a long time the tape is in balance and resting stops "
           "accumulate just outside it; the first break after such a spell is usually those stops being run by a small "
           "push, after which the balancing participants step back in, so fade it.",
           {"win_min": [10, 15, 30], "quiet_min": [30, 60, 90]}, _quiet_spell_break_fade,
           markets=("WIN",), source=SRC, author="agent"),
    Family("E-404", "Klinger volume-force hook fade",
           "The Klinger oscillator measures signed volume force; once it has reached an extreme for this market and then "
           "turns back inside the band, the aggressive volume that drove the move is spent and the counterparties who "
           "absorbed it now hold the better inventory, so fade the move at the hook.",
           {"scale": [1, 2, 3], "k": [1.5, 2.0, 3.0]}, _klinger_hook_fade,
           markets=("WIN",), source=SRC, author="agent"),
    Family("E-405", "Laguerre RSI hook fade",
           "Ehlers' Laguerre RSI reacts quickly with little lag; a hook back out of its oversold (overbought) zone shows "
           "the short burst of selling (buying) has stopped making progress, and the market makers who absorbed it lean "
           "the other way, so trade the hook against the burst.",
           {"gamma": [0.5, 0.6, 0.7], "th": [0.15, 0.2]}, _laguerre_hook_fade,
           markets=("WIN",), source=SRC, author="agent"),
    Family("E-406", "Two-horizon range-position mismatch fade",
           "A close at the top of the last 15 to 60 minutes while still in the lower part of a wide day's range is a "
           "short-covering bounce inside a weak session: the participants who sold higher still hold the inventory above "
           "and sell into it, so fade the local extreme toward the day's side (and the reverse on strong days).",
           {"win_min": [15, 30, 60], "q": [0.3, 0.4, 0.5]}, _range_position_mismatch,
           markets=("WIN",), source=SRC, author="agent"),
    Family("E-407", "Ultimate Oscillator hook fade",
           "Williams' Ultimate Oscillator blends buying pressure over three horizons, so an extreme reading means every "
           "horizon agrees the move was one-sided; when it turns back out of the extreme the multi-horizon pressure is "
           "fading and the absorbing side gets paid, so trade the hook against the move.",
           {"scale": [1, 2], "lo": [25, 30, 35]}, _ultimate_hook_fade,
           markets=("WIN",), source=SRC, author="agent"),
]
