"""Print the baseline-by-cycle JSON as markdown tables."""
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
pairs = sys.argv[2:] or ["BTC/USDT"]


def pct(v):
    return "-" if v is None else f"{v * 100:.0f}%"


for scenario, by_pair in data["scenarios"].items():
    for pair in pairs:
        print(f"\n#### {data['strategy']} vs buy-and-hold, {pair}, costs {scenario}")
        print("| Window | Trades | Strat return | Strat maxDD | Strat Sharpe | B&H return | B&H maxDD | B&H Sharpe |")
        print("|---|--:|--:|--:|--:|--:|--:|--:|")
        for window, row in by_pair[pair]["windows"].items():
            s, b = row["strategy"], row["buy_and_hold"]
            if "note" in s or "note" in b:
                print(f"| {window} | - | no data |"); continue
            print(f"| {window} | {row['trades']} | {pct(s['return'])} | {pct(s['max_drawdown'])} | {s['sharpe_annualised']:.2f} | "
                  f"{pct(b['return'])} | {pct(b['max_drawdown'])} | {b['sharpe_annualised']:.2f} |")
