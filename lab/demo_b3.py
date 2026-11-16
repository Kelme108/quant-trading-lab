"""The B3 demonstration on the Clear DEMO for the portal (GET /api/demo-b3).

Owner, 2026-11-16: "quero apenas demonstração de como está se portando no demo". Reads, never writes:
- live/config/demo-b3-*.json      one file per demonstration (rule, contract, risk limits);
- the engine's snapshot           live/state/<name>.json: today's session bars, the position, the last decision;
- the engine's journal            live/journal.<name>.sqlite (append-only), opened READ-ONLY;
- research/b3/ledger.jsonl        what the research already decided about the same rule and contract.
Demonstration trades are NOT evidence and never enter the research ledger.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc
STALE_MIN = 12          # no snapshot for this long while the session is open -> the robot is not running
FEED_STALE_S = 60       # no live feed (written every 5 s) for this long while the session is open -> not running


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _journal(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    db = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=2)
    try:
        rows = db.execute("SELECT id, ts, kind, symbol, key, payload FROM events ORDER BY id").fetchall()
    finally:
        db.close()
    out = []
    for i, ts, kind, symbol, key, payload in rows:
        try:
            p = json.loads(payload)
        except ValueError:
            p = {}
        out.append({**p, "id": i, "ts": ts, "kind": kind, "symbol": symbol, "key": key})
    return out


def round_trips(fills: list[dict]) -> list[dict]:
    """Pair the journal's fills into trades: an entry (pnl None) and the fills that close it (pnl set)."""
    trades, open_ = [], None
    for f in fills:
        if f.get("pnl") is None:
            if open_ is None:
                open_ = {"entry": f, "exits": []}
            continue
        if open_ is None:
            continue
        open_["exits"].append(f)
        closed = sum(x["volume"] for x in open_["exits"])
        if closed + 1e-9 >= open_["entry"]["volume"]:
            e, xs = open_["entry"], open_["exits"]
            sign = 1.0 if e["side"] == "buy" else -1.0
            px = sum(x["price"] * x["volume"] for x in xs) / closed
            trades.append({"side": "compra" if sign > 0 else "venda", "volume": e["volume"],
                           "entry_time": e.get("fill_time") or e["ts"], "entry_price": e["price"], "entry_reason": e.get("reason", ""),
                           "exit_time": xs[-1].get("fill_time") or xs[-1]["ts"], "exit_price": px, "exit_reason": xs[-1].get("reason", ""),
                           "points": round((px - e["price"]) * sign, 6), "pnl_brl": round(sum(x["pnl"] for x in xs), 2),
                           "cost_brl": round((e.get("cost") or 0) + sum(x.get("cost") or 0 for x in xs), 2)})
            open_ = None
    return trades


def _research(rule: str, market: str, root: Path) -> list[dict]:
    out = []
    led = root / "research" / "b3" / "ledger.jsonl"
    if led.is_file():
        for line in led.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("rule") == rule and r.get("symbol") == market:
                out.append({"split": r.get("split"), "decision": r.get("decision"), "read_at": r.get("read_at_utc"),
                            "hash": r.get("strategy_hash")})
    return out


def _phase(snapshot: dict | None, now: datetime) -> str:
    s = (snapshot or {}).get("session")
    if not s or (snapshot or {}).get("day") != now.astimezone(timezone(timedelta(hours=-3))).date().isoformat():
        return "unknown"
    t = {k: datetime.fromisoformat(v) for k, v in s.items()}
    if now < t["open"] or now >= t["close"]:
        return "closed"
    if now >= t["flatten_at"]:
        return "flatten"
    if t["entry_start"] <= now < t["entry_end"]:
        return "entry"
    return "no_entry"


def demo_one(cfg_path: Path, root: Path = ROOT, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    cfg = _read_json(cfg_path) or {}
    name = cfg_path.stem
    st = cfg.get("strategy", {})
    snap = _read_json(root / cfg["snapshot_file"]) if cfg.get("snapshot_file") else None
    feed = _read_json(root / cfg["feed_file"]) if cfg.get("feed_file") else None
    events = _journal(root / cfg.get("journal_db", f"live/journal.{name}.sqlite"))
    fills = [e for e in events if e["kind"] == "fill"]
    trades = round_trips(fills)
    starts = [e for e in events if e["kind"] == "start"]
    last_ts = events[-1]["ts"] if events else None
    updated = datetime.fromisoformat(snap["updated_at"]) if snap and snap.get("updated_at") else None
    phase = _phase(snap, now)
    fed = datetime.fromisoformat(feed["updated_at"]) if feed and feed.get("updated_at") else None
    open_now = phase in ("entry", "no_entry", "flatten")
    if updated is None and fed is None:
        running = "sem dados" if not events else "aguardando o próximo candle"
    elif open_now and fed is not None and now - fed > timedelta(seconds=FEED_STALE_S):
        running = "parado"
    elif open_now and fed is None and now - updated > timedelta(minutes=STALE_MIN):
        running = "parado"
    elif not open_now:
        running = "fora do pregão"
    else:
        running = "rodando"
    today = now.astimezone(timezone(timedelta(hours=-3))).date().isoformat()
    def local_day(t: str) -> str:
        return datetime.fromisoformat(t.replace("Z", "+00:00")).astimezone(timezone(timedelta(hours=-3))).date().isoformat()
    return {
        "id": name, "rule": st.get("rule"), "market": st.get("market"), "symbol": (cfg.get("symbols") or [""])[0],
        "timeframe_min": cfg.get("timeframe_min"), "volume": cfg.get("volume"), "risk": cfg.get("risk", {}),
        "note": cfg.get("_note", ""), "status": running, "phase": phase, "snapshot": snap, "feed": feed, "last_event": last_ts,
        "started": [e["ts"] for e in starts][-5:], "trades": trades,
        "trades_today": [t for t in trades if local_day(t["entry_time"]) == today],
        "open_entry": next((f for f in reversed(fills) if f.get("pnl") is None), None) if snap and snap.get("position") else None,
        "pnl_total_brl": round(sum(t["pnl_brl"] for t in trades), 2), "points_total": round(sum(t["points"] for t in trades), 2),
        "wins": sum(1 for t in trades if t["pnl_brl"] > 0),
        "alerts": [{"ts": e["ts"], "message": e.get("message", "")} for e in events if e["kind"] == "alert"][-10:],
        "vetoes": [{"ts": e["ts"], "reasons": e.get("reasons", []), "side": e.get("side")} for e in events if e["kind"] == "veto"][-10:],
        "killswitch": (root / cfg.get("killswitch_file", "live/STOP")).exists(),
        "research": _research(st.get("rule"), st.get("market"), root),
    }


def demo_state(root: Path = ROOT, now: datetime | None = None) -> dict:
    items = []
    for p in sorted((root / "live" / "config").glob("demo-b3-*.json")):
        try:
            items.append(demo_one(p, root, now))
        except Exception as exc:           # one broken demonstration must not hide the others
            items.append({"id": p.stem, "error": repr(exc)})
    return {"generated_at": (now or datetime.now(UTC)).isoformat(timespec="seconds"), "items": items}
