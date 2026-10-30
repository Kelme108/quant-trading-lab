"""Local monitoring dashboard for the research lab.

    python -m lab.dashboard serve            # http://127.0.0.1:8765, refreshes itself
    python -m lab.dashboard export           # one self-contained snapshot file

It shows what FreqUI does not: the research pipeline (funnel, gates, trial
counts, agent spend, data freshness, safety state). The live bot view is
FreqUI's job, and only matters once a forward test is running.

Read-only by construction: the registry is opened with SQLite `mode=ro`, nothing
here writes to the project, and the server answers GET only, on loopback only.
Text in the page comes from agents and from the web, so it is untrusted: the
page inserts it with textContent, the state is embedded with `<` escaped, and a
per-request nonce CSP forbids every script but the page's own.
"""

from __future__ import annotations

import argparse
import json
import re
import secrets
import sqlite3
import sys
import threading
import time
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable

from lab import gates, guard, runner

ROOT = Path(__file__).parents[1]
DB_PATH = ROOT / "research" / "lab.sqlite"
ASSET_PATH = Path(__file__).parent / "dashboard_assets" / "index.html"
BUDGET_PATH = Path(__file__).parent / "config" / "budget.json"
DEFAULT_PORT = 8765
STALE_AFTER_HOURS = 48
SCENARIO_ORDER = ("optimistic", "base", "conservative", "stress")
GATE_LINE = re.compile(r"^([a-z_]+)(?:\[[^\]]*\])?:\s*(FAIL|inconclusive)")

_cache: dict[tuple, object] = {}


# --- small readers --------------------------------------------------------------

def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def open_readonly(db_path: Path) -> sqlite3.Connection | None:
    """The registry, opened so that it cannot be written. None if it is missing."""
    if not db_path.is_file():
        return None
    conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone()
    return row is not None


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _failing_gates(reasons: list[str]) -> list[dict]:
    """[{gate, kind}] for every gate line that is not a pass; one per gate."""
    seen: dict[str, str] = {}
    for line in reasons:
        match = GATE_LINE.match(line)
        if match and match.group(1) not in seen:
            seen[match.group(1)] = "fail" if match.group(2) == "FAIL" else "inconclusive"
    return [{"gate": gate, "kind": kind} for gate, kind in seen.items()]


# --- sections -------------------------------------------------------------------

def _safety(root: Path, splits: dict) -> dict:
    config = _read_json(root / "user_data" / "config.dryrun.json") or {}
    exchange = config.get("exchange", {})
    try:
        changed = guard.check_protected_files_unchanged(root)
    except Exception:  # not a git checkout, git missing: unknown, not "fine"
        changed = None
    return {
        "dry_run": config.get("dry_run") is True,
        "trading_mode": config.get("trading_mode"),
        "no_exchange_keys": not exchange.get("key") and not exchange.get("secret"),
        "api_disabled": not config.get("api_server", {}).get("enabled", False),
        "final_test_locked": splits.get("final_test", {}).get("final_test_unlocked") is not True,
        "protected_files_changed": changed,
        "wallet": config.get("dry_run_wallet"),
        "stake_amount": config.get("stake_amount"),
    }


def _data_range(path: Path) -> dict:
    try:
        stat = path.stat()
    except OSError:
        return {"error": "no data file"}
    key = ("data", str(path), stat.st_mtime_ns)
    if key in _cache:
        return _cache[key]  # type: ignore[return-value]
    try:
        import pandas as pd

        dates = pd.to_datetime(pd.read_feather(path, columns=["date"])["date"], utc=True).sort_values()
        largest = dates.diff().max()
        info = {
            "first": _iso(dates.iloc[0].to_pydatetime()),
            "last": _iso(dates.iloc[-1].to_pydatetime()),
            "rows": int(len(dates)),
            "largest_gap_hours": round(float(largest / pd.Timedelta(hours=1)), 1) if len(dates) > 1 else 0.0,
        }
    except Exception as error:  # a view must not crash on a bad file
        info = {"error": f"{type(error).__name__}: {error}"[:160]}
    _cache[key] = info
    return info


def _data_health(root: Path, pairs: list[str], timeframes: list[str], now: datetime) -> list[dict]:
    rows = []
    for pair in pairs:
        for timeframe in timeframes:
            path = root / "user_data" / "data" / "binance" / f"{pair.replace('/', '_')}-{timeframe}.feather"
            info = _data_range(path)
            row = {"pair": pair, "timeframe": timeframe, **info}
            if "last" in info:
                last = datetime.strptime(info["last"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                row["age_hours"] = round((now - last).total_seconds() / 3600, 1)
                row["stale"] = row["age_hours"] > STALE_AFTER_HOURS
            rows.append(row)
    return rows


def _equity(root: Path, artifact_path: str | None, starting_wallet: float) -> list[list[float]] | None:
    """[[epoch_ms, balance]] from a Freqtrade export (base cost scenario)."""
    if not artifact_path:
        return None
    path = root / artifact_path
    try:
        stat = path.stat()
    except OSError:
        return None
    key = ("equity", str(path), stat.st_mtime_ns)
    if key in _cache:
        return _cache[key]  # type: ignore[return-value]
    try:
        trades = sorted(runner.read_trades(path), key=lambda t: t["close_date"])
        start = runner.read_starting_balance(path) or starting_wallet
    except (ValueError, KeyError, OSError):
        return None
    points: list[list[float]] = []
    balance = start
    if trades:
        first = datetime.fromisoformat(trades[0]["open_date"])
        points.append([first.timestamp() * 1000, balance])
    for trade in trades:
        balance += float(trade["profit_abs"])
        points.append([datetime.fromisoformat(trade["close_date"]).timestamp() * 1000, balance])
    _cache[key] = points
    return points


def _latest_portfolio(root: Path) -> dict | None:
    files = sorted((root / "research" / "portfolio").glob("*.json"))
    if not files:
        return None
    snapshot = _read_json(files[-1])
    if snapshot is None:
        return None
    return {
        "file": files[-1].name,
        "created_at_utc": snapshot.get("created_at_utc"),
        "included": [entry["hypothesis_id"] for entry in snapshot.get("included", [])],
        "evaluated": len(snapshot.get("evaluations", [])),
    }


def _cycles(root: Path, limit: int = 8) -> list[dict]:
    rows = []
    for path in sorted((root / "research" / "experiments").glob("cycle-*.md"))[-limit:]:
        text = path.read_text(encoding="utf-8", errors="replace")
        outcome = re.search(r"- Outcome: (.+)", text)
        spend = re.search(r"- Agent spend this cycle: ([\d.]+) USD", text)
        started = re.search(r"# Cycle (\S+)", text)
        rows.append(
            {
                "file": path.name,
                "started": started.group(1) if started else None,
                "outcome": outcome.group(1).strip() if outcome else "unknown",
                "spend_usd": float(spend.group(1)) if spend else None,
            }
        )
    return list(reversed(rows))


def _forward_test(root: Path) -> dict:
    path = root / "user_data" / "tradesv3.dryrun.sqlite"
    info: dict = {"db_found": path.is_file(), "open": 0, "closed": 0, "profit_abs": 0.0}
    conn = None
    try:
        conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        if not _table_exists(conn, "trades"):
            return info
        row = conn.execute(
            "SELECT COALESCE(SUM(is_open), 0), COUNT(*) - COALESCE(SUM(is_open), 0), "
            "COALESCE(SUM(CASE WHEN is_open = 0 THEN close_profit_abs END), 0) FROM trades"
        ).fetchone()
        info.update(open=int(row[0]), closed=int(row[1]), profit_abs=float(row[2]))
    except sqlite3.Error as error:
        info["error"] = str(error)[:160]
    finally:
        if conn is not None:
            conn.close()
    return info


# --- the state ------------------------------------------------------------------

def build_state(
    *,
    db_path: Path = DB_PATH,
    root: Path = ROOT,
    now: datetime | None = None,
    splits: dict | None = None,
    scenarios: dict | None = None,
    budget: dict | None = None,
    gates_config: dict | None = None,
) -> dict:
    """Everything the page shows, as plain JSON-able data. Never writes."""
    now = now or datetime.now(timezone.utc)
    splits = splits if splits is not None else runner.load_splits()
    scenarios = scenarios if scenarios is not None else runner.load_scenarios()
    budget = budget if budget is not None else (_read_json(BUDGET_PATH) or {})
    gates_config = gates_config if gates_config is not None else gates.load_gates()
    pairs = runner.enabled_pairs(scenarios)
    timeframes = runner.enabled_timeframes(scenarios)

    safety = _safety(root, splits)
    wallet = float(safety["wallet"]) if isinstance(safety["wallet"], (int, float)) else 100.0
    portfolio_snapshot = _latest_portfolio(root)
    in_portfolio = set(portfolio_snapshot["included"]) if portfolio_snapshot else set()
    data_health = _data_health(root, pairs, timeframes, now)

    state: dict = {
        "generated_at": _iso(now),
        "pairs": pairs,
        "timeframes": timeframes,
        "wallet": wallet,
        "safety": safety,
        "data_health": data_health,
        "cycles": _cycles(root),
        "forward_test": _forward_test(root),
        "portfolio": portfolio_snapshot,
        "budget": {
            "max_variants_per_family": budget.get("max_variants_per_family"),
            "agent_budget_usd_per_call": budget.get("agent_budget_usd_per_call"),
            "max_agent_budget_usd_per_cycle": budget.get("max_agent_budget_usd_per_cycle"),
        },
        "gate_bar": {
            "base_threshold_quote": gates_config["net_profit"]["base_threshold_quote"],
            "per_variant_increase": gates_config["net_profit"]["multiple_testing_penalty"]["per_variant_increase"],
            "max_drawdown_pct": gates_config["max_drawdown"]["max_ratio"] * 100,
            "minimum_trades": gates_config["minimum_trades"]["value"],
        },
        "hypotheses": [],
        "families": [],
        "funnel": [],
        "gate_failures": [],
        "agents": {"total_cost_usd": 0.0, "recent": []},
        "experiments": {"total": 0, "failed": 0},
        "database": {"found": False},
    }

    conn = open_readonly(db_path)
    if conn is None:
        state["attention"] = _attention(state, now)
        return state
    try:
        state["database"] = {"found": True}
        _fill_from_registry(conn, state, root, wallet, in_portfolio)
    finally:
        conn.close()
    state["attention"] = _attention(state, now)
    return state


def _fill_from_registry(conn, state: dict, root: Path, wallet: float, in_portfolio: set[str]) -> None:
    pairs = state["pairs"]

    latest: dict[tuple[str, str, str], sqlite3.Row] = {}
    for row in conn.execute(
        "SELECT e.id AS experiment_id, e.hypothesis_id, e.pair, e.split, e.artifact_path, e.created_at_utc, "
        "       d.decision, d.reasons_json, d.decided_at_utc "
        "FROM experiments e JOIN decisions d ON d.experiment_id = e.id "
        "WHERE d.id = (SELECT MAX(id) FROM decisions WHERE experiment_id = e.id) "
        "ORDER BY e.created_at_utc, e.rowid"
    ):
        latest[(row["hypothesis_id"], row["pair"], row["split"])] = row

    metrics_by_experiment: dict[str, dict[str, object]] = {}
    for row in conn.execute("SELECT experiment_id, name, value, text_value FROM metrics"):
        value = row["value"] if row["value"] is not None else row["text_value"]
        metrics_by_experiment.setdefault(row["experiment_id"], {})[row["name"]] = value

    experiments_started = {
        (row["hypothesis_id"], row["pair"], row["split"])
        for row in conn.execute("SELECT hypothesis_id, pair, split FROM experiments WHERE status = 'completed'")
    }

    families: dict[str, int] = {}
    gate_counts: dict[str, dict[str, int]] = {}
    stages = {"registered": 0, "explored": 0, "explore_passed": 0, "validation_run": 0,
              "validation_passed": 0, "in_portfolio": 0}
    hypotheses = []

    for hypothesis in conn.execute("SELECT * FROM hypotheses ORDER BY rowid"):
        hid = hypothesis["id"]
        status = str(hypothesis["status"])
        invalid = status.startswith("invalid")
        families[hypothesis["family"]] = families.get(hypothesis["family"], 0) + 1

        cells = []
        for pair in pairs:
            for split in ("exploration", "validation"):
                row = latest.get((hid, pair, split))
                if row is None:
                    continue
                metrics = metrics_by_experiment.get(row["experiment_id"], {})
                reasons = json.loads(row["reasons_json"])
                failing = _failing_gates(reasons)
                base_profit = metrics.get("net_profit_quote__base")
                cells.append(
                    {
                        "pair": pair,
                        "split": split,
                        "experiment_id": row["experiment_id"],
                        "decision": row["decision"],
                        "trades": metrics.get("trades__base"),
                        "return_pct": (base_profit / wallet * 100) if isinstance(base_profit, (int, float)) else None,
                        "max_drawdown_pct": metrics.get("max_drawdown_pct__base"),
                        "buy_and_hold_pct": metrics.get("benchmark_buy_and_hold_return_pct"),
                        "profit_by_cost": {
                            name: metrics.get(f"net_profit_quote__{name}") for name in SCENARIO_ORDER
                        },
                        "failing_gates": failing,
                        "reasons": reasons,
                        "equity": _equity(root, row["artifact_path"], wallet),
                    }
                )
                if not invalid:
                    for item in failing:
                        counts = gate_counts.setdefault(item["gate"], {"fail": 0, "inconclusive": 0})
                        counts[item["kind"]] += 1

        def decisions_for(split: str) -> list[str | None]:
            return [latest[(hid, p, split)]["decision"] if (hid, p, split) in latest else None for p in pairs]

        def ran(split: str) -> bool:
            return all((hid, p, split) in experiments_started for p in pairs)

        if not invalid:
            stages["registered"] += 1
            stages["explored"] += int(ran("exploration"))
            stages["explore_passed"] += int(all(d == "candidate_for_portfolio" for d in decisions_for("exploration")))
            stages["validation_run"] += int(ran("validation"))
            stages["validation_passed"] += int(all(d == "candidate_for_portfolio" for d in decisions_for("validation")))
            stages["in_portfolio"] += int(hid in in_portfolio)

        hypotheses.append(
            {
                "id": hid,
                "family": hypothesis["family"],
                "status": status,
                "invalid": invalid,
                "in_portfolio": hid in in_portfolio,
                "rule": hypothesis["ex_ante_rule"],
                "notes": hypothesis["notes"] or "",
                "proposed_at_utc": hypothesis["proposed_at_utc"],
                "cells": cells,
            }
        )

    state["hypotheses"] = hypotheses
    cap = state["budget"]["max_variants_per_family"]
    state["families"] = [
        {"family": name, "used": used, "cap": cap,
         "next_bar_quote": gates.required_net_profit(
             {"net_profit": {"base_threshold_quote": state["gate_bar"]["base_threshold_quote"],
                             "multiple_testing_penalty": {"per_variant_increase": state["gate_bar"]["per_variant_increase"]}}},
             used)}
        for name, used in sorted(families.items())
    ]
    state["funnel"] = [
        {"key": key, "count": stages[key]}
        for key in ("registered", "explored", "explore_passed", "validation_run", "validation_passed", "in_portfolio")
    ]
    state["gate_failures"] = sorted(
        ({"gate": gate, **counts, "total": counts["fail"] + counts["inconclusive"]} for gate, counts in gate_counts.items()),
        key=lambda item: -item["total"],
    )

    if _table_exists(conn, "agent_runs"):
        state["agents"] = {
            "total_cost_usd": float(
                conn.execute("SELECT COALESCE(SUM(cost_usd), 0) FROM agent_runs").fetchone()[0]
            ),
            "recent": [
                dict(row)
                for row in conn.execute(
                    "SELECT agent, hypothesis_id, purpose, status, cost_usd, num_turns, duration_s, "
                    "started_at_utc, substr(result_excerpt, 1, 240) AS excerpt "
                    "FROM agent_runs ORDER BY id DESC LIMIT 20"
                )
            ],
        }
    counts = dict(conn.execute("SELECT status, COUNT(*) FROM experiments GROUP BY status").fetchall())
    failed_at = conn.execute("SELECT MAX(created_at_utc) FROM experiments WHERE status = 'failed'").fetchone()[0]
    state["experiments"] = {"total": sum(counts.values()), "failed": counts.get("failed", 0), "failed_latest_at": failed_at}


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _attention(state: dict, now: datetime) -> list[dict]:
    items: list[dict] = []
    safety = state["safety"]
    if safety["protected_files_changed"]:
        items.append({"level": "critical", "text": f"Arquivos protegidos alterados: {', '.join(safety['protected_files_changed'])}"})
    if not safety["dry_run"]:
        items.append({"level": "critical", "text": "dry_run NÃO está ligado em config.dryrun.json"})
    if not safety["no_exchange_keys"]:
        items.append({"level": "critical", "text": "Há chave de corretora preenchida em config.dryrun.json"})
    if safety["trading_mode"] != "spot":
        items.append({"level": "critical", "text": f"trading_mode é '{safety['trading_mode']}', esperado 'spot'"})
    if not safety["final_test_locked"]:
        items.append({"level": "warning", "text": "O teste final está destrancado: a composição do portfólio não pode mais mudar."})
    if not safety["api_disabled"]:
        items.append({"level": "warning", "text": "A API do Freqtrade está habilitada em config.dryrun.json."})
    if not state["database"]["found"]:
        items.append({"level": "warning", "text": "research/lab.sqlite não existe: nenhum experimento registrado."})

    # An incident that a LATER completed cycle has superseded is history, not an
    # alarm: it stays in the agents table, but a dashboard that keeps showing red
    # for something already fixed teaches people to ignore red.
    last_ok = max(
        (_parse_time(c["started"]) for c in state["cycles"] if str(c["outcome"]).startswith("completed") and c["started"]),
        default=None,
    )

    def unresolved(when: str | None) -> bool:
        moment = _parse_time(when)
        if moment is None or now - moment > timedelta(days=7):
            return False
        return last_ok is None or moment > last_ok

    for run in state["agents"]["recent"]:
        if not unresolved(run["started_at_utc"]):
            continue
        if run["status"] == "guard_violation":
            items.append({"level": "critical", "text": f"Violação do guard pelo agente {run['agent']} ({run['hypothesis_id'] or '-'}): {run['excerpt']}"})
        elif run["status"] == "failed":
            items.append({"level": "warning", "text": f"Chamada do agente {run['agent']} falhou ({run['hypothesis_id'] or '-'}): {run['excerpt']}"})
    if state["experiments"]["failed"] and unresolved(state["experiments"].get("failed_latest_at")):
        items.append({"level": "warning", "text": f"{state['experiments']['failed']} experimento(s) com status 'failed' desde o último ciclo completo."})
    for cycle in state["cycles"][:1]:
        if not str(cycle["outcome"]).startswith("completed") and unresolved(cycle["started"]):
            items.append({"level": "warning", "text": f"O último ciclo parou: {cycle['outcome']}"})
    for row in state["data_health"]:
        if row.get("error"):
            items.append({"level": "warning", "text": f"{row['pair']} {row['timeframe']}: {row['error']}"})
        elif row.get("stale"):
            days = row["age_hours"] / 24
            items.append({"level": "warning", "text": f"{row['pair']} {row['timeframe']}: último candle há {days:.0f} dias. Rode `python -m lab.orchestrator expand-data`."})
    return items


# --- page and server ------------------------------------------------------------

def _embed(state: dict) -> str:
    """JSON safe to place inside a <script> element."""
    text = json.dumps(state, separators=(",", ":"), allow_nan=False, default=str)
    for char, escape in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"),
                         (" ", "\\u2028"), (" ", "\\u2029")):
        text = text.replace(char, escape)
    return text


def render_page(state: dict, *, nonce: str | None, live: bool) -> str:
    template = ASSET_PATH.read_text(encoding="utf-8")
    return (
        template.replace("__NONCE_ATTR__", f' nonce="{nonce}"' if nonce else "")
        .replace("__LIVE__", "true" if live else "false")
        .replace("__STATE__", _embed(state))
    )


class StateProvider:
    """build_state() behind a short cache, so a few open tabs do not rebuild it
    on every poll."""

    def __init__(self, build: Callable[[], dict], ttl_seconds: float = 5.0) -> None:
        self._build, self._ttl = build, ttl_seconds
        self._lock = threading.Lock()
        self._value: dict | None = None
        self._at = 0.0

    def __call__(self) -> dict:
        with self._lock:
            if self._value is None or time.monotonic() - self._at > self._ttl:
                self._value, self._at = self._build(), time.monotonic()
            return self._value


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    provider: Callable[[], dict]


class _Handler(BaseHTTPRequestHandler):
    server: _Server

    def log_message(self, format: str, *args) -> None:  # keep the console quiet
        pass

    def _host_allowed(self) -> bool:
        port = self.server.server_address[1]
        return self.headers.get("Host", "") in {f"127.0.0.1:{port}", f"localhost:{port}"}

    def _send(self, status: int, body: bytes, content_type: str, extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for name, value in (extra or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _handle(self) -> None:
        # A page on another site can make the browser send requests to
        # 127.0.0.1 under its own hostname (DNS rebinding); only our own names pass.
        if not self._host_allowed():
            self._send(403, b"forbidden host", "text/plain; charset=utf-8")
            return
        path = self.path.split("?", 1)[0]
        try:
            if path == "/api/state":
                body = _embed(self.server.provider()).encode("utf-8")
                self._send(200, body, "application/json; charset=utf-8")
            elif path == "/":
                nonce = secrets.token_urlsafe(16)
                page = render_page(self.server.provider(), nonce=nonce, live=True).encode("utf-8")
                csp = (
                    "default-src 'none'; "
                    f"script-src 'nonce-{nonce}'; style-src 'unsafe-inline'; "
                    "connect-src 'self'; img-src data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
                )
                self._send(200, page, "text/html; charset=utf-8", {"Content-Security-Policy": csp})
            elif path == "/healthz":
                self._send(200, b"ok", "text/plain; charset=utf-8")
            else:
                self._send(404, b"not found", "text/plain; charset=utf-8")
        except Exception as error:  # report, do not take the server down
            self._send(500, f"error: {type(error).__name__}".encode(), "text/plain; charset=utf-8")
            print(f"dashboard error on {path}: {error!r}", file=sys.stderr)

    do_GET = do_HEAD = _handle

    def _refuse(self) -> None:
        self._send(405, b"read-only", "text/plain; charset=utf-8", {"Allow": "GET, HEAD"})

    do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _refuse


def create_server(provider: Callable[[], dict], port: int = DEFAULT_PORT) -> _Server:
    """A server bound to loopback only; port 0 picks a free port (used by tests)."""
    server = _Server(("127.0.0.1", port), _Handler)
    server.provider = provider
    return server


def export_html(out_path: Path, state: dict) -> Path:
    """One self-contained file: no server, no network, no refresh."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_page(state, nonce=None, live=False), encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m lab.dashboard", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve", help="serve the live dashboard on loopback")
    serve.add_argument("--port", type=int, default=DEFAULT_PORT)
    serve.add_argument("--open", action="store_true", help="open it in the browser")
    export = sub.add_parser("export", help="write a static snapshot")
    export.add_argument("--out", type=Path, default=ROOT / "research" / "dashboard.html")
    args = parser.parse_args(argv)

    if args.command == "export":
        print(export_html(args.out, build_state()))
        return 0

    try:
        server = create_server(StateProvider(build_state), args.port)
    except OSError as error:
        print(f"cannot listen on 127.0.0.1:{args.port}: {error}", file=sys.stderr)
        return 1
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"dashboard on {url} (read-only, loopback only; Ctrl+C to stop)")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
