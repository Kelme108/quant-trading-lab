"""Execution-quality report of the dry-run bots of a frozen hypothesis (fills, slippage, fees, missed entries).

  python research/tools/forward_report.py H-009 [--returns]

The freeze check runs first and the report is refused if any frozen file changed. The databases are opened read-only.
Aggregate returns are left out unless --returns is given, and then they carry the label "monitoring, not evaluated":
the formal evaluation is the prospective holdout. Writes research/forward/<H>-execution.md.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import forward  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hypothesis_id")
    parser.add_argument("--returns", action="store_true", help="also show net profit (monitoring, not evaluated)")
    args = parser.parse_args()
    hid = args.hypothesis_id
    problems = forward.check_freeze(hid)
    if problems:
        print("refused: the freeze check failed\n" + "\n".join(problems))
        return 3
    frozen = json.loads(forward.freeze_path(hid).read_text(encoding="utf-8"))
    by_pair, returns = {}, {}
    for pair, db in frozen["databases"].items():
        trades, orders = forward.read_database(ROOT / db)
        by_pair[pair] = forward.execution_quality(trades, orders)
        closed = forward.closed_as_backtest_trades(trades)
        returns[pair] = {"closed": len(closed), "net_profit_abs": sum(t["profit_abs"] for t in closed)}
    text = forward.render_markdown(hid, by_pair, frozen, returns if args.returns else None)
    out = ROOT / "research" / "forward" / f"{hid}-execution.md"
    out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
