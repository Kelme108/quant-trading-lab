"""Builds and runs Freqtrade commands via docker compose, as argv lists
(never shell=True), and reads metrics only from the files Freqtrade itself
exports — never from LLM-generated text.

The compose file only mounts ./user_data into the container, so Freqtrade
can only write under user_data/. This module runs the command with output
inside user_data/backtest_results/<experiment_id>/, then copies the raw
stdout/stderr and exported artifacts into research/experiments/<experiment_id>/raw/
on the host side, where the rest of the lab (and research/) can see them.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).parents[1]
USER_DATA = ROOT / "user_data"
EXPERIMENTS_DIR = ROOT / "research" / "experiments"
CONTAINER_USER_DATA = "/freqtrade/user_data"

SPLITS_PATH = Path(__file__).parent / "config" / "splits.json"
SCENARIOS_PATH = Path(__file__).parent / "config" / "scenarios.json"


def load_scenarios(scenarios_path: Path = SCENARIOS_PATH) -> dict:
    return json.loads(scenarios_path.read_text(encoding="utf-8"))


def enabled_pairs(scenarios: dict | None = None) -> list[str]:
    """Pairs marked enabled in scenarios.json, in file order.

    An empty result is an error, not "nothing to do": a cycle that silently
    tests no pair would look like a clean run.
    """
    if scenarios is None:
        scenarios = load_scenarios()
    pairs = [entry["pair"] for entry in scenarios["pairs"] if entry.get("enabled") is True]
    if not pairs:
        raise ValueError("no pair is enabled in lab/config/scenarios.json")
    return pairs


def max_gap_hours(scenarios: dict | None = None) -> float:
    """Gap tolerance (missing hours) for validate_ohlcv; see scenarios.json."""
    if scenarios is None:
        scenarios = load_scenarios()
    return float(scenarios["data_quality"]["max_gap_hours"])


def enabled_timeframes(scenarios: dict | None = None) -> list[str]:
    if scenarios is None:
        scenarios = load_scenarios()
    timeframes = [
        entry["timeframe"] for entry in scenarios["timeframes"] if entry.get("enabled") is True
    ]
    if not timeframes:
        raise ValueError("no timeframe is enabled in lab/config/scenarios.json")
    return timeframes


class FinalTestLockedError(RuntimeError):
    """Raised when something tries to run the final_test split while locked."""


def _docker_env() -> dict:
    """Environment for subprocess calls to docker compose.

    MSYS_NO_PATHCONV=1 stops Git Bash/MSYS2 on Windows from rewriting
    /freqtrade/... container paths into host paths (observed turning
    `/freqtrade/user_data/data/binance` into a bogus host directory).
    Harmless to set on any other shell/OS.
    """
    env = dict(os.environ)
    env["MSYS_NO_PATHCONV"] = "1"
    return env


def run_compose(args: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess:
    """Run `docker compose run --rm freqtrade <args...>` as an argv list.

    Freqtrade's Rich-formatted output uses box-drawing characters that are
    not representable in the Windows console's default cp1252 codec, which
    Python's subprocess otherwise inherits for text-mode pipes. Decoding is
    forced to UTF-8 (with replacement for anything still undecodable)
    regardless of host OS.
    """
    argv = ["docker", "compose", "run", "--rm", "freqtrade", *args]
    return subprocess.run(
        argv,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_docker_env(),
        check=False,
    )


def load_splits(splits_path: Path = SPLITS_PATH) -> dict:
    return json.loads(splits_path.read_text(encoding="utf-8"))


def resolve_split_timerange(
    split_name: str, splits: dict | None = None, pair: str | None = None
) -> str:
    """Returns the Freqtrade --timerange string for a named split.

    Refuses final_test while splits.json marks it locked — this is the
    enforcement point the task requires; nothing downstream can bypass it
    by calling run_compose directly without going through here, since this
    is the only place that turns a split name into a timerange.

    exploration and validation are per pair, so `pair` is required for them.
    final_test is the same open-ended window for every pair.
    """
    if splits is None:
        splits = load_splits()
    if split_name not in ("exploration", "validation", "final_test"):
        raise ValueError(f"unknown split '{split_name}'")

    if split_name == "final_test":
        split = splits["final_test"]
        if not split.get("final_test_unlocked", False):
            raise FinalTestLockedError(
                "final_test split is locked in lab/config/splits.json "
                "(final_test_unlocked: false). Only the user may unlock it."
            )
        return split["timerange"]

    if pair is None:
        raise ValueError(f"split '{split_name}' is per pair: pass pair=")
    if pair not in splits["pairs"]:
        raise KeyError(f"splits.json has no boundaries for {pair}")
    return splits["pairs"][pair][split_name]["timerange"]


def raw_dir(experiment_id: str) -> Path:
    directory = EXPERIMENTS_DIR / experiment_id / "raw"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _save_process_output(experiment_id: str, label: str, result: subprocess.CompletedProcess) -> None:
    out_dir = raw_dir(experiment_id)
    (out_dir / f"{label}.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (out_dir / f"{label}.stderr.txt").write_text(result.stderr, encoding="utf-8")
    (out_dir / f"{label}.returncode.txt").write_text(str(result.returncode), encoding="utf-8")


def run_backtest(
    *,
    experiment_id: str,
    strategy: str,
    timerange: str,
    fee: float,
    pair: str = "BTC/USDT",
    timeframe: str = "1h",
    dry_run_wallet: float = 100.0,
    stake_amount: float | str = "unlimited",
) -> dict:
    """Runs `backtesting --export trades`, saves raw output + artifacts, and
    returns parsed metrics read from the exported zip (never from stdout text).

    The stake defaults to "unlimited" (the whole available balance, one open
    trade at a time) on purpose. A fixed stake equal to the wallet (100 on a
    100 USDT wallet) silently stops all trading after the first losing trade,
    because the balance then falls below the stake: the same Donchian run on
    ETH/USDT made 1 trade with a fixed 100 and 284 with "unlimited". Trade
    counts, and therefore the minimum-trades gate, are meaningless otherwise.
    """
    export_dir_name = f"experiments/{experiment_id}"
    container_export_dir = f"{CONTAINER_USER_DATA}/backtest_results/{export_dir_name}"
    host_export_dir = USER_DATA / "backtest_results" / export_dir_name
    # Freqtrade does not create intermediate directories for
    # --export-directory; the shared volume means creating it on the host
    # also creates it inside the container.
    host_export_dir.mkdir(parents=True, exist_ok=True)

    args = [
        "backtesting",
        "--config", f"{CONTAINER_USER_DATA}/config.dryrun.json",
        "--strategy", strategy,
        "--strategy-path", f"{CONTAINER_USER_DATA}/strategies",
        "--timeframe", timeframe,
        "--pairs", pair,
        "--timerange", timerange,
        "--dry-run-wallet", str(dry_run_wallet),
        "--stake-amount", str(stake_amount),
        "--fee", str(fee),
        "--export", "trades",
        "--export-directory", container_export_dir,
        "--cache", "none",
        # Without this flag Freqtrade silently ignores a strategy's `protections`
        # (e.g. a cooldown), so the backtest would not trade the declared rule.
        "--enable-protections",
    ]
    result = run_compose(args)
    _save_process_output(experiment_id, "backtesting", result)

    artifact_zip = _latest_zip(host_export_dir)
    metrics = {"command": " ".join(["docker", "compose", "run", "--rm", "freqtrade", *args])}

    if result.returncode != 0 or artifact_zip is None:
        metrics.update({"status": "failed", "returncode": result.returncode})
        return metrics

    dest_zip = raw_dir(experiment_id) / artifact_zip.name
    shutil.copy2(artifact_zip, dest_zip)
    metrics.update(_read_backtest_zip(dest_zip))
    metrics["status"] = "completed"
    metrics["artifact_path"] = str(dest_zip.relative_to(ROOT)).replace("\\", "/")
    return metrics


def _latest_zip(directory: Path) -> Path | None:
    if not directory.is_dir():
        return None
    zips = sorted(directory.glob("backtest-result-*.zip"), key=lambda p: p.stat().st_mtime)
    return zips[-1] if zips else None


def smoke_backtest(*, strategy: str, pair: str, timerange: str) -> tuple[bool, str]:
    """Run a short backtest only to learn whether Freqtrade can load and run a
    strategy. Nothing is exported or recorded, and the numbers are ignored: the
    unit tests stub TA-Lib and Freqtrade, so this is what catches a strategy
    that passes them and still fails in the real engine."""
    result = run_compose(
        [
            "backtesting",
            "--config", f"{CONTAINER_USER_DATA}/config.dryrun.json",
            "--strategy", strategy,
            "--strategy-path", f"{CONTAINER_USER_DATA}/strategies",
            "--timeframe", "1h",
            "--pairs", pair,
            "--timerange", timerange,
            "--dry-run-wallet", "100",
            "--stake-amount", "unlimited",
            "--fee", "0.001",
            "--export", "none",
            "--cache", "none",
            "--enable-protections",
        ]
    )
    output = result.stdout + result.stderr
    failed = result.returncode != 0 or "Traceback" in output
    return (not failed), output[-1500:]


def _load_strategy_stats(zip_path: Path) -> tuple[dict | None, str]:
    """Open Freqtrade's exported result JSON and return its single strategy's
    stats as (stats, ""), or (None, reason) when the zip has no usable result."""
    with zipfile.ZipFile(zip_path) as archive:
        json_names = [
            name for name in archive.namelist()
            if name.endswith(".json") and not name.endswith("_config.json")
        ]
        if not json_names:
            return None, "no result json in export zip"
        with archive.open(json_names[0]) as handle:
            data = json.load(handle)

    strategy_results = data.get("strategy", {})
    if not strategy_results:
        return None, "no strategy results in export json"
    return strategy_results[next(iter(strategy_results))], ""


def read_trades(zip_path: Path) -> list[dict]:
    """The trade list exactly as Freqtrade exported it (open_date, close_date,
    profit_ratio, profit_abs, ...). Raises ValueError if the zip has no result."""
    stats, reason = _load_strategy_stats(zip_path)
    if stats is None:
        raise ValueError(f"{zip_path}: {reason}")
    return list(stats.get("trades", []))


def compounded_profit_excluding_best(trades: list[dict], starting_balance: float) -> float:
    """Net profit (quote) of the same run with its single best trade removed.

    With the default "unlimited" stake every trade uses the whole balance, so
    profits compound and the best trade also enlarges every later trade.
    Subtracting its profit_abs from the total would ignore that and punish
    long, compounding runs. Instead the balance curve is rebuilt without the
    trade with the highest profit_ratio: starting_balance * prod(1 + r) - starting_balance.
    Zero trades, or a single trade, gives 0.0.
    """
    if not trades:
        return 0.0
    ratios = sorted(float(t["profit_ratio"]) for t in trades)[:-1]  # drop the best
    balance = starting_balance
    for ratio in ratios:
        balance *= 1 + ratio
    return balance - starting_balance


def read_starting_balance(zip_path: Path) -> float:
    """The wallet the exported run started with."""
    stats, reason = _load_strategy_stats(zip_path)
    if stats is None:
        raise ValueError(f"{zip_path}: {reason}")
    return float(stats.get("starting_balance", 0.0))


def _read_backtest_zip(zip_path: Path) -> dict:
    """Extract metrics strictly from Freqtrade's own exported JSON inside the zip."""
    stats, reason = _load_strategy_stats(zip_path)
    if stats is None:
        return {"status": "failed", "reason": reason}

    trades = stats.get("trades", [])
    net_profit = float(stats.get("profit_total_abs", 0.0))
    net_profit_excl_best = compounded_profit_excluding_best(
        trades, float(stats.get("starting_balance", 0.0))
    )

    return {
        "total_trades": int(stats.get("total_trades", 0)),
        "net_profit_quote": net_profit,
        "net_profit_excl_best_trade": net_profit_excl_best,
        "max_drawdown_pct": float(stats.get("max_drawdown_account", 0.0)) * 100,
        "starting_balance": float(stats.get("starting_balance", 0.0)),
        "final_balance": float(stats.get("final_balance", 0.0)),
        "winrate": float(stats.get("winrate", 0.0)),
        "profit_factor": stats.get("profit_factor"),
        "backtest_start": stats.get("backtest_start"),
        "backtest_end": stats.get("backtest_end"),
    }


def run_lookahead_analysis(
    *,
    experiment_id: str,
    strategy: str,
    timerange: str,
    fee: float,
    pair: str = "BTC/USDT",
    timeframe: str = "1h",
    minimum_trade_amount: int = 1,
) -> dict:
    """Runs lookahead-analysis, requesting a CSV export, and parses that CSV
    (not the stdout text) for the bias verdict."""
    csv_name = f"lookahead-{experiment_id}.csv"
    container_csv_path = f"{CONTAINER_USER_DATA}/{csv_name}"

    args = [
        "lookahead-analysis",
        "--config", f"{CONTAINER_USER_DATA}/config.dryrun.json",
        "--strategy", strategy,
        "--strategy-path", f"{CONTAINER_USER_DATA}/strategies",
        "--timeframe", timeframe,
        "--pairs", pair,
        "--timerange", timerange,
        "--fee", str(fee),
        "--minimum-trade-amount", str(minimum_trade_amount),
        "--lookahead-analysis-exportfilename", container_csv_path,
        "--enable-protections",
    ]
    result = run_compose(args)
    _save_process_output(experiment_id, "lookahead-analysis", result)

    host_csv_path = USER_DATA / csv_name
    metrics = {"status": "completed" if result.returncode == 0 else "failed"}
    if host_csv_path.is_file():
        dest_csv = raw_dir(experiment_id) / csv_name
        shutil.copy2(host_csv_path, dest_csv)
        host_csv_path.unlink()
        metrics.update(_parse_lookahead_csv(dest_csv))
    else:
        metrics["lookahead_has_bias"] = None
        metrics["reason"] = "no CSV produced by lookahead-analysis"
    return metrics


def _parse_lookahead_csv(csv_path: Path) -> dict:
    """Parse the lookahead-analysis CSV. Stdlib csv module, no assumptions
    beyond a header row with a 'has_bias' column (Freqtrade's documented
    lookahead-analysis export format)."""
    import csv

    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return {"lookahead_has_bias": None, "reason": "empty lookahead CSV"}

    row = rows[0]
    has_bias_raw = row.get("has_bias", "").strip().lower()
    has_bias = has_bias_raw in ("true", "yes", "1")
    return {"lookahead_has_bias": has_bias, "lookahead_raw_row": row}


def run_recursive_analysis(
    *,
    experiment_id: str,
    strategy: str,
    timerange: str,
    pair: str = "BTC/USDT",
    timeframe: str = "1h",
) -> dict:
    """Runs recursive-analysis. It has no structured export flag, so the
    verdict is parsed from its stdout table, and the raw stdout is always
    kept alongside for a human to re-check the parse."""
    args = [
        "recursive-analysis",
        "--config", f"{CONTAINER_USER_DATA}/config.dryrun.json",
        "--strategy", strategy,
        "--strategy-path", f"{CONTAINER_USER_DATA}/strategies",
        "--timeframe", timeframe,
        "--pairs", pair,
        "--timerange", timerange,
    ]
    result = run_compose(args)
    _save_process_output(experiment_id, "recursive-analysis", result)

    metrics = {"status": "completed" if result.returncode == 0 else "failed"}
    # Freqtrade logs to stderr by default and only prints the Rich results
    # table (when there is one) via stdout; the "no variance" shortcut
    # message and the table are not reliably on the same stream, so both
    # are searched together.
    metrics.update(_parse_recursive_stdout(result.stdout + "\n" + result.stderr))
    return metrics


def _parse_recursive_stdout(combined_output: str) -> dict:
    """Parse Freqtrade's recursive-analysis output.

    Confirmed behaviour (freqtradeorg/freqtrade:2026.9, 2026-10-27), on the
    combined stdout+stderr log stream:

    - When every indicator is perfectly stable across all tested startup
      candle counts, Freqtrade logs
      "No variance on indicator(s) found due to recursive formula." and
      prints no results table at all.
    - Otherwise it prints a Rich table like:

          ┃ Indicators ┃    199 ┃ 200 (from strategy) ┃    399 ┃ ... ┃
          │   sma_fast │ 0.000% │              0.000% │ 0.000% │ ... │

      where each remaining column is a percentage variation observed when
      recomputing that indicator with a different startup candle count, or
      "-" when that startup candle count had too little data. Any nonzero
      percentage means the indicator's value depends on how much history
      preceded it -- the recursive-bias failure this check exists to catch.
    """
    if "no variance on indicator" in combined_output.lower():
        return {
            "recursive_is_stable": True,
            "recursive_nonzero_cells": [],
            "recursive_raw_stdout_excerpt": combined_output[-2000:],
        }

    # Only the table rows count. Log lines such as "Using fee 0.1000%" or
    # "Price jump ... of 23.53%" also contain percentages and are not
    # recursive-bias evidence.
    table_rows = [line for line in combined_output.splitlines() if line.lstrip().startswith("│")]
    percent_cells = re.findall(r"(-?\d+\.\d+)%", "\n".join(table_rows))
    if not percent_cells:
        return {
            "recursive_is_stable": None,
            "reason": "no percentage cells and no 'no variance' log line found",
            "recursive_raw_stdout_excerpt": combined_output[-2000:],
        }

    nonzero = [value for value in percent_cells if abs(float(value)) > 1e-9]
    is_stable = len(nonzero) == 0
    return {
        "recursive_is_stable": is_stable,
        "recursive_nonzero_cells": nonzero,
        "recursive_raw_stdout_excerpt": combined_output[-2000:],
    }
