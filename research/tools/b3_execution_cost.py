"""Execution cost of WIN measured from the Clear demo's tick history (owner 2026-11-16, lever 1 of
docs/plano-busca-padroes-b3.md: "comece pela 1"). Replaces the HYPOTHESIS of b3/costs.py (1 tick per side) with
measured values, as plan F3.4 foresaw.

The tick history reaches only ~6 months back, i.e. inside the locked final-test window (from 2025-10-01). This tool
therefore measures EXECUTION ONLY, at fixed clock times (every minute boundary), with no strategy signal and no
directional statistic of any rule:
  1. quoted spread (ask - bid) in ticks, by hour;
  2. market orders: buy at the ask / sell at the bid at a minute boundary, against the backtest's model
     (bar open +/- 1 tick);
  3. stop orders: a sell stop N ticks under the mid (buy stop above), filled at the bid (ask) on the tick that
     trades through it, against the model (stop -/+ 2 ticks: 1 slippage + 1 stop extra);
  4. passive limit orders at the touch (buy at the bid / sell at the ask at a minute boundary): fill rate within
     W seconds (a trade strictly through the price = surely filled; a trade at the price = maybe, queue unknown),
     and the result H minutes later against a market order sent at the same moment (adverse selection).
Read-only: attaches to the logged-in terminal, refuses a non-demo account, sends nothing.

    live/.venv/Scripts/python.exe research/tools/b3_execution_cost.py [--sessions 30]
    live/.venv/Scripts/python.exe research/tools/b3_execution_cost.py --symbol WDOZ26 --since 2026-10-30
    (WDO: owner 2026-11-16 "rode o projeto no maximo"; output research/b3/execution_cost_wdo.json)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "research" / "b3" / "execution_cost.json"
SYM = "WINZ26"                 # the tradable contract: the continuous WIN$N ticks carry no bid/ask; --symbol
SP = __import__("zoneinfo").ZoneInfo("America/Sao_Paulo")
TICK = 5.0                     # WIN 5 points; WDO 0.5 (set by --symbol)
WINDOW = (time(9, 15), time(17, 55))      # B3 time; inside every session's regular hours (17:55 closes in US summer)
STOP_TICKS = (10, 20, 40)
LIMIT_WAIT_S = (15, 60)
HORIZONS_MIN = (15, 30)


def _ticks(mt5, day: date):
    # time_msc is the SERVER wall clock (B3 time) counted as UTC, and requests use that clock: pass B3 wall time as an
    # aware UTC datetime. (Fixed 2026-11-16: the first version passed naive local times, which the package shifts by
    # +3 h, so it read 12:00-18:30 B3 time labelled 09:00-15:30; see docs/plano-busca-padroes-b3.md section 9.)
    # one request per 20 minutes: a single request is cut at the terminal's tick limit (~100k ticks per half hour)
    start = datetime.combine(day, time(9, 0), timezone.utc)
    parts = []
    for k in range(29):                                  # 09:00 .. 18:40
        a0 = start + timedelta(minutes=20 * k)
        t = mt5.copy_ticks_range(SYM, a0, a0 + timedelta(minutes=20), mt5.COPY_TICKS_ALL)
        if t is not None and len(t):
            parts.append(t)
    if not parts:
        return None
    t = np.concatenate(parts)
    return t[np.argsort(t["time_msc"], kind="stable")]


def earliest_day(mt5, today: date) -> date:
    lo = today - timedelta(days=400)
    hi = today - timedelta(days=1)
    have = lambda d: any(_ticks(mt5, d - timedelta(days=k)) is not None for k in range(5))  # noqa: E731
    while (hi - lo).days > 5:
        mid = lo + (hi - lo) / 2
        if have(mid):
            hi = mid
        else:
            lo = mid
    return hi


def measure_day(mt5, day: date, rng) -> dict | None:
    t = _ticks(mt5, day)
    if t is None:
        return None
    ms = t["time_msc"].astype(np.int64)
    bid, ask, last = t["bid"].astype(float), t["ask"].astype(float), t["last"].astype(float)
    flags = t["flags"].astype(np.int64)
    trade = ((flags & mt5.TICK_FLAG_LAST) != 0) & (last > 0)
    # forward-fill quotes (a zero means "unchanged")
    for a in (bid, ask):
        a[a <= 0] = np.nan
        idx = np.where(~np.isnan(a), np.arange(len(a)), 0)
        np.maximum.accumulate(idx, out=idx)
        a[:] = a[idx]
    ok = ~np.isnan(bid) & ~np.isnan(ask) & (ask > bid)
    t0 = int(datetime.combine(day, WINDOW[0], timezone.utc).timestamp() * 1000)
    t1 = int(datetime.combine(day, WINDOW[1], timezone.utc).timestamp() * 1000)
    tr_ms, tr_px = ms[trade], last[trade]
    buy_aggr = ((flags & mt5.TICK_FLAG_BUY) != 0) & ((flags & mt5.TICK_FLAG_SELL) == 0)
    sell_aggr = ((flags & mt5.TICK_FLAG_SELL) != 0) & ((flags & mt5.TICK_FLAG_BUY) == 0)
    tb_ms, tb_px = ms[trade & buy_aggr], last[trade & buy_aggr]       # a market BUY fills like these (at the ask)
    ts_ms, ts_px = ms[trade & sell_aggr], last[trade & sell_aggr]     # a market SELL fills like these (at the bid)

    def next_fill(side, x):     # price of the first aggressor trade of that side at or after x (the real fill)
        arr_ms, arr_px = (tb_ms, tb_px) if side > 0 else (ts_ms, ts_px)
        i = np.searchsorted(arr_ms, x)
        return arr_px[i] if i < len(arr_ms) and arr_ms[i] < x + 5_000 else np.nan
    mid = (bid + ask) / 2

    def quote_at(x):            # last quote at or before x
        i = np.searchsorted(ms, x, side="right") - 1
        return (bid[i], ask[i]) if i >= 0 and ok[i] else (np.nan, np.nan)

    def mid_at(x):
        i = np.searchsorted(ms, x, side="right") - 1
        return mid[i] if i >= 0 and ok[i] else np.nan

    rows = {"spread": [], "hour": [], "buy_vs_model": [], "sell_vs_model": [], "buy_aggr_vs_model": [], "sell_aggr_vs_model": [], "stop": {n: [] for n in STOP_TICKS},
            "limit": {(w, h): {"through": 0, "touch": 0, "n": 0, "gain_through": [], "gain_market": []}
                      for w in LIMIT_WAIT_S for h in HORIZONS_MIN}}
    for m in range(t0, t1, 60_000):
        b, a = quote_at(m)
        j = np.searchsorted(tr_ms, m)
        if np.isnan(b) or j >= len(tr_ms) or tr_ms[j] >= m + 60_000:
            continue
        open_px = tr_px[j]                       # the 1-minute bar's open: first trade of the minute
        rows["spread"].append((a - b) / TICK)
        rows["hour"].append(datetime.fromtimestamp(m / 1000, timezone.utc).hour)     # B3 wall-clock hour
        rows["buy_vs_model"].append((open_px + TICK - a) / TICK)     # > 0: the model (open + 1 tick) pays more than the ask
        rows["sell_vs_model"].append((b - (open_px - TICK)) / TICK)  # > 0: the model receives less than the bid
        fb, fs = next_fill(+1, m), next_fill(-1, m)
        if not np.isnan(fb):
            rows["buy_aggr_vs_model"].append((open_px + TICK - fb) / TICK)
        if not np.isnan(fs):
            rows["sell_aggr_vs_model"].append((fs - (open_px - TICK)) / TICK)
        # stops: every 5th minute, a sell stop under the mid and a buy stop above, alive 30 minutes
        if (m // 60_000) % 5 == 0:
            md = (a + b) / 2
            for n in STOP_TICKS:
                for side in (+1, -1):            # +1 = protective sell stop of a long, -1 = buy stop of a short
                    level = np.floor((md - n * TICK) / TICK) * TICK if side > 0 else np.ceil((md + n * TICK) / TICK) * TICK
                    k0, k1 = j, np.searchsorted(tr_ms, m + 30 * 60_000)
                    seg = tr_px[k0:k1]
                    hit = np.flatnonzero(seg <= level) if side > 0 else np.flatnonzero(seg >= level)
                    if len(hit):
                        when = tr_ms[k0 + hit[0]]
                        fill = next_fill(-side, when)    # the stop sends a market SELL (long) / BUY (short)
                        if not np.isnan(fill):
                            # ticks paid beyond the stop level; the model pays 2 (1 slippage + 1 stop extra)
                            rows["stop"][n].append(((level - fill) if side > 0 else (fill - level)) / TICK)
        # passive limit at the touch, both sides, against a market order at the same moment
        for side in (+1, -1):
            lim = b if side > 0 else a
            mkt = a if side > 0 else b
            for w in LIMIT_WAIT_S:
                k0, k1 = j, np.searchsorted(tr_ms, m + w * 1000)
                seg = tr_px[k0:k1]
                through = np.flatnonzero(seg < lim) if side > 0 else np.flatnonzero(seg > lim)
                touch = np.flatnonzero(seg <= lim) if side > 0 else np.flatnonzero(seg >= lim)
                for h in HORIZONS_MIN:
                    r = rows["limit"][(w, h)]
                    r["n"] += 1
                    r["touch"] += int(len(touch) > 0)
                    later = mid_at(m + h * 60_000)
                    if np.isnan(later):
                        continue
                    r["gain_market"].append(side * (later - mkt) / TICK)
                    if len(through):
                        f_ms = tr_ms[k0 + through[0]]
                        r["through"] += 1
                        r["gain_through"].append(side * (mid_at(f_ms + h * 60_000) - lim) / TICK)
    return rows


def summarize(days: list[dict]) -> dict:
    sp = np.concatenate([np.array(d["spread"]) for d in days])
    hr = np.concatenate([np.array(d["hour"]) for d in days])
    buy = np.concatenate([np.array(d["buy_vs_model"]) for d in days])
    sell = np.concatenate([np.array(d["sell_vs_model"]) for d in days])
    buy_a = np.concatenate([np.array(d["buy_aggr_vs_model"]) for d in days])
    sell_a = np.concatenate([np.array(d["sell_aggr_vs_model"]) for d in days])
    out = {
        "minutes_measured": int(len(sp)),
        "spread_ticks": {"mean": float(sp.mean()), "median": float(np.median(sp)), "share_1_tick": float((sp <= 1.001).mean()),
                         "share_2_plus": float((sp > 1.001).mean()), "p95": float(np.percentile(sp, 95))},
        "spread_by_hour_sao_paulo": {int(h): float(sp[hr == h].mean()) for h in np.unique(hr)},
        "market_order_vs_model_ticks": {
            "_meaning": "model fill (bar open +/- 1 tick) minus the real touch (ask for a buy, bid for a sell), per side; > 0 = the model is pessimistic by that many ticks",
            "quotes": {"buy_mean": float(buy.mean()), "sell_mean": float(sell.mean())},
            "aggressor_trades": {"buy_mean": float(buy_a.mean()), "sell_mean": float(sell_a.mean()),
                                 "_meaning": "the first buy- (sell-) aggressor trade within 5 s of the minute boundary = what a market order gets"},
            "real_slippage_vs_open_ticks_per_side": float(1 - (buy_a.mean() + sell_a.mean()) / 2),
            "real_slippage_vs_open_ticks_per_side_p90": float(1 - np.percentile(np.concatenate([buy_a, sell_a]), 10))},
        "stop_ticks_beyond_level": {}, "limit_at_touch": {}}
    for n in STOP_TICKS:
        s = np.concatenate([np.array(d["stop"][n]) for d in days])
        if len(s):
            s = s[~np.isnan(s)]
            out["stop_ticks_beyond_level"][f"{n}_ticks_away"] = {"n": int(len(s)), "mean": float(s.mean()),
                                                                 "p95": float(np.percentile(s, 95)), "model": 2.0}
    for w in LIMIT_WAIT_S:
        for h in HORIZONS_MIN:
            n = sum(d["limit"][(w, h)]["n"] for d in days)
            th = sum(d["limit"][(w, h)]["through"] for d in days)
            tc = sum(d["limit"][(w, h)]["touch"] for d in days)
            g_t = np.concatenate([np.array(d["limit"][(w, h)]["gain_through"]) for d in days])
            g_m = np.concatenate([np.array(d["limit"][(w, h)]["gain_market"]) for d in days])
            out["limit_at_touch"][f"wait_{w}s_horizon_{h}min"] = {
                "orders": n, "filled_through_share": th / n if n else None, "touched_share": tc / n if n else None,
                "mean_result_if_filled_ticks": float(np.nanmean(g_t)) if len(g_t) else None,
                "mean_result_market_ticks": float(np.nanmean(g_m)) if len(g_m) else None,
                "_meaning": "mid H minutes after the fill minus the fill price, signed by the side, in ticks; the market order is sent at the same minute boundary"}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", type=int, default=30)
    ap.add_argument("--since", default="2026-10-15", help="first session as the front contract")
    ap.add_argument("--symbol", default="WINZ26")
    a = ap.parse_args(argv)
    global SYM, TICK, OUT
    SYM = a.symbol.upper()
    TICK = {"WIN": 5.0, "WDO": 0.5}[SYM[:3]]
    if SYM[:3] == "WDO":
        OUT = ROOT / "research" / "b3" / "execution_cost_wdo.json"
    import MetaTrader5 as mt5
    from b3.data.mt5_history import attach
    attach(mt5, ROOT / "b3" / "config" / "broker_mt5.json")
    try:
        if not mt5.symbol_select(SYM, True):
            raise SystemExit(f"{SYM} not available")
        today = (datetime.now(timezone.utc) - timedelta(hours=3)).date()
        first = date.fromisoformat(a.since)      # the day WINZ26 became the front contract (b3_data.roll_days)
        span = [first + timedelta(days=i) for i in range((today - first).days)]
        span = [d for d in span if d.weekday() < 5]
        pick = [span[int(i)] for i in np.linspace(0, len(span) - 1, min(a.sessions, len(span)))]
        rng = np.random.default_rng(1)
        days, used = [], []
        for d in pick:
            r = measure_day(mt5, d, rng)
            if r and len(r["spread"]) > 300:
                days.append(r)
                used.append(d.isoformat())
                print(d, len(r["spread"]), flush=True)
        res = summarize(days)
        res = {"generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "symbol": SYM,
               "tick_history_from": first.isoformat(), "sessions": used,
               "_scope": "execution only, at fixed minute boundaries, no strategy signal (the tick window is inside the locked final test)",
               "_coverage": "the terminal's tick history has holes (e.g. 2026-11-13 stops near 16:30): only minutes with ticks count; see spread_by_hour_sao_paulo for the hours covered",
               **res}
        OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
        print(json.dumps({k: res[k] for k in ("tick_history_from", "spread_ticks", "market_order_vs_model_ticks",
                                              "stop_ticks_beyond_level", "limit_at_touch")}, indent=1))
    finally:
        mt5.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
