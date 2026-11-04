"""Trade-by-trade review of a hypothesis, EXPLORATION split only, from the exports the lab already registered.

No backtest is run: it reads the base-cost export recorded as `artifact_path` of the latest exploration experiment of
each pair (lab/registry.py), so the numbers are the very ones the gates saw. The validation split and the prospective
holdout are not accepted by this tool.

usage: python research/tools/trade_review.py H-009
Writes research/audit/trade-review/<H>-exploration.json and .md (the work is lab/tradereport.py).
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import registry, tradereport  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hypothesis_id")
    parser.add_argument("--split", choices=["exploration"], default="exploration")
    args = parser.parse_args()
    try:
        paths = tradereport.write_report(registry.connect(), args.hypothesis_id)
    except ValueError as error:
        print(error)
        return 2
    print("wrote", paths[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
