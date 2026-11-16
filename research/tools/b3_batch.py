"""Recorded EXPLORATION reads of several rules on WIN/WDO (b3 lane of b3/proxy_research.py), skipping pairs the
ledger already has. Every read is a trial for the multiple-testing bar; `--family` tags them in the ledger.

    python research/tools/b3_batch.py --rules P-001,P-002 --symbols WIN,WDO --family proxy-rules-on-b3
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import b3.proxy_research as pr  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", required=True)
    ap.add_argument("--symbols", default="WIN,WDO")
    ap.add_argument("--family", default=None)
    a = ap.parse_args(argv)
    done = {(r["rule"], r["symbol"]) for r in pr.ledger_rows(pr.B3_LEDGER) if r["split"] == "exploration"}
    for rule in a.rules.split(","):
        for sym in a.symbols.split(","):
            if (rule, sym) in done:
                print(f"{rule} {sym}: already read on exploration, skipped", flush=True)
                continue
            try:
                o = pr.evaluate(rule, sym, "exploration", family=a.family)
            except Exception as exc:  # noqa: BLE001 - one failing rule must not stop the batch
                print(f"{rule} {sym}: ERROR {exc!r}", flush=True)
                traceback.print_exc()
                continue
            b, c = o["scenarios"]["base"], o["scenarios"]["conservative"]
            print(json.dumps({"rule": rule, "symbol": sym, "trades": b["trades"],
                              "per_year": round(b["trades_per_year"]), "gross_pct": b.get("mean_gross_pct"),
                              "net_base": round(b["net_return_pct"], 2), "net_cons": round(c["net_return_pct"], 2),
                              "dd_base": round(b.get("max_drawdown_pct", 0), 1), "decision": o["gates"]["decision"],
                              "bar": round(o["gates"].get("net_bar_pct", 0), 2)}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
