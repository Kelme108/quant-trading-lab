"""Write lab/config/splits_futures.json, the splits of the futures lane (docs/faixa-futuros.md, section 4; the owner
confirmed the proposal on 2026-11-13: "faça o ideal").

Rule, fixed before any futures hypothesis is tested: for every pair, the SAME boundaries as its spot split in
lab/config/splits.json (exploration end, validation start and end, final test), except that the exploration starts at
the later of the spot exploration start and the first futures candle of BOTH timeframes (1h and 15m). Nothing here looks
at a return; only the first and last candle times of the downloaded futures files are read.

Usage: python research/tools/build_futures_splits.py [--check]   (--check: exit 1 if the file on disk differs)
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lab import lanes  # noqa: E402

SPOT = ROOT / "lab" / "config" / "splits.json"
OUT = ROOT / "lab" / "config" / "splits_futures.json"


def _iso(ts) -> str:
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _epoch(iso: str) -> int:
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


def build(root: Path = ROOT) -> dict:
    import pandas as pd

    spot = json.loads((root / "lab" / "config" / "splits.json").read_text(encoding="utf-8"))
    pairs = {}
    for pair, cell in spot["pairs"].items():
        firsts, lasts = [], []
        for tf in ("1h", "15m"):
            path = lanes.FUTURES.feather_path(pair, tf, root)
            dates = pd.read_feather(path, columns=["date"])["date"]
            firsts.append(dates.min())
            lasts.append(dates.max())
        start = max(datetime.fromisoformat(cell["exploration"]["start_utc"].replace("Z", "+00:00")), max(firsts).to_pydatetime())
        start_iso = _iso(start)
        exp_end, val = cell["exploration"]["end_utc"], cell["validation"]
        pairs[pair] = {
            "futures_pair": lanes.FUTURES.pair(pair),
            "source_data_path": str(lanes.FUTURES.feather_path(pair, "1h", root).relative_to(root)).replace("\\", "/"),
            "futures_first_candle_utc": {"1h": _iso(firsts[0]), "15m": _iso(firsts[1])},
            "exploration": {"start_utc": start_iso, "end_utc": exp_end, "timerange": f"{_epoch(start_iso)}-{_epoch(exp_end)}"},
            "validation": dict(val),
        }
    return {
        "_comment": "Futures lane splits (owner decision D2, 2026-11-13; rule in research/tools/build_futures_splits.py and "
                    "docs/faixa-futuros.md section 4): the spot boundaries of each pair, with the exploration starting at the "
                    "first futures candle when futures history is shorter. A futures hypothesis whose family already had its "
                    "SPOT validation read may not read the futures validation (lab/autopilot.py): futures prices track spot, "
                    "so that window is not out of sample for it. Edits need the owner.",
        "historical_cutoff_utc_exclusive": spot.get("historical_cutoff_utc_exclusive"),
        "final_test": spot["final_test"],
        "pairs": pairs,
    }


def main(argv: list[str]) -> int:
    text = json.dumps(build(), indent=2) + "\n"
    if "--check" in argv:
        same = OUT.is_file() and json.loads(OUT.read_text(encoding="utf-8")) == json.loads(text)
        print("splits_futures.json matches the rule" if same else "splits_futures.json DIFFERS from the rule")
        return 0 if same else 1
    OUT.write_bytes(text.encode("utf-8"))
    print(f"wrote {OUT.relative_to(ROOT)} ({len(json.loads(text)['pairs'])} pairs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
