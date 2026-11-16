"""Measure and download B3 history from a MetaTrader 5 terminal. Plan, F1.2 and F1.3. Sends no orders.

Runs on the Windows host, terminal open and logged in, with the live venv:

    live/.venv/Scripts/python.exe -m b3.data.mt5_history symbols
    live/.venv/Scripts/python.exe -m b3.data.mt5_history depth --symbols 'WIN$N' 'WDO$N' WINZ26 WDOZ26
    live/.venv/Scripts/python.exe -m b3.data.mt5_history download --symbols 'WIN$N' --timeframes M5 --start 2010-01-01
    live/.venv/Scripts/python.exe -m b3.data.mt5_history ticks --symbols WINZ26 --start 2026-11-03 --end 2026-11-06

(Single quotes matter in PowerShell: an unquoted `$N` is a variable and silently disappears.)

Only the standard library and the injected `MetaTrader5` module are used (the live venv has no
pandas). Times are stored exactly as the server returns them (`time_server`, seconds of the
SERVER's wall clock); b3/data/store.py converts them to UTC with a stated server time zone, so the
conversion can be redone if the broker's server clock turns out to be different (F1.2 checks it).
Credentials come from the environment or live/.env and are never printed or written.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

UTC = timezone.utc
TIMEFRAMES = {"M1": "TIMEFRAME_M1", "M5": "TIMEFRAME_M5", "M15": "TIMEFRAME_M15", "M30": "TIMEFRAME_M30",
              "H1": "TIMEFRAME_H1", "D1": "TIMEFRAME_D1"}
RATE_FIELDS = ("time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume")
TICK_FIELDS = ("time_msc", "bid", "ask", "last", "volume_real", "flags")
TICK_FLAG_BUY, TICK_FLAG_SELL = 32, 64          # MetaTrader5 constants (the module's own values win)
DEFAULT_PATTERNS = ("WIN*", "WDO*", "IND*", "DOL*")
SUSPICIOUS_COUNTS = (65_000, 100_000, 500_000, 1_000_000)   # "Max bars in chart" terminal settings


def load_env_file(path: str | Path) -> None:
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def connect(mt5: Any) -> None:
    kw = {"path": os.environ.get("MT5_PATH"), "login": os.environ.get("MT5_LOGIN"),
          "password": os.environ.get("MT5_PASSWORD"), "server": os.environ.get("MT5_SERVER")}
    kw = {k: v for k, v in kw.items() if v}
    if "login" in kw:
        kw["login"] = int(kw["login"])
    if not mt5.initialize(**kw):
        raise ConnectionError(f"MT5 initialize failed: {mt5.last_error()}")
    if mt5.account_info() is None:
        raise ConnectionError("MT5: no account logged in")


def attach(mt5: Any, broker_config: str | Path) -> None:
    """Attach to the broker terminal named in b3/config/broker_mt5.json AS IT IS ALREADY LOGGED IN: no login, no
    password, live/.env ignored (it may hold another broker's account). Refuses anything but a demo account."""
    cfg = json.loads(Path(broker_config).read_text(encoding="utf-8"))
    if not mt5.initialize(path=cfg["terminal_path"]):
        raise ConnectionError(f"MT5 initialize failed: {mt5.last_error()}")
    a = mt5.account_info()
    if a is None:
        raise ConnectionError("MT5: no account logged in")
    if getattr(a, "trade_mode", None) != getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", 0):
        mt5.shutdown()
        raise ConnectionError("MT5: the logged-in account is not a demo account; refusing to continue")
    if cfg.get("server") and getattr(a, "server", None) != cfg["server"]:
        mt5.shutdown()
        raise ConnectionError(f"MT5: logged in to {getattr(a, 'server', None)}, expected {cfg['server']}")


def account_meta(mt5: Any) -> dict:
    """Broker identity for the manifest. Never the login or the password."""
    a, t = mt5.account_info(), mt5.terminal_info()
    return {"company": getattr(a, "company", ""), "server": getattr(a, "server", ""),
            "trade_mode": getattr(a, "trade_mode", None), "margin_mode": getattr(a, "margin_mode", None),
            "currency": getattr(a, "currency", ""), "terminal_build": getattr(t, "build", None)}


def _field(rec, name):
    return rec[name]


def list_symbols(mt5: Any, patterns=DEFAULT_PATTERNS) -> dict[str, list[str]]:
    return {p: sorted(s.name for s in (mt5.symbols_get(p) or ())) for p in patterns}


def _rates(mt5: Any, symbol: str, tf: str, start: datetime, end: datetime):
    rates = mt5.copy_rates_range(symbol, getattr(mt5, TIMEFRAMES[tf]), start, end)
    return [] if rates is None else list(rates)


def bar_depth(mt5: Any, symbol: str, tf: str, *, first_year: int = 2000,
              now: Callable[[], datetime] = lambda: datetime.now(UTC)) -> dict:
    """First and last bar (server epochs) and the bar count, scanning year by year."""
    if not mt5.symbol_select(symbol, True):
        return {"symbol": symbol, "timeframe": tf, "error": "symbol not available"}
    end_year = now().year
    first = last = None
    count = 0
    per_year = {}
    for year in range(first_year, end_year + 1):
        bars = _rates(mt5, symbol, tf, datetime(year, 1, 1, tzinfo=UTC), datetime(year + 1, 1, 1, tzinfo=UTC))
        if not bars:
            continue
        times = [int(_field(b, "time")) for b in bars]
        first = min(times) if first is None else min(first, min(times))
        last = max(times) if last is None else max(last, max(times))
        count += len(bars)
        per_year[year] = len(bars)
    out = {"symbol": symbol, "timeframe": tf, "first_server": first, "last_server": last,
           "first": _iso(first), "last": _iso(last), "bars": count, "bars_per_year": per_year}
    if count in SUSPICIOUS_COUNTS:
        out["warning"] = (f"exactly {count} bars: probably cut by the terminal's 'Max bars in chart' "
                          "setting (Tools > Options > Charts); raise it and restart MT5")
    return out


def tick_depth(mt5: Any, symbol: str, *, probe_from: datetime = datetime(2000, 1, 1, tzinfo=UTC),
               now: Callable[[], datetime] = lambda: datetime.now(UTC)) -> dict:
    """First tick available and whether recent ticks carry the aggressor flags (BUY / SELL)."""
    if not mt5.symbol_select(symbol, True):
        return {"symbol": symbol, "error": "symbol not available"}
    flags_all = getattr(mt5, "COPY_TICKS_ALL", -1)
    first = mt5.copy_ticks_from(symbol, probe_from, 1, flags_all)
    recent = mt5.copy_ticks_from(symbol, now() - timedelta(days=5), 5000, flags_all)
    recent = [] if recent is None else list(recent)
    buy = getattr(mt5, "TICK_FLAG_BUY", TICK_FLAG_BUY)
    sell = getattr(mt5, "TICK_FLAG_SELL", TICK_FLAG_SELL)
    flagged = sum(1 for t in recent if int(_field(t, "flags")) & (buy | sell))
    first_ms = int(_field(list(first)[0], "time_msc")) if first is not None and len(first) else None
    return {"symbol": symbol, "first_tick_server_ms": first_ms,
            "first_tick": _iso(first_ms / 1000) if first_ms else None,
            "recent_ticks_sampled": len(recent), "recent_with_aggressor_flag": flagged}


def _iso(epoch) -> str | None:
    return None if epoch is None else datetime.fromtimestamp(epoch, UTC).strftime("%Y-%m-%d %H:%M:%S") + " (server clock)"


def depth_report(mt5: Any, symbols: list[str], timeframes: list[str], **kw) -> dict:
    return {"collected_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "account": account_meta(mt5),
            "symbols_found": list_symbols(mt5),
            "bars": [bar_depth(mt5, s, tf, **kw) for s in symbols for tf in timeframes],
            "ticks": [tick_depth(mt5, s) for s in symbols]}


def _month_windows(start: datetime, end: datetime):
    cur = datetime(start.year, start.month, 1, tzinfo=UTC)
    while cur < end:
        nxt = datetime(cur.year + (cur.month == 12), cur.month % 12 + 1, 1, tzinfo=UTC)
        yield max(cur, start), min(nxt, end)
        cur = nxt


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_name(symbol: str) -> str:
    return symbol.replace("$", "_S_").replace("/", "_")


def download_rates(mt5: Any, symbol: str, tf: str, start: datetime, end: datetime, out_dir: Path) -> dict:
    """Write <out_dir>/<symbol>-<tf>.csv.gz and its .manifest.json. Server epochs are kept as returned."""
    if not mt5.symbol_select(symbol, True):
        raise ValueError(f"{symbol}: not available on this server")
    rows: dict[int, tuple] = {}
    for a, b in _month_windows(start - timedelta(days=1), end + timedelta(days=1)):
        for r in _rates(mt5, symbol, tf, a, b):
            rows[int(_field(r, "time"))] = tuple(_field(r, f) for f in RATE_FIELDS)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{safe_name(symbol)}-{tf}.csv.gz"
    with gzip.open(path, "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(("time_server",) + RATE_FIELDS[1:])
        for t in sorted(rows):
            w.writerow((t,) + tuple(rows[t][1:]))
    times = sorted(rows)
    manifest = {"symbol": symbol, "timeframe": tf, "file": path.name, "sha256": _sha256(path),
                "rows": len(rows), "first_server": times[0] if times else None,
                "last_server": times[-1] if times else None,
                "requested": [start.isoformat(), end.isoformat()],
                "collected_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "account": account_meta(mt5),
                "time_note": "time_server = bar OPEN time on the trade server's wall clock; convert with b3.data.store"}
    path.with_suffix("").with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def download_ticks(mt5: Any, symbol: str, start: datetime, end: datetime, out_dir: Path) -> dict:
    """All ticks (COPY_TICKS_ALL) in [start, end), one day per request."""
    if not mt5.symbol_select(symbol, True):
        raise ValueError(f"{symbol}: not available on this server")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{safe_name(symbol)}-ticks-{start:%Y%m%d}-{end:%Y%m%d}.csv.gz"
    n = 0
    flags_all = getattr(mt5, "COPY_TICKS_ALL", -1)
    with gzip.open(path, "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(TICK_FIELDS)
        day = start
        while day < end:
            ticks = mt5.copy_ticks_range(symbol, day, min(day + timedelta(days=1), end), flags_all)
            for t in ([] if ticks is None else ticks):
                w.writerow(tuple(_field(t, k) for k in TICK_FIELDS))
                n += 1
            day += timedelta(days=1)
    manifest = {"symbol": symbol, "file": path.name, "sha256": _sha256(path), "rows": n,
                "requested": [start.isoformat(), end.isoformat()],
                "collected_at_utc": datetime.now(UTC).isoformat(timespec="seconds"), "account": account_meta(mt5),
                "time_note": "time_msc = server wall clock in milliseconds; flags: BUY=32, SELL=64 (aggressor)"}
    path.with_name(path.name.replace(".csv.gz", ".manifest.json")).write_text(json.dumps(manifest, indent=2),
                                                                              encoding="utf-8")
    return manifest


def _date(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def main(argv: list[str] | None = None, mt5_module: Any = None) -> int:
    ap = argparse.ArgumentParser(prog="b3.data.mt5_history")
    ap.add_argument("command", choices=("symbols", "depth", "download", "ticks"))
    ap.add_argument("--symbols", nargs="*", default=[])
    ap.add_argument("--timeframes", nargs="*", default=["M1", "M5", "M15", "H1", "D1"])
    ap.add_argument("--start", default="2005-01-01")
    ap.add_argument("--end", default=None)
    ap.add_argument("--first-year", type=int, default=2000)
    ap.add_argument("--env", default="live/.env")
    ap.add_argument("--out", default="user_data/data/b3")
    ap.add_argument("--report", default=None, help="depth: where to write the JSON report")
    ap.add_argument("--attach", default=None, metavar="BROKER_JSON",
                    help="attach to the logged-in terminal of b3/config/broker_mt5.json (demo only; ignores --env)")
    args = ap.parse_args(argv)
    if mt5_module is None:
        import MetaTrader5 as mt5_module  # noqa: N813  (Windows only)
    mt5 = mt5_module
    if args.attach:
        attach(mt5, args.attach)
    else:
        load_env_file(args.env)
        connect(mt5)
    try:
        if args.command == "symbols":
            print(json.dumps({"account": account_meta(mt5), "symbols": list_symbols(mt5)}, indent=2))
            return 0
        if not args.symbols:
            print("--symbols is required", file=sys.stderr)
            return 2
        if args.command == "depth":
            rep = depth_report(mt5, args.symbols, args.timeframes, first_year=args.first_year)
            text = json.dumps(rep, indent=2)
            if args.report:
                Path(args.report).parent.mkdir(parents=True, exist_ok=True)
                Path(args.report).write_text(text, encoding="utf-8")
            print(text)
            return 0
        end = _date(args.end) if args.end else datetime.now(UTC)
        out = Path(args.out)
        for s in args.symbols:
            if args.command == "download":
                for tf in args.timeframes:
                    m = download_rates(mt5, s, tf, _date(args.start), end, out)
                    print(f"{s} {tf}: {m['rows']} bars -> {out / m['file']}")
            else:
                m = download_ticks(mt5, s, _date(args.start), end, out)
                print(f"{s}: {m['rows']} ticks -> {out / m['file']}")
        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    sys.exit(main())
