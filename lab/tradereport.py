"""Writes the trade review of a hypothesis (exploration only) from the exports already registered for it.

Shared by research/tools/trade_review.py and the weekly pipeline. The review itself is lab/tradereview.py (pure)."""

from __future__ import annotations

import json
from pathlib import Path

from lab import registry, runner, tradereview

ROOT = Path(__file__).parents[1]


def write_report(conn, hypothesis_id: str, *, root: Path = ROOT, read_trades=runner.read_trades, pairs: list[str] | None = None) -> list[Path]:
    """research/audit/trade-review/<H>-exploration.{json,md}. Raises ValueError when there is nothing to review."""
    if registry.get_hypothesis(conn, hypothesis_id) is None:
        raise ValueError(f"{hypothesis_id} is not registered")
    experiments = registry.latest_experiments(conn, hypothesis_id, "exploration")
    if not experiments:
        raise ValueError(f"{hypothesis_id} has no completed exploration experiment")
    by_pair, sources = {}, {}
    for pair in pairs or runner.enabled_pairs():
        row = experiments.get(pair)
        if row is None:
            continue
        by_pair[pair] = tradereview.review(read_trades(root / row["artifact_path"]))
        sources[pair] = row["artifact_path"]
    out = root / "research" / "audit" / "trade-review"
    out.mkdir(parents=True, exist_ok=True)
    payload = {"hypothesis": hypothesis_id, "split": "exploration", "cost_scenario": "base", "validation_read": False,
               "holdout_read": False, "sources": sources, "pairs": by_pair}
    json_path = out / f"{hypothesis_id}-exploration.json"
    md_path = out / f"{hypothesis_id}-exploration.md"
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    md_path.write_text(
        tradereview.render_markdown(f"Revisão de trades: {hypothesis_id} (exploração)", "; ".join(f"`{p}`" for p in sources.values()), by_pair),
        encoding="utf-8",
    )
    return [json_path, md_path]
