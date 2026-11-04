"""Baselines by market cycle: buy-and-hold vs Sma200Baseline (daily SMA200, 1h execution), costs 1x and 2x.

Reads only data before the prospective holdout (lab/cycles.assert_before_holdout). One backtest per pair and cost
scenario over the whole history; the equity curve is rebuilt from the exported trades (lab/returns.py) and sliced
into cycles and into the labelled periods (IS / OOS / last 12 months). Positions that straddle a boundary are cut
there (mark-to-market), so windows are comparable with buy-and-hold.

Self-check: the rebuilt equity must reproduce Freqtrade's own total profit for the whole run.

usage: python research/tools/baseline_cycles.py [--strategy Sma200Baseline]
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import costs, cycles, returns, runner, stats  # noqa: E402

OUT = ROOT / "research" / "baselines"
SCENARIOS = ("base", "base_2x")


def load_hourly(pair: str) -> pd.DataFrame:
    frame = pd.read_feather(ROOT / "user_data" / "data" / "binance" / f"{pair.replace('/', '_')}-1h.feather")
    frame["date"] = pd.to_datetime(frame["date"], utc=True)
    return frame.sort_values("date").reset_index(drop=True)


def window_summary(equity: pd.Series, start, end) -> dict:
    part = equity[(equity.index >= start) & (equity.index <= end)]
    if len(part) < 48:
        return {"note": "no data"}
    rebased = part / part.iloc[0]
    out = returns.summarise(rebased)
    out["return"] = float(rebased.iloc[-1] - 1.0)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", default="Sma200Baseline")
    parser.add_argument("--exposure", type=float, default=1.0)
    parser.add_argument("--label", default="sma200")
    args = parser.parse_args()
    splits = runner.load_splits()
    cutoff = cycles.prospective_start()
    result = {"strategy": args.strategy, "exposure": args.exposure, "scenarios": {}, "cost_table": costs.cost_table(),
              "prospective_holdout_read": False}
    for pair in runner.enabled_pairs():
        hourly = load_hourly(pair)
        hourly = hourly[hourly["date"] < cutoff]
        end = hourly["date"].iloc[-1]
        cycles.assert_before_holdout(end)
        windows = {**{f"cycle {k}": v for k, v in cycles.cycles().items()}, **cycles.labelled_periods(pair, splits)}
        timerange = f"{hourly['date'].iloc[0].strftime('%Y%m%d')}-{cutoff.strftime('%Y%m%d')}"
        for name in SCENARIOS:
            scenario = costs.get_scenario(name)
            fee = scenario.effective_fee_per_side
            run = runner.run_backtest(experiment_id=f"baseline-{args.label}-{pair.replace('/', '-').lower()}-{name}",
                                      strategy=args.strategy, timerange=timerange, fee=fee, pair=pair, exposure=args.exposure)
            if run.get("status") != "completed":
                print("failed", pair, name, run)
                return 2
            zip_path = ROOT / run["artifact_path"]
            trades = runner.read_trades(zip_path)
            stats_ft = runner.read_strategy_stats(zip_path)
            equity = returns.equity_curve(trades, hourly, exposure=args.exposure, fee_per_side=fee)
            check = {"freqtrade_profit_total": stats_ft.get("profit_total"), "rebuilt_return": float(equity.iloc[-1] - 1.0)}
            hold_full = returns.buy_and_hold_equity(hourly, start=hourly["date"].iloc[0], end=end, fee_per_side=fee)
            rows = {}
            for window, (start, stop) in windows.items():
                stop = min(stop, end)
                hold = window_summary(returns.buy_and_hold_equity(hourly, start=start, end=stop, fee_per_side=fee), start, stop)
                strat = window_summary(equity, start, stop)
                rows[window] = {"strategy": strat, "buy_and_hold": hold,
                                "trades": sum(1 for t in trades if start <= pd.Timestamp(t["open_date"]) <= stop)}
            daily = returns.daily_returns(equity)
            rows["full history"] = {"strategy": returns.summarise(equity), "buy_and_hold": returns.summarise(hold_full),
                                    "trades": len(trades),
                                    "dsr_1_trial": stats.deflated_sharpe(daily.to_numpy(), 1, 0.0)}
            result["scenarios"].setdefault(name, {})[pair] = {"windows": rows, "self_check": check,
                                                              "trades_ci_mean_trade_return": stats.block_bootstrap_ci(
                                                                  [float(t["profit_ratio"]) for t in trades], lambda x: float(x.mean()), block=3)}
            print(pair, name, "trades", len(trades), "freqtrade", round(check["freqtrade_profit_total"], 4),
                  "rebuilt", round(check["rebuilt_return"], 4), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{args.label}-cycles.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
