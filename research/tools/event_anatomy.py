"""Plan item 3 (review 2026-11-14-veredito-1m-5m): does a SCHEDULED US macro event give a gross move per trade of
3x the cost or more? EXPLORATION split only, index proxies only, 5-minute session bars, days with >= 90% of the
session (b3/config/scope_proxies.json). Event dates: b3/config/events_us.json (federalreserve.gov, bls.gov).

Written 2026-11-14 BEFORE the first run. Prices are read at bar opens (the engine fills at the open of the bar
that starts when the order is sent). Gross per trade has no cost and no stop; base cost = 0.01% round trip.

Move size (median |return|, as a multiple of the base round trip):
  FOMC (14:00 NY)        windows 14:00 -> 14:30, 15:00, 15:55 (US indices; DE40 is closed by then)
  CPI / NFP (08:30 NY)   US indices: session open 09:30 NY -> 10:00, 11:00, 12:00, against non-event days
                         DE40: release -> +30, +60, +120 minutes (the release falls inside the Xetra session)
Candidate rules, fixed here (sign: + = the rule makes money gross):
  E1 FOMC pre-announcement drift (Lucca & Moench, JF 2015): long 10:00 -> 13:55 NY on FOMC days.
  E2 FOMC first reaction continues: sign of 14:00 -> 14:15, enter 14:15, exit 15:55 (negative = it reverses).
  E3 FOMC 30-minute reaction continues: sign of 14:00 -> 14:30, enter 14:30, exit 15:55.
  E4 CPI/NFP morning continues (US indices): sign of previous close -> 10:00, enter 10:00, exit 12:00;
     the same rule on non-event days is reported as the control.
  E5 CPI/NFP release continues on DE40: sign of release -> +15 min, enter +15, exit +75 min.
Decision, fixed here: the event line goes on (a rule is registered through b3/proxy_research.py, counted as
variants) only if a candidate's mean gross is >= 3x the base cost (0.03%) on at least 2 markets with a pooled
t-statistic >= 2; otherwise it stops (plan: "parar se a medicao na exploracao mostrar bruto menor que 3x o custo").
These are diagnostics on exploration only, like research/tools/proxy_failure_anatomy.py; the 5 candidates are
listed in the output so the multiple testing is visible.

    python research/tools/event_anatomy.py [--out research/proxies/event_anatomy.json]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, time, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from b3.events import event_times  # noqa: E402
from b3.markets import incomplete_days, load_bars, market, session_only  # noqa: E402
from b3.proxy_research import SCOPE_PATH, split_window  # noqa: E402

NY = "America/New_York"
US = ("US500", "USTEC", "US30", "US2000")
COST = 0.0001          # base round trip of every index proxy (b3/markets.py)
TARGET = 3 * COST


def price_book(symbol: str):
    mkt = market(symbol)
    bars = session_only(load_bars(symbol, "5m"), mkt)
    start, end = split_window(symbol, "exploration")
    bars = bars[(bars["time"] >= start) & (bars["time"] < end)].reset_index(drop=True)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    bad = incomplete_days(bars, mkt, 5, scope["min_session_coverage"])
    local_day = bars["time"].dt.tz_convert(mkt.zone).dt.date
    bars = bars[~local_day.isin(bad)].reset_index(drop=True)
    opens = dict(zip(bars["time"], bars["open"]))
    day = bars["time"].dt.tz_convert(mkt.zone).dt.date
    last_close = bars.groupby(day)["close"].last()
    days = list(last_close.index)
    prev_close = {d: last_close[days[i - 1]] for i, d in enumerate(days) if i > 0}
    return mkt, opens, set(days), prev_close, (start, end), len(bad)


def at(opens: dict, day, hhmm: str, zone) -> float | None:
    hh, mm = map(int, hhmm.split(":"))
    t = pd.Timestamp(datetime.combine(day, time(hh, mm)), tz=zone).tz_convert("UTC")
    return opens.get(t)


def stats(r: list[float]) -> dict:
    a = np.asarray([x for x in r if x is not None and not math.isnan(x)])
    if len(a) == 0:
        return {"n": 0}
    sd = float(a.std(ddof=1)) if len(a) > 1 else math.nan
    return {"n": int(len(a)), "mean_gross_pct": round(100 * float(a.mean()), 4),
            "x_cost": round(float(a.mean()) / COST, 2),
            "t": round(float(a.mean()) / (sd / math.sqrt(len(a))), 2) if sd and sd > 0 else None,
            "hit": round(float((a > 0).mean()), 3)}


def size(r: list[float]) -> dict:
    a = np.abs(np.asarray([x for x in r if x is not None]))
    return {"n": int(len(a)), "median_abs_pct": round(100 * float(np.median(a)), 4) if len(a) else None,
            "x_cost": round(float(np.median(a)) / COST, 2) if len(a) else None}


def ret(p0, p1):
    return None if p0 is None or p1 is None else p1 / p0 - 1.0


def by_year(days: list, r: list) -> dict:
    out: dict = {}
    for d, x in zip(days, r):
        if x is not None:
            out.setdefault(d.year, []).append(x)
    return {str(y): round(100 * float(np.mean(v)), 4) for y, v in sorted(out.items())}


def us_market(symbol: str) -> dict:
    mkt, opens, days, prev_close, (start, end), skipped = price_book(symbol)
    z = mkt.zone
    ev_days = {k: sorted(t.tz_convert(NY).date() for t in event_times(k)
                         if start <= t < end and t.tz_convert(NY).date() in days) for k in ("FOMC", "CPI", "NFP")}
    out = {"symbol": symbol, "exploration": [str(start), str(end)], "days_skipped_incomplete": skipped,
           "event_days": {k: len(v) for k, v in ev_days.items()}}
    fomc = ev_days["FOMC"]
    out["fomc_move_size"] = {w: size([ret(at(opens, d, "14:00", z), at(opens, d, w, z)) for d in fomc])
                             for w in ("14:30", "15:00", "15:55")}
    e1 = [ret(at(opens, d, "10:00", z), at(opens, d, "13:55", z)) for d in fomc]
    out["E1_fomc_pre_drift_long"] = stats(e1) | {"by_year": by_year(fomc, e1)}
    for name, sig_end in (("E2_fomc_15min_continuation", "14:15"), ("E3_fomc_30min_continuation", "14:30")):
        r = []
        for d in fomc:
            s = ret(at(opens, d, "14:00", z), at(opens, d, sig_end, z))
            g = ret(at(opens, d, sig_end, z), at(opens, d, "15:55", z))
            r.append(None if s is None or g is None or s == 0 else math.copysign(1, s) * g)
        out[name] = stats(r) | {"by_year": by_year(fomc, r)}
    macro = sorted(set(ev_days["CPI"]) | set(ev_days["NFP"]))
    others = sorted(days - set(macro) - set(fomc))
    out["macro_morning_move_size"] = {
        group: {w: size([ret(at(opens, d, "09:30", z), at(opens, d, w, z)) for d in dd]) for w in ("10:00", "11:00", "12:00")}
        for group, dd in (("cpi_or_nfp_days", macro), ("other_days", others))}

    def e4(dd):
        r = []
        for d in dd:
            s = ret(prev_close.get(d), at(opens, d, "10:00", z))
            g = ret(at(opens, d, "10:00", z), at(opens, d, "12:00", z))
            r.append(None if s is None or g is None or s == 0 else math.copysign(1, s) * g)
        return r
    r4 = e4(macro)
    out["E4_macro_morning_continuation"] = stats(r4) | {"by_year": by_year(macro, r4)}
    out["E4_control_other_days"] = stats(e4(others))
    return out


def de40() -> dict:
    mkt, opens, days, _, (start, end), skipped = price_book("DE40")
    out = {"symbol": "DE40", "exploration": [str(start), str(end)], "days_skipped_incomplete": skipped}
    rel = sorted(t for k in ("CPI", "NFP") for t in event_times(k) if start <= t < end)
    rel = [t for t in rel if t.tz_convert(mkt.zone).date() in days]
    out["event_days"] = len(rel)

    def p(t):
        return opens.get(t)
    out["release_move_size"] = {f"+{m}min": size([ret(p(t), p(t + timedelta(minutes=m))) for t in rel])
                                for m in (30, 60, 120)}
    r = []
    for t in rel:
        s = ret(p(t), p(t + timedelta(minutes=15)))
        g = ret(p(t + timedelta(minutes=15)), p(t + timedelta(minutes=75)))
        r.append(None if s is None or g is None or s == 0 else math.copysign(1, s) * g)
    out["E5_de40_release_continuation"] = stats(r) | {"by_year": by_year([t.date() for t in rel], r)}
    return out


def decision(rows: list[dict]) -> dict:
    out = {}
    for c in ("E1_fomc_pre_drift_long", "E2_fomc_15min_continuation", "E3_fomc_30min_continuation",
              "E4_macro_morning_continuation", "E5_de40_release_continuation"):
        cells = [(r["symbol"], r[c]) for r in rows if c in r and r[c].get("n")]
        over = [s for s, m in cells if m["mean_gross_pct"] / 100 >= TARGET]
        n = sum(m["n"] for _, m in cells)
        pooled_mean = sum(m["mean_gross_pct"] * m["n"] for _, m in cells) / n if n else 0.0
        ts = [m["t"] for _, m in cells if m.get("t") is not None]
        pooled_t = sum(ts) / math.sqrt(len(ts)) if ts else 0.0       # Stouffer-style, markets treated as independent
        out[c] = {"markets_at_3x_cost": over, "pooled_mean_gross_pct": round(pooled_mean, 4),
                  "pooled_t": round(pooled_t, 2),
                  "goes_on": len(over) >= 2 and pooled_t >= 2}
    out["event_line_goes_on"] = any(v["goes_on"] for v in out.values() if isinstance(v, dict))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "research/proxies/event_anatomy.json"))
    a = ap.parse_args()
    rows = [us_market(s) for s in US] + [de40()]
    res = {"written": "2026-11-14", "split": "exploration", "cost_round_trip_base_pct": 100 * COST,
           "candidates_measured": 5, "markets": rows, "decision": decision(rows)}
    Path(a.out).write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    for r in rows:
        keys = [k for k in r if k.startswith("E")]
        print(r["symbol"], {k: (r[k].get("n"), r[k].get("mean_gross_pct"), r[k].get("x_cost"), r[k].get("t")) for k in keys})
    print(json.dumps(res["decision"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
