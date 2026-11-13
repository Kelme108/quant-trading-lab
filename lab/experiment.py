"""Run one hypothesis on one (pair, split) and decide it.

run_experiment() executes the four cost scenarios, lookahead-analysis,
recursive-analysis and the benchmarks, stores the metrics, and writes the
(immutable) manifest. It does not decide: decide_experiment() applies the
frozen gates to the stored metrics and records the verdict. Keeping the two
apart lets the orchestrator run a split and decide it as separate steps.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from lab import benchmarks, costs, gates, manifest, registry, runner

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "research"))
import validate_ohlcv  # noqa: E402


class ExperimentFailed(RuntimeError):
    """A backtest (or another required step) did not complete."""


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


def compose_image() -> str:
    """The image name pinned in docker-compose.yml (the tag is never `stable`)."""
    match = re.search(r"^\s*image:\s*(\S+)", (ROOT / "docker-compose.yml").read_text(encoding="utf-8"), re.M)
    return match.group(1) if match else ""


def runtime_fingerprint(run=subprocess.run) -> dict:
    """Image digest and ccxt version for the manifest. Best effort: a value that
    cannot be read stays empty and never fails an experiment."""
    image = compose_image()
    out = {"docker_image_digest": "", "ccxt_version": ""}
    if not image:
        return out
    try:
        inspect = run(
            ["docker", "image", "inspect", image, "--format", "{{.Id}} {{join .RepoDigests \",\"}}"],
            capture_output=True, text=True, check=True,
        )
        out["docker_image_digest"] = inspect.stdout.strip()
        ccxt = run(
            ["docker", "run", "--rm", "--entrypoint", "python", image, "-c", "import ccxt;print(ccxt.__version__)"],
            capture_output=True, text=True, check=True,
        )
        out["ccxt_version"] = ccxt.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        pass
    return out


def feather_path(pair: str, timeframe: str = "1h") -> Path:
    return ROOT / "user_data" / "data" / "binance" / f"{pair.replace('/', '_')}-{timeframe}.feather"


def experiment_id_for(timestamp: str, hypothesis_id: str, split_name: str, pair: str) -> str:
    return f"{timestamp}-{hypothesis_id.lower()}-{split_name}-{pair.replace('/', '-').lower()}"


def experiment_dir(experiment_id: str) -> Path:
    return runner.EXPERIMENTS_DIR / experiment_id


def run_experiment(
    conn,
    *,
    hypothesis_id: str,
    strategy_name: str,
    strategy_file: str,
    pair: str,
    split_name: str,
    timestamp: str,
    splits: dict,
    version: str,
    notes: str = "",
    exposure: float = 1.0,
    timeframe: str = "1h",
) -> str:
    """Run the experiment and return its id. Raises ExperimentFailed on a failed
    backtest, after marking the experiment row `failed`."""
    experiment_id = experiment_id_for(timestamp, hypothesis_id, split_name, pair)
    timerange = runner.resolve_split_timerange(split_name, splits, pair=pair)
    split = splits["pairs"][pair][split_name]
    print(f"\n===== {pair} / {split_name}: {experiment_id} =====")
    print(f"window {split['start_utc']} -> {split['end_utc']}, timerange {timerange}")

    registry.add_experiment(
        conn,
        experiment_id=experiment_id,
        hypothesis_id=hypothesis_id,
        strategy_file=strategy_file,
        strategy_sha256=sha256_file(ROOT / strategy_file),
        cost_scenario="multi:optimistic,base,conservative,stress",
        split=split_name,
        command="see raw/*.stdout.txt per cost scenario",
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        pair=pair,
    )
    registry.set_experiment_status(conn, experiment_id, "running")

    all_metrics: dict = {"exposure": exposure}
    commands: list[str] = []
    base_bt: dict = {}

    for scenario in costs.all_required_scenarios():
        bt = runner.run_backtest(
            experiment_id=experiment_id,
            strategy=strategy_name,
            timerange=timerange,
            fee=scenario.effective_fee_per_side,
            pair=pair,
            exposure=exposure,
            timeframe=timeframe,
        )
        commands.append(bt.get("command", ""))
        if bt.get("status") != "completed":
            registry.set_experiment_status(conn, experiment_id, "failed")
            raise ExperimentFailed(f"{experiment_id}: backtest failed in scenario {scenario.name}: {bt}")
        if scenario.name == "base":
            base_bt = bt
        all_metrics[f"trades__{scenario.name}"] = bt["total_trades"]
        all_metrics[f"net_profit_quote__{scenario.name}"] = bt["net_profit_quote"]
        all_metrics[f"net_profit_excl_best_trade__{scenario.name}"] = bt["net_profit_excl_best_trade"]
        all_metrics[f"max_drawdown_pct__{scenario.name}"] = bt["max_drawdown_pct"]
        all_metrics[f"max_relative_drawdown_pct__{scenario.name}"] = bt["max_relative_drawdown_pct"]
        print(
            f"  {pair} {scenario.name:12s} trades={bt['total_trades']:5d} "
            f"net_profit={bt['net_profit_quote']:10.2f} max_dd%={bt['max_drawdown_pct']:6.1f}"
        )

    base_scenario = costs.get_scenario("base")
    lookahead = runner.run_lookahead_analysis(
        experiment_id=experiment_id,
        strategy=strategy_name,
        timerange=timerange,
        fee=base_scenario.effective_fee_per_side,
        pair=pair,
        timeframe=timeframe,
    )
    all_metrics["lookahead_has_bias"] = lookahead.get("lookahead_has_bias")
    recursive = runner.run_recursive_analysis(
        experiment_id=experiment_id, strategy=strategy_name, timerange=timerange, pair=pair,
        timeframe=timeframe,
    )
    all_metrics["recursive_is_stable"] = recursive.get("recursive_is_stable")
    print(
        f"  {pair} lookahead has_bias={all_metrics['lookahead_has_bias']} "
        f"recursive stable={all_metrics['recursive_is_stable']}"
    )

    data_path = feather_path(pair, timeframe)
    bench = benchmarks.compute_benchmarks(data_path, split["start_utc"], split["end_utc"])
    all_metrics["benchmark_cash_return_pct"] = bench["cash"]["return_pct"]
    all_metrics["benchmark_buy_and_hold_return_pct"] = bench["buy_and_hold"]["return_pct"]
    print(f"  buy_and_hold={bench['buy_and_hold']['return_pct']:.1f}% cash=0%")

    registry.record_metrics(conn, experiment_id, all_metrics)
    registry.set_experiment_status(
        conn, experiment_id, "completed", artifact_path=base_bt.get("artifact_path")
    )

    gap_tolerance = runner.max_gap_hours()
    ohlcv = validate_ohlcv.validate(data_path, timeframe=timeframe, max_gap_hours=gap_tolerance)
    prior = registry.count_prior_variants(conn, hypothesis_id)

    data = manifest.default_manifest_skeleton()
    data["experiment_id"] = experiment_id
    data["created_at_utc"] = datetime.now(timezone.utc).isoformat()
    data["code"]["repository_state"] = "git"
    data["code"]["strategy_file"] = strategy_file
    data["code"]["strategy_sha256"] = sha256_file(ROOT / strategy_file)
    data["code"]["config_sha256_redacted"] = sha256_file(ROOT / "user_data" / "config.dryrun.json")
    data["runtime"]["freqtrade_version"] = version
    data["runtime"].update(runtime_fingerprint())
    data["runtime"]["host"] = "Windows 11 / Docker Desktop"
    data["runtime"]["command"] = " | ".join(commands)
    data["market"]["pair"] = pair
    data["market"]["timeframe"] = timeframe
    data["backtest"]["requested_timerange"] = timerange
    data["backtest"]["effective_timerange"] = (
        f"{base_bt.get('backtest_start', '')} -> {base_bt.get('backtest_end', '')}"
    )
    data["backtest"]["strategy"] = strategy_name
    data["backtest"]["fee_rate_per_side"] = base_scenario.fee_per_side
    data["backtest"]["slippage_rate_per_side"] = base_scenario.slippage_per_side
    data["backtest"]["spread_rate"] = base_scenario.spread_total
    data["backtest"]["initial_wallet"] = runner.BACKTEST_WALLET
    data["backtest"]["order_types"] = {"entry": "limit", "exit": "limit", "stoploss": "market"}
    data["data"]["path"] = str(data_path.relative_to(ROOT)).replace("\\", "/")
    data["data"]["sha256"] = ohlcv["sha256"]
    data["data"]["source"] = "Binance public OHLCV through Freqtrade download-data"
    data["data"]["first_candle_utc"] = ohlcv["first_candle_utc"]
    data["data"]["last_complete_candle_utc"] = ohlcv["last_candle_utc"]
    data["data"]["candle_count"] = ohlcv["rows"]
    data["data"]["gaps"] = ohlcv["gaps"]
    data["data"]["duplicates"] = ohlcv["duplicate_timestamps"]
    data["validation"]["lookahead_analysis"] = str(all_metrics["lookahead_has_bias"])
    data["validation"]["recursive_analysis"] = str(all_metrics["recursive_is_stable"])
    data["validation"]["benchmarks"] = (
        f"cash=0.0%, buy_and_hold={bench['buy_and_hold']['return_pct']:.4f}%"
    )
    data["validation"]["hypotheses_tested_before"] = prior
    data["result"]["artifact"] = base_bt.get("artifact_path", "")
    data["result"]["trades"] = all_metrics.get("trades__base")
    data["result"]["net_profit_quote"] = all_metrics.get("net_profit_quote__base")
    data["result"]["decision"] = "pending (see research/lab.sqlite decisions and decision.json)"
    data["result"]["notes"] = (
        f"{hypothesis_id} {split_name} split of {pair}. Data file has {ohlcv['gaps']} gap(s), all "
        f"within the {gap_tolerance}h tolerance in scenarios.json (largest "
        f"{ohlcv['largest_gap_missing_hours']}h); not filled. {notes}"
    ).strip()
    manifest.write_manifest(experiment_id, data)
    return experiment_id


def decide_experiment(conn, experiment_id: str, hypothesis_id: str) -> tuple[str, list[str]]:
    """Apply the frozen gates to a completed experiment's stored metrics, record
    the verdict, and write decision.json next to its artifacts."""
    experiment = registry.get_experiment(conn, experiment_id)
    if experiment is None or experiment["status"] != "completed":
        raise ExperimentFailed(f"{experiment_id} is not a completed experiment")

    metrics = registry.get_metrics(conn, experiment_id)
    prior = registry.count_prior_variants(conn, hypothesis_id)
    decision, reasons = gates.decide(metrics, variants_tested_in_family=prior)
    decided_at = datetime.now(timezone.utc).isoformat()
    registry.record_decision(
        conn,
        experiment_id=experiment_id,
        decision=decision,
        reasons=reasons,
        gates_sha256=gates.gates_sha256(),
        decided_at_utc=decided_at,
    )

    directory = experiment_dir(experiment_id)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "decision.json").write_text(
        json.dumps(
            {
                "experiment_id": experiment_id,
                "hypothesis_id": hypothesis_id,
                "pair": experiment["pair"],
                "split": experiment["split"],
                "decision": decision,
                "variants_tested_in_family": prior,
                "gates_sha256": gates.gates_sha256(),
                "decided_at_utc": decided_at,
                "reasons": reasons,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return decision, reasons
