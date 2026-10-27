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


def resolve_split_timerange(split_name: str, splits: dict | None = None) -> str:
    """Returns the Freqtrade --timerange string for a named split.

    Refuses final_test while splits.json marks it locked — this is the
    enforcement point the task requires; nothing downstream can bypass it
    by calling run_compose directly without going through here, since this
    is the only place that turns a split name into a timerange.
    """
    if splits is None:
        splits = load_splits()
    if split_name not in ("exploration", "validation", "final_test"):
        raise ValueError(f"unknown split '{split_name}'")

    split = splits[split_name]
    if split_name == "final_test" and not split.get("final_test_unlocked", False):
        raise FinalTestLockedError(
            "final_test split is locked in lab/config/splits.json "
            "(final_test_unlocked: false). Only the user may unlock it."
        )
    return split["timerange"]


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
    stake_amount: float = 100.0,
) -> dict:
    """Runs `backtesting --export trades`, saves raw output + artifacts, and
    returns parsed metrics read from the exported zip (never from stdout text).
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


def _read_backtest_zip(zip_path: Path) -> dict:
    """Extract metrics strictly from Freqtrade's own exported JSON inside the zip."""
    with zipfile.ZipFile(zip_path) as archive:
        json_names = [
            name for name in archive.namelist()
            if name.endswith(".json") and not name.endswith("_config.json")
        ]
        if not json_names:
            return {"status": "failed", "reason": "no result json in export zip"}
        with archive.open(json_names[0]) as handle:
            data = json.load(handle)

    strategy_results = data.get("strategy", {})
    if not strategy_results:
        return {"status": "failed", "reason": "no strategy results in export json"}
    strategy_key = next(iter(strategy_results))
    stats = strategy_results[strategy_key]

    trades = stats.get("trades", [])
    net_profit = float(stats.get("profit_total_abs", 0.0))
    if trades:
        best_trade_profit = max(t.get("profit_abs", 0.0) for t in trades)
        net_profit_excl_best = net_profit - best_trade_profit
    else:
        net_profit_excl_best = net_profit

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

    percent_cells = re.findall(r"(-?\d+\.\d+)%", combined_output)
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
