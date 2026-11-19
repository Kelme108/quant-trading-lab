"""Conveyor batch B-036 (agent, 2026-11-19). Hour-candle context, momentum peaks, twin-market breaks, VWAP departures, cumulative delta and joint-calm regimes."""
from __future__ import annotations
import numpy as np
import pandas as pd
from b3.esteira import Family


# ----------------------------------------------------------------------------- shared helpers

def _breaks(ctx, win_min):
    def f():
        n = ctx.bars(win_min)
        hi = ctx.roll(ctx.h, n, "max", include_current=False)
        lo = ctx.roll(ctx.l, n, "min", include_current=False)
        return ctx.cross(ctx.c > hi), ctx.cross(ctx.c < lo)
    return ctx.cached(("b036_breaks", win_min), f)


def _hour_key(ctx):
    return ctx.cached("b036_hkey", lambda: ctx.day.astype(np.int64) * 100 + (ctx.minute // 60).astype(np.int64))


def _hour_open(ctx):
    return ctx.cached("b036_hopen", lambda: pd.Series(ctx.o).groupby(_hour_key(ctx)).transform("first").to_numpy(float))


def _typ_move(ctx, minutes):
    def f():
        nb = ctx.bars(minutes)
        return ctx.same_minute(np.abs(ctx.c - ctx.prev(ctx.c, nb)), "median")
    return ctx.cached(("b036_typmove", minutes), f)


def _out(long, short):
    long = np.asarray(long, bool)
    short = np.asarray(short, bool)
    return long.astype(int) - short.astype(int)


# ----------------------------------------------------------------------------- families

def _counter_hour_candle_fade(ctx, p):
    up, dn = _breaks(ctx, p["win_min"])
    ho = _hour_open(ctx)
    typ = _typ_move(ctx, 15)
    short = up & (ctx.c < ho - p["k"] * typ)
    long = dn & (ctx.c > ho + p["k"] * typ)
    return _out(long, short)


def _strong_hour_pullback(ctx, p):
    ho = _hour_open(ctx)
    hk = _hour_key(ctx).astype(float)
    mv = ctx.c - ho
    typ = ctx.same_minute(np.abs(mv), "median")
    same_hour = (ctx.prev(hk) == hk) & (ctx.prev(hk, 2) == hk)
    pc, ppc = ctx.prev(ctx.c), ctx.prev(ctx.c, 2)
    long = same_hour & (mv > p["k"] * typ) & (pc < ppc) & (ctx.c > ctx.prev(ctx.h))
    short = same_hour & (mv < -p["k"] * typ) & (pc > ppc) & (ctx.c < ctx.prev(ctx.l))
    return _out(ctx.cross(long), ctx.cross(short))


def _momentum_peak_turn(ctx, p):
    nb = ctx.bars(p["win_min"])
    m = ctx.c - ctx.prev(ctx.c, nb)
    typ = ctx.same_minute(np.abs(m), "median")
    z = m / np.where(typ > 0, typ, np.nan)
    w = ctx.bars(30)
    zmax = ctx.roll(z, w, "max")
    zmin = ctx.roll(z, w, "min")
    zp = ctx.prev(z)
    peak = (zp >= p["k"]) & (zp >= ctx.prev(zmax) - 1e-12)
    trough = (zp <= -p["k"]) & (zp <= ctx.prev(zmin) + 1e-12)
    short = peak & (ctx.c < ctx.prev(ctx.l))
    long = trough & (ctx.c > ctx.prev(ctx.h))
    return _out(ctx.cross(long), ctx.cross(short))


def _twin_break_fade(ctx, p):
    up, dn = _breaks(ctx, p["win_min"])
    n = ctx.bars(p["win_min"])
    w = ctx.other_close()
    wdo_up = (w > ctx.roll(w, n, "max", include_current=False)).astype(float)
    wdo_dn = (w < ctx.roll(w, n, "min", include_current=False)).astype(float)
    m = ctx.bars(p["within_min"])
    rec_up = ctx.roll(wdo_up, m, "max") > 0
    rec_dn = ctx.roll(wdo_dn, m, "max") > 0
    short = up & rec_up
    long = dn & rec_dn
    return _out(long, short)


def _fast_vwap_departure_snapback(ctx, p):
    nb = ctx.bars(p["win_min"])
    d = ctx.c - ctx.vwap()
    typ = _typ_move(ctx, p["win_min"])
    near_before = np.abs(ctx.prev(d, nb)) < 0.5 * typ
    s_up = ((d > p["k"] * typ) & near_before).astype(float)
    s_dn = ((d < -p["k"] * typ) & near_before).astype(float)
    short = (ctx.prev(s_up) == 1) & (ctx.c < ctx.prev(ctx.l))
    long = (ctx.prev(s_dn) == 1) & (ctx.c > ctx.prev(ctx.h))
    return _out(ctx.cross(long), ctx.cross(short))


def _counter_delta_break_fade(ctx, p):
    up, dn = _breaks(ctx, p["win_min"])
    def f():
        sv = np.sign(ctx.c - ctx.o) * ctx.v
        cd = pd.Series(sv).groupby(ctx.day).cumsum().to_numpy(float)
        cv = pd.Series(ctx.v).groupby(ctx.day).cumsum().to_numpy(float)
        return cd / np.where(cv > 0, cv, np.nan)
    r = ctx.cached("b036_cumdelta", f)
    started = ctx.bar_in_day >= ctx.bars(30)
    short = up & started & (r < -p["th"])
    long = dn & started & (r > p["th"])
    return _out(long, short)


def _trend_day_extreme_after_pullback(ctx, p):
    dm = ctx.c - ctx.day_open
    typ_dm = ctx.same_minute(np.abs(dm), "median")
    typ15 = _typ_move(ctx, 15)
    w = ctx.bars(30)
    shh = ctx.session_high(False)
    sll = ctx.session_low(False)
    depth_up = shh - ctx.roll(ctx.l, w, "min")
    depth_dn = ctx.roll(ctx.h, w, "max") - sll
    long = (dm > p["k"] * typ_dm) & (ctx.c > shh) & (depth_up >= p["m"] * typ15)
    short = (dm < -p["k"] * typ_dm) & (ctx.c < sll) & (depth_dn >= p["m"] * typ15)
    return _out(ctx.cross(long), ctx.cross(short))


def _symmetric_volume_day_fade(ctx, p):
    up, dn = _breaks(ctx, p["win_min"])
    sh = ctx.session_high(True)
    sl = ctx.session_low(True)
    rng = sh - sl
    skew = (ctx.vwap() - (sh + sl) / 2.0) / np.where(rng > 0, rng, np.nan)
    ok = (np.abs(skew) < p["th"]) & (ctx.bar_in_day >= ctx.bars(30))
    return _out(dn & ok, up & ok)


def _inside_hour_regime_fade(ctx, p):
    up, dn = _breaks(ctx, p["win_min"])
    def f():
        key = _hour_key(ctx)
        g = pd.DataFrame({"k": key, "h": ctx.h, "l": ctx.l}).groupby("k").agg(H=("h", "max"), L=("l", "min"))
        keys = g.index.to_numpy()
        kd = keys // 100
        H = g["H"].to_numpy(float)
        L = g["L"].to_numpy(float)
        H1 = np.full(len(keys), np.nan); L1 = H1.copy(); H2 = H1.copy(); L2 = H1.copy()
        s1 = np.r_[False, kd[1:] == kd[:-1]]
        s2 = np.r_[False, False, kd[2:] == kd[:-2]]
        H1[1:] = H[:-1]; L1[1:] = L[:-1]
        H2[2:] = H[:-2]; L2[2:] = L[:-2]
        inside = s1 & s2 & (H1 <= H2) & (L1 >= L2)
        idx = np.searchsorted(keys, key)
        return inside[idx]
    ok = ctx.cached("b036_inside_hour", f)
    return _out(dn & ok, up & ok)


def _joint_calm_fade(ctx, p):
    up, dn = _breaks(ctx, p["win_min"])
    def f():
        n = ctx.bars(60)
        w = ctx.other_close()
        rw = ctx.roll(ctx.c, n, "max") - ctx.roll(ctx.c, n, "min")
        rd = ctx.roll(w, n, "max") - ctx.roll(w, n, "min")
        tw = ctx.same_minute(rw, "median")
        td = ctx.same_minute(rd, "median")
        return rw / np.where(tw > 0, tw, np.nan), rd / np.where(td > 0, td, np.nan)
    a, b = ctx.cached("b036_joint_calm", f)
    ok = (a < p["q"]) & (b < p["q"])
    return _out(dn & ok, up & ok)


FAMILIES = [
    Family("E-358", "Counter-hour-candle micro-break fade",
           "A short-term up-break printed while the current clock-hour candle is still clearly red (price well below the hour's open) is a small push against what hourly-chart desks see as a selling hour; the hour's sellers still hold the initiative and lean on it, so the breakout buyers get no follow-through: fade it (mirror for down-breaks in a green hour).",
           {"win_min": [10, 15, 30], "k": [0.25, 0.5, 1.0]}, _counter_hour_candle_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-359", "Strong-hour pullback resumption",
           "When the current clock hour has already moved far more than usual for this point of the hour, a parent order is being worked inside the hour; a one-bar counter close is profit-taking by short-term traders, and the next close beyond the previous bar's extreme shows the hour's initiator resuming, so follow it (mirror).",
           {"k": [1.5, 2.0, 3.0]}, _strong_hour_pullback,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-360", "Momentum-peak turn fade",
           "When the trailing move, scaled by its usual size at this minute, peaks at the highest value of the last half hour and the next bar closes below the previous low, the urgency of the buyers has just topped out; the chasers who bought at peak speed are the first offside and their exits revert the move (mirror for a momentum trough).",
           {"win_min": [10, 15, 30], "k": [1.5, 2.0, 3.0]}, _momentum_peak_turn,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-361", "Twin-market same-direction break fade",
           "Foreign flow buys the index and sells the dollar together, so a genuine WIN up-break comes with the dollar falling; when WIN breaks its recent high at the same time WDO is also breaking its own recent high, the two breaks contradict the macro flow and are local stop runs in both books that dealers lean back; fade the WIN break (mirror).",
           {"win_min": [10, 15, 30], "within_min": [5, 10, 15]}, _twin_break_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-362", "Fast departure from VWAP snapback",
           "A price that was sitting at the session VWAP and then ran a multiple of its usual move away within a few minutes was pushed by an impatient order, not by a migration of value; the VWAP-benchmarked desks fill against it, and once a bar closes back beyond the previous bar toward VWAP the burst is over, so trade back toward value.",
           {"win_min": [10, 15, 30], "k": [1.5, 2.0, 3.0]}, _fast_vwap_departure_snapback,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-363", "Counter-delta micro-break fade",
           "The session's cumulative signed volume (bar volume signed by the bar's colour, over total volume) shows which side has been the aggressor all day; a short-term up-break while that cumulative delta is negative is a small push against the day's net seller, who keeps selling into it, so fade the break (mirror).",
           {"win_min": [10, 15, 30], "th": [0.05, 0.1, 0.2]}, _counter_delta_break_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-364", "Trend-day new extreme after a deep pullback",
           "On a day already far from its open for the time of day, a pullback from the session extreme deeper than a typical 15-minute move shakes out the weak holders; when price then closes at a new session extreme anyway, the day's initiator absorbed the whole pullback and the shaken-out traders must buy back above, so follow the new extreme (mirror).",
           {"k": [1.0, 1.5, 2.0], "m": [1.0, 2.0, 3.0]}, _trend_day_extreme_after_pullback,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-365", "Symmetric-volume day micro-break fade",
           "When the session VWAP sits at the midpoint of the day's range, the day's volume is spread evenly across its range: neither buyers nor sellers own the inventory and both edges are defended responsively; short-term breaks in such a symmetric session have no inventory owner behind them and are faded.",
           {"win_min": [10, 15, 30], "th": [0.05, 0.1, 0.2]}, _symmetric_volume_day_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-366", "Inside-hour regime micro-break fade",
           "When the last completed clock hour traded entirely inside the hour before it, hourly-chart traders see a contracting, two-way market with their stops parked at the bigger hour's edges; short-term breaks in the following hour happen inside that frame, reach no stop pool and are leaned back by liquidity providers, so fade them.",
           {"win_min": [10, 15, 30]}, _inside_hour_regime_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-367", "Joint-calm index and dollar micro-break fade",
           "When both WIN and WDO have traded a narrower last hour than usual for this time of day, neither local nor macro (foreign, FX) flow is active and the books are run by market makers in both markets; a short-term WIN break then has no informed side behind it and is faded.",
           {"win_min": [10, 15, 30], "q": [0.6, 0.8, 1.0]}, _joint_calm_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
]
