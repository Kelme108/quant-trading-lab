"""Read-only tick recorder for WIN and WDO (owner 2026-11-16, "rode o projeto no maximo"; lever 2 of
docs/plano-busca-padroes-b3.md: the aggressor side exists only in the ticks of the tradable contract, and the
terminal keeps a few weeks of them, with holes, so research on order flow needs the ticks recorded day by day).

For every trading day it saves ALL ticks (COPY_TICKS_ALL) of the active contract and the next one of each root:

    user_data/data/b3/clear/ticks/<CONTRACT>/<YYYY-MM-DD>.csv.gz      time_msc,bid,ask,last,volume_real,flags
    user_data/data/b3/clear/ticks/<CONTRACT>/<YYYY-MM-DD>.json        rows, trades, aggressor counts, coverage

`time_msc` is UTC milliseconds as MT5 returns it. Flags: BUY=32 / SELL=64 mark the aggressor of a trade
(LAST=8); 1336 = buy aggressor at the ask, 1368 = sell aggressor at the bid on the Clear feed.

The terminal caps one request near 100,000 ticks, so a day is read in 20-minute windows, and a window that comes
back near the cap is split in halves until it is not. A day is "final" when it was read after 19:00 Sao Paulo of
that day; a partial day is read again on the next run. Days already final are never read again.

Attaches to the logged-in Clear terminal (b3/config/broker_mt5.json) without credentials, refuses a non-demo
account, sends no order. Runs next to the demo robots (MetaTrader5 allows several attached processes).

    live/.venv/Scripts/python.exe -m b3.data.tick_recorder                 # yesterday and today, plus any gap
    live/.venv/Scripts/python.exe -m b3.data.tick_recorder --since 2026-05-01   # backfill what the terminal has

The ticks are inside the bar program's locked final test (from 2025-10-01, b3/config/splits_b3.json): reading
any strategy result on them needs a tick program with its own splits, approved by the owner, before any read.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from b3.calendar import Holidays, UnknownCalendarYear  # noqa: E402
from b3.contracts import CONTRACT_MONTHS, active_contract, contract_code  # noqa: E402

SP = ZoneInfo("America/Sao_Paulo")
OUT = ROOT / "user_data" / "data" / "b3" / "clear" / "ticks"
BROKER = ROOT / "b3" / "config" / "broker_mt5.json"
ROOTS = ("WIN", "WDO")
FIELDS = ("time_msc", "bid", "ask", "last", "volume_real", "flags")
DAY_FROM, DAY_TO = time(8, 50), time(18, 50)      # pre-opening auction .. after the last close (summer and winter)
FINAL_AFTER = time(19, 0)
WINDOW_MIN = 20
NEAR_CAP = 90_000                                  # the terminal cuts one request near 100,000 ticks
TICK_FLAG_LAST, TICK_FLAG_BUY, TICK_FLAG_SELL = 8, 32, 64


def _ms(d: date, t: time) -> int:
    return int(datetime.combine(d, t, SP).timestamp() * 1000)


def _local(ms: int) -> datetime:
    # the MetaTrader5 package reads a NAIVE datetime as this machine's local time, so pass an aware UTC datetime
    # (checked against time_msc by tests/b3/test_tick_recorder.py's window filter and the first real run)
    return datetime.fromtimestamp(ms / 1000, timezone.utc)


def read_window(mt5, sym: str, a_ms: int, b_ms: int, depth: int = 0) -> list:
    t = mt5.copy_ticks_range(sym, _local(a_ms), _local(b_ms), mt5.COPY_TICKS_ALL)
    if t is None or len(t) == 0:
        return []
    if len(t) >= NEAR_CAP and b_ms - a_ms > 30_000 and depth < 8:
        mid = a_ms + (b_ms - a_ms) // 2
        return read_window(mt5, sym, a_ms, mid, depth + 1) + read_window(mt5, sym, mid, b_ms, depth + 1)
    ms = t["time_msc"]
    keep = (ms >= a_ms) & (ms < b_ms)                # half-open windows: no tick counted twice at a boundary
    return [t[keep]] if keep.any() else []


def read_day(mt5, sym: str, day: date) -> list:
    start, end = _ms(day, DAY_FROM), _ms(day, DAY_TO)
    parts = []
    a = start
    while a < end:
        b = min(a + WINDOW_MIN * 60_000, end)
        parts += read_window(mt5, sym, a, b)
        a = b
    return parts


def summarize(parts: list, day: date) -> dict:
    rows = sum(len(p) for p in parts)
    trades = buy = sell = 0
    minutes = set()
    first = last = None
    for p in parts:
        f = p["flags"].astype("int64")
        tr = (f & TICK_FLAG_LAST) != 0
        trades += int(tr.sum())
        buy += int(((f & TICK_FLAG_BUY) != 0).sum())
        sell += int(((f & TICK_FLAG_SELL) != 0).sum())
        minutes.update((p["time_msc"][tr] // 60_000).tolist())
        if len(p):
            first = int(p["time_msc"][0]) if first is None else first
            last = int(p["time_msc"][-1])
    iso = lambda x: None if x is None else datetime.fromtimestamp(x / 1000, SP).isoformat(timespec="seconds")  # noqa: E731
    return {"day": day.isoformat(), "rows": rows, "trades": trades, "buy_aggressor": buy, "sell_aggressor": sell,
            "minutes_with_trades": len(minutes), "first_tick_sp": iso(first), "last_tick_sp": iso(last)}


def write_day(sym: str, day: date, parts: list, final: bool, out: Path = OUT) -> dict:
    d = out / sym
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{day.isoformat()}.csv.gz"
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(FIELDS)
        for p in parts:
            for r in p:
                w.writerow([int(r["time_msc"]), float(r["bid"]), float(r["ask"]), float(r["last"]),
                            float(r["volume_real"]), int(r["flags"])])
    tmp.replace(path)
    meta = {"symbol": sym, **summarize(parts, day), "final": final, "file": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": "Clear MT5 demo terminal, copy_ticks_range COPY_TICKS_ALL, 20-minute windows"}
    (d / f"{day.isoformat()}.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return meta


def is_final(sym: str, day: date, out: Path = OUT) -> bool:
    m = out / sym / f"{day.isoformat()}.json"
    if not m.exists():
        return False
    try:
        return bool(json.loads(m.read_text(encoding="utf-8")).get("final"))
    except (OSError, ValueError):
        return False


def symbols_for(day: date, holidays: Holidays) -> list[str]:
    out = []
    for root in ROOTS:
        c = active_contract(root, day, holidays)
        y, m = c.year, c.month               # the next contract by month only: its expiry may be in an unknown year
        while True:
            m += 1
            if m > 12:
                y, m = y + 1, 1
            if m in CONTRACT_MONTHS[root]:
                break
        out += [c.code, contract_code(root, y, m)]
    return out


def run(mt5, since: date, until: date, now_sp: datetime, out: Path = OUT, log=print) -> list[dict]:
    holidays = Holidays.from_file()
    done = []
    try:
        days = holidays.trading_days(since, until)
    except UnknownCalendarYear:
        days = [since + timedelta(days=i) for i in range((until - since).days + 1)]
        days = [d for d in days if d.weekday() < 5]
    for day in days:
        if datetime.combine(day, DAY_FROM, SP) > now_sp:
            continue
        final = now_sp >= datetime.combine(day, FINAL_AFTER, SP)
        for sym in symbols_for(day, holidays):
            if is_final(sym, day, out):
                continue
            if not mt5.symbol_select(sym, True):
                log(f"{day} {sym}: not selectable")
                continue
            parts = read_day(mt5, sym, day)
            if not parts and final and day < now_sp.date() - timedelta(days=3):
                # nothing in the terminal for an old day: record the absence once so it is not asked again
                meta = write_day(sym, day, [], True, out)
            elif not parts:
                log(f"{day} {sym}: no ticks yet")
                continue
            else:
                meta = write_day(sym, day, parts, final, out)
            done.append(meta)
            log(f"{day} {sym}: {meta['rows']} ticks, {meta['trades']} trades, {meta['minutes_with_trades']} min"
                f"{'' if final else ' (partial)'}")
    return done


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="b3.data.tick_recorder")
    ap.add_argument("--since", default=None, help="first day (default: 7 days ago; earlier days fill gaps only)")
    ap.add_argument("--until", default=None, help="last day (default: today)")
    a = ap.parse_args(argv)
    now_sp = datetime.now(SP)
    since = date.fromisoformat(a.since) if a.since else now_sp.date() - timedelta(days=7)
    until = date.fromisoformat(a.until) if a.until else now_sp.date()
    import MetaTrader5 as mt5
    from b3.data.mt5_history import attach
    attach(mt5, BROKER)
    try:
        done = run(mt5, since, until, now_sp)
    finally:
        mt5.shutdown()
    print(json.dumps({"days_written": len(done), "ticks": sum(m["rows"] for m in done)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
