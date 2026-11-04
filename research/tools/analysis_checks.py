"""Smoke backtest + lookahead-analysis + recursive-analysis of one registered strategy on the three pairs
(exploration window only). usage: python research/tools/analysis_checks.py <StrategyName> [timeframe]
The work is done by lab/checks.py (shared with the weekly pipeline)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import checks  # noqa: E402

if __name__ == "__main__":
    result = checks.run_checks(sys.argv[1], timeframe=sys.argv[2] if len(sys.argv) > 2 else "1h")
    for pair, cell in result.items():
        print(pair, json.dumps({k: v for k, v in cell.items() if k != "lookahead_row"}))
