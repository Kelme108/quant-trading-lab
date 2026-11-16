"""Read-only probe of the Clear demo terminal's TICK history for WIN (owner 2026-11-16, lever 1: measure the real
execution cost). Attaches to the logged-in terminal (b3/config/broker_mt5.json) without credentials, refuses a
non-demo account, sends no order, prints only depth and counts.

    live/.venv/Scripts/python.exe research/tools/b3_tick_probe.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main() -> int:
    import MetaTrader5 as mt5
    from b3.data.mt5_history import attach
    attach(mt5, ROOT / "b3" / "config" / "broker_mt5.json")
    try:
        out = {}
        now = datetime.now(timezone.utc) + timedelta(hours=-3)        # server clock = Sao Paulo
        for sym in ("WINZ26", "WINV26", "WINQ26", "WIN$N", "WDOZ26"):
            ok = mt5.symbol_select(sym, True)
            info = mt5.symbol_info(sym) if ok else None
            row = {"selectable": bool(ok and info)}
            if info:
                for months_back in (1, 2, 3, 6, 12):
                    start = (now - timedelta(days=30 * months_back)).replace(tzinfo=None)
                    t = mt5.copy_ticks_range(sym, start, start + timedelta(days=1), mt5.COPY_TICKS_ALL)
                    row[f"ticks_on_a_day_{months_back}m_ago"] = 0 if t is None else int(len(t))
                last = mt5.copy_ticks_from(sym, (now - timedelta(days=1)).replace(tzinfo=None), 5, mt5.COPY_TICKS_ALL)
                row["fields"] = list(last.dtype.names) if last is not None and len(last) else []
            out[sym] = row
        print(json.dumps(out, indent=1))
    finally:
        mt5.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
