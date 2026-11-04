"""Descriptive dossier of one strategy on one pair: rolling yearly windows (walk-forward of a FIXED rule).

The rules under study have no fitted parameters, so "walk-forward" here means: the same frozen rule is run on
consecutive non-overlapping calendar-year windows, each one out-of-sample with respect to every other window
(nothing is trained). It measures stability across regimes, not a re-optimisation.

Only the EXPLORATION split is read. The validation split stays locked unless a hypothesis passes exploration
(validation protocol v2); the final test is untouched.

For every window (base cost scenario, whole-balance stake and, separately, a risk-sized view):
  trades, win rate, profit factor, expectancy (ratio per trade), Sharpe, Sortino, max drawdown, return,
  and buy-and-hold over the same window.
Risk-sized view: each trade is re-weighted post hoc to risk RISK_PER_TRADE of the account at its own initial stop
(fraction = risk / stop distance, capped at 1.0, spot, no leverage) and compounded. It uses the exported trades only.

usage: python research/tools/dossier.py <Strategy> <label> [--pair BTC/USDT] [--exposure 1.0] [--timeframe 1h]
"""
import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import costs, runner  # noqa: E402

RISK_PER_TRADE = 0.01
OUT = ROOT / "research" / "dossiers"


def windows(pair: str, splits: dict) -> list[tuple[str, int, int]]:
    start = pd.Timestamp(splits["pairs"][pair]["exploration"]["start_utc"])
    end = pd.Timestamp(splits["pairs"][pair]["exploration"]["end_utc"])
    out = []
    for year in range(start.year, end.year + 1):
        a = max(start, pd.Timestamp(f"{year}-01-01", tz="UTC"))
        b = min(end, pd.Timestamp(f"{year}-12-31 23:00", tz="UTC"))
        if (b - a).days >= 60:
            out.append((str(year), int(a.timestamp()), int(b.timestamp())))
    out.append(("exploration", int(start.timestamp()), int(end.timestamp())))
    return out


def buy_and_hold(pair: str, timeframe: str, a: int, b: int) -> float:
    path = ROOT / "user_data" / "data" / "binance" / f"{pair.replace('/', '_')}-{timeframe}.feather"
    df = pd.read_feather(path)
    sel = df[(df["date"] >= pd.Timestamp(a, unit="s", tz="UTC")) & (df["date"] <= pd.Timestamp(b, unit="s", tz="UTC"))]
    if sel.empty:
        return float("nan")
    return float(sel["close"].iloc[-1] / sel["open"].iloc[0] - 1.0)


def risk_sized(trades: list[dict]) -> dict:
    balance, curve, peak, max_dd, used = 1.0, [1.0], 1.0, 0.0, []
    for t in sorted(trades, key=lambda t: t["open_date"]):
        stop_ratio = abs(float(t.get("initial_stop_loss_ratio") or 0.0))
        fraction = min(1.0, RISK_PER_TRADE / stop_ratio) if stop_ratio > 0 else 0.0
        used.append(fraction)
        balance *= 1.0 + fraction * float(t["profit_ratio"])
        peak = max(peak, balance)
        max_dd = max(max_dd, 1.0 - balance / peak)
    return {"return": balance - 1.0, "max_drawdown": max_dd, "mean_fraction": float(np.mean(used)) if used else 0.0}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("strategy")
    parser.add_argument("label")
    parser.add_argument("--pair", default="BTC/USDT")
    parser.add_argument("--exposure", type=float, default=1.0)
    parser.add_argument("--timeframe", default="1h")
    args = parser.parse_args()

    splits = runner.load_splits()
    base = costs.get_scenario("base")
    rows = []
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for label, a, b in windows(args.pair, splits):
        result = runner.run_backtest(
            experiment_id=f"dossier-{args.label}-{stamp}-{label}",
            strategy=args.strategy, timerange=f"{a}-{b}", fee=base.effective_fee_per_side, pair=args.pair,
            timeframe=args.timeframe, exposure=args.exposure,
        )
        row = {"window": label, "status": result.get("status")}
        if result.get("status") == "completed":
            stats = runner.read_strategy_stats(ROOT / result["artifact_path"])
            trades = runner.read_trades(ROOT / result["artifact_path"])
            row.update({
                "trades": stats.get("total_trades", 0),
                "win_rate": stats.get("winrate"),
                "profit_factor": stats.get("profit_factor"),
                "expectancy": stats.get("expectancy"),
                "expectancy_ratio": stats.get("expectancy_ratio"),
                "sharpe": stats.get("sharpe"),
                "sortino": stats.get("sortino"),
                "max_dd_account": stats.get("max_drawdown_account"),
                "profit_total": stats.get("profit_total"),
                "buy_and_hold": buy_and_hold(args.pair, args.timeframe, a, b),
                "risk_sized": risk_sized(trades),
                "exit_reasons": {k: v for k, v in pd.Series([t.get("exit_reason") for t in trades]).value_counts().items()},
            })
        rows.append(row)
        print(json.dumps({k: v for k, v in row.items() if k != "exit_reasons"}, default=str))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{args.label}.json").write_text(json.dumps({
        "strategy": args.strategy, "pair": args.pair, "timeframe": args.timeframe, "exposure": args.exposure,
        "cost_scenario": base.as_dict(), "split": "exploration (validation and final test not read)",
        "risk_per_trade": RISK_PER_TRADE, "rows": rows}, indent=2, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
