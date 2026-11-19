"""Conveyor batch B-019 (agent, 2026-11-18). New regime filters for micro-break fades (WIN-WDO coupling, decaying
volatility, balanced flow), PTAX-window spill, change-of-character bars, two-close acceptance, chandelier-stop
sweeps, volume-clock milestones, dollar-jump overreaction and MFI failure swings; WIN only (WDO cannot carry R$30)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _safe_div(a, b):
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.asarray(a, float) / np.asarray(b, float)
    out[~np.isfinite(out)] = np.nan
    return out


def _break_flags(ctx, minutes):
    """Bars that close beyond the previous `minutes` high (up) or low (dn), first bar only."""
    lb = ctx.bars(minutes)
    hi = ctx.roll(ctx.h, lb, "max", include_current=False)
    lo = ctx.roll(ctx.l, lb, "min", include_current=False)
    return ctx.cross(ctx.c > hi), ctx.cross(ctx.c < lo)


# E-188 ---------------------------------------------------------------------------------------------
def _decoupled_fade(ctx, p):
    nb = ctx.bars(p["win_min"])
    w = ctx.other_close()
    r = _safe_div(ctx.c, ctx.prev(ctx.c)) - 1.0
    rw = _safe_div(w, ctx.prev(w)) - 1.0
    mr, mw, mrw = ctx.roll(r, nb), ctx.roll(rw, nb), ctx.roll(r * rw, nb)
    sr, sw = ctx.roll(r, nb, "std"), ctx.roll(rw, nb, "std")
    corr = _safe_div(mrw - mr * mw, sr * sw)
    calm = corr > p["th"]
    up, dn = _break_flags(ctx, 10)
    return (dn & calm).astype(int) - (up & calm).astype(int)


# E-189 ---------------------------------------------------------------------------------------------
def _ptax_spill_fade(ctx, p):
    span = int(p["span_min"])
    ends = np.isin(ctx.minute + ctx.tf, [610, 670, 730, 790])      # bar closing at 10:10, 11:10, 12:10, 13:10
    mv = ctx.c - ctx.prev(ctx.c, ctx.bars(span))
    typ = ctx.same_minute(np.abs(mv), "median")
    big = ends & (np.abs(mv) >= p["k"] * typ) & (typ > 0)
    return (big & (mv < 0)).astype(int) - (big & (mv > 0)).astype(int)


# E-190 ---------------------------------------------------------------------------------------------
def _choch_bar(ctx, p):
    nb = ctx.bars(p["win_min"])
    body = ctx.c - ctx.o
    max_up = ctx.roll(np.maximum(body, 0.0), nb, "max", include_current=False)
    max_dn = ctx.roll(np.maximum(-body, 0.0), nb, "max", include_current=False)
    move = ctx.prev(ctx.c, 1) - ctx.prev(ctx.c, nb + 1)
    typ = ctx.same_minute(np.abs(ctx.c - ctx.prev(ctx.c, nb)), "median")
    short = (move >= p["k"] * typ) & (body < 0) & (-body > max_up)
    long = (move <= -p["k"] * typ) & (body > 0) & (body > max_dn)
    return long.astype(int) - short.astype(int)


# E-191 ---------------------------------------------------------------------------------------------
def _two_close_accept(ctx, p):
    nb = ctx.bars(p["win_min"])
    hi = ctx.prev(ctx.roll(ctx.h, nb, "max", include_current=False))
    lo = ctx.prev(ctx.roll(ctx.l, nb, "min", include_current=False))
    vok = (ctx.v >= p["vk"] * ctx.same_minute(ctx.v, "median")).astype(float)
    both = (vok == 1) & (ctx.prev(vok) == 1)
    pc = ctx.prev(ctx.c)
    up = (pc > hi) & (ctx.c > hi) & both
    dn = (pc < lo) & (ctx.c < lo) & both
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


# E-192 ---------------------------------------------------------------------------------------------
def _chandelier_sweep_fade(ctx, p):
    n, m = int(p["n_bars"]), float(p["m"])
    pc = ctx.prev(ctx.c)
    tr = np.fmax(ctx.h - ctx.l, np.fmax(np.abs(ctx.h - pc), np.abs(ctx.l - pc)))
    atr = ctx.roll(tr, n, "mean", include_current=False)
    long_stop = ctx.roll(ctx.h, n, "max", include_current=False) - m * atr
    short_stop = ctx.roll(ctx.l, n, "min", include_current=False) + m * atr
    buy = ctx.cross(ctx.c < long_stop)        # longs' trailing stops just fired: forced selling is spent
    sell = ctx.cross(ctx.c > short_stop)
    return buy.astype(int) - sell.astype(int)


# E-193 ---------------------------------------------------------------------------------------------
def _volume_milestone(ctx, p):
    step, k = float(p["step"]), float(p["k"])
    per = pd.Series(ctx.v).groupby(ctx.day).sum().reindex(range(int(ctx.day.max()) + 1))
    tot = per.shift(1).rolling(20, min_periods=20).mean().to_numpy()[ctx.day]
    cv = pd.Series(ctx.v).groupby(ctx.day).cumsum().to_numpy()
    mile = np.floor(_safe_div(cv, tot) / step)
    prev_mile = np.nan_to_num(ctx.prev(mile), nan=0.0)
    hit = np.isfinite(mile) & (mile > prev_mile) & (mile >= 1)
    dm = ctx.c - ctx.day_open
    typ = ctx.same_minute(np.abs(dm), "median")
    strong = np.abs(dm) >= k * typ
    return (hit & strong & (dm > 0)).astype(int) - (hit & strong & (dm < 0)).astype(int)


# E-194 ---------------------------------------------------------------------------------------------
def _dollar_jump_fade(ctx, p):
    w = ctx.other_close()
    rw = _safe_div(w, ctx.prev(w)) - 1.0
    r = _safe_div(ctx.c, ctx.prev(ctx.c)) - 1.0
    tw = ctx.same_minute(np.abs(rw), "median")
    ti = ctx.same_minute(np.abs(r), "median")
    jump = (np.abs(rw) >= p["k"] * tw) & (tw > 0)
    react = (np.abs(r) >= p["m"] * ti) & (ti > 0) & (r * rw < 0)
    ev = jump & react
    return (ev & (r < 0)).astype(int) - (ev & (r > 0)).astype(int)


# E-195 ---------------------------------------------------------------------------------------------
def _mfi_failure_swing(ctx, p):
    n, lvl = int(p["n"]), float(p["level"])
    low_lvl = 100.0 - lvl
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    ptp = ctx.prev(tp)
    mf = tp * ctx.v
    sp = ctx.roll(np.where(tp > ptp, mf, 0.0), n, "sum")
    sn = ctx.roll(np.where(tp < ptp, mf, 0.0), n, "sum")
    mfi = 100.0 * _safe_div(sp, sp + sn)
    x_all, d_all = mfi.tolist(), ctx.day.tolist()
    out = np.zeros(ctx.n, dtype=int)
    bear = bull = 0
    b_tr = b_pk = u_pk = u_tr = 0.0
    for i in range(ctx.n):
        if i == 0 or d_all[i] != d_all[i - 1]:
            bear = bull = 0
        x = x_all[i]
        if not (x == x):
            continue
        # bearish: above lvl, back below, bounce that fails under lvl, break of the reaction low
        if bear == 0:
            if x > lvl:
                bear = 1
        elif bear == 1:
            if x <= lvl:
                bear, b_tr, b_pk = 2, x, x
        else:
            if x > lvl:
                bear = 1
            elif x < b_tr:
                if b_pk - b_tr >= 5.0:
                    out[i], bear = -1, 0
                else:
                    b_tr = b_pk = x
            else:
                b_pk = max(b_pk, x)
        # bullish mirror
        if bull == 0:
            if x < low_lvl:
                bull = 1
        elif bull == 1:
            if x >= low_lvl:
                bull, u_pk, u_tr = 2, x, x
        else:
            if x < low_lvl:
                bull = 1
            elif x > u_pk:
                if u_pk - u_tr >= 5.0:
                    out[i], bull = 1, 0
                else:
                    u_pk = u_tr = x
            else:
                u_tr = min(u_tr, x)
    return out


# E-196 ---------------------------------------------------------------------------------------------
def _vol_decay_fade(ctx, p):
    nb = ctx.bars(p["win_min"])
    rv = ctx.roll(ctx.h - ctx.l, nb, "mean")
    before = ctx.prev(rv, nb)
    decaying = rv <= p["q"] * before
    up, dn = _break_flags(ctx, 15)
    return (dn & decaying).astype(int) - (up & decaying).astype(int)


# E-197 ---------------------------------------------------------------------------------------------
def _balanced_flow_fade(ctx, p):
    nb = ctx.bars(p["win_min"])
    sv = np.sign(ctx.c - ctx.o) * ctx.v
    imb = np.abs(_safe_div(ctx.roll(sv, nb, "sum"), ctx.roll(ctx.v, nb, "sum")))
    bal = imb <= p["th"]
    up, dn = _break_flags(ctx, 15)
    return (dn & bal).astype(int) - (up & bal).astype(int)


FAMILIES = [
    Family("E-188", "Decoupled-tape micro-break fade",
           "WIN and WDO normally move against each other because foreign flow trades both; when the rolling correlation "
           "of their 1-bar returns is no longer clearly negative, the index tape is local churn without macro flow, so a "
           "close beyond the last 10 minutes' high/low is a small local push that liquidity providers lean back; fade it.",
           {"win_min": [30, 60, 120], "th": [-0.4, -0.2, 0.0]}, _decoupled_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-189", "PTAX-window index spill fade",
           "During the four 10-minute PTAX consultation windows (10:00, 11:00, 12:00, 13:00) dealers push the dollar for "
           "the fixing and foreign desks hedge index exposure mechanically, so a WIN move made inside the window is "
           "fixing-related flow, not information; once the window closes that flow stops, so fade the window move.",
           {"span_min": [10, 15, 20], "k": [0.5, 1.0, 1.5]}, _ptax_spill_fade, markets=("WIN",),
           source="Formação da taxa de câmbio PTAX (Senado document, via search) "
                  "https://legis.senado.leg.br/sdleg-getter/documento/download/3252f6d6-c510-4df6-811a-3504f980a778",
           author="agent"),
    Family("E-190", "Change-of-character counter bar follow",
           "After a move larger than usual for the window, a counter bar whose body is larger than ANY trend-direction body "
           "of the window shows the counter side now trades with more urgency than the trend side ever did (Wyckoff "
           "change of character); the trend holders are no longer the strongest flow, so follow the counter bar.",
           {"win_min": [30, 60, 90], "k": [0.5, 1.0, 1.5]}, _choch_bar, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-191", "Two-close volume acceptance break follow",
           "Market Profile traders treat a single close beyond a range as a probe and two consecutive closes beyond it as "
           "acceptance; when both closes also trade at least normal volume for their minute, the new prices are being "
           "accepted by real participation rather than a stop sweep, so responsive traders give up and the move extends.",
           {"win_min": [30, 60, 120], "vk": [0.8, 1.0, 1.2]}, _two_close_accept, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-192", "Chandelier-stop sweep fade",
           "Many trend followers trail stops at the chandelier level (recent high minus m x ATR); a close through it fills "
           "that whole cluster of forced sell orders at once, and once the stop flow is spent nobody is left to sell, so "
           "liquidity providers who absorbed it lean the price back; buy the sweep (mirror at the short stop).",
           {"n_bars": [14, 22, 30], "m": [2.0, 2.5, 3.0]}, _chandelier_sweep_fade, markets=("WIN",),
           source="Chandelier Exit, StockCharts ChartSchool (via search) "
                  "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/chandelier-exit",
           author="agent"),
    Family("E-193", "Volume-clock milestone momentum",
           "Execution algorithms schedule parent orders against the expected daily volume curve and check progress at "
           "volume milestones; when the session crosses each fixed share of a typical day's volume while the day has "
           "already moved more than usual from the open, the scheduled remainder of those orders pushes the same way.",
           {"step": [0.2, 0.25, 0.33], "k": [0.0, 0.5, 1.0]}, _volume_milestone, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-194", "Dollar-jump index overreaction fade",
           "When the dollar jumps in one bar, index algorithms re-price WIN off it mechanically and overshoot; a WIN bar "
           "moving the opposite way much more than usual for its minute in the same bar is that mechanical repricing, "
           "and once the dollar news is absorbed local liquidity providers lean it back; fade the WIN reaction bar.",
           {"k": [2.0, 3.0, 4.0], "m": [1.5, 2.0, 3.0]}, _dollar_jump_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-195", "MFI failure swing",
           "Wilder-style failure swing on the volume-weighted Money Flow Index: after money flow was overbought, a bounce "
           "that fails below the level and then breaks the prior MFI reaction low shows buying volume drying up on each "
           "attempt; the volume-backed buyers have left and the price follows the money flow down (mirror for oversold).",
           {"n": [10, 14, 20], "level": [75, 80, 85]}, _mfi_failure_swing, markets=("WIN",),
           source="Money Flow Index (MFI), StockCharts ChartSchool (via search) "
                  "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/money-flow-index-mfi",
           author="agent"),
    Family("E-196", "Decaying-volatility micro-break fade",
           "When the recent bar ranges have shrunk well below those of the window before, the active flow of the earlier "
           "window is finished and market makers are re-centering their quotes; a close beyond the last 15 minutes' "
           "high/low in that state is a leftover push with no initiator behind it, so fade it.",
           {"win_min": [15, 30, 60], "q": [0.6, 0.75, 0.9]}, _vol_decay_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-197", "Balanced-flow micro-break fade",
           "When volume on up bars and down bars over the window nearly cancel, aggressive buyers and sellers are trading "
           "against each other with no net side; a close beyond the last 15 minutes' high/low in that balance is not "
           "backed by net flow and is reabsorbed by the other side, so fade it.",
           {"win_min": [30, 60, 90], "th": [0.1, 0.2, 0.3]}, _balanced_flow_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
