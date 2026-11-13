"""Calibration -> exposure by rule -> official exploration experiment, for one hypothesis.

1. Calibration (exploration split, base cost, full exposure): the trade list of each pair. Fewer than 30 trades on any
   pair drops the hypothesis (recorded, nothing is retuned).
2. Exposure = lab.bootstrap.choose_exposure on those trades (seeded; exploration data only).
3. Official experiment: 4 cost scenarios, lookahead, recursive, gates; exploration only.

The validation split is never touched here. Shared by research/tools/calibrate_and_run.py and the weekly pipeline.
`backtest`, `read_trades` and `experiments` are injectable so the flow can be tested without Docker.

Speed (2026-11-13; one hypothesis on 26 pairs took ~1h50, ~3.5 min per pair, each Freqtrade call in its own container):
- `workers` pairs run at the same time (default LAB_PARALLEL_PAIRS or 3). Each worker opens its own connection to the
  registry file; every gate decision is still taken one pair at a time in the calling thread, on the stored metrics.
- `early_stop`: once so many pairs are not candidates that the breadth rule can no longer be met, AND at least one of
  them is 'rejected', no new pair is started. The hypothesis status is then exactly what running every pair would
  give ('rejected at exploration': the passing count stays below K and a 'rejected' exists); only the pairs that were
  never started have no exploration record. Pairs already running finish and are decided.
"""

from __future__ import annotations

import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from lab import breadth, bootstrap, costs, experiment, registry, runner

ROOT = Path(__file__).parents[1]
MIN_TRADES = 30
WALLET_QUOTE = runner.BACKTEST_WALLET  # the --dry-run-wallet of every lab backtest (lab/runner.py)
MIN_STAKE_QUOTE = 10.0  # smallest stake Freqtrade places on Binance spot here (5 USDT notional plus its reserves)
DEFAULT_WORKERS = 3     # Freqtrade containers at once; three fit the 16 GB Docker Desktop limit with room to spare


def default_workers() -> int:
    try:
        return max(1, int(os.environ.get("LAB_PARALLEL_PAIRS", DEFAULT_WORKERS)))
    except ValueError:
        return DEFAULT_WORKERS


def _db_file(conn) -> str:
    """The registry file behind `conn`; '' for an in-memory database (then everything runs in this thread)."""
    try:
        row = conn.execute("PRAGMA database_list").fetchone()
    except Exception:  # a fake connection in a test
        return ""
    return (row[2] or "") if row else ""


def _in_order(items, fn, workers: int):
    """fn(item) for every item, `workers` at a time; returns the results in the order of `items`."""
    if workers <= 1 or len(items) <= 1:
        return [fn(item) for item in items]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(fn, items))


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def calibrate_and_explore(
    conn, hypothesis_id: str, *, strategy_name: str, strategy_file: str, timeframe: str = "1h",
    root: Path = ROOT, splits: dict | None = None, backtest=runner.run_backtest, read_trades=runner.read_trades,
    experiments=experiment, pairs: list[str] | None = None, workers: int | None = None, early_stop: bool = True,
) -> dict:
    """{'outcome': 'explored'|'dropped_trades'|'dropped_exposure'|'failed', 'counts', 'exposure', 'status', 'decisions'}."""
    splits = splits if splits is not None else runner.load_splits()
    pairs = pairs or runner.enabled_pairs()
    stamp = _stamp()
    base = costs.get_scenario("base")
    workers = default_workers() if workers is None else max(1, int(workers))
    db_file = _db_file(conn)
    if not db_file:
        workers = 1

    def calibration(pair: str) -> dict:
        timerange = runner.resolve_split_timerange("exploration", splits, pair=pair)
        return backtest(
            experiment_id=f"calib-{hypothesis_id.lower()}-{stamp}-{pair.replace('/', '-').lower()}",
            strategy=strategy_name, timerange=timerange, fee=base.effective_fee_per_side, pair=pair, timeframe=timeframe,
        )

    ratios, counts = {}, {}
    for pair, result in zip(pairs, _in_order(pairs, calibration, workers)):
        if result.get("status") != "completed":
            return {"outcome": "failed", "counts": counts, "exposure": None, "status": None,
                    "reason": f"calibration backtest failed on {pair}"}
        trades = read_trades(root / result["artifact_path"])
        ratios[pair] = [float(t["profit_ratio"]) for t in sorted(trades, key=lambda t: t["open_date"])]
        counts[pair] = len(trades)
    need = breadth.exploration_min_pairs(len(pairs))
    enough = [p for p in pairs if counts[p] >= MIN_TRADES]
    if len(enough) < need:
        status = "dropped: fewer than 30 trades"
        note = (f"DROPPED by the pre-registered rule: calibration trades {counts} (30 or more on {len(enough)} "
                f"pair(s), {need} needed); not retuned.")
        registry.set_hypothesis_status(conn, hypothesis_id, status)
        _append_note(conn, hypothesis_id, note)
        return {"outcome": "dropped_trades", "counts": counts, "exposure": None, "status": status}
    chosen = bootstrap.choose_exposure({p: ratios[p] for p in enough}, min_pairs=need)
    exposure = chosen["exposure"]
    if exposure is None:
        status = "dropped: no exposure meets the 25% bootstrap drawdown"
        registry.set_hypothesis_status(conn, hypothesis_id, status)
        _append_note(conn, hypothesis_id, f"No exposure on the 5% grid keeps the bootstrap p95 drawdown within 25% on {need} pair(s); calibration trades {counts}.")
        return {"outcome": "dropped_exposure", "counts": counts, "exposure": None, "status": status}
    if exposure * WALLET_QUOTE < MIN_STAKE_QUOTE:
        # Freqtrade cannot place an order this small (Binance minimum notional plus its reserves): the exploration
        # backtest would make no trade at all and read as a 'minimum trades' rejection, which is not what happened.
        status = "dropped: calibrated exposure below the minimum order"
        registry.set_hypothesis_status(conn, hypothesis_id, status)
        _append_note(conn, hypothesis_id, f"Calibrated exposure: {exposure} gives a stake of {exposure * WALLET_QUOTE:g} "
                                          f"on the {WALLET_QUOTE:g} wallet, below the {MIN_STAKE_QUOTE:g} minimum order; "
                                          f"the drawdown control needs a smaller stake than the exchange accepts. "
                                          f"Calibration trades {counts}.")
        return {"outcome": "dropped_exposure", "counts": counts, "exposure": exposure, "status": status}
    version = experiments.freqtrade_version()
    stop = threading.Event()

    def explore(pair: str, own_connection: bool) -> str | None:
        if stop.is_set():
            return None
        worker_conn = registry.connect(Path(db_file)) if own_connection else conn
        try:
            return experiments.run_experiment(
                worker_conn, hypothesis_id=hypothesis_id, strategy_name=strategy_name, strategy_file=strategy_file,
                pair=pair, split_name="exploration", timestamp=stamp, splits=splits, version=version,
                notes=f"exposure {exposure} (p95 {chosen['p95_by_pair']}); calibration trades {counts}",
                exposure=exposure, timeframe=timeframe,
            )
        finally:
            if own_connection:
                worker_conn.close()

    decisions, failed_gates, by_pair = {}, {}, {}
    max_not_passing = len(pairs) - need

    def decide(pair: str, experiment_id: str) -> None:
        decision, reasons = experiments.decide_experiment(conn, experiment_id, hypothesis_id)
        decisions[experiment_id] = decision
        by_pair[pair] = decision
        failing = [r.split(":", 1)[0] for r in reasons if ": FAIL" in r or ": inconclusive" in r]
        if failing:
            failed_gates[pair] = failing
        not_passing = sum(d != "candidate_for_portfolio" for d in by_pair.values())
        if early_stop and not_passing > max_not_passing and "rejected" in by_pair.values():
            stop.set()

    if workers <= 1:
        for pair in pairs:
            experiment_id = explore(pair, False)
            if experiment_id is None:
                break
            decide(pair, experiment_id)
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(explore, pair, True): pair for pair in pairs}
            try:
                for future in as_completed(futures):
                    experiment_id = future.result()
                    if experiment_id is not None:
                        decide(futures[future], experiment_id)
            except BaseException:
                stop.set()          # no new pair starts; the ones running finish before the error goes up
                raise
    skipped = [p for p in pairs if p not in by_pair]
    values = set(decisions.values())
    passing = sum(d == "candidate_for_portfolio" for d in decisions.values())
    status = (
        "exploration: candidate" if passing >= need
        else "rejected at exploration" if "rejected" in values else "inconclusive at exploration"
    )
    registry.set_hypothesis_status(conn, hypothesis_id, status)
    _append_note(conn, hypothesis_id, f"Calibrated exposure: {exposure} (p95 by pair {chosen['p95_by_pair']}). Calibration trades: {counts}.")
    if passing < need:
        _append_note(conn, hypothesis_id, f"Breadth: candidate on {passing} of {len(pairs)} pairs, {need} needed.")
    if skipped:
        _append_note(conn, hypothesis_id, f"Early stop: {len(by_pair) - passing} of {len(by_pair)} pairs run were not "
                                          f"candidates, so {need} of {len(pairs)} could no longer be reached; not started: "
                                          f"{', '.join(skipped)}.")
    return {"outcome": "explored", "counts": counts, "exposure": exposure, "status": status, "decisions": decisions,
            "failed_gates": failed_gates, "skipped_pairs": skipped}


def _append_note(conn, hypothesis_id: str, note: str) -> None:
    conn.execute("UPDATE hypotheses SET notes = COALESCE(notes, '') || ' ' || ? WHERE id = ?", (note, hypothesis_id))
    conn.commit()
