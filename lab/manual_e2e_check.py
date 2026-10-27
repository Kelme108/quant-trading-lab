"""Phase 1 end-to-end manual check: DonchianBreakoutBaseline (H-002) on the
exploration split, across all four cost scenarios, producing a manifest,
registry rows, and a gate decision.

This is a one-off verification script for the Phase 1 completion criterion,
not part of the orchestrator (that comes in Phase 3). Safe to re-run: it
creates a fresh experiment_id per run (timestamped) so it never collides
with or overwrites a prior manifest.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from lab import benchmarks, costs, gates, manifest, registry, runner

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "research"))
import validate_ohlcv  # noqa: E402

STRATEGY_FILE = "user_data/strategies/DonchianBreakoutBaseline.py"
STRATEGY_NAME = "DonchianBreakoutBaseline"
HYPOTHESIS_ID = "H-002"
SPLIT_NAME = "exploration"
FEATHER_PATH = ROOT / "user_data" / "data" / "binance" / "BTC_USDT-1h.feather"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def freqtrade_version() -> str:
    result = subprocess.run(
        ["docker", "compose", "run", "--rm", "freqtrade", "--version"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    for line in (result.stdout + result.stderr).splitlines():
        if "freqtrade" in line.lower():
            return line.strip()
    return "unknown"


def main() -> int:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    experiment_id = f"{timestamp}-donchian-h002-explore"
    print(f"experiment_id = {experiment_id}")

    splits = runner.load_splits()
    timerange = runner.resolve_split_timerange(SPLIT_NAME, splits)
    print(f"split = {SPLIT_NAME}, timerange = {timerange}")

    conn = registry.connect()
    registry.add_experiment(
        conn,
        experiment_id=experiment_id,
        hypothesis_id=HYPOTHESIS_ID,
        strategy_file=STRATEGY_FILE,
        strategy_sha256=sha256_file(ROOT / STRATEGY_FILE),
        cost_scenario="multi:optimistic,base,conservative,stress",
        split=SPLIT_NAME,
        command="see raw/*.stdout.txt per cost scenario",
        created_at_utc=datetime.now(timezone.utc).isoformat(),
    )
    registry.set_experiment_status(conn, experiment_id, "running")

    all_metrics: dict = {}
    per_scenario_commands = []
    base_bt_metrics: dict = {}

    for scenario in costs.all_required_scenarios():
        print(f"--- cost scenario: {scenario.name} (effective fee/side={scenario.effective_fee_per_side}) ---")
        bt_metrics = runner.run_backtest(
            experiment_id=experiment_id,
            strategy=STRATEGY_NAME,
            timerange=timerange,
            fee=scenario.effective_fee_per_side,
        )
        per_scenario_commands.append(bt_metrics.get("command", ""))
        if bt_metrics.get("status") != "completed":
            print(f"backtest FAILED for scenario {scenario.name}: {bt_metrics}")
            registry.set_experiment_status(conn, experiment_id, "failed")
            return 1

        if scenario.name == "base":
            base_bt_metrics = bt_metrics

        suffix = scenario.name
        all_metrics[f"trades__{suffix}"] = bt_metrics["total_trades"]
        all_metrics[f"net_profit_quote__{suffix}"] = bt_metrics["net_profit_quote"]
        all_metrics[f"net_profit_excl_best_trade__{suffix}"] = bt_metrics["net_profit_excl_best_trade"]
        all_metrics[f"max_drawdown_pct__{suffix}"] = bt_metrics["max_drawdown_pct"]
        print(
            f"  trades={bt_metrics['total_trades']} "
            f"net_profit={bt_metrics['net_profit_quote']:.4f} "
            f"max_dd%={bt_metrics['max_drawdown_pct']:.4f}"
        )

    print("--- lookahead-analysis (base scenario fee) ---")
    base_scenario = costs.get_scenario("base")
    lookahead_metrics = runner.run_lookahead_analysis(
        experiment_id=experiment_id,
        strategy=STRATEGY_NAME,
        timerange=timerange,
        fee=base_scenario.effective_fee_per_side,
    )
    print(f"  has_bias={lookahead_metrics.get('lookahead_has_bias')}")
    all_metrics["lookahead_has_bias"] = lookahead_metrics.get("lookahead_has_bias")

    print("--- recursive-analysis ---")
    recursive_metrics = runner.run_recursive_analysis(
        experiment_id=experiment_id,
        strategy=STRATEGY_NAME,
        timerange=timerange,
    )
    print(f"  is_stable={recursive_metrics.get('recursive_is_stable')}")
    all_metrics["recursive_is_stable"] = recursive_metrics.get("recursive_is_stable")

    print("--- benchmarks ---")
    split = splits[SPLIT_NAME]
    bench = benchmarks.compute_benchmarks(FEATHER_PATH, split["start_utc"], split["end_utc"])
    all_metrics["benchmark_cash_return_pct"] = bench["cash"]["return_pct"]
    all_metrics["benchmark_buy_and_hold_return_pct"] = bench["buy_and_hold"]["return_pct"]
    print(f"  cash={bench['cash']['return_pct']}% buy_and_hold={bench['buy_and_hold']['return_pct']:.2f}%")

    registry.record_metrics(conn, experiment_id, all_metrics)
    registry.set_experiment_status(conn, experiment_id, "completed")

    decision, reasons = gates.decide(all_metrics)
    registry.record_decision(
        conn,
        experiment_id=experiment_id,
        decision=decision,
        reasons=reasons,
        gates_sha256=gates.gates_sha256(),
        decided_at_utc=datetime.now(timezone.utc).isoformat(),
    )
    print(f"\nDECISION = {decision}")
    for reason in reasons:
        print(f"  - {reason}")

    manifest_data = manifest.default_manifest_skeleton()
    manifest_data["experiment_id"] = experiment_id
    manifest_data["created_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest_data["code"]["repository_state"] = "git"
    manifest_data["code"]["strategy_file"] = STRATEGY_FILE
    manifest_data["code"]["strategy_sha256"] = sha256_file(ROOT / STRATEGY_FILE)
    manifest_data["code"]["config_sha256_redacted"] = sha256_file(
        ROOT / "user_data" / "config.dryrun.json"
    )
    manifest_data["runtime"]["freqtrade_version"] = freqtrade_version()
    manifest_data["runtime"]["host"] = "Windows 11 / Git Bash (MSYS2), Docker Desktop"
    manifest_data["runtime"]["command"] = " | ".join(per_scenario_commands)
    manifest_data["backtest"]["requested_timerange"] = timerange
    manifest_data["backtest"]["strategy"] = STRATEGY_NAME
    manifest_data["backtest"]["fee_rate_per_side"] = base_scenario.fee_per_side
    manifest_data["backtest"]["slippage_rate_per_side"] = base_scenario.slippage_per_side
    manifest_data["backtest"]["spread_rate"] = base_scenario.spread_total
    ohlcv_report = validate_ohlcv.validate(FEATHER_PATH, timeframe="1h")
    manifest_data["data"]["path"] = str(FEATHER_PATH.relative_to(ROOT)).replace("\\", "/")
    manifest_data["data"]["sha256"] = ohlcv_report["sha256"]
    manifest_data["data"]["source"] = "Binance public OHLCV through Freqtrade download-data"
    manifest_data["data"]["first_candle_utc"] = ohlcv_report["first_candle_utc"]
    manifest_data["data"]["last_complete_candle_utc"] = ohlcv_report["last_candle_utc"]
    manifest_data["data"]["candle_count"] = ohlcv_report["rows"]
    manifest_data["data"]["gaps"] = ohlcv_report["gaps"]
    manifest_data["data"]["duplicates"] = ohlcv_report["duplicate_timestamps"]

    manifest_data["backtest"]["effective_timerange"] = (
        f"{base_bt_metrics.get('backtest_start', '')} -> {base_bt_metrics.get('backtest_end', '')}"
    )
    manifest_data["backtest"]["order_types"] = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
    }

    manifest_data["validation"]["lookahead_analysis"] = str(lookahead_metrics.get("lookahead_has_bias"))
    manifest_data["validation"]["recursive_analysis"] = str(recursive_metrics.get("recursive_is_stable"))
    manifest_data["validation"]["benchmarks"] = (
        f"cash={bench['cash']['return_pct']}%, buy_and_hold={bench['buy_and_hold']['return_pct']:.4f}%"
    )
    manifest_data["validation"]["hypotheses_tested_before"] = registry.count_variants_in_family(
        conn, STRATEGY_NAME
    )
    manifest_data["result"]["artifact"] = base_bt_metrics.get("artifact_path", "")
    manifest_data["result"]["trades"] = all_metrics.get("trades__base")
    manifest_data["result"]["net_profit_quote"] = all_metrics.get("net_profit_quote__base")
    manifest_data["result"]["decision"] = decision
    manifest_data["result"]["notes"] = "Phase 1 manual end-to-end verification run."

    manifest_path = manifest.write_manifest(experiment_id, manifest_data)
    print(f"\nmanifest written to {manifest_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
