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
from urllib.parse import parse_qs
from typing import Callable

from lab import analytics, costs, gates, guard, runner

ROOT = Path(__file__).parents[1]
DB_PATH = ROOT / "research" / "lab.sqlite"
ASSET_DIR = Path(__file__).parent / "dashboard_assets"
ASSET_PATH = ASSET_DIR / "index.html"
VENDOR_CHARTS_PATH = ASSET_DIR / "vendor" / "lightweight-charts.standalone.production.js"
TRADES_VIEW_PATH = ASSET_DIR / "trades_view.js"
PORTAL_PATH = ASSET_DIR / "portal.js"
RESULTS_PATH = ASSET_DIR / "results.js"
DRYRUN_LIVE_PATH = ASSET_DIR / "dryrun_live.js"
INDICES_JS_PATH = ASSET_DIR / "indices.js"
INDICES_TRADE_FILE = re.compile(r"[A-Za-z0-9/._-]{1,160}")
BUDGET_PATH = Path(__file__).parent / "config" / "budget.json"
DEFAULT_PORT = 8765
STALE_AFTER_HOURS = 48
SCENARIO_ORDER = ("optimistic", "base", "conservative", "stress")
GATE_LINE = re.compile(r"^([a-z_]+)(?:\[[^\]]*\])?:\s*(FAIL|inconclusive)")
GATE_DETAIL_LINE = re.compile(r"^([a-z_]+)(?:\[([^\]]*)\])?:\s*(FAIL|inconclusive)")
EXPAND_DATA_COMMAND = "python -m lab.orchestrator expand-data"
INCIDENT_WINDOW = timedelta(days=7)
EXPERIMENT_ID = re.compile(r"[A-Za-z0-9._-]{1,120}")
CANDLE_MARGIN = timedelta(days=5)
MAX_CANDLES = 80000
TRADE_FIELDS = (
    "pair", "open_rate", "close_rate", "profit_ratio", "profit_abs", "stake_amount", "exit_reason", "enter_tag",
    "trade_duration", "min_rate", "max_rate", "initial_stop_loss_abs", "fee_open", "fee_close",
)
RUN_STATS = (
    "total_trades", "winrate", "profit_factor", "sharpe", "sortino", "calmar", "expectancy", "expectancy_ratio",
    "max_relative_drawdown", "profit_total_abs", "starting_balance", "final_balance", "timeframe", "backtest_start",
    "backtest_end",
)

# Every state path the page reads. The page carries the same list (CONTRACT) and a test keeps
# both in step, so a field the server stops emitting, or the page misspells, is caught early.
STATE_CONTRACT = (
    "generated_at", "pairs", "timeframes", "wallet", "safety", "data_health", "cycles", "periods", "cost_scenarios",
    "history.cycles", "history.spend_by_day", "history.bar_by_variant", "forward_test", "portfolio", "budget",
    "gate_bar", "hypotheses", "families", "funnel", "gate_failures", "agents.total_cost_usd", "agents.recent",
    "agents.by_agent", "experiments.total", "experiments.failed", "experiments.cells", "experiments.cells_valid",
    "experiments.cells_invalid", "experiments.earlier_attempts", "experiments.items", "reviews", "proposals",
    "activity", "database", "attention", "strategies",
)

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


def _failing_detail(reasons: list[str]) -> list[dict]:
    """[{gate, scenario, kind}] for every failing line, so the page can say WHICH
    cost scenario broke a gate (scenario is None for gates that have none)."""
    out = []
    for line in reasons:
        match = GATE_DETAIL_LINE.match(line)
        if match:
            out.append({"gate": match.group(1), "scenario": match.group(2),
                        "kind": "fail" if match.group(3) == "FAIL" else "inconclusive"})
    return out


def _periods(splits: dict, pairs: list[str]) -> dict:
    """{pair: {split: {start, end}}} from splits.json, the windows each stage ran on."""
    out: dict = {}
    for pair in pairs:
        entry = splits.get("pairs", {}).get(pair, {})
        out[pair] = {
            name: {"start": entry.get(name, {}).get("start_utc"), "end": entry.get(name, {}).get("end_utc")}
            for name in ("exploration", "validation")
        }
    return out


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


def _largest_gap_after(ordered) -> str | None:
    """Timestamp of the candle right before the largest hole, so the page can show WHERE it is
    (the same hole in several pairs is a shared exchange outage, not a repeated bug)."""
    if len(ordered) < 2:
        return None
    position = int(ordered.reset_index(drop=True).diff().fillna(ordered.iloc[0] - ordered.iloc[0]).values.argmax())
    return _iso(ordered.reset_index(drop=True).iloc[position - 1].to_pydatetime()) if position > 0 else None


def _invalid_candles(frame) -> int | None:
    """Rows whose OHLC cannot be a real candle: any NaN, any value <= 0, or high < low.
    None when the file has no OHLC columns (the check does not apply, not "zero")."""
    columns = ["open", "high", "low", "close"]
    if not all(name in frame.columns for name in columns):
        return None
    ohlc = frame[columns]
    bad = ohlc.isna().any(axis=1) | (ohlc <= 0).any(axis=1) | (ohlc["high"] < ohlc["low"])
    return int(bad.sum())


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

        frame = pd.read_feather(path)
        dates = pd.to_datetime(frame["date"], utc=True)
        ordered = dates.sort_values()
        largest = ordered.diff().max()
        info = {
            "first": _iso(ordered.iloc[0].to_pydatetime()),
            "last": _iso(ordered.iloc[-1].to_pydatetime()),
            "rows": int(len(ordered)),
            "largest_gap_hours": round(float(largest / pd.Timedelta(hours=1)), 1) if len(ordered) > 1 else 0.0,
            "largest_gap_after": _largest_gap_after(ordered),
            "duplicate_timestamps": int(dates.duplicated().sum()),
            "invalid_candles": _invalid_candles(frame),
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


def _run_facts(root: Path, artifact_path: str | None, pair: str) -> dict | None:
    """Trades and Freqtrade's own ratios of one exported backtest (base cost), cached by file mtime."""
    if not artifact_path:
        return None
    path = root / artifact_path
    try:
        stat = path.stat()
    except OSError:
        return None
    key = ("facts", str(path), pair, stat.st_mtime_ns)
    if key in _cache:
        return _cache[key]  # type: ignore[return-value]
    try:
        stats = runner.read_strategy_stats(path)
    except (ValueError, KeyError, OSError):
        return None
    keep = ("open_date", "close_date", "profit_ratio", "profit_abs", "stake_amount", "fee_open", "fee_close",
            "trade_duration", "exit_reason")
    trades = [{k: t.get(k) for k in keep} for t in stats.get("trades", []) if t.get("pair") == pair]
    facts = {"trades": trades, "start": stats.get("starting_balance"),
             "ratios": {k: stats.get(k) for k in ("sharpe", "sortino", "calmar")}}
    _cache[key] = facts
    return facts


# --- one backtest run, for the Trades page ----------------------------------------

def _candles(root: Path, pair: str, timeframe: str, start: datetime, end: datetime) -> list[list[float]] | str:
    """[[epoch_s, open, high, low, close, volume]] around the run, or a reason string."""
    path = root / "user_data" / "data" / "binance" / f"{pair.replace('/', '_')}-{timeframe}.feather"
    if not path.is_file():
        return f"no candle file for {pair} {timeframe}"
    try:
        import pandas as pd

        frame = pd.read_feather(path)
        dates = pd.to_datetime(frame["date"], utc=True)
        keep = (dates >= start - CANDLE_MARGIN) & (dates <= end + CANDLE_MARGIN)
        frame, dates = frame[keep].tail(MAX_CANDLES), dates[keep].tail(MAX_CANDLES)
        seconds = (dates - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(seconds=1)
        return [
            [int(t), float(o), float(h), float(low), float(c), float(v)]
            for t, o, h, low, c, v in zip(
                seconds, frame["open"], frame["high"], frame["low"], frame["close"], frame["volume"]
            )
        ]
    except Exception as error:  # a bad file must not take the page down
        return f"{type(error).__name__}: {error}"[:160]


def trades_payload(root: Path, db_path: Path, experiment_id: str) -> tuple[int, dict]:
    """(http status, body) for GET /api/trades?experiment=N: the trades Freqtrade exported for that
    backtest (origin: simulated), the stats Freqtrade computed, and the candles they happened on."""
    conn = open_readonly(db_path)
    if conn is None:
        return 404, {"error": "registry not found"}
    try:
        row = conn.execute(
            "SELECT id, hypothesis_id, pair, split, artifact_path FROM experiments WHERE id = ?", (experiment_id,)
        ).fetchone()
    finally:
        conn.close()
    if row is None or not row["artifact_path"]:
        return 404, {"error": "no backtest result for this experiment"}
    path = (root / row["artifact_path"]).resolve()
    try:
        path.relative_to(root.resolve())  # the path comes from the registry: keep it inside the project
    except ValueError:
        return 404, {"error": "artifact outside the project"}
    try:
        stats = runner.read_strategy_stats(path)
    except (ValueError, OSError, KeyError) as error:
        return 404, {"error": f"result not readable: {type(error).__name__}"}
    trades = [
        {"open_ts": t.get("open_timestamp"), "close_ts": t.get("close_timestamp"), **{k: t.get(k) for k in TRADE_FIELDS}}
        for t in stats.get("trades", [])
        if t.get("pair") == row["pair"] and t.get("open_timestamp") and t.get("close_timestamp")
    ]
    trades.sort(key=lambda t: t["open_ts"])
    for index, trade in enumerate(trades):
        trade["n"] = index + 1
    timeframe = stats.get("timeframe") or "1h"
    candles: list | str = []
    if trades:
        start = datetime.fromtimestamp(trades[0]["open_ts"] / 1000, timezone.utc)
        end = datetime.fromtimestamp(trades[-1]["close_ts"] / 1000, timezone.utc)
        candles = _candles(root, row["pair"], timeframe, start, end)
    return 200, {
        "experiment_id": row["id"], "hypothesis_id": row["hypothesis_id"], "pair": row["pair"], "split": row["split"],
        "origin": "simulated", "stats": {k: stats.get(k) for k in RUN_STATS}, "trades": trades,
        "candles": candles if isinstance(candles, list) else [],
        "candles_error": candles if isinstance(candles, str) else None,
    }


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


def _dryrun(root: Path) -> list[dict]:
    """One entry per frozen hypothesis (research/forward/*-freeze.json): freeze check and execution quality per pair.
    Read-only. No profit is aggregated here: the dry-run result is monitoring, not an evaluation."""
    from lab import forward  # local import: the dashboard stays importable without the forward harness

    out = []
    for record in sorted((root / "research" / "forward").glob("H-*-freeze.json")):
        frozen = _read_json(record)
        if not isinstance(frozen, dict):
            continue
        hid = record.name.removesuffix("-freeze.json")
        try:
            problems = forward.check_freeze(hid, root)
        except Exception as error:  # a broken git or file must show as a problem, not hide the card
            problems = [f"check failed: {str(error)[:120]}"]
        pairs = {}
        for pair, db in (frozen.get("databases") or {}).items():
            try:
                trades, orders = forward.read_database(root / db)
                quality = forward.execution_quality(trades, orders)
                quality["last_open_date"] = max((str(t["open_date"]) for t in trades), default=None)
                pairs[pair] = quality
            except Exception as error:
                pairs[pair] = {"error": str(error)[:160]}
        out.append({"id": hid, "frozen_at": frozen.get("frozen_at_utc"), "commit": str(frozen.get("git_commit") or "")[:10],
                    "freeze_ok": not problems, "problems": problems[:5], "pairs": pairs, "label": forward.LABEL})
    return out


def _intake(root: Path) -> dict:
    """Ideas by state (F0-F2 of the funnel), read-only from the registry."""
    path = root / "research" / "lab.sqlite"
    counts: dict = {}
    conn = None
    try:
        conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        if _table_exists(conn, "ideas"):
            counts = {state: int(n) for state, n in conn.execute("SELECT state, COUNT(*) FROM ideas GROUP BY state")}
    except sqlite3.Error:
        pass
    finally:
        if conn is not None:
            conn.close()
    return counts


def _forward_test(root: Path) -> dict:
    path = root / "user_data" / "tradesv3.dryrun.sqlite"
    info: dict = {"db_found": path.is_file(), "open": 0, "closed": 0, "profit_abs": 0.0,
                  "hypotheses": _dryrun(root), "intake": _intake(root)}
    try:  # the dry-run rule the pages show (lab/config/dryrun.json): trades and days to decide, days without a trade to discard
        from lab import dryrun
        cfg = dryrun.load_config()
        rule = cfg.get("inactivity") or {}
        info["rule"] = {"need_trades": cfg["min_closed_trades"], "need_days": cfg["min_days"],
                        "discard_after_days": rule.get("discard_after_days"), "max_days_without_trade": rule.get("max_days_without_trade")}
    except (OSError, ValueError, KeyError):
        info["rule"] = None
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


REVIEW_AGENTS = ("validator", "quant", "risk")
REVIEW_NAME = re.compile(r"^(H-\d+)-(exploration|validation|final_test)$")
REVIEW_TEXT_LIMIT = 20_000
FACTS_LIMIT = 12_000
PROPOSAL_TEXT_LIMIT = 4_000
ACTIVITY_LIMIT = 40
AGENT_RUN_LIMIT = 200


def _bool_metric(value) -> bool | None:
    """lookahead_has_bias and recursive_is_stable are stored as 'true'/'false' text."""
    if isinstance(value, str):
        return {"true": True, "false": False}.get(value.strip().lower())
    return None if value is None else bool(value)


def _clip(text: str, limit: int) -> dict:
    return {"text": text[:limit], "truncated": len(text) > limit, "chars": len(text)}


def _reviews(root: Path) -> dict:
    """{hypothesis: {split: {validator|quant|risk: {text, truncated, chars} | None, facts}}} from
    research/experiments/<H>-<split>/. The text is exactly what the agent wrote."""
    base = root / "research" / "experiments"
    out: dict = {}
    if not base.is_dir():
        return out
    for folder in sorted(base.iterdir()):
        match = REVIEW_NAME.match(folder.name)
        if not match or not folder.is_dir():
            continue
        entry: dict = {}
        for agent in REVIEW_AGENTS:
            path = folder / f"{agent}.md"
            try:
                entry[agent] = _clip(path.read_text(encoding="utf-8", errors="replace"), REVIEW_TEXT_LIMIT)
            except OSError:
                entry[agent] = None
        facts = _read_json(folder / "facts.json")
        if facts is None:
            entry["facts"] = None
        else:
            raw = json.dumps(facts, separators=(",", ":"), default=str)
            entry["facts"] = facts if len(raw) <= FACTS_LIMIT else {"truncated": True, "chars": len(raw)}
        out.setdefault(match.group(1), {})[match.group(2)] = entry
    return out


def _proposals(root: Path) -> dict:
    """{hypothesis: {title, rationale, parameters, sources}} from research/proposals/<H>.json."""
    out: dict = {}
    for path in sorted((root / "research" / "proposals").glob("H-*.json")):
        data = _read_json(path)
        if not isinstance(data, dict):
            continue
        parameters = data.get("parameters")
        if len(json.dumps(parameters, default=str)) > PROPOSAL_TEXT_LIMIT:
            parameters = {"truncated": True}
        sources = data.get("sources")
        out[path.stem] = {
            "title": str(data.get("title") or "")[:300],
            "rationale": str(data.get("rationale") or "")[:PROPOSAL_TEXT_LIMIT],
            "parameters": parameters if isinstance(parameters, dict) else {},
            "sources": [
                {"title": str(item.get("title") or "")[:300], "url": str(item.get("url") or "")[:500]}
                for item in sources[:20] if isinstance(item, dict)
            ] if isinstance(sources, list) else [],
        }
    return out


def _activity(events: list[dict], cycles: list[dict]) -> list[dict]:
    """Newest-first feed. Every row is one timestamp that exists in the registry or in a
    cycle report; nothing here is inferred."""
    rows = list(events)
    for cycle in cycles:
        rows.append({"at": cycle["started"], "kind": "cycle", "file": cycle["file"],
                     "completed": str(cycle["outcome"]).startswith("completed"), "spend_usd": cycle["spend_usd"]})
    floor = datetime.min.replace(tzinfo=timezone.utc)
    rows = [row for row in rows if row.get("at")]
    rows.sort(key=lambda row: _parse_time(row["at"]) or floor, reverse=True)
    return rows[:ACTIVITY_LIMIT]


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
        "periods": _periods(splits, pairs),
        "cost_scenarios": [
            {"name": name, "fee_per_side": c.fee_per_side, "slippage_per_side": c.slippage_per_side,
             "spread_total": c.spread_total, "effective_fee_per_side": c.effective_fee_per_side}
            for name, c in costs.SCENARIOS.items()
        ],
        "history": {"cycles": _cycles(root, limit=200), "spend_by_day": [], "bar_by_variant": []},
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
        "strategies": [],
        "trade_index": {"fields": list(TRADE_INDEX_FIELDS), "cells": [], "exit_reasons": [], "trades": []},
        "families": [],
        "funnel": [],
        "gate_failures": [],
        "agents": {"total_cost_usd": 0.0, "recent": [], "by_agent": []},
        "experiments": {"total": 0, "failed": 0, "cells": 0, "cells_valid": 0, "cells_invalid": 0,
                        "earlier_attempts": 0, "items": []},
        "reviews": _reviews(root),
        "proposals": _proposals(root),
        "activity": [],
        "database": {"found": False, "path": None},
    }

    conn = open_readonly(db_path)
    if conn is None:
        state["activity"] = _activity([], state["cycles"])
        state["attention"] = _attention(state, now) + _indices_attention(root, now)
        return state
    try:
        state["database"] = {"found": True, "path": _relative(db_path, root)}
        events = _fill_from_registry(conn, state, root, wallet, in_portfolio)
    finally:
        conn.close()
    state["activity"] = _activity(events, state["cycles"])
    state["attention"] = _attention(state, now) + _indices_attention(root, now)
    return state


def _indices_attention(root: Path, now: datetime) -> list[dict]:
    """Alerts of the index-proxy research (lab/indices_portal.py) for the page header; they link to #/indices.
    Never breaks the main state: a failure here only drops these alerts."""
    try:
        from lab import indices_portal
        alerts = indices_portal.build_indices(root, now)["alerts"]
    except Exception as error:  # noqa: BLE001
        return [{"level": "warning", "text": f"Índices: não foi possível ler os dados ({type(error).__name__})",
                 "kind": "indices", "anchor": "ix", "resolved": False}]
    return [{"level": "warning", "text": a["text"], "kind": "indices", "anchor": "ix", "resolved": False,
             "ix_kind": a.get("kind"), "action": a.get("action")} for a in alerts]


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _starting_wallet(root: Path, artifact_path: str | None, default: float) -> float:
    """The wallet a backtest started with (100 before 2026-11-08, 1000 after), from its export."""
    if not artifact_path:
        return default
    try:
        return runner.read_starting_balance(root / artifact_path) or default
    except (ValueError, KeyError, OSError):
        return default


def _cell_analytics(root: Path, row, wallet: float, run_trades: dict) -> dict | None:
    """Per-backtest metrics from the exported trades; None when the export is not readable."""
    facts = _run_facts(root, row["artifact_path"], row["pair"])
    if facts is None:
        return None
    start = facts["start"] if isinstance(facts["start"], (int, float)) and facts["start"] else wallet
    metrics = analytics.trade_metrics(facts["trades"], float(start))
    metrics.update({k: v for k, v in facts["ratios"].items() if isinstance(v, (int, float))})
    run_trades[row["experiment_id"]] = facts["trades"]
    return metrics


def is_candidate(status: str, in_portfolio: bool) -> bool:
    """True for a hypothesis still alive as a candidate (passed a stage, or in the portfolio). Rejected, dropped,
    failed, invalid, 'not approved' and inconclusive hypotheses are not candidates: the portal hides them by default."""
    text = str(status).lower()
    if in_portfolio:
        return True
    dead = ("reject", "drop", "fail", "invalid", "not approved", "inconclusive")
    return "candidate" in text and not any(word in text for word in dead)


def _strategies(hypotheses: list[dict], run_trades: dict[str, list[dict]], wallet: float) -> list[dict]:
    """One row per (strategy, stage), pooled over the pairs: what the leaderboard, comparison and explorer read.

    Stages are never mixed: exploration and validation are separate rows. Invalid hypotheses are left out (their
    numbers are discarded by the lab). Hypotheses with no readable result do not appear."""
    rows: list[dict] = []
    by_key: dict[tuple[str, str], dict] = {}
    for hy in hypotheses:
        if hy["invalid"]:
            continue
        for split in ("exploration", "validation"):
            cells = [c for c in hy["cells"] if c["split"] == split and c.get("analytics")]
            if not cells:
                continue
            trades = [t for c in cells for t in run_trades.get(c["experiment_id"], [])]
            capital = sum(float(c.get("wallet") or wallet) for c in cells)
            pooled = analytics.trade_metrics(trades, capital)
            per_pair = []
            for c in cells:
                a = c["analytics"]
                stress = c["profit_by_cost"].get("stress")
                per_pair.append({
                    "pair": c["pair"], "experiment_id": c["experiment_id"], "decision": c["decision"], "trades": a["trades"],
                    "roi_pct": a.get("roi_pct"), "winrate": a.get("winrate"), "profit_factor": a.get("profit_factor"),
                    "max_dd_pct": c.get("max_drawdown_pct"), "expectancy_pct": a.get("expectancy_pct"),
                    "expectancy_abs": a.get("expectancy_abs"), "sharpe": a.get("sharpe"), "net_profit_abs": a.get("net_profit_abs"),
                    "profit_excl_best_abs": a.get("profit_excl_best_abs"),
                    "roi_stress_pct": stress / float(c.get("wallet") or wallet) * 100 if isinstance(stress, (int, float)) else None,
                })
            by_year: dict[str, float] = {}
            for t in trades:
                year = str(t["close_date"])[:4]
                by_year[year] = by_year.get(year, 0.0) + float(t["profit_abs"])
            stress_vals = [p["roi_stress_pct"] for p in per_pair if p["roi_stress_pct"] is not None]
            dds = [p["max_dd_pct"] for p in per_pair if isinstance(p["max_dd_pct"], (int, float))]
            sharpes = [p["sharpe"] for p in per_pair if isinstance(p["sharpe"], (int, float))]
            decisions = [p["decision"] for p in per_pair]
            row = {
                "key": f"{hy['id']}:{split}", "id": hy["id"], "family": hy["family"], "status": hy["status"], "stage": split,
                "candidate": is_candidate(hy["status"], hy["in_portfolio"]),
                "archived": bool(hy.get("archived")), "in_dryrun": bool(hy.get("in_dryrun")),
                "in_portfolio": hy["in_portfolio"], "n_pairs": len(cells), "pairs": [p["pair"] for p in per_pair],
                "trades": pooled["trades"], "min_trades_pair": min(p["trades"] for p in per_pair),
                "winrate": pooled.get("winrate"), "winrate_ci": pooled.get("winrate_ci"),
                "profit_factor": pooled.get("profit_factor"), "profit_factor_note": pooled.get("profit_factor_note"),
                "gross_profit_abs": pooled.get("gross_profit_abs"), "gross_loss_abs": pooled.get("gross_loss_abs"), "net_profit_abs": pooled["net_profit_abs"],
                "roi_pct": sum(p["roi_pct"] for p in per_pair if p["roi_pct"] is not None) / len(per_pair),
                "roi_stress_pct": sum(stress_vals) / len(stress_vals) if len(stress_vals) == len(per_pair) else None,
                "expectancy_abs": pooled.get("expectancy_abs"), "expectancy_pct": pooled.get("expectancy_pct"),
                "expectancy_first_pct": pooled.get("expectancy_first_pct"), "expectancy_last_pct": pooled.get("expectancy_last_pct"),
                "trades_last": pooled.get("trades_last"),
                "max_dd_pct": max(dds) if dds else None,
                "sharpe": sum(sharpes) / len(sharpes) if sharpes else None,
                "avg_win_pct": pooled.get("avg_win_pct"), "avg_loss_pct": pooled.get("avg_loss_pct"), "payoff": pooled.get("payoff"),
                "streaks": pooled.get("streaks"), "histogram": pooled.get("histogram"), "monthly": pooled.get("monthly"),
                "exit_reasons": pooled.get("exit_reasons"), "avg_duration_h": pooled.get("avg_duration_h"),
                "fees_paid_abs": pooled.get("fees_paid_abs"), "top_trade_share": pooled.get("top_trade_share"),
                "period": pooled.get("period"),
                "pairs_positive": sum(1 for p in per_pair if (p["net_profit_abs"] or 0) > 0),
                "pairs_excl_best_positive": sum(1 for p in per_pair if (p["profit_excl_best_abs"] or 0) > 0),
                "positive_year_share": sum(1 for v in by_year.values() if v > 0) / len(by_year) if by_year else None,
                "years": {y: v / capital * 100 for y, v in sorted(by_year.items())},
                "gates_all_pass": all(d == "candidate_for_portfolio" for d in decisions),
                "gates_any_rejected": any(d == "rejected" for d in decisions),
                "decisions": {p["pair"]: p["decision"] for p in per_pair},
                "per_pair": per_pair,
                "curve": analytics.downsample([[t, v / capital * 100] for t, v in analytics.cumulative_profit(trades)]),
            }
            by_key[(hy["id"], split)] = row
            rows.append(row)
    for row in rows:
        other = by_key.get((row["id"], "validation" if row["stage"] == "exploration" else "exploration"))
        row["flags"] = analytics.flags(row, other_stage=other if row["stage"] == "exploration" else None)
        row["score"], row["score_parts"] = analytics.evidence_score(row)
    return rows


TRADE_INDEX_FIELDS = ("cell", "open_min", "duration_min", "profit_pct", "profit_abs", "exit_reason")


def _trade_index(hypotheses: list[dict], run_trades: dict[str, list[dict]]) -> dict:
    """Every trade of every current backtest cell (base cost) as one compact table, for the Operations page.

    One row per trade: [cell index, open time in epoch minutes (UTC), duration in minutes, profit in % of the stake,
    profit in quote currency, exit reason index]. Cells carry the hypothesis, pair, stage and starting wallet, so the
    page can express a profit as % of the backtest's own capital (wallets were 100 USDT before 2026-11-08, 1000 after).
    It is large (tens of thousands of rows), so the live page fetches it once from /api/trade-index instead of
    receiving it with every state poll; only the static export embeds it."""
    cells: list[dict] = []
    reasons: dict[str, int] = {}
    rows: list[list] = []
    for hy in hypotheses:
        for cell in hy["cells"]:
            trades = run_trades.get(cell["experiment_id"])
            if not trades:
                continue
            index = len(cells)
            cells.append({"id": hy["id"], "pair": cell["pair"], "split": cell["split"],
                          "experiment_id": cell["experiment_id"], "wallet": cell["wallet"]})
            for trade in trades:
                try:
                    opened = datetime.fromisoformat(str(trade["open_date"]))
                except (KeyError, ValueError):
                    continue
                if opened.tzinfo is None:
                    opened = opened.replace(tzinfo=timezone.utc)
                reason = str(trade.get("exit_reason") or "?")
                rows.append([index, int(opened.timestamp() // 60), int(trade.get("trade_duration") or 0),
                             round(float(trade.get("profit_ratio") or 0.0) * 100, 3),
                             round(float(trade.get("profit_abs") or 0.0), 4), reasons.setdefault(reason, len(reasons))])
    return {"fields": list(TRADE_INDEX_FIELDS), "cells": cells, "exit_reasons": list(reasons), "trades": rows}


def _fill_from_registry(conn, state: dict, root: Path, wallet: float, in_portfolio: set[str]) -> list[dict]:
    """Fills the registry-backed parts of `state`; returns the dated events for the activity feed."""
    pairs = state["pairs"]
    events: list[dict] = []

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

    families: dict[str, dict[str, int]] = {}
    gate_counts: dict[str, dict[str, int]] = {}
    stages = {"registered": 0, "explored": 0, "explore_passed": 0, "validation_run": 0,
              "validation_passed": 0, "in_portfolio": 0}
    hypotheses = []
    run_trades: dict[str, list[dict]] = {}

    for hypothesis in conn.execute("SELECT * FROM hypotheses ORDER BY rowid"):
        hid = hypothesis["id"]
        status = str(hypothesis["status"])
        invalid = status.startswith("invalid")
        family_counts = families.setdefault(hypothesis["family"], {"registered": 0, "tested": 0, "invalid": 0})
        family_counts["registered"] += 1
        events.append({"at": hypothesis["proposed_at_utc"], "kind": "hypothesis", "hypothesis_id": hid,
                       "family": hypothesis["family"]})

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
                cell_wallet = _starting_wallet(root, row["artifact_path"], wallet)
                cells.append(
                    {
                        "pair": pair,
                        "split": split,
                        "experiment_id": row["experiment_id"],
                        "decision": row["decision"],
                        "trades": metrics.get("trades__base"),
                        "return_pct": (base_profit / cell_wallet * 100) if isinstance(base_profit, (int, float)) else None,
                        "wallet": cell_wallet,
                        "max_drawdown_pct": metrics.get("max_drawdown_pct__base"),
                        "buy_and_hold_pct": metrics.get("benchmark_buy_and_hold_return_pct"),
                        "profit_by_cost": {
                            name: metrics.get(f"net_profit_quote__{name}") for name in SCENARIO_ORDER
                        },
                        "profit_excl_best_by_cost": {
                            name: metrics.get(f"net_profit_excl_best_trade__{name}") for name in SCENARIO_ORDER
                        },
                        "drawdown_by_cost": {
                            name: metrics.get(f"max_drawdown_pct__{name}") for name in SCENARIO_ORDER
                        },
                        "trades_by_cost": {name: metrics.get(f"trades__{name}") for name in SCENARIO_ORDER},
                        "benchmark_cash_pct": metrics.get("benchmark_cash_return_pct"),
                        "lookahead_has_bias": _bool_metric(metrics.get("lookahead_has_bias")),
                        "recursive_is_stable": _bool_metric(metrics.get("recursive_is_stable")),
                        "decided_at_utc": row["decided_at_utc"],
                        "failing_gates": failing,
                        "failing_detail": _failing_detail(reasons),
                        "reasons": reasons,
                        "equity": _equity(root, row["artifact_path"], cell_wallet),
                        "analytics": _cell_analytics(root, row, cell_wallet, run_trades),
                    }
                )
                if not invalid:
                    for item in failing:
                        counts = gate_counts.setdefault(item["gate"], {"fail": 0, "inconclusive": 0})
                        counts[item["kind"]] += 1

        family_counts["tested"] += int(bool(cells))
        family_counts["invalid"] += int(invalid)

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
                "candidate": is_candidate(status, hid in in_portfolio),
                "rule": hypothesis["ex_ante_rule"],
                "notes": hypothesis["notes"] or "",
                "proposed_at_utc": hypothesis["proposed_at_utc"],
                "cells": cells,
            }
        )

    # `archived` marks what is no longer alive (not a candidate, not in the portfolio, not in dry-run). Since the
    # portal v4 (2026-11-08, owner's request: "quero ver todas as estratégias") every valid hypothesis with results
    # reaches the rankings and comparisons, each row carrying its status and `archived` flag so the page labels it;
    # invalid hypotheses stay out, because the lab discards their numbers.
    in_dryrun = {path.name.split("-freeze.json")[0] for path in (root / "research" / "forward").glob("H-*-freeze.json")}
    for hy in hypotheses:
        hy["in_dryrun"] = hy["id"] in in_dryrun
        hy["candidate"] = hy["candidate"] or hy["in_dryrun"]
        hy["archived"] = not (hy["candidate"] and not hy["invalid"])
    live = [hy for hy in hypotheses if not hy["archived"]]
    state["archived_count"] = len(hypotheses) - len(live)
    state["hypotheses"] = hypotheses  # every one, flagged
    valid = [hy for hy in hypotheses if not hy["invalid"]]
    state["strategies"] = _strategies(valid, run_trades, wallet)
    state["trade_index"] = _trade_index(valid, run_trades)
    cap = state["budget"]["max_variants_per_family"]
    gate_config = {"net_profit": {"base_threshold_quote": state["gate_bar"]["base_threshold_quote"],
                                  "multiple_testing_penalty": {"per_variant_increase": state["gate_bar"]["per_variant_increase"]}}}
    # `used` is what the lab counts toward the cap and the rising bar: every
    # hypothesis REGISTERED in the family (registry.count_variants_in_family),
    # tested or not. `tested` is how many of them actually have results.
    state["families"] = [
        {"family": name, "used": counts["registered"], "tested": counts["tested"], "invalid": counts["invalid"],
         "cap": cap, "next_bar_quote": gates.required_net_profit(gate_config, counts["registered"])}
        for name, counts in sorted(families.items())
    ]
    state["history"]["bar_by_variant"] = [
        {"prior_variants": n, "required_quote": gates.required_net_profit(gate_config, n)} for n in range(int(cap or 0))
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
        runs = [
            dict(row)
            for row in conn.execute(
                "SELECT id, agent, hypothesis_id, purpose, status, cost_usd, num_turns, duration_s, "
                "started_at_utc, substr(result_excerpt, 1, 1000) AS excerpt, length(result_excerpt) AS excerpt_chars "
                f"FROM agent_runs ORDER BY id DESC LIMIT {AGENT_RUN_LIMIT}"
            )
        ]
        by_agent = [
            {"agent": row[0], "runs": int(row[1]), "last_started_at_utc": row[2], "total_cost_usd": float(row[3]),
             "avg_turns": row[4], "avg_duration_s": row[5]}
            for row in conn.execute(
                "SELECT agent, COUNT(*), MAX(started_at_utc), COALESCE(SUM(cost_usd), 0), AVG(num_turns), AVG(duration_s) "
                "FROM agent_runs GROUP BY agent"
            )
        ]
        for entry in by_agent:
            last = conn.execute(
                "SELECT status, hypothesis_id, purpose FROM agent_runs WHERE agent = ? ORDER BY id DESC LIMIT 1",
                (entry["agent"],),
            ).fetchone()
            entry.update(last_status=last[0], last_hypothesis_id=last[1], last_purpose=last[2])
        state["agents"] = {
            "total_cost_usd": float(conn.execute("SELECT COALESCE(SUM(cost_usd), 0) FROM agent_runs").fetchone()[0]),
            "recent": runs,
            "by_agent": by_agent,
        }
        events.extend({"at": r["started_at_utc"], "kind": "agent", "agent": r["agent"], "hypothesis_id": r["hypothesis_id"],
                       "purpose": r["purpose"], "status": r["status"]} for r in runs)
        state["history"]["spend_by_day"] = [
            {"day": row[0], "usd": float(row[1]), "calls": int(row[2])}
            for row in conn.execute(
                "SELECT substr(started_at_utc, 1, 10), COALESCE(SUM(cost_usd), 0), COUNT(*) FROM agent_runs "
                "GROUP BY 1 ORDER BY 1 DESC LIMIT 30"
            )
        ]
    counts = dict(conn.execute("SELECT status, COUNT(*) FROM experiments GROUP BY status").fetchall())
    failed_at = conn.execute("SELECT MAX(created_at_utc) FROM experiments WHERE status = 'failed'").fetchone()[0]
    cells_total, cells_invalid = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(h.status LIKE 'invalid%'), 0) FROM "
        "(SELECT DISTINCT hypothesis_id, pair, split FROM experiments) c JOIN hypotheses h ON h.id = c.hypothesis_id"
    ).fetchone()
    total = sum(counts.values())

    current_ids = {row["experiment_id"] for row in latest.values()}
    items = []
    for row in conn.execute(
        "SELECT e.id, e.hypothesis_id, e.pair, e.split, e.cost_scenario, e.strategy_file, e.strategy_sha256, "
        "       e.command, e.status, e.created_at_utc, e.artifact_path, d.decision, d.decided_at_utc, d.reasons_json "
        "FROM experiments e LEFT JOIN decisions d ON d.id = (SELECT MAX(id) FROM decisions WHERE experiment_id = e.id) "
        "ORDER BY e.created_at_utc DESC, e.rowid DESC"
    ):
        item = dict(row)
        item["reasons"] = json.loads(item.pop("reasons_json")) if row["reasons_json"] else []
        item["current"] = row["id"] in current_ids
        items.append(item)
        events.append({"at": row["created_at_utc"], "kind": "experiment", "experiment_id": row["id"],
                       "hypothesis_id": row["hypothesis_id"], "pair": row["pair"], "split": row["split"], "status": row["status"]})
    for row in conn.execute(
        "SELECT d.experiment_id, d.decision, d.decided_at_utc, e.hypothesis_id, e.pair, e.split "
        "FROM decisions d JOIN experiments e ON e.id = d.experiment_id"
    ):
        events.append({"at": row["decided_at_utc"], "kind": "decision", "experiment_id": row["experiment_id"],
                       "hypothesis_id": row["hypothesis_id"], "pair": row["pair"], "split": row["split"],
                       "decision": row["decision"]})
    state["experiments"] = {
        "total": total, "failed": counts.get("failed", 0), "failed_latest_at": failed_at,
        # what the 11 are made of: one current result per hypothesis x pair x stage,
        # plus the earlier attempts of the same cell that a rerun replaced
        "cells": int(cells_total), "cells_invalid": int(cells_invalid), "cells_valid": int(cells_total - cells_invalid),
        "earlier_attempts": total - int(cells_total),
        "items": items,
    }
    return events


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _short_pair(pair: str) -> str:
    return pair.split("/")[0]


def _attention(state: dict, now: datetime) -> list[dict]:
    """What needs a person's eyes. `level` and `text` are the plain reading; the
    other fields let the page word the impact and link to the detail section
    (`anchor`). `resolved` marks an incident that a later completed cycle has
    superseded: it stays visible as history but does not count as open."""
    items: list[dict] = []

    def add(level: str, text: str, kind: str, anchor: str, **extra) -> None:
        items.append({"level": level, "text": text, "kind": kind, "anchor": anchor, **extra})

    safety = state["safety"]
    if safety["protected_files_changed"]:
        add("critical", f"Arquivos protegidos alterados: {', '.join(safety['protected_files_changed'])}", "safety", "sec-seguranca")
    if not safety["dry_run"]:
        add("critical", "dry_run NÃO está ligado em config.dryrun.json", "safety", "sec-seguranca")
    if not safety["no_exchange_keys"]:
        add("critical", "Há chave de corretora preenchida em config.dryrun.json", "safety", "sec-seguranca")
    if safety["trading_mode"] != "spot":
        add("critical", f"trading_mode é '{safety['trading_mode']}', esperado 'spot'", "safety", "sec-seguranca")
    if not safety["final_test_locked"]:
        add("warning", "O teste final está destrancado: a composição do portfólio não pode mais mudar.", "safety", "sec-seguranca")
    if not safety["api_disabled"]:
        add("warning", "A API do Freqtrade está habilitada em config.dryrun.json.", "safety", "sec-seguranca")
    if not state["database"]["found"]:
        add("warning", "research/lab.sqlite não existe: nenhum experimento registrado.", "database_missing", "sec-hipoteses")

    # An incident that a LATER completed cycle has superseded is history, not an
    # alarm: it stays in the agents table, but a dashboard that keeps showing red
    # for something already fixed teaches people to ignore red.
    completed = sorted(
        moment for moment in (_parse_time(c["started"]) for c in state["cycles"]
                              if str(c["outcome"]).startswith("completed") and c["started"]) if moment
    )
    last_ok = completed[-1] if completed else None

    def unresolved(when: str | None) -> bool:
        moment = _parse_time(when)
        if moment is None or now - moment > INCIDENT_WINDOW:
            return False
        return last_ok is None or moment > last_ok

    for run in state["agents"]["recent"]:
        if not unresolved(run["started_at_utc"]):
            continue
        who = {"agent": run["agent"], "hypothesis_id": run["hypothesis_id"], "raw": run["excerpt"]}
        if run["status"] == "guard_violation":
            add("critical", f"Violação do guard pelo agente {run['agent']} ({run['hypothesis_id'] or '-'}): {run['excerpt']}", "guard_violation", "sec-agentes", **who)
        elif run["status"] == "failed":
            add("warning", f"Chamada do agente {run['agent']} falhou ({run['hypothesis_id'] or '-'}): {run['excerpt']}", "agent_failed", "sec-agentes", **who)
    if state["experiments"]["failed"] and unresolved(state["experiments"].get("failed_latest_at")):
        add("warning", f"{state['experiments']['failed']} experimento(s) com status 'failed' desde o último ciclo completo.",
            "failed_experiments", "sec-hipoteses", count=state["experiments"]["failed"])
    for index, cycle in enumerate(state["cycles"]):
        outcome = str(cycle["outcome"])
        started = _parse_time(cycle["started"])
        if outcome.startswith("completed") or started is None or now - started > INCIDENT_WINDOW:
            continue
        paths = re.findall(r"'([^']+)'", (re.search(r"\[(.*)\]", outcome) or [None, ""])[1])
        facts = {"cycle_started": cycle["started"], "raw": outcome, "paths": paths,
                 "guard": "GuardAbort" in outcome, "file": cycle["file"]}
        if unresolved(cycle["started"]):
            if index == 0:
                add("warning", f"O último ciclo parou: {outcome}", "stopped_cycle", "sec-ciclos", resolved=False, **facts)
        else:
            later = next((m for m in completed if m > started), None)
            add("warning", f"Ciclo interrompido em {cycle['started']} (superado por um ciclo completo posterior): {outcome}",
                "stopped_cycle", "sec-ciclos", resolved=True, superseded_by=later.isoformat() if later else None, **facts)

    stale = [row for row in state["data_health"] if row.get("stale")]
    for row in state["data_health"]:
        if row.get("error"):
            add("warning", f"{row['pair']} {row['timeframe']}: {row['error']}", "data_error", "sec-dados",
                pair=row["pair"], timeframe=row["timeframe"], raw=row["error"])
        elif row.get("stale"):
            days = row["age_hours"] / 24
            fresh = [_short_pair(r["pair"]) for r in state["data_health"]
                     if r["timeframe"] == row["timeframe"] and r.get("last") and not r.get("stale")]
            add("warning", f"{row['pair']} {row['timeframe']}: último candle há {days:.0f} dias. Rode `{EXPAND_DATA_COMMAND}`.",
                "stale_data", "sec-dados", pair=row["pair"], timeframe=row["timeframe"], age_days=round(days, 1),
                fresh_pairs=fresh, stale_pairs=[_short_pair(r["pair"]) for r in stale], command=EXPAND_DATA_COMMAND)
    return items


# --- page and server ------------------------------------------------------------

def _embed(state: dict) -> str:
    """JSON safe to place inside a <script> element."""
    text = json.dumps(state, separators=(",", ":"), allow_nan=False, default=str)
    for char, escape in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"),
                         (" ", "\\u2028"), (" ", "\\u2029")):
        text = text.replace(char, escape)
    return text


def _without_trade_index(state: dict) -> dict:
    """The state the live page polls: the trade index is served on its own (GET /api/trade-index)."""
    return {k: v for k, v in state.items() if k != "trade_index"}


def render_page(state: dict, *, nonce: str | None, live: bool) -> str:
    template = ASSET_PATH.read_text(encoding="utf-8")
    if live:
        state = _without_trade_index(state)
    nonce_attr = f' nonce="{nonce}"' if nonce else ""
    # bundled, trusted files first; the state (agent and web text) goes in last so nothing in it is re-scanned
    return (
        template.replace("/*__TRADES_VIEW__*/", TRADES_VIEW_PATH.read_text(encoding="utf-8"))
        .replace("/*__PORTAL__*/", PORTAL_PATH.read_text(encoding="utf-8"))
        .replace("/*__RESULTS__*/", RESULTS_PATH.read_text(encoding="utf-8"))
        .replace("/*__DRYRUN_LIVE__*/", DRYRUN_LIVE_PATH.read_text(encoding="utf-8"))
        .replace("/*__INDICES__*/", INDICES_JS_PATH.read_text(encoding="utf-8"))
        .replace("/*__VENDOR_CHARTS__*/", VENDOR_CHARTS_PATH.read_text(encoding="utf-8"))
        .replace("__NONCE_ATTR__", nonce_attr)
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
    trades: Callable[[str], tuple[int, dict]]


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

    @staticmethod
    def _served(state: dict) -> dict:
        """The state plus the instant THIS response was made. `generated_at` can be
        a few seconds older (the provider caches), and neither says whether the
        lab itself is idle; this one only says the server is alive."""
        return {**_without_trade_index(state), "served_at": _iso(datetime.now(timezone.utc))}

    def _handle(self) -> None:
        # A page on another site can make the browser send requests to
        # 127.0.0.1 under its own hostname (DNS rebinding); only our own names pass.
        if not self._host_allowed():
            self._send(403, b"forbidden host", "text/plain; charset=utf-8")
            return
        path, _, query = self.path.partition("?")
        try:
            if path == "/api/trades":
                raw = parse_qs(query).get("experiment", [""])[0]
                if not EXPERIMENT_ID.fullmatch(raw):
                    self._send(400, b'{"error": "bad experiment id"}', "application/json; charset=utf-8")
                    return
                status, body = self.server.trades(raw)
                self._send(status, json.dumps(body, allow_nan=False).encode("utf-8"), "application/json; charset=utf-8")
            elif path == "/api/dryrun":
                from lab import livedata  # local import: the dashboard stays importable without the live feeds

                self._send(200, json.dumps(livedata.clean(livedata.bots_state(ROOT, livedata.last_prices(ROOT))), allow_nan=False).encode("utf-8"), "application/json; charset=utf-8")
            elif path == "/api/live":
                from lab import livedata

                query_args = parse_qs(query)
                try:
                    payload = livedata.live_chart(query_args.get("pair", [""])[0], query_args.get("tf", [""])[0], ROOT)
                except ValueError as error:
                    self._send(400, json.dumps({"error": str(error)}).encode("utf-8"), "application/json; charset=utf-8")
                    return
                self._send(200, json.dumps(livedata.clean(payload), allow_nan=False).encode("utf-8"), "application/json; charset=utf-8")
            elif path == "/api/indices":
                from lab import indices_portal

                self._send(200, _embed(indices_portal.cached_indices(ROOT)).encode("utf-8"), "application/json; charset=utf-8")
            elif path == "/api/indices/trades":
                from lab import indices_portal

                raw = parse_qs(query).get("file", [""])[0]
                if not INDICES_TRADE_FILE.fullmatch(raw):
                    self._send(400, b'{"error": "bad file name"}', "application/json; charset=utf-8")
                    return
                status, body = indices_portal.trades_file(raw, ROOT)
                self._send(status, _embed(indices_portal.clean(body)).encode("utf-8"), "application/json; charset=utf-8")
            elif path == "/api/trade-index":
                index = self.server.provider().get("trade_index") or {}
                self._send(200, _embed(index).encode("utf-8"), "application/json; charset=utf-8")
            elif path == "/api/state":
                body = _embed(self._served(self.server.provider())).encode("utf-8")
                self._send(200, body, "application/json; charset=utf-8")
            elif path == "/":
                nonce = secrets.token_urlsafe(16)
                page = render_page(self._served(self.server.provider()), nonce=nonce, live=True).encode("utf-8")
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


def create_server(
    provider: Callable[[], dict], port: int = DEFAULT_PORT, trades: Callable[[str], tuple[int, dict]] | None = None
) -> _Server:
    """A server bound to loopback only; port 0 picks a free port (used by tests)."""
    server = _Server(("127.0.0.1", port), _Handler)
    server.provider = provider
    server.trades = trades or (lambda experiment_id: trades_payload(ROOT, DB_PATH, experiment_id))
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
        from lab import indices_portal

        state = build_state()
        state["indices"] = indices_portal.build_indices()      # the static file has no /api/indices to fetch
        print(export_html(args.out, state))
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
