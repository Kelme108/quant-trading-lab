"""Conveyor batch B-145 (agent, 2026-11-24). Bar-structure, block-level and volume-share ideas for WIN."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _typ_abs_move(ctx, nb):
    move = ctx.c - ctx.prev(ctx.c, nb)
    typ = ctx.cached(("abs_move_b145", nb), lambda: ctx.prev_sessions(np.abs(move), "mean"))
    return move, typ


def _bald_bar_after_leg(ctx, p):
    nb = ctx.bars(p["leg_min"])
    shave = p["shave"]
    move, typ = _typ_abs_move(ctx, nb)
    leg = ctx.prev(move, 1)
    rng = ctx.h - ctx.l
    long = (rng > 0) & (ctx.o - ctx.l <= shave * rng) & (ctx.c > ctx.o) & (leg <= -typ)
    short = (rng > 0) & (ctx.h - ctx.o <= shave * rng) & (ctx.c < ctx.o) & (leg >= typ)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _block_false_break(ctx, p):
    B = int(p["block_min"])
    key = ctx.day.astype(np.int64) * 10000 + (ctx.minute.astype(np.int64) // B)
    df = pd.DataFrame({"k": key, "d": ctx.day, "h": ctx.h, "l": ctx.l})
    g = df.groupby("k").agg(h=("h", "max"), l=("l", "min"), d=("d", "first"))
    same = g["d"].shift(1) == g["d"]
    ph = g["h"].shift(1).where(same)
    pl = g["l"].shift(1).where(same)
    pbh = ph.reindex(key).to_numpy()
    pbl = pl.reindex(key).to_numpy()
    short = (ctx.h > pbh) & (ctx.c < pbh)
    long = (ctx.l < pbl) & (ctx.c > pbl)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _mid_recovery(ctx, p):
    n = ctx.bars(p["win_min"])
    thr = p["thr"]
    hi = ctx.roll(ctx.h, n, "max")
    lo = ctx.roll(ctx.l, n, "min")
    width = hi - lo
    pos = np.where(width > 0, (ctx.c - lo) / np.where(width > 0, width, 1.0), np.nan)
    was_low = ctx.roll((pos < thr).astype(float), n, "max", include_current=False) == 1
    was_high = ctx.roll((pos > 1 - thr).astype(float), n, "max", include_current=False) == 1
    long = was_low & (pos > 0.5)
    short = was_high & (pos < 0.5)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _push_count(ctx, p):
    n = ctx.bars(p["win_min"])
    m = p["pushes"]
    push_up = (ctx.h > ctx.session_high(False)).astype(float)
    push_dn = (ctx.l < ctx.session_low(False)).astype(float)
    cu = ctx.roll(push_up, n, "sum")
    cd = ctx.roll(push_dn, n, "sum")
    long = (cu >= m) & (ctx.c > ctx.o)
    short = (cd >= m) & (ctx.c < ctx.o)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _micro_poke_vwap_trend(ctx, p):
    n = ctx.bars(p["win_min"])
    s = p["share"]
    vw = ctx.vwap()
    sh_up = ctx.roll((ctx.c > vw).astype(float), n, "mean", include_current=False)
    sh_dn = ctx.roll((ctx.c < vw).astype(float), n, "mean", include_current=False)
    pl, ph = ctx.prev(ctx.l, 1), ctx.prev(ctx.h, 1)
    long = (sh_up >= s) & (ctx.l < pl) & (ctx.c > pl) & (ctx.c > vw)
    short = (sh_dn >= s) & (ctx.h > ph) & (ctx.c < ph) & (ctx.c < vw)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _effort_no_result(ctx, p):
    n, m = int(p["n"]), p["m"]
    rng = ctx.h - ctx.l
    ok = np.ones(ctx.n, bool)
    for i in range(n):
        ok &= ctx.prev(ctx.v, i) > ctx.prev(ctx.v, i + 1)
        ok &= ctx.prev(rng, i) < ctx.prev(rng, i + 1)
    typ = ctx.cached("rng_typ_b145", lambda: ctx.prev_sessions(rng, "mean"))
    mv = ctx.c - ctx.prev(ctx.c, n + 1)
    short = ok & (mv >= m * typ)
    long = ok & (mv <= -m * typ)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _midday_momentum_flip(ctx, p):
    nb = ctx.bars(p["look_min"])
    k = p["k"]
    move, typ = _typ_abs_move(ctx, nb)
    mid = (ctx.minute >= 690) & (ctx.minute < 870)
    long = mid & (move >= k * typ)
    short = mid & (move <= -k * typ)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _volume_above_mid_share(ctx, p):
    thr, mn = p["thr"], p["min_min"]
    mid = (ctx.session_high(True) + ctx.session_low(True)) / 2.0
    up = pd.Series(ctx.v * (ctx.c > mid)).groupby(ctx.day).cumsum().to_numpy()
    tot = pd.Series(ctx.v).groupby(ctx.day).cumsum().to_numpy()
    share = np.where(tot > 0, up / np.where(tot > 0, tot, 1.0), np.nan)
    elapsed = ctx.bar_in_day * ctx.tf >= mn
    long = elapsed & (share >= thr)
    short = elapsed & (share <= 1 - thr)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _open_reclaim_pair(ctx, p):
    k, mode = p["body_k"], p["mode"]
    n = ctx.bars(60)
    ema = ctx.cached(("ema_b145", n), lambda: ctx.ema(ctx.c, n))
    rng = ctx.h - ctx.l
    typ = ctx.cached("rng_typ_b145", lambda: ctx.prev_sessions(rng, "mean"))
    po, pc = ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1)
    body = np.abs(pc - po)
    long = (pc < po) & (body >= k * typ) & (ctx.c > po) & (ctx.c > ctx.o)
    short = (pc > po) & (body >= k * typ) & (ctx.c < po) & (ctx.c < ctx.o)
    if mode == "with":
        long &= ctx.c > ema
        short &= ctx.c < ema
    else:
        long &= ctx.c < ema
        short &= ctx.c > ema
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _flush_bounce(ctx, p):
    n, k = int(p["n"]), p["k"]
    move, typ = _typ_abs_move(ctx, n)
    fl = ctx.prev(move, 1)
    long = (fl <= -k * typ) & (ctx.c > ctx.prev(ctx.h, 1))
    short = (fl >= k * typ) & (ctx.c < ctx.prev(ctx.l, 1))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


W = ("WIN",)
FAMILIES = [
    Family("E-1448", "Bald bar after a leg",
           "A bar that opens on its extreme and closes away from it right after a leg the other way shows one-sided "
           "aggression with no counter-trading at the open; trade against the leg.",
           {"leg_min": [10, 20, 30], "shave": [0.05, 0.15]}, _bald_bar_after_leg, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1449", "Previous-block false break fade",
           "Poking beyond the prior 15/30/60-minute block's high or low and closing back inside it traps stop orders "
           "placed at the block edge; fade back into the block.",
           {"block_min": [15, 30, 60]}, _block_false_break, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1450", "Recovery through the mid of the rolling range",
           "After price sat at the bottom (top) of its rolling range, a close through the middle means the extreme "
           "was absorbed and the other side took control; follow it.",
           {"win_min": [30, 60, 90], "thr": [0.1, 0.2]}, _mid_recovery, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1451", "New-extreme push count follow",
           "Several separate bars each making a new session high (low) in a short window show repeated, "
           "successful aggression by one side; follow when a push bar closes with the move.",
           {"win_min": [15, 30, 60], "pushes": [2, 3, 4]}, _push_count, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1452", "Micro-poke in a VWAP trend",
           "When price has stayed on one side of VWAP, a bar that pokes through the prior bar's extreme and closes "
           "back is a shallow pullback absorbed by the trend side; trade with the trend.",
           {"win_min": [20, 40, 60], "share": [0.6, 0.8, 1.0]}, _micro_poke_vwap_trend, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1453", "Rising effort, shrinking result",
           "Volume growing while ranges shrink after a move means the move meets resting orders that absorb it; "
           "fade the move.",
           {"n": [2, 3, 4], "m": [1.0, 2.0]}, _effort_no_result, markets=W,
           source="Wyckoff effort versus result (assistant reasoning)", author="agent"),
    Family("E-1454", "Midday momentum flip",
           "In the thin 11:30-14:30 window a move that grows larger than usual for the horizon is driven by few "
           "large orders that keep working; follow its onset.",
           {"look_min": [10, 20, 30], "k": [0.75, 1.0, 1.5]}, _midday_momentum_flip, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1455", "Volume above the session midpoint",
           "When most of the session's volume has traded above (below) the running range midpoint, the market "
           "accepts higher (lower) prices; follow the crossing of that share.",
           {"thr": [0.6, 0.7, 0.8], "min_min": [30, 60]}, _volume_above_mid_share, markets=W,
           source="market profile acceptance idea (assistant reasoning)", author="agent"),
    Family("E-1456", "Prior-bar open reclaim pair",
           "A bar that closes beyond the open of a large opposite bar reverses it fully; with or against the "
           "60-minute EMA side this marks who is trapped.",
           {"body_k": [0.5, 1.0, 1.5], "mode": ["with", "against"]}, _open_reclaim_pair, markets=W,
           source="candlestick engulfing literature (assistant reasoning)", author="agent"),
    Family("E-1457", "Flush bounce through the prior bar",
           "A fast multi-bar flush larger than usual triggers stops; the first bar to close beyond the previous "
           "bar's extreme the other way shows forced sellers (buyers) are done.",
           {"n": [2, 3, 5], "k": [1.5, 2.0, 3.0]}, _flush_bounce, markets=W,
           source="assistant reasoning", author="agent"),
]
