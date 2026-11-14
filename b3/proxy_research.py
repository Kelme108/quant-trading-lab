"""Research runner for the proxy markets: splits, four cost scenarios, metrics as a share of notional, gates,
and a ledger of every read (trials for the multiple-testing bar; validation read ONCE per rule and market).

Nothing is read before the owner approves b3/config/splits_proxies.json and gates_proxies.json
("approved_by_owner": true). The final test is never read while "final_test_unlocked" is false.

    python -m b3.proxy_research run P-001 --symbols US500,USTEC --split exploration
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from b3.backtest import BacktestConfig, run
from b3.costs import REQUIRED_SCENARIOS
from b3.markets import ProxySessionCalendar, infer_closed_days, load_bars, market, session_only
from b3.strategies.proxies import RULES

ROOT = Path(__file__).resolve().parents[1]
SPLITS_PATH = ROOT / "b3" / "config" / "splits_proxies.json"
GATES_PATH = ROOT / "b3" / "config" / "gates_proxies.json"
OUT_DIR = ROOT / "research" / "proxies"
LEDGER = OUT_DIR / "ledger.jsonl"
CONFIGS = {"P-001": BacktestConfig(max_entries_per_day=1)}


class NotApproved(RuntimeError):
    """The splits or the gates are not approved by the owner yet."""


class AlreadyRead(RuntimeError):
    """This rule's validation on this market was already read."""


def _approved(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if cfg.get("approved_by_owner") is not True:
        raise NotApproved(f"{path.name} is not approved by the owner; nothing is read before that")
    return cfg


def final_test_open(rule_id: str | None, symbol: str, splits: dict) -> bool:
    """Globally unlocked, or unlocked by the owner for this rule on this market only."""
    if splits.get("final_test_unlocked"):
        return True
    return any(u["rule"] == rule_id and symbol in u["symbols"] for u in splits.get("final_test_unlocked_for", []))


def split_window(symbol: str, split: str, splits: dict | None = None,
                 rule_id: str | None = None) -> tuple[pd.Timestamp, pd.Timestamp]:
    splits = splits or _approved(SPLITS_PATH)
    if split == "final_test" and not final_test_open(rule_id, symbol, splits):
        raise NotApproved(f"the final test is locked for {rule_id} on {symbol}; only the owner unlocks it")
    s = splits["symbols"][symbol][split]
    end = s.get("end_utc") or datetime.now(timezone.utc).isoformat()
    return pd.Timestamp(s["start_utc"]), pd.Timestamp(end)


def ledger_rows(path: Path | None = None) -> list[dict]:
    path = path or LEDGER
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def prior_variants(rule_id: str, symbol: str, ledger: list[dict]) -> int:
    """Distinct OTHER (rule, market) pairs already read on exploration, across the proxy lab: each is a draw
    from the same histories, so the bar rises with them (same rule as lab/config/gates.json)."""
    return len({(r["rule"], r["symbol"]) for r in ledger
                if r["split"] == "exploration" and (r["rule"], r["symbol"]) != (rule_id, symbol)})


# ---------------------------------------------------------------------------------------------
# Metrics (share of notional: 1 unit per trade, the return of a trade is net / entry price)
# ---------------------------------------------------------------------------------------------

def metrics(trades: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, tz) -> dict:
    years = max((end - start).total_seconds() / (365.25 * 86400), 1e-9)
    n = len(trades)
    if n == 0:
        return {"trades": 0, "trades_per_year": 0.0, "net_return_pct": 0.0}
    t = trades.sort_values("exit_time").reset_index(drop=True)
    r_net = t["net_brl"] / t["entry_price"]
    r_gross = t["gross_brl"] / t["entry_price"]
    equity = (1.0 + r_net).cumprod()
    peak = equity.cummax().clip(lower=1.0)
    dd = float(((peak - equity) / peak).max())
    year = pd.to_datetime(t["exit_time"], utc=True).dt.tz_convert(tz).dt.year
    per_year = (1.0 + r_net).groupby(year).prod() - 1.0
    wins, losses = r_net[r_net > 0], r_net[r_net <= 0]
    daily = r_net.groupby(pd.to_datetime(t["exit_time"], utc=True).dt.tz_convert(tz).dt.date).sum()
    best = r_net.idxmax()
    hold = (pd.to_datetime(t["exit_time"]) - pd.to_datetime(t["entry_time"])).dt.total_seconds() / 60
    sd = float(daily.std(ddof=1)) if len(daily) > 2 else math.nan
    return {
        "trades": n,
        "trades_per_year": n / years,
        "mean_gross_pct": 100 * float(r_gross.mean()),
        "mean_net_pct": 100 * float(r_net.mean()),
        "net_return_pct": 100 * float(equity.iloc[-1] - 1.0),
        "net_return_excl_best_pct": 100 * float((1.0 + r_net.drop(index=best)).prod() - 1.0),
        "max_drawdown_pct": 100 * dd,
        "profit_factor": float(wins.sum() / -losses.sum()) if losses.sum() < 0 else math.inf,
        "win_rate_pct": 100 * len(wins) / n,
        "daily_sharpe_annualised": float(daily.mean() / sd * math.sqrt(252)) if sd and sd > 0 else math.nan,
        "positive_years_share": float((per_year > 0).mean()),
        "per_year_return_pct": {int(y): round(100 * float(v), 3) for y, v in per_year.items()},
        "long_trades": int((t["side"] == "long").sum()),
        "short_trades": int((t["side"] == "short").sum()),
        "median_hold_min": float(hold.median()),
        "exit_reasons": t["exit_reason"].value_counts().to_dict(),
    }


def gate_report(by_scenario: dict, gates: dict, variants: int) -> dict:
    g, fails = gates, []
    base, cons = by_scenario["base"], by_scenario["conservative"]
    if base["trades"] < g["minimum_trades"]:
        return {"decision": "inconclusive", "fails": [f"trades {base['trades']} < {g['minimum_trades']}"]}
    bar = g["net_return_pct_floor"] * (1 + g["per_variant_increase"] * variants)
    for name, m in (("base", base), ("conservative", cons)):
        if not m["net_return_pct"] > bar:
            fails.append(f"{name}: net {m['net_return_pct']:.2f}% <= bar {bar:.2f}%")
    if not base["net_return_excl_best_pct"] > 0:
        fails.append("base: net without the best trade <= 0")
    for name in g["drawdown_scenarios"]:
        if by_scenario[name]["max_drawdown_pct"] > g["max_drawdown_pct"]:
            fails.append(f"{name}: drawdown {by_scenario[name]['max_drawdown_pct']:.1f}% > {g['max_drawdown_pct']}%")
    if base["positive_years_share"] < g["positive_years_share"]:
        fails.append(f"base: positive years {base['positive_years_share']:.0%} < {g['positive_years_share']:.0%}")
    return {"decision": "rejected" if fails else "passed", "fails": fails, "net_bar_pct": bar}


# ---------------------------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------------------------

def evaluate(rule_id: str, symbol: str, split: str, *, data_dir: Path | None = None, record: bool = True) -> dict:
    splits, gates = _approved(SPLITS_PATH), _approved(GATES_PATH)
    ledger = ledger_rows()
    if split in ("validation", "final_test") and any(
            r["rule"] == rule_id and r["symbol"] == symbol and r["split"] == split for r in ledger):
        raise AlreadyRead(f"{rule_id} on {symbol}: {split} was already read; it is read once")
    start, end = split_window(symbol, split, splits, rule_id)
    mkt = market(symbol)
    rule = RULES[rule_id].on(symbol)
    bars = load_bars(symbol, f"{rule.timeframe_min}m", **({"data_dir": data_dir} if data_dir else {}))
    bars = session_only(bars, mkt)
    bars = bars[bars["time"] < end]
    first = bars.index[bars["time"] >= start]
    if len(first) == 0:
        raise ValueError(f"{symbol}: no bars in {split}")
    bars = bars.iloc[max(0, first[0] - rule.warmup):].reset_index(drop=True)     # warm-up from the earlier data
    cal = ProxySessionCalendar(mkt, rule.rules, infer_closed_days(bars, mkt))
    strategy = rule(cal)
    out = {"rule": rule_id, "strategy": strategy.name, "strategy_hash": strategy.hash, "symbol": symbol,
           "stands_for": mkt.stands_for, "split": split, "start_utc": str(start), "end_utc": str(end),
           "bars": len(bars), "cost_round_trip_base_pct": 100 * mkt.base_round_trip, "scenarios": {}}
    for scen in REQUIRED_SCENARIOS:
        res = run(bars, strategy, mkt.cost(scen), CONFIGS.get(rule_id, BacktestConfig()))
        tr = res.trades_frame()
        if not tr.empty:
            tr = tr[pd.to_datetime(tr["entry_time"], utc=True) >= start]
        out["scenarios"][scen] = metrics(tr, start, end, mkt.zone)
        out["scenarios"][scen]["vetoes"] = dict(res.vetoes)
        out["scenarios"][scen]["positions_held_overnight"] = res.positions_held_overnight
    variants = prior_variants(rule_id, symbol, ledger)
    out["prior_variants"] = variants
    out["gates"] = gate_report(out["scenarios"], gates, variants)
    out["read_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if record:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        with LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({k: out[k] for k in ("rule", "symbol", "split", "strategy_hash", "read_at_utc")}
                                | {"decision": out["gates"]["decision"]}) + "\n")
        name = f"{rule_id}-{symbol}-{split}-{out['read_at_utc'][:19].replace(':', '')}.json"
        (OUT_DIR / "results").mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "results" / name).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("rule", choices=sorted(RULES))
    r.add_argument("--symbols", required=True)
    r.add_argument("--split", default="exploration", choices=["exploration", "validation", "final_test"])
    a = ap.parse_args(argv)
    for sym in a.symbols.split(","):
        o = evaluate(a.rule, sym, a.split)
        b, c = o["scenarios"]["base"], o["scenarios"]["conservative"]
        print(f"{a.rule} {sym} {a.split}: {b['trades']} trades ({b['trades_per_year']:.0f}/yr), "
              f"gross/trade {b.get('mean_gross_pct', 0):.4f}%, net base {b['net_return_pct']:.2f}%, "
              f"net conservative {c['net_return_pct']:.2f}%, dd base {b.get('max_drawdown_pct', 0):.1f}% "
              f"-> {o['gates']['decision']} {o['gates']['fails']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
