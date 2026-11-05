"""Append-only SQLite journal: every signal, veto, order, fill, error.

UPDATE and DELETE are blocked by triggers. Rows with a `key` are unique per
(kind, key), which makes writes idempotent (restart-safe).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from live.core.clock import Clock

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL, kind TEXT NOT NULL, symbol TEXT, strategy TEXT,
  key TEXT, payload TEXT NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS ux_events_key ON events(kind, key) WHERE key IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_events_kind_ts ON events(kind, ts);
CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
  BEGIN SELECT RAISE(ABORT, 'journal is append-only'); END;
CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
  BEGIN SELECT RAISE(ABORT, 'journal is append-only'); END;
"""


def _fmt(dt: datetime) -> str:
    """Fixed-width UTC text so string order equals time order."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class Journal:
    def __init__(self, path: str | Path, clock: Clock, strategy: str = "") -> None:
        self.clock, self.strategy = clock, strategy
        self.db = sqlite3.connect(str(path))
        self.db.executescript(_SCHEMA)
        self.db.commit()

    def log(self, kind: str, symbol: str | None = None, key: str | None = None,
            **payload) -> bool:
        """Append one event. Returns False if (kind, key) already exists."""
        try:
            self.db.execute(
                "INSERT INTO events(ts,kind,symbol,strategy,key,payload) VALUES(?,?,?,?,?,?)",
                (_fmt(self.clock.now()), kind, symbol, self.strategy, key,
                 json.dumps(payload, default=str, sort_keys=True)))
            self.db.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def has(self, kind: str, key: str) -> bool:
        return self.db.execute(
            "SELECT 1 FROM events WHERE kind=? AND key=?", (kind, key)).fetchone() is not None

    def events(self, kind: str | None = None, since: datetime | None = None,
               symbol: str | None = None) -> list[dict]:
        q, args = "SELECT id,ts,kind,symbol,strategy,key,payload FROM events WHERE 1=1", []
        if kind:
            q += " AND kind=?"
            args.append(kind)
        if since:
            q += " AND ts>=?"
            args.append(_fmt(since))
        if symbol:
            q += " AND symbol=?"
            args.append(symbol)
        rows = self.db.execute(q + " ORDER BY id", args).fetchall()
        return [{**json.loads(r[6]), "id": r[0], "ts": r[1], "kind": r[2],
                 "symbol": r[3], "strategy": r[4], "key": r[5]} for r in rows]

    def net_volume(self, symbol: str) -> float:
        """Position implied by journalled fills (+ manual adjustments)."""
        net = 0.0
        for e in self.events("fill", symbol=symbol):
            net += e["volume"] if e["side"] == "buy" else -e["volume"]
        for e in self.events("adjust", symbol=symbol):
            net += e["delta"]
        return round(net, 8)

    def realized_pnl(self, since: datetime) -> float:
        return sum(e["pnl"] for e in self.events("fill", since=since)
                   if e.get("pnl") is not None)

    def entries_sent(self, since: datetime) -> int:
        return sum(1 for e in self.events("order_sent", since=since)
                   if not e.get("reduce_only"))

    def close(self) -> None:
        self.db.close()
