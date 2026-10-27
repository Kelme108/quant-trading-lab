"""One-time seed: import H-001/H-002/H-003 from the original hand-written
research/hypothesis-ledger.md into research/lab.sqlite.

Run this once, before the database has any hypotheses, so the database
becomes authoritative without losing the pre-existing history. Running it
again is safe: it skips any hypothesis_id already present.
"""

from __future__ import annotations

from lab import registry

SEED_HYPOTHESES = [
    dict(
        hypothesis_id="H-001",
        family="SmaTrendBaseline",
        ex_ante_rule=(
            "SMA20/SMA50 cross, close > SMA200, stop -10%"
        ),
        proposed_at_utc="2026-10-20T00:00:00Z",
        data_visible_at_proposal="BTC/USDT 1h through 2026-10-20",
        status="frozen reference",
        notes="One trade; inconclusive",
    ),
    dict(
        hypothesis_id="H-002",
        family="DonchianBreakoutBaseline",
        ex_ante_rule=(
            "Close > prior 20-candle high; exit below prior 10-candle low; stop -10%"
        ),
        proposed_at_utc="2026-10-20T00:00:00Z",
        data_visible_at_proposal="BTC/USDT 1h through 2026-10-20",
        status="candidate",
        notes="Do not select by return alone",
    ),
    dict(
        hypothesis_id="H-003",
        family="BollingerMeanReversionBaseline",
        ex_ante_rule=(
            "Lower 20-band, RSI14 < 30, close > SMA200; exit at middle band; stop -10%"
        ),
        proposed_at_utc="2026-10-20T00:00:00Z",
        data_visible_at_proposal="BTC/USDT 1h through 2026-10-20",
        status="candidate",
        notes="Trend-failure risk",
    ),
]


def seed(conn) -> list[str]:
    """Insert any seed hypothesis not already present. Returns the ids inserted."""
    inserted = []
    for entry in SEED_HYPOTHESES:
        if registry.get_hypothesis(conn, entry["hypothesis_id"]) is None:
            registry.add_hypothesis(conn, **entry)
            inserted.append(entry["hypothesis_id"])
    return inserted


def main() -> int:
    conn = registry.connect()
    inserted = seed(conn)
    registry.sync_ledger_markdown(conn)
    if inserted:
        print(f"Seeded hypotheses: {', '.join(inserted)}")
    else:
        print("No new hypotheses to seed (already present).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
