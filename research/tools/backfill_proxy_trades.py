"""Owner decision D2 (docs/plano-portal-proxies.md): the reads made before 2026-11-15 kept only metrics. This
re-runs the EXPLORATION split of every (rule, market) already read on exploration that has no trade list,
with record=False (no ledger row, no new variant), and writes the base-scenario trades for the portal to
research/proxies/trades/recalc/<rule>-<market>-exploration.json, marked as recalculated with today's engine
(stop slippage and the 90% session rule of 2026-11-14 make the numbers differ a little from the original read).
Validation and final-test reads are never re-run: they are read once. 1-minute rules are skipped (heavy, out of
scope since 2026-11-14).

    python research/tools/backfill_proxy_trades.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from b3.proxy_research import OUT_DIR, evaluate, ledger_rows  # noqa: E402
from b3.proxy_rules import RULES  # noqa: E402

RECALC = OUT_DIR / "trades" / "recalc"


def has_trades(rule: str, symbol: str) -> bool:
    return any((OUT_DIR / "trades").glob(f"{rule}-{symbol}-exploration-*.json"))


def main() -> int:
    RECALC.mkdir(parents=True, exist_ok=True)
    pairs = sorted({(r["rule"], r["symbol"]) for r in ledger_rows() if r["split"] == "exploration"})
    for rule, symbol in pairs:
        target = RECALC / f"{rule}-{symbol}-exploration.json"
        if target.exists() or has_trades(rule, symbol) or rule not in RULES:
            continue
        if RULES[rule].timeframe_min < 5:
            print(f"skip {rule} {symbol}: 1-minute rule, out of scope", flush=True)
            continue
        out = evaluate(rule, symbol, "exploration", record=False, enforce_scope=False)
        b = out["scenarios"]["base"]
        target.write_text(json.dumps({
            "rule": rule, "symbol": symbol, "split": "exploration", "recalculated": True,
            "recalculated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "note": "re-run with the engine of 2026-11-15 (stop slippage, 90% session rule); not a new read",
            "strategy_hash": out["strategy_hash"], "decision_now": out["gates"]["decision"],
            "base_now": {k: b.get(k) for k in ("trades", "mean_gross_pct", "net_return_pct", "max_drawdown_pct")},
            **out["trades_base"]}, separators=(",", ":")), encoding="utf-8")
        print(f"{rule} {symbol}: {b['trades']} trades, net base now {b['net_return_pct']:.2f}%", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
