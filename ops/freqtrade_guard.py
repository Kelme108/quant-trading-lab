"""Portfolio guard for the Freqtrade bots: health, loss limits and kill switch.

Freqtrade 2026.9 refuses `protections` in the config (they live in the strategy),
and frozen strategies cannot change. So the portfolio-level limits live here,
OUTSIDE the bots, reading their trade databases read-only.

    python ops/freqtrade_guard.py --config ops/guard.forward.json          # report
    python ops/freqtrade_guard.py --config ops/guard.live.json --enforce   # act

Each run (schedule it every 5 minutes with cron / Task Scheduler):
  1. health: container running? last "Bot heartbeat" in the log recent?
  2. realized PnL today (UTC) and since `since_utc`, summed over all bots;
  3. kill switch: if the stop file exists, or a loss limit is hit, and
     --enforce is given (or "enforce": true in the config), `docker stop` every
     bot and write the stop file with the reason. Nothing restarts the bots by
     itself: the operator deletes the stop file and starts them on purpose.

What a stop does: Freqtrade cancels its OPEN ORDERS on exit
(cancel_open_orders_on_exit). Open POSITIONS stay on the exchange, protected
by their exchange-side stop (stoploss_on_exchange). Flattening them is a manual
step on the exchange (documented in docs/runbook-ao-vivo.md).

Writes a JSON status (for the dashboard) and appends alerts to a log file.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc
HEARTBEAT = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ .*Bot heartbeat")

DockerRunner = Callable[[list[str]], tuple[int, str]]


def run_docker(args: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=60)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, repr(exc)


def _path(p: str) -> Path:
    q = Path(p)
    return q if q.is_absolute() else ROOT / q


def realized_pnl(db: Path, since: datetime | None) -> tuple[float, int]:
    """Sum of close_profit_abs of trades closed at/after `since` (UTC). Read-only."""
    if not db.exists():
        return 0.0, 0
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        q, args = "SELECT COALESCE(SUM(close_profit_abs),0), COUNT(*) FROM trades WHERE is_open=0", []
        if since is not None:
            q += " AND close_date >= ?"
            args.append(since.astimezone(UTC).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S"))
        total, n = con.execute(q, args).fetchone()
        open_n = con.execute("SELECT COUNT(*) FROM trades WHERE is_open=1").fetchone()[0]
        return float(total or 0.0), int(open_n)
    finally:
        con.close()


def last_heartbeat(log: Path, tail_bytes: int = 200_000) -> datetime | None:
    if not log.exists():
        return None
    with log.open("rb") as fh:
        fh.seek(max(0, log.stat().st_size - tail_bytes))
        lines = fh.read().decode("utf-8", "replace").splitlines()
    for line in reversed(lines):
        m = HEARTBEAT.match(line)
        if m:
            return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    return None


def evaluate(cfg: dict, now: datetime, docker: DockerRunner) -> dict:
    day_start = datetime.combine(now.astimezone(UTC).date(), time.min, UTC)
    since = cfg.get("since_utc")
    since_dt = datetime.fromisoformat(since).astimezone(UTC) if since else None
    max_age = timedelta(minutes=float(cfg.get("heartbeat_max_minutes", 5)))
    bots, problems = [], []
    day_total = all_total = 0.0
    for b in cfg["bots"]:
        rc, out = docker(["inspect", "-f", "{{.State.Running}}", b["container"]])
        running = rc == 0 and out.strip().lower() == "true"
        hb = last_heartbeat(_path(b["log"]))
        day, open_n = realized_pnl(_path(b["db"]), day_start)
        total, _ = realized_pnl(_path(b["db"]), since_dt)
        day_total += day
        all_total += total
        stale = hb is None or now - hb > max_age
        if not running:
            problems.append(f"{b['name']}: container not running")
        elif stale:
            problems.append(f"{b['name']}: no heartbeat since {hb.isoformat() if hb else 'never'}")
        bots.append({"name": b["name"], "running": running, "last_heartbeat": hb.isoformat() if hb else None,
                     "heartbeat_stale": stale, "open_trades": open_n,
                     "realized_today": round(day, 4), "realized_total": round(total, 4)})
    limits, breaches = cfg.get("limits") or {}, []
    if limits.get("max_daily_loss") is not None and day_total <= -float(limits["max_daily_loss"]):
        breaches.append(f"daily loss {day_total:.2f} <= -{limits['max_daily_loss']}")
    if limits.get("max_total_loss") is not None and all_total <= -float(limits["max_total_loss"]):
        breaches.append(f"total loss {all_total:.2f} <= -{limits['max_total_loss']}")
    return {"checked_at_utc": now.isoformat(), "bots": bots, "problems": problems, "breaches": breaches,
            "realized_today": round(day_total, 4), "realized_total": round(all_total, 4),
            "currency": limits.get("currency", "USDT")}


def stop_all(cfg: dict, docker: DockerRunner) -> list[str]:
    failed = []
    for b in cfg["bots"]:
        rc, out = docker(["stop", b["container"]])
        if rc != 0 and "No such container" not in out:
            failed.append(f"{b['container']}: {out}")
    return failed


def alert(cfg: dict, now: datetime, text: str) -> None:
    line = f"{now.isoformat()} {text}"
    print(line)
    path = _path(cfg.get("alerts_log", "ops/state/alerts.log"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def main(argv: list[str] | None = None, docker: DockerRunner = run_docker,
         now: datetime | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--enforce", action="store_true", help="stop the bots on a breach or stop file")
    args = ap.parse_args(argv)
    cfg = json.loads(_path(args.config).read_text(encoding="utf-8"))
    now = now or datetime.now(UTC)
    enforce = args.enforce or bool(cfg.get("enforce", False))
    status = evaluate(cfg, now, docker)
    stop_file = _path(cfg.get("stop_file", "ops/STOP"))
    status["stop_file_present"] = stop_file.exists()
    status["enforce"] = enforce

    for p in status["problems"]:
        alert(cfg, now, f"[{cfg.get('name', 'guard')}] HEALTH {p}")
    reasons = list(status["breaches"]) + (["stop file present"] if stop_file.exists() else [])
    status["stopped"] = False
    if reasons:
        alert(cfg, now, f"[{cfg.get('name', 'guard')}] KILL {'; '.join(reasons)}"
                        f"{'' if enforce else ' (report only: --enforce not set)'}")
        if enforce:
            if not stop_file.exists():
                stop_file.parent.mkdir(parents=True, exist_ok=True)
                stop_file.write_text(f"{now.isoformat()} {'; '.join(reasons)}\n", encoding="utf-8")
            failed = stop_all(cfg, docker)
            status["stopped"] = not failed
            for f in failed:
                alert(cfg, now, f"[{cfg.get('name', 'guard')}] STOP FAILED {f}")

    out = _path(cfg.get("status_file", "ops/state/guard-status.json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(status, indent=2), encoding="utf-8")
    if reasons:
        return 2
    return 1 if status["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
