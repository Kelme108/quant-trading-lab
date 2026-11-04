"""Causality checks of a registered strategy on the exploration window: smoke backtest, lookahead-analysis and
recursive-analysis on every enabled pair. Needs Docker (Freqtrade). Nothing here reads validation or the holdout."""

from __future__ import annotations

import json
from pathlib import Path

from lab import costs, runner

ROOT = Path(__file__).parents[1]


def run_checks(name: str, *, timeframe: str = "1h", root: Path = ROOT, splits: dict | None = None, run=runner) -> dict:
    """{pair: {smoke_ok, lookahead_has_bias, recursive_is_stable, ...}}; also written to research/baselines/."""
    splits = splits if splits is not None else run.load_splits()
    fee = costs.get_scenario("base").effective_fee_per_side
    out: dict = {}
    for pair in run.enabled_pairs():
        timerange = run.resolve_split_timerange("exploration", splits, pair=pair)
        tag = f"{name.lower()}-{pair.replace('/', '-').lower()}"
        ok, _text = run.smoke_backtest(strategy=name, pair=pair, timerange=timerange)
        lookahead = run.run_lookahead_analysis(
            experiment_id=f"check-la-{tag}", strategy=name, timerange=timerange, fee=fee, pair=pair, timeframe=timeframe)
        recursive = run.run_recursive_analysis(
            experiment_id=f"check-rec-{tag}", strategy=name, timerange=timerange, pair=pair, timeframe=timeframe)
        out[pair] = {
            "smoke_ok": ok, "lookahead_has_bias": lookahead.get("lookahead_has_bias"),
            "lookahead_row": lookahead.get("lookahead_raw_row"),
            "recursive_is_stable": recursive.get("recursive_is_stable"),
            "recursive_nonzero_cells": recursive.get("recursive_nonzero_cells"),
        }
    target = root / "research" / "baselines"
    target.mkdir(parents=True, exist_ok=True)
    (target / f"checks-{name}.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def passed(result: dict) -> bool:
    """Every pair loads, shows no lookahead bias and is stable after the start-up candles. Unknown counts as failed."""
    return bool(result) and all(
        cell.get("smoke_ok") is True and cell.get("lookahead_has_bias") is False and cell.get("recursive_is_stable") is True
        for cell in result.values()
    )
