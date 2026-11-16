"""Screen of the portable crypto strategies on WIN/WDO (protocol: b3/config/crypto_screen_b3.json, fixed 2026-11-16
before any read). Each (strategy, market) is ONE recorded exploration read of the b3 lane (family crypto-screen);
pairs already in the ledger are not read again.

    python research/tools/b3_crypto_screen.py run --markets WIN [--limit N]   (one process per market is fine)
    python research/tools/b3_crypto_screen.py summary                         -> research/b3/crypto_screen.json
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import b3.proxy_research as pr  # noqa: E402

CONFIG = ROOT / "b3" / "config" / "crypto_screen_b3.json"
OUT = ROOT / "research" / "b3" / "crypto_screen.json"


def config() -> dict:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    if cfg.get("approved_by_owner") is not True:
        raise SystemExit("crypto_screen_b3.json is not approved")
    return cfg


def run(markets: list[str], limit: int | None) -> int:
    cfg = config()
    # a pair is read again only when its code changed (adapter fix): the ledger keeps every read
    done = {(r["rule"], r["symbol"], r["strategy_hash"]) for r in pr.ledger_rows(pr.B3_LEDGER)
            if r["split"] == "exploration"}
    n = 0
    for s in cfg["strategies"]:
        rid = f"C-{s['strategy']}"
        for sym in markets:
            try:
                h = pr.rule_class(rid).on(sym)().hash
            except Exception:  # noqa: BLE001
                h = None
            if (rid, sym, h) in done:
                continue
            if limit is not None and n >= limit:
                return 0
            n += 1
            t0 = time.time()
            try:
                o = pr.evaluate(rid, sym, cfg["split"], family=cfg["family"])
            except Exception as exc:  # noqa: BLE001 - a strategy that cannot run is reported, not fatal
                print(json.dumps({"rule": rid, "symbol": sym, "error": repr(exc)[:300]}), flush=True)
                _record_error(rid, sym, exc)
                continue
            b, c = o["scenarios"]["base"], o["scenarios"]["conservative"]
            print(json.dumps({"rule": rid, "symbol": sym, "trades": b["trades"], "gross_pct": b.get("mean_gross_pct"),
                              "net_base": round(b["net_return_pct"], 2), "net_cons": round(c["net_return_pct"], 2),
                              "decision": o["gates"]["decision"], "seconds": round(time.time() - t0)}), flush=True)
    return 0


def _record_error(rid: str, sym: str, exc: Exception) -> None:
    path = ROOT / "research" / "b3" / "crypto_screen_errors.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"rule": rid, "symbol": sym, "error": repr(exc)[:500],
                             "at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}) + "\n")


def latest_results() -> dict[tuple[str, str], dict]:
    out = {}
    for f in sorted(glob.glob(str(pr.B3_OUT_DIR / "results" / "C-*-exploration-*.json"))):
        r = json.loads(Path(f).read_text(encoding="utf-8"))
        out[(r["rule"], r["symbol"])] = r
    return out


def summary() -> int:
    cfg = config()
    tri = cfg["triage"]
    rows = []
    for (rid, sym), r in sorted(latest_results().items()):
        b, c = r["scenarios"]["base"], r["scenarios"]["conservative"]
        cost = r["cost_round_trip_base_pct"]
        gross = b.get("mean_gross_pct")
        ok = (b["trades"] >= tri["min_trades"] and gross is not None and gross >= tri["min_gross_over_cost"] * cost
              and c["net_return_pct"] > 0)
        rows.append({"rule": rid, "strategy": rid[2:], "symbol": sym, "trades": b["trades"],
                     "trades_per_year": round(b["trades_per_year"], 1), "mean_gross_pct": gross,
                     "cost_round_trip_pct": cost, "gross_over_cost": (gross / cost) if gross is not None else None,
                     "net_base_pct": b["net_return_pct"], "net_conservative_pct": c["net_return_pct"],
                     "max_drawdown_base_pct": b.get("max_drawdown_pct"), "gate_decision": r["gates"]["decision"],
                     "net_bar_pct": r["gates"].get("net_bar_pct"), "passes_triage": ok})
    passing = sorted([x for x in rows if x["passes_triage"]], key=lambda x: -x["net_conservative_pct"])
    top = passing[: tri["top_n"]]
    errors = []
    ep = ROOT / "research" / "b3" / "crypto_screen_errors.jsonl"
    if ep.exists():
        errors = [json.loads(l) for l in ep.read_text(encoding="utf-8").splitlines() if l.strip()]
    expected = len(cfg["strategies"]) * len(cfg["markets"])
    out = {"generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "protocol": "b3/config/crypto_screen_b3.json",
           "reads": len(rows), "expected_reads": expected, "errors": len({(e["rule"], e["symbol"]) for e in errors}),
           "passing_triage": len(passing), "top": [x["rule"] + "@" + x["symbol"] for x in top],
           "top_passing_gates": [x["rule"] + "@" + x["symbol"] for x in top if x["gate_decision"] == "passed"],
           "rows": rows}
    OUT.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(f"{len(rows)}/{expected} reads, {len(passing)} pass the triage; top: {out['top']}; "
          f"passing the gates: {out['top_passing_gates']}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--markets", default="WIN,WDO")
    r.add_argument("--limit", type=int, default=None)
    sub.add_parser("summary")
    a = ap.parse_args(argv)
    return run(a.markets.split(","), a.limit) if a.cmd == "run" else summary()


if __name__ == "__main__":
    raise SystemExit(main())
