"""Exit-management study (b3/config/exit_study_b3.json, docs/plano-gestao-saida-b3.md; owner approval 2026-11-17).

Entries are the registered rules' OWN trades (the official backtester, b3/backtest.py, on the exploration split).
Only the exit varies: each trade is replayed on 1-minute bars from its fill to the rule's own exit, and an
exit variant may close it EARLIER (target, tighter stop, breakeven, trailing stop). It can never hold longer
and never adds an entry. Conservative fills: stop before target in the same minute, the target is a limit order
that needs a trade 1 tick through it, the trailing/breakeven stop moves only with the PREVIOUS minutes' prices.

X00 replays the rule's own exits on the same 1-minute path (its stop checked minute by minute; the other exits at
the official exit time), so every variant is compared on the same footing; the fidelity block reports how X00
matches the official engine.

Usage: python -m b3.exit_study run            (exploration only; refuses to run unless the protocol is approved)
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from b3 import b3_data
from b3.backtest import BacktestConfig, run
from b3.instruments import instrument_for
from b3.markets import market
from b3.proxy_research import CONFIGS, _prepare_b3, rule_class, split_window, _approved, lane_paths

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "b3" / "config" / "exit_study_b3.json"
PS_CONFIG = ROOT / "b3" / "config" / "pattern_search_b3.json"
OUT = ROOT / "research" / "b3" / "exit_study"
PRIOR_DAILY = {"WIN": ["A-measured-exploration-daily.csv.gz", "B-exploration-daily.csv.gz", "C-exploration-daily.csv.gz"],
               "WDO": ["wdo/A-measured-exploration-daily.csv.gz", "wdo/C-exploration-daily.csv.gz"]}
PRIOR_TRIALS = {"WIN": 849, "WDO": 840}


def load_config() -> dict:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    if cfg.get("approved_by_owner") is not True:
        raise SystemExit("exit_study_b3.json is not approved by the owner: nothing is read")
    return cfg


def costs(root: str) -> dict:
    ps = json.loads(PS_CONFIG.read_text(encoding="utf-8"))
    src = ps["cost_reevaluation"] if root == "WIN" else ps["wdo_extension"]["costs"]
    return {"measured": src["measured"], "measured_p90": src["measured_p90"]}


# ---------------------------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------------------------

def minute_path(root: str, series: str, rules) -> pd.DataFrame:
    """1-minute bars of the regular session, same price series (raw / back-adjusted) as the rule."""
    raw = b3_data.load_b3_bars(root, "1m", None)
    bars = b3_data.back_adjusted(raw, b3_data.roll_days(root, None)) if series == "back_adjusted" else raw.assign(adj_offset=0.0)
    cal = b3_data.history_calendar(root, raw, rules)
    bars = b3_data.session_only_b3(bars, cal, 1)
    return bars.reset_index(drop=True)


def official_trades(rule_id: str, symbol: str) -> tuple[pd.DataFrame, pd.Timestamp, pd.Timestamp, object]:
    paths = lane_paths(symbol)
    scope = _approved(paths["scope"])
    mkt = market(symbol)
    rule = rule_class(rule_id).on(mkt.symbol)
    start, end = split_window(mkt.symbol, "exploration", _approved(paths["splits"]), rule_id)
    bars, cal, _, _ = _prepare_b3(mkt, rule, start, end, scope, None)
    res = run(bars, rule(cal), mkt.cost("base"), CONFIGS.get(rule_id, BacktestConfig()))
    tr = res.trades_frame()
    tr = tr[pd.to_datetime(tr["entry_time"], utc=True) >= start].reset_index(drop=True)
    return tr, start, end, rule


# ---------------------------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------------------------

def _grid_pts(brl: float, point_value: float, tick: float) -> float:
    return math.ceil(brl / point_value / tick - 1e-9) * tick


def replay(trade, mins: dict, ex: dict, inst, slip_ticks: float) -> tuple[float, float, str, pd.Timestamp, bool]:
    """(entry_ref, exit_price_with_slippage, reason, exit_time, fallback). Prices are the series' prices."""
    tick, pv = inst.tick_size, inst.point_value_brl
    s = 1 if trade.side == "long" else -1
    t0, t1 = pd.Timestamp(trade.entry_time), pd.Timestamp(trade.exit_time)
    i0 = mins["pos"].get(t0.value)
    slip = slip_ticks * tick
    if i0 is None:
        return math.nan, math.nan, "no_minute", t1, True
    E = mins["open"][i0]
    stop = trade.stop_price if trade.stop_price == trade.stop_price else None
    kind = ex["kind"]
    if kind in ("target_stop",):
        own = E - s * _grid_pts(ex["stop_brl"], pv, tick)
        stop = own if stop is None else (max(stop, own) if s > 0 else min(stop, own))
    target = E + s * _grid_pts(ex["target_brl"], pv, tick) if kind in ("target", "target_stop", "target_breakeven") else None
    trig = _grid_pts(ex["trigger_brl"], pv, tick) if kind in ("breakeven", "target_breakeven") else None
    dist = _grid_pts(ex["distance_brl"], pv, tick) if kind == "trailing" else None
    best = E
    i = i0
    n = len(mins["open"])
    while i < n and mins["time"][i] < t1.value:
        o, h, lo = mins["open"][i], mins["high"][i], mins["low"][i]
        t = pd.Timestamp(mins["time"][i], tz="UTC")
        if stop is not None and ((s > 0 and lo <= stop) or (s < 0 and h >= stop)):
            px = min(o, stop) if s > 0 else max(o, stop)
            why = "stop_loss" if stop == trade.stop_price else ex["kind"] + "_stop"
            return E, px - s * slip, why, t + pd.Timedelta(minutes=1), False
        if target is not None and ((s > 0 and h >= target + tick) or (s < 0 and lo <= target - tick)):
            return E, target, "target", t + pd.Timedelta(minutes=1), False
        best = max(best, h) if s > 0 else min(best, lo)
        gain = (best - E) * s
        if trig is not None and gain >= trig:
            be = E + s * tick
            stop = be if stop is None else (max(stop, be) if s > 0 else min(stop, be))
        if dist is not None and gain >= dist:
            tr = best - s * dist
            stop = tr if stop is None else (max(stop, tr) if s > 0 else min(stop, tr))
        i += 1
    # the rule's own exit at t1
    j = mins["pos"].get(t1.value)
    if trade.exit_reason == "stop_loss" or j is None:
        # official stop the 1-minute path did not show (or no minute at t1): the official price, base slippage removed
        ref = trade.exit_price + s * mins["base_slip"]
        return E, ref - s * slip, trade.exit_reason, t1, True
    return E, mins["open"][j] - s * slip, trade.exit_reason, t1, False


def evaluate_market(rule_id: str, symbol: str, cfg: dict, cache: dict) -> dict:
    tr, start, end, rule = official_trades(rule_id, symbol)
    root = market(symbol).root
    inst = instrument_for(root)
    series = getattr(rule, "price_series", "raw")
    key = (root, series, rule.rules)
    if key not in cache:
        cache[key] = minute_path(root, series, rule.rules)
    m = cache[key]
    m = m[(m["time"] >= start - pd.Timedelta(days=1)) & (m["time"] < end + pd.Timedelta(days=1))].reset_index(drop=True)
    tv = m["time"].astype("int64").to_numpy()
    mins = {"time": tv, "open": m["open"].to_numpy(), "high": m["high"].to_numpy(), "low": m["low"].to_numpy(),
            "pos": {int(v): k for k, v in enumerate(tv)},
            "base_slip": market(symbol).cost("base").slippage_ticks_per_side * inst.tick_size}
    offs = dict(zip(m["time"].dt.tz_convert("America/Sao_Paulo").dt.date, m["adj_offset"]))
    years = (end - start).total_seconds() / (365.25 * 86400)
    days = sorted(set(m.loc[(m["time"] >= start) & (m["time"] < end), "time"].dt.tz_convert("America/Sao_Paulo").dt.date))
    cst = costs(root)
    out = {"rule": rule_id, "symbol": symbol, "official_trades": len(tr), "trades_per_year": len(tr) / years,
           "variants": {}}
    for xid, ex in cfg["exits"].items():
        if xid.startswith("_"):
            continue
        per = {}
        for scen, c in cst.items():
            rows = []
            for t in tr.itertuples(index=False):
                E, X, why, tx, fb = replay(t, mins, ex, inst, c["slippage_ticks_per_side"])
                if E != E:
                    continue
                s = 1 if t.side == "long" else -1
                Eslip = E + s * c["slippage_ticks_per_side"] * inst.tick_size
                pts = (X - Eslip) * s
                gross_pts = (X - E) * s if why != "target" else (X - E) * s
                d = pd.Timestamp(t.entry_time).tz_convert("America/Sao_Paulo").date()
                notional = (E - float(offs.get(d, 0.0))) * inst.point_value_brl
                net = pts * inst.point_value_brl - 2 * c["fees_per_side_brl"]
                rows.append({"entry_time": t.entry_time, "exit_time": tx, "side": t.side, "reason": why, "fallback": fb,
                             "gross_pct": 100 * gross_pts * inst.point_value_brl / notional,
                             "net_pct": 100 * net / notional, "net_brl": net})
            df = pd.DataFrame(rows)
            r = df["net_pct"].to_numpy() / 100
            eq = np.cumprod(1 + r)
            yr = pd.to_datetime(df["exit_time"], utc=True).dt.tz_convert("America/Sao_Paulo").dt.year
            by_year = df.groupby(yr)["net_pct"].sum()
            best = int(np.argmax(r))
            daily = df.groupby(pd.to_datetime(df["exit_time"], utc=True).dt.tz_convert("America/Sao_Paulo").dt.date)["net_pct"].sum()
            per[scen] = {"trades": len(df), "trades_per_year": len(df) / years,
                         "mean_gross_pct": float(df["gross_pct"].mean()), "mean_net_pct": float(df["net_pct"].mean()),
                         "mean_net_brl": float(df["net_brl"].mean()), "hit_rate": float((df["net_brl"] > 0).mean()),
                         "net_return_pct": float((eq[-1] - 1) * 100),
                         "net_without_best_pct": float((np.prod(np.delete(1 + r, best)) - 1) * 100),
                         "max_drawdown_pct": float((1 - eq / np.maximum.accumulate(eq)).max() * 100),
                         "positive_years_share": float((by_year > 0).mean()),
                         "exit_reasons": df["reason"].value_counts().to_dict(),
                         "fallback_exits": int(df["fallback"].sum())}
            if scen == "measured":
                per["_daily"] = daily.reindex(days, fill_value=0.0)
        out["variants"][xid] = per
    return out


def run_study() -> Path:
    from lab import stats
    cfg = load_config()
    gate = json.loads(PS_CONFIG.read_text(encoding="utf-8"))["gate_search"]
    pairs = [(r, "WIN") for r in cfg["entries"]["rules"]] + [("P-004", m) for m in cfg["entries"]["p004"]["markets"]]
    cache, results = {}, []
    for rid, sym in pairs:
        res = evaluate_market(rid, sym, cfg, cache)
        res["eligible"] = res["trades_per_year"] >= cfg["gate"]["min_trades_per_year"]
        results.append(res)
        x0 = res["variants"]["X00"]["measured"]
        print(f"{rid} {sym}: {res['official_trades']} trades ({res['trades_per_year']:.0f}/yr) X00 net/trade "
              f"{x0['mean_net_brl']:.2f} BRL", flush=True)
    report = {"generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "config": "b3/config/exit_study_b3.json", "split": "exploration", "markets": {}}
    OUT.mkdir(parents=True, exist_ok=True)
    for sym in ("WIN", "WDO"):
        rs = [r for r in results if r["symbol"] == sym and r["eligible"]]
        if not rs:
            continue
        daily = {f"{r['rule']}|{x}": v["_daily"] for r in rs for x, v in r["variants"].items()}
        mat = pd.DataFrame(daily).fillna(0.0)
        prior = []
        for f in PRIOR_DAILY[sym]:
            p = ROOT / "research" / "b3" / "search" / f
            if p.exists():
                d = pd.read_csv(p, index_col=0)
                prior += [stats.sharpe(d[c].to_numpy()) for c in d.columns]
        new_ids = [k for k in mat.columns if not k.endswith("|X00")]       # X00 rows were already counted as rules
        n_trials = PRIOR_TRIALS[sym] + len(new_ids)
        sharpes = [stats.sharpe(mat[k].to_numpy()) for k in mat.columns] + prior
        var = float(np.var(sharpes, ddof=1))
        pbo = stats.pbo_cscv(mat.to_numpy(), n_slices=cfg["gate"]["pbo_slices"]) if mat.shape[1] >= 2 else None
        rows = []
        for r in rs:
            for x, v in r["variants"].items():
                k = f"{r['rule']}|{x}"
                ds = stats.deflated_sharpe(mat[k].to_numpy(), n_trials, var)
                b, c = v["measured"], v["measured_p90"]
                fails = []
                if b["trades_per_year"] < gate["min_trades_per_year"]:
                    fails.append("trades_per_year")
                if not b["net_return_pct"] > 0:
                    fails.append("net_base")
                if not c["net_return_pct"] > 0:
                    fails.append("net_conservative")
                if not b["net_without_best_pct"] > 0:
                    fails.append("net_without_best")
                if max(b["max_drawdown_pct"], c["max_drawdown_pct"]) > gate["max_drawdown_pct"]:
                    fails.append("drawdown")
                if b["positive_years_share"] < gate["positive_years_share"]:
                    fails.append("positive_years")
                if not ds["dsr"] >= cfg["gate"]["dsr_min"]:
                    fails.append("deflated_sharpe")
                if pbo is None or pbo["pbo"] > cfg["gate"]["pbo_max"]:
                    fails.append("pbo")
                rows.append({"variant": k, "rule": r["rule"], "exit": x, "measured": b, "measured_p90": c,
                             "dsr": ds["dsr"], "sharpe_annualised": ds["sharpe_annualised"], "fails": fails,
                             "passed": not fails})
        rows.sort(key=lambda z: -z["measured"]["mean_net_brl"])
        report["markets"][sym] = {"n_variants": len(mat.columns), "n_new_trials": len(new_ids), "n_trials_for_dsr": n_trials,
                                  "pbo": {k: v for k, v in pbo.items() if k != "logits"} if pbo else None,
                                  "passed": [z["variant"] for z in rows if z["passed"]], "rows": rows}
        mat.to_csv(OUT / f"{sym}-exploration-daily.csv.gz")
    report["not_eligible"] = [f"{r['rule']} {r['symbol']} ({r['trades_per_year']:.0f}/yr)" for r in results if not r["eligible"]]
    path = OUT / "exploration.json"
    path.write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run"])
    a = ap.parse_args(argv)
    if a.cmd == "run":
        print(run_study())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
