"""Step 1.4: does vol_regime help? Ablation on the exploration (IS) window only, costs base and base_2x.

Reads only each pair's exploration split (never validation, never the holdout). Strategies come from
regime_strategies.py (written to the strategy path for the run and removed). The equity curve is rebuilt from the
exported trades (lab/returns.py), marked on the 1h closes.

Criterion fixed BEFORE running (docs/prompt-proxima-etapa.md, step 1.4), per family:
  a pair "benefits" if, at base_2x over the IS window, Sharpe(with) > Sharpe(without) AND maxDD(with) < maxDD(without),
  and Sharpe(with) < Sharpe(without) in at most 2 of the 5 cycles;
  the family shows benefit if >= 2 of 3 pairs benefit. vol_regime is switched on by default only if BOTH families do.
Fairness: vol_regime needs ~395 daily candles, so for every pair all windows start no earlier than the first day the
filter is defined; both arms are always compared on the identical window. Windows under 90 days are not scored.
Cycles are clipped to the IS end (2023+ ends at the IS end, not at the cut-off).
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from lab import costs, cycles, returns, runner  # noqa: E402
import regime_strategies  # noqa: E402
from baseline_cycles import load_hourly  # noqa: E402

STRATS = ROOT / "user_data" / "strategies"
OUT = ROOT / "research" / "baselines"
FAMILIES = {"sma200": "1h", "donchian": "4h"}
SCENARIOS = ("base", "base_2x")
MIN_DAYS = 90
MEDIAN_DEFINED_AT = 30 + 365 - 1  # daily index of the first defined vol/median


def regime_start(pair: str) -> pd.Timestamp:
    daily = pd.read_feather(ROOT / "user_data" / "data" / "binance" / f"{pair.replace('/', '_')}-1d.feather")
    daily["date"] = pd.to_datetime(daily["date"], utc=True)
    return daily["date"].sort_values().iloc[MEDIAN_DEFINED_AT] + pd.Timedelta(days=1)


def summary(equity: pd.Series, start, end) -> dict | None:
    part = equity[(equity.index >= start) & (equity.index <= end)]
    if len(part) < MIN_DAYS * 24:
        return None
    return returns.summarise(part / part.iloc[0])


def main() -> int:
    splits = runner.load_splits()
    result = {"criterion": __doc__, "pairs": {}, "validation_read": False, "holdout_read": False}
    for pair in runner.enabled_pairs():
        exploration = splits["pairs"][pair]["exploration"]
        is_start = pd.Timestamp(exploration["start_utc"])
        is_end = pd.Timestamp(exploration["end_utc"])
        floor = max(is_start, regime_start(pair))
        windows = {f"cycle {k}": (max(a, floor), min(b, is_end)) for k, (a, b) in cycles.cycles().items()}
        windows["IS (from filter start)"] = (floor, is_end)
        hourly = load_hourly(pair)
        hourly = hourly[hourly["date"] <= is_end]
        timerange = exploration["timerange"]
        equities, counts = {}, {}
        for family, tf in FAMILIES.items():
            for use_vol in (False, True):
                name = f"Abl{family.capitalize()}{'On' if use_vol else 'Off'}"
                path = STRATS / f"{name}.py"
                path.write_text(regime_strategies.source(family, use_vol, name), encoding="utf-8")
                try:
                    for scenario in SCENARIOS:
                        fee = costs.get_scenario(scenario).effective_fee_per_side
                        run = runner.run_backtest(
                            experiment_id=f"ablation-regime-{name.lower()}-{pair.replace('/', '-').lower()}-{scenario}",
                            strategy=name, timerange=timerange, fee=fee, pair=pair, timeframe=tf)
                        if run.get("status") != "completed":
                            print("FAILED", name, pair, scenario, run)
                            return 2
                        trades = runner.read_trades(ROOT / run["artifact_path"])
                        equities[(family, use_vol, scenario)] = returns.equity_curve(trades, hourly, fee_per_side=fee)
                        counts[(family, use_vol, scenario)] = len(trades)
                        print(pair, name, scenario, "trades", len(trades), flush=True)
                finally:
                    path.unlink(missing_ok=True)
        table = {}
        for family in FAMILIES:
            for scenario in SCENARIOS:
                for window, (a, b) in windows.items():
                    off = summary(equities[(family, False, scenario)], a, b)
                    on = summary(equities[(family, True, scenario)], a, b)
                    table[f"{family}|{scenario}|{window}"] = {
                        "start": str(a), "end": str(b), "without": off, "with": on,
                        "trades_without": counts[(family, False, scenario)], "trades_with": counts[(family, True, scenario)]}
        result["pairs"][pair] = table
    # verdict
    verdict = {}
    for family in FAMILIES:
        benefits = {}
        for pair, table in result["pairs"].items():
            whole = table[f"{family}|base_2x|IS (from filter start)"]
            worse = valid = 0
            for window in [w for w in cycles.cycles()]:
                row = table[f"{family}|base_2x|cycle {window}"]
                if row["without"] and row["with"]:
                    valid += 1
                    worse += row["with"]["sharpe_annualised"] < row["without"]["sharpe_annualised"]
            ok = bool(whole["with"] and whole["without"]
                      and whole["with"]["sharpe_annualised"] > whole["without"]["sharpe_annualised"]
                      and whole["with"]["max_drawdown"] < whole["without"]["max_drawdown"] and worse <= 2)
            benefits[pair] = {"benefit": ok, "cycles_scored": valid, "cycles_sharpe_worse": int(worse)}
        verdict[family] = {"pairs": benefits, "family_benefit": sum(v["benefit"] for v in benefits.values()) >= 2}
    verdict["vol_regime_on_by_default"] = all(verdict[f]["family_benefit"] for f in FAMILIES)
    result["verdict"] = verdict
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "regime-ablation.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(verdict, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
