"""Print dossier JSON files as compact markdown tables."""
import json
import sys
from pathlib import Path


def fmt(v, pct=False, nd=2):
    if v is None:
        return "-"
    if isinstance(v, float) and v != v:
        return "-"
    return f"{v*100:.1f}%" if pct else f"{v:.{nd}f}"


for name in sys.argv[1:]:
    d = json.loads(Path(f"research/dossiers/{name}.json").read_text(encoding="utf-8"))
    print(f"\n### {d['strategy']} {d['pair']} {d['timeframe']} exposure {d['exposure']} (base cost, exploration)")
    print("| Window | Trades | Win | PF | Expect. (ratio) | Sharpe | Sortino | MaxDD | Return | B&H | Risk-sized 1%/trade ret / DD |")
    print("|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
    for r in d["rows"]:
        if r.get("status") != "completed":
            print(f"| {r['window']} | failed |"); continue
        rs = r["risk_sized"]
        print(f"| {r['window']} | {r['trades']} | {fmt(r['win_rate'], True, 0)} | {fmt(r['profit_factor'])} | {fmt(r['expectancy_ratio'])} | "
              f"{fmt(r['sharpe'])} | {fmt(r['sortino'])} | {fmt(r['max_dd_account'], True, 1)} | {fmt(r['profit_total'], True, 1)} | "
              f"{fmt(r['buy_and_hold'], True, 0)} | {fmt(rs['return'], True, 1)} / {fmt(rs['max_drawdown'], True, 1)} |")
