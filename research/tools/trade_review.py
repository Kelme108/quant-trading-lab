"""Trade-by-trade review of a hypothesis, EXPLORATION split only, from the exports the lab already registered.

No backtest is run: it reads the base-cost export recorded as `artifact_path` of the latest exploration experiment of
each pair (lab/registry.py), so the numbers are the very ones the gates saw. The validation split and the prospective
holdout are not accepted by this tool.

usage: python research/tools/trade_review.py H-009
Writes research/audit/trade-review/<H>-exploration.json and .md
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import registry, runner, tradereview  # noqa: E402

OUT = ROOT / "research" / "audit" / "trade-review"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hypothesis_id")
    parser.add_argument("--split", choices=["exploration"], default="exploration")
    args = parser.parse_args()
    conn = registry.connect()
    if registry.get_hypothesis(conn, args.hypothesis_id) is None:
        print(f"{args.hypothesis_id} is not registered")
        return 2
    experiments = registry.latest_experiments(conn, args.hypothesis_id, "exploration")
    if not experiments:
        print(f"{args.hypothesis_id} has no completed exploration experiment")
        return 2
    by_pair, sources = {}, {}
    for pair in runner.enabled_pairs():
        row = experiments.get(pair)
        if row is None:
            continue
        zip_path = ROOT / row["artifact_path"]
        by_pair[pair] = tradereview.review(runner.read_trades(zip_path))
        sources[pair] = row["artifact_path"]
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {"hypothesis": args.hypothesis_id, "split": "exploration", "cost_scenario": "base",
               "validation_read": False, "holdout_read": False, "sources": sources, "pairs": by_pair}
    (OUT / f"{args.hypothesis_id}-exploration.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    markdown = tradereview.render_markdown(
        f"Revisão de trades: {args.hypothesis_id} (exploração)", "; ".join(f"`{p}`" for p in sources.values()), by_pair)
    (OUT / f"{args.hypothesis_id}-exploration.md").write_text(markdown, encoding="utf-8")
    print(f"wrote {OUT / (args.hypothesis_id + '-exploration.md')}")
    for pair, rv in by_pair.items():
        print(pair, "trades", rv.get("trades"), "net", round(rv.get("net_profit_abs", 0.0), 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
