"""Research universes beyond crypto for the portal's Resultados pages (plan docs/plano-b3-reuso.md F4; owner
2026-11-16: "a seção que estava usando para os cripto, a seção para esses novos ativos, mini índice, mini dólar,
também para os outros que vão entrar").

Each universe is a lane of b3/proxy_research.py (research/<lane>/results + trades): its reads are turned into the
SAME structures the crypto pages already read (hypotheses with cells, strategies rows, trade index, experiments),
through the SAME functions (lab.dashboard._strategies / _trade_index, lab.analytics). The pages stay one code path.

Conventions (shown on the pages): every rule trades 1 contract (B3) or 1 unit (proxies) and every trade's result is
its net return as a share of that notional, so a backtest "wallet" is 100 and a trade's profit_abs is its net % of
the notional. Sums are simple (not compounded), as on the crypto pages. Origin: BACKTEST, base cost scenario.

Adding a universe = adding an entry to UNIVERSES (a lane directory + labels).
"""

from __future__ import annotations

import ast
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SP = ZoneInfo("America/Sao_Paulo")
WALLET = 100.0
DECISION = {"passed": "candidate_for_portfolio", "rejected": "rejected", "inconclusive": "inconclusive"}
RESULT_NAME = re.compile(r"^(?P<rule>[PC]-[A-Za-z0-9_]+?)-(?P<symbol>[A-Z0-9]+)-(?P<split>exploration|validation|final_test)-(?P<at>\d{4}-\d{2}-\d{2}T\d{6})$")


@dataclass(frozen=True)
class Universe:
    id: str
    label: str
    lane_dir: str
    unit: str
    markets_label: str
    periods: dict
    note: str


UNIVERSES: dict[str, Universe] = {
    "b3": Universe("b3", "B3 (WIN/WDO)", "research/b3", "1 contrato", "contratos",
                   {"exploration": "nov/2021 a jun/2024", "validation": "jul/2024 a set/2025", "final_test": "out/2025 em diante"},
                   "Mini índice (WIN) e mini dólar (WDO) reais, da conta de demonstração da Clear, em 5 anos de barras de "
                   "1 e 5 minutos. Custos em reais por contrato; operações sempre zeradas antes do fim do pregão."),
    "proxies": Universe("proxies", "Substitutos (índices dos EUA e DAX)", "research/proxies", "1 unidade", "mercados",
                        {"exploration": "2017 a 2023", "validation": "2024 a jun/2025", "final_test": "jul/2025 em diante"},
                        "Índices dos EUA e o DAX da MetaQuotes-Demo, usados como ponte antes dos dados da B3."),
}


def _read(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _ms(iso: str) -> int:
    return int(datetime.fromisoformat(iso).timestamp() * 1000)


def _trade_dicts(rows: list[list], columns: list[str], symbol: str) -> list[dict]:
    """Rows of a lane's trade list -> the Freqtrade-like dicts lab.analytics reads (wallet 100 = the notional)."""
    ix = {c: i for i, c in enumerate(columns)}
    out = []
    for r in rows:
        opened, closed = datetime.fromisoformat(r[ix["entry_time"]]), datetime.fromisoformat(r[ix["exit_time"]])
        net = float(r[ix["net_pct"]])
        out.append({"pair": symbol, "open_date": opened.isoformat(), "close_date": closed.isoformat(),
                    "open_timestamp": int(opened.timestamp() * 1000), "close_timestamp": int(closed.timestamp() * 1000),
                    "open_rate": float(r[ix["entry_price"]]), "close_rate": float(r[ix["exit_price"]]),
                    "profit_ratio": net / 100.0, "profit_abs": net, "stake_amount": WALLET,
                    "trade_duration": int((closed - opened).total_seconds() // 60),
                    "exit_reason": str(r[ix["exit_reason"]]), "enter_tag": str(r[ix["entry_reason"]]),
                    "is_short": r[ix["side"]] == "short", "side": r[ix["side"]],
                    "gross_pct": float(r[ix["gross_pct"]])})
    return out


def _latest_reads(lane_dir: Path) -> dict[tuple[str, str, str], tuple[dict, Path]]:
    """(rule, symbol, split) -> the most recent result and its file (exploration may be re-read after a code fix)."""
    out: dict = {}
    for f in sorted((lane_dir / "results").glob("*.json")):
        m = RESULT_NAME.match(f.stem)
        if not m:
            continue
        res = _read(f)
        if not isinstance(res, dict) or "scenarios" not in res:
            continue
        out[(m["rule"], m["symbol"], m["split"])] = (res, f)
    return out


def _trades_for(lane_dir: Path, stem: str) -> dict | None:
    """The read's own trade list, or the recalculated one of a read made before trade lists were saved."""
    m = RESULT_NAME.match(stem)
    short = f"{m['rule']}-{m['symbol']}-{m['split']}" if m else stem          # without the read's time stamp
    for p in (lane_dir / "trades" / f"{stem}.json", lane_dir / "trades" / "recalc" / f"{stem}.json",
              lane_dir / "trades" / "recalc" / f"{short}.json"):
        if p.is_file():
            return _read(p)
    return None


def _equity(trades: list[dict]) -> list[list]:
    eq, out = WALLET, []
    for t in sorted(trades, key=lambda t: t["close_timestamp"]):
        eq += t["profit_abs"]
        out.append([t["close_timestamp"], round(eq, 4)])
    return out


# ---------------------------------------------------------------------------------------------
# Descriptions of the rules (text only)
# ---------------------------------------------------------------------------------------------

def _doc_of(path: Path) -> str:
    try:
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
    except (OSError, SyntaxError, ValueError):
        return ""
    return " ".join(doc.split("\n\n")[0].split())[:900]


def _describe(rule_id: str, strategy_name: str, root: Path) -> tuple[str, str, str]:
    """(family name in CamelCase, timeframe token, plain description)."""
    if rule_id.startswith("C-"):
        name = rule_id[2:]
        files = [root / "user_data" / "strategies" / f"{name}.py", root / "user_data" / "strategies" / "_archive" / f"{name}.py"]
        path = next((p for p in files if p.is_file()), None)
        tf = "1h"
        if path:
            m = re.search(r'^\s*timeframe\s*=\s*["\'](\w+)["\']', path.read_text(encoding="utf-8", errors="replace"), re.M)
            tf = m.group(1) if m else tf
        family = re.sub(r"_H\d+_v\d+$|_v\d+$", "", name)
        doc = _doc_of(path) if path else ""
        return family, tf, (f"Estratégia de cripto ({name}, candles de {tf}) rodada no motor da B3 pelo adaptador "
                            f"b3/freqtrade_adapter.py, execução em 5 minutos e zerada antes do fim do pregão. " + doc).strip()
    snake = re.sub(r"^P-\d+_", "", strategy_name or rule_id)
    family = "".join(w.capitalize() for w in snake.split("_") if w)
    prop = _read(root / "research" / "proxies" / "proposals" / f"{rule_id}.json") or {}
    idea = prop.get("idea") or prop.get("hypothesis") or prop.get("summary") or ""
    if not idea:
        num = rule_id[2:]
        hits = list((root / "b3" / "proxy_rules").glob(f"p{num}_*.py"))
        idea = _doc_of(hits[0]) if hits else ""
    tf = "1m" if "1m" in (strategy_name or "") else "5m"
    return family, tf, (f"Regra intradiária {rule_id} (candles de {tf}). " + str(idea)).strip()


def _status(cells: list[dict]) -> str:
    val = [c for c in cells if c["split"] == "validation"]
    exp = [c for c in cells if c["split"] == "exploration"]
    if any(c["decision"] == "candidate_for_portfolio" for c in val):
        return "validation: candidate"
    if val:
        return "not approved at validation"
    if any(c["decision"] == "candidate_for_portfolio" for c in exp):
        return "exploration: candidate"
    if exp and all(c["decision"] == "inconclusive" for c in exp):
        return "inconclusive (fewer than 30 trades)"
    return "rejected at exploration"


# ---------------------------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------------------------

def build_universe(uid: str, root: Path = ROOT, with_index: bool = True) -> dict:
    from lab import dashboard   # the same row builders as the crypto pages
    u = UNIVERSES[uid]
    lane_dir = root / u.lane_dir
    reads = _latest_reads(lane_dir)
    scope = _read(root / "b3" / "config" / ("scope_b3.json" if uid == "b3" else "scope_proxies.json")) or {}
    allowed_tf = {f"{m}m" for m in scope.get("timeframes_min", [])}
    hyps: dict[str, dict] = {}
    run_trades: dict[str, list[dict]] = {}
    experiments = []
    symbols: list[str] = []
    for (rule, symbol, split), (res, f) in sorted(reads.items()):
        if split == "final_test":
            continue          # the locked split never reaches the Resultados pages (P-003 proxies: Índices section)
        if allowed_tf and _describe(rule, res.get("strategy", ""), root)[1] not in allowed_tf:
            continue          # owner 2026-11-16: only 1/5/15-minute rules on the pages (1h/4h reads stay in the ledger)
        tl = _trades_for(lane_dir, f.stem)
        if tl is None:
            continue
        trades = _trade_dicts(tl.get("rows", []), tl.get("columns", []), symbol)
        exp_id = f"{uid}.{f.stem}"
        run_trades[exp_id] = trades
        if symbol not in symbols:
            symbols.append(symbol)
        sc = res["scenarios"]
        analytics_ = dashboard.analytics.trade_metrics(trades, WALLET) if trades else {"trades": 0}
        if trades:
            first, last = trades[0]["open_date"], trades[-1]["close_date"]
            analytics_["period"] = analytics_.get("period") or [first, last]
        cell = {"experiment_id": exp_id, "pair": symbol, "split": split, "wallet": WALLET,
                "decision": DECISION.get(res["gates"]["decision"], "inconclusive"),
                "analytics": analytics_ if trades else None,
                "profit_by_cost": {k: v.get("net_return_pct") for k, v in sc.items()},
                "max_drawdown_pct": sc["base"].get("max_drawdown_pct"),
                "failing_gates": [{"gate": x} for x in res["gates"].get("fails", [])],
                "equity": _equity(trades), "buy_and_hold_pct": None,
                "net_bar_pct": res["gates"].get("net_bar_pct"), "prior_variants": res.get("prior_variants"),
                "cost_round_trip_base_pct": res.get("cost_round_trip_base_pct"), "read_at_utc": res.get("read_at_utc")}
        hy = hyps.get(rule)
        if hy is None:
            family, tf, rule_text = _describe(rule, res.get("strategy", ""), root)
            hy = hyps[rule] = {"id": rule, "family": family, "status": "", "invalid": False, "archived": False,
                               "in_dryrun": False, "in_portfolio": False, "rule": f"{tf} · {rule_text}",
                               "notes": rule_text, "proposed_at_utc": res.get("read_at_utc"), "cells": [],
                               "origin": "crypto-adapter" if rule.startswith("C-") else "intraday-rule"}
        hy["cells"].append(cell)
        hy["proposed_at_utc"] = min(hy["proposed_at_utc"] or cell["read_at_utc"], cell["read_at_utc"] or "")
        experiments.append({"id": exp_id, "hypothesis_id": rule, "pair": symbol, "split": split,
                            "artifact_path": f"{u.lane_dir}/results/{f.name}", "status": "completed", "current": True,
                            "created_at_utc": res.get("read_at_utc"), "decision": cell["decision"]})
    for hy in hyps.values():
        hy["status"] = _status(hy["cells"])
    hypotheses = sorted(hyps.values(), key=lambda x: x["id"])
    gates = _read(root / "b3" / "config" / ("gates_b3.json" if uid == "b3" else "gates_proxies.json")) or {}
    ledger = [json.loads(line) for line in (lane_dir / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
              if line.strip()] if (lane_dir / "ledger.jsonl").is_file() else []
    pairs_read = {(r["rule"], r["symbol"]) for r in ledger if r.get("split") == "exploration"}
    out = {
        "id": uid, "label": u.label, "unit": u.unit, "markets_label": u.markets_label, "periods": u.periods, "note": u.note,
        "pairs": symbols, "hypotheses": hypotheses,
        "strategies": dashboard._strategies(hypotheses, run_trades, WALLET),
        "experiments": {"items": sorted(experiments, key=lambda e: e["created_at_utc"] or "", reverse=True)},
        "gate_bar": {"minimum_trades": gates.get("minimum_trades", 30), "per_variant_increase": gates.get("per_variant_increase"),
                     "net_floor_pct": gates.get("net_return_pct_floor"), "trials": len(pairs_read),
                     "current_bar_pct": (gates.get("net_return_pct_floor", 1.0) * (1 + gates.get("per_variant_increase", 0.1) * len(pairs_read)))},
        "families": sorted({h["family"] for h in hypotheses}),
        "screen": _read(lane_dir / "crypto_screen.json") if uid == "b3" else None,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if out["screen"]:
        out["screen"] = {k: v for k, v in out["screen"].items() if k != "rows"} | {
            "rows": [{k: r.get(k) for k in ("rule", "symbol", "trades", "mean_gross_pct", "gross_over_cost",
                                            "net_base_pct", "net_conservative_pct", "passes_triage", "gate_decision")}
                     for r in out["screen"].get("rows", [])]}
    if with_index:
        out["trade_index"] = dashboard._trade_index(hypotheses, run_trades)
    return out


_CACHE: dict[str, tuple[float, dict]] = {}
TTL_S = 30.0


def cached(uid: str, root: Path = ROOT) -> dict:
    now = time.monotonic()
    hit = _CACHE.get(uid)
    if hit and now - hit[0] < TTL_S:
        return hit[1]
    data = build_universe(uid, root)
    _CACHE[uid] = (now, data)
    return data


def summaries(root: Path = ROOT) -> dict:
    """What the state poll carries: every universe without its trade index (served by /api/trade-index?universe=)."""
    out = {}
    for uid in UNIVERSES:
        try:
            out[uid] = {k: v for k, v in cached(uid, root).items() if k != "trade_index"}
        except Exception as exc:  # noqa: BLE001 - a broken lane must not take the page down
            out[uid] = {"id": uid, "label": UNIVERSES[uid].label, "error": f"{type(exc).__name__}: {exc}"[:200],
                        "hypotheses": [], "strategies": [], "pairs": [], "experiments": {"items": []}}
    return out


CHART_TIMEFRAMES = ("1m", "5m", "15m")      # owner 2026-11-16: charts on 1, 5 and 15 minutes, 1 and 5 first


def default_timeframe(rule_tf: str | None) -> str:
    """The chart opens on the rule's own clock when it is 1 or 5 minutes, else on 5 minutes."""
    return rule_tf if rule_tf in ("1m", "5m") else "5m"


def _session_day(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, timezone.utc).astimezone(SP).date().isoformat()


def trades_payload(experiment_id: str, root: Path = ROOT, tf: str | None = None, day: str | None = None) -> tuple[int, dict]:
    """GET /api/trades?experiment=<uid>.<result stem>[&tf=1m|5m|15m][&day=YYYY-MM-DD]: the same shape as the crypto
    chart page reads. Candles are ONE session (Sao Paulo day) on the chosen timeframe: by default the day of the last
    trade; `days` lists every session with a trade so the page can move between them."""
    uid, _, stem = experiment_id.partition(".")
    if uid not in UNIVERSES or not RESULT_NAME.match(stem):
        return 404, {"error": "unknown experiment"}
    u = UNIVERSES[uid]
    lane_dir = root / u.lane_dir
    res = _read(lane_dir / "results" / f"{stem}.json")
    tl = _trades_for(lane_dir, stem)
    if not res or tl is None or res.get("split") == "final_test":
        return 404, {"error": "no trade list for this read"}
    symbol = res["symbol"]
    trades = []
    for i, t in enumerate(_trade_dicts(tl.get("rows", []), tl.get("columns", []), symbol)):
        trades.append({"open_ts": t["open_timestamp"], "close_ts": t["close_timestamp"], "n": i + 1, "unit": u.unit,
                       **{k: t.get(k) for k in ("pair", "open_rate", "close_rate", "profit_ratio", "profit_abs",
                                                "stake_amount", "exit_reason", "enter_tag", "trade_duration")}})
    rule_tf = _rule_timeframe(res)
    timeframe = tf if tf in CHART_TIMEFRAMES else default_timeframe(rule_tf)
    days = sorted({_session_day(t["open_ts"]) for t in trades})
    if day not in days:
        day = days[-1] if days else None
    candles: list | str = []
    if day:
        candles = _candles(uid, symbol, timeframe, day, root)
    stats = {"total_trades": len(trades), "timeframe": timeframe, "starting_balance": WALLET,
             "backtest_start": res.get("start_utc"), "backtest_end": res.get("end_utc"),
             "profit_total_abs": sum(t["profit_abs"] for t in trades)}
    return 200, {"experiment_id": experiment_id, "hypothesis_id": res["rule"], "pair": symbol, "split": res["split"],
                 "origin": "simulated", "stats": stats, "trades": trades,
                 "candles": candles if isinstance(candles, list) else [],
                 "candles_error": candles if isinstance(candles, str) else None,
                 "timeframe": timeframe, "timeframes": list(CHART_TIMEFRAMES), "rule_timeframe": rule_tf,
                 "day": day, "days": days,
                 "unit_note": f"Resultados em % do valor de {u.unit}; preços em pontos do {symbol}."}


def _rule_timeframe(res: dict) -> str | None:
    m = re.search(r"(\d+)m\b", str(res.get("strategy", "")))
    if res.get("rule", "").startswith("C-"):
        return None                      # a crypto strategy: its signal clock is in its own file (15m and up)
    return f"{m.group(1)}m" if m and m.group(1) in ("1", "5", "15") else "5m"


_BARS: dict = {}


def _bars(uid: str, symbol: str, tf: str, root: Path):
    """Whole history of one symbol and timeframe, cached (a 1-minute file is ~700k bars)."""
    key = (uid, symbol, tf, str(root))
    if key not in _BARS:
        if uid == "b3":
            from b3 import b3_data
            _BARS[key] = b3_data.load_b3_bars(symbol, tf, root / "user_data" / "data" / "b3" / "clear")
        else:
            from b3.markets import load_bars
            if tf == "15m":            # the MetaQuotes export has 1m and 5m: 15m is built from 5m
                b = load_bars(symbol, "5m").set_index("time")
                df = b.resample("15min", label="left", closed="left").agg(
                    {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna().reset_index()
                _BARS[key] = df
            else:
                _BARS[key] = load_bars(symbol, tf)
    return _BARS[key]


def _candles(uid: str, symbol: str, tf: str, day: str, root: Path) -> list | str:
    try:
        import pandas as pd
        df = _bars(uid, symbol, tf, root)
        t = pd.to_datetime(df["time"], utc=True)
        keep = (t.dt.tz_convert(SP).dt.date.astype(str) == day).to_numpy()
        df, t = df[keep], t[keep]
        secs = (t - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(seconds=1)
        return [[int(s), float(o), float(h), float(lw), float(c), float(v)]
                for s, o, h, lw, c, v in zip(secs, df["open"], df["high"], df["low"], df["close"], df["volume"])]
    except Exception as exc:  # noqa: BLE001
        return f"{type(exc).__name__}: {exc}"[:160]
