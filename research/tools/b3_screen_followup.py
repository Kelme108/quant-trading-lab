"""After the crypto screen (b3/config/crypto_screen_b3.json "after_triage"): for the top 10 of the triage, the deflated
Sharpe (DSR) and the PBO of lab/stats.py over ALL the screen's trials (daily net returns on exploration), and ONE
validation read for those that passed the exploration gates. The final test stays locked.

    python research/tools/b3_screen_followup.py [--no-validation]   -> research/b3/screen_followup.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import b3.proxy_research as pr  # noqa: E402
from lab import stats  # noqa: E402

SCREEN = ROOT / "research" / "b3" / "crypto_screen.json"
OUT = ROOT / "research" / "b3" / "screen_followup.json"


def daily_returns(stem: str) -> pd.Series:
    tl = json.loads((pr.B3_OUT_DIR / "trades" / f"{stem}.json").read_text(encoding="utf-8"))
    ix = {c: i for i, c in enumerate(tl["columns"])}
    if not tl["rows"]:
        return pd.Series(dtype=float)
    t = pd.to_datetime([r[ix["exit_time"]] for r in tl["rows"]], utc=True).tz_convert("America/Sao_Paulo").date
    return pd.Series([r[ix["net_pct"]] / 100 for r in tl["rows"]], index=t).groupby(level=0).sum()


def latest_stems() -> dict[tuple[str, str], str]:
    out = {}
    for f in sorted((pr.B3_OUT_DIR / "results").glob("C-*-exploration-*.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        out[(r["rule"], r["symbol"])] = f.stem
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-validation", action="store_true")
    a = ap.parse_args(argv)
    screen = json.loads(SCREEN.read_text(encoding="utf-8"))
    stems = latest_stems()
    series = {k: daily_returns(s) for k, s in stems.items()}
    series = {k: v for k, v in series.items() if len(v) >= 10}
    days = sorted(set().union(*[set(v.index) for v in series.values()]))
    keys = sorted(series)
    matrix = np.array([[series[k].get(d, 0.0) for k in keys] for d in days])
    n_trials = len({(r["rule"], r["symbol"]) for r in pr.ledger_rows(pr.B3_LEDGER) if r["split"] == "exploration"})
    var = stats.trial_sharpe_variance([matrix[:, j] for j in range(matrix.shape[1])])
    pbo = stats.pbo_cscv(matrix, n_slices=16) if len(keys) >= 2 and len(days) >= 32 else None
    top = []
    rows = {(r["rule"], r["symbol"]): r for r in screen["rows"]}
    for name in screen["top"]:
        rule, sym = name.rsplit("@", 1)
        row = rows[(rule, sym)]
        col = matrix[:, keys.index((rule, sym))] if (rule, sym) in keys else np.zeros(len(days))
        entry = {"rule": rule, "symbol": sym, "gate_decision": row["gate_decision"], "net_conservative_pct": row["net_conservative_pct"],
                 "gross_over_cost": row["gross_over_cost"], "deflated_sharpe": stats.deflated_sharpe(col, n_trials, var)}
        if row["gate_decision"] == "passed" and not a.no_validation:
            already = any(r["rule"] == rule and r["symbol"] == sym and r["split"] == "validation" for r in pr.ledger_rows(pr.B3_LEDGER))
            if not already:
                o = pr.evaluate(rule, sym, "validation", family="crypto-screen")
                b, c = o["scenarios"]["base"], o["scenarios"]["conservative"]
                entry["validation"] = {"decision": o["gates"]["decision"], "fails": o["gates"]["fails"], "trades": b["trades"],
                                       "net_base_pct": b["net_return_pct"], "net_conservative_pct": c["net_return_pct"],
                                       "bar_pct": o["gates"].get("net_bar_pct")}
                print(rule, sym, "validation:", entry["validation"]["decision"], entry["validation"]["fails"], flush=True)
        top.append(entry)
    out = {"generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "protocol": "b3/config/crypto_screen_b3.json after_triage", "configs_in_matrix": len(keys), "days": len(days),
           "n_trials_for_dsr": n_trials, "variance_of_trial_sharpes": var, "pbo_over_screen": pbo, "top": top}
    OUT.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(json.dumps({"pbo": pbo and pbo["pbo"], "top": [(t["rule"], t["symbol"], t["gate_decision"],
                      round(t["deflated_sharpe"]["dsr"], 3), (t.get("validation") or {}).get("decision")) for t in top]}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
