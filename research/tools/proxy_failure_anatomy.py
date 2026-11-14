"""Why did the proxy rules fail? Re-runs a rule on the EXPLORATION split only (record=False: this is a
diagnostic re-read of data already read, not a new variant) and splits the GROSS move per trade by year,
side, weekday, entry hour and the volatility of the PREVIOUS session (causal: known before the day starts).

    python research/tools/proxy_failure_anatomy.py P-001,P-003 US500,USTEC [--out file.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from b3.backtest import BacktestConfig, run  # noqa: E402
from b3.markets import ProxySessionCalendar, infer_closed_days, load_bars, market, session_only  # noqa: E402
from b3.proxy_research import CONFIGS, split_window  # noqa: E402
from b3.proxy_rules import RULES  # noqa: E402


def previous_day_volatility(bars: pd.DataFrame, zone) -> pd.Series:
    """Per session day: the previous session's high-low range over its open, ranked against the 60
    sessions before it (0 = calmest, 1 = most volatile). Known before the day opens."""
    day = bars["time"].dt.tz_convert(zone).dt.date
    g = bars.groupby(day)
    rng = (g["high"].max() - g["low"].min()) / g["open"].first()
    prev = rng.shift(1)
    rank = prev.rolling(60, min_periods=20).apply(lambda w: (w[:-1] < w[-1]).mean() if len(w) > 1 else np.nan, raw=True)
    return rank


def gross_table(t: pd.DataFrame, key: pd.Series) -> dict:
    g = pd.DataFrame({"k": key.values, "r": t["r_gross"].values}).groupby("k")["r"]
    return {str(k): {"trades": int(n), "mean_gross_pct": round(100 * float(m), 4)}
            for k, n, m in zip(g.size().index, g.size().values, g.mean().values)}


def anatomy(rule_id: str, symbol: str) -> dict:
    mkt = market(symbol)
    start, end = split_window(symbol, "exploration", rule_id=rule_id)
    rule = RULES[rule_id].on(symbol)
    bars = session_only(load_bars(symbol, f"{rule.timeframe_min}m"), mkt)
    bars = bars[bars["time"] < end]
    first = bars.index[bars["time"] >= start][0]
    bars = bars.iloc[max(0, first - rule.warmup):].reset_index(drop=True)
    cal = ProxySessionCalendar(mkt, rule.rules, infer_closed_days(bars, mkt))
    res = run(bars, rule(cal), mkt.cost("base"), CONFIGS.get(rule_id, BacktestConfig()))
    t = res.trades_frame()
    t = t[pd.to_datetime(t["entry_time"], utc=True) >= start].reset_index(drop=True)
    if t.empty:
        return {"rule": rule_id, "symbol": symbol, "trades": 0}
    t["r_gross"] = t["gross_brl"] / t["entry_price"]
    loc = pd.to_datetime(t["entry_time"], utc=True).dt.tz_convert(mkt.zone)
    vol = previous_day_volatility(bars, mkt.zone)
    vol_bucket = loc.dt.date.map(lambda d: vol.get(d, np.nan))
    tercile = pd.cut(vol_bucket, [-0.01, 1 / 3, 2 / 3, 1.0], labels=["calm", "normal", "volatile"]).astype(str)
    cost = 100 * mkt.base_round_trip
    return {
        "rule": rule_id, "symbol": symbol, "trades": len(t), "cost_round_trip_base_pct": cost,
        "mean_gross_pct": round(100 * float(t["r_gross"].mean()), 4),
        "gross_over_cost": round(100 * float(t["r_gross"].mean()) / cost, 2),
        "hit_rate_gross": round(float((t["r_gross"] > 0).mean()), 3),
        "by_side": gross_table(t, t["side"]),
        "by_year": gross_table(t, loc.dt.year),
        "by_prev_day_volatility": gross_table(t, tercile),
        "by_entry_hour": gross_table(t, loc.dt.hour),
        "by_weekday": gross_table(t, loc.dt.day_name().str[:3]),
        "exit_reasons": t["exit_reason"].value_counts().to_dict(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rules")
    ap.add_argument("symbols")
    ap.add_argument("--out", default=str(ROOT / "research/proxies/failure_anatomy.json"))
    a = ap.parse_args()
    out_path = Path(a.out)
    rows = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else []
    done = {(r["rule"], r["symbol"]) for r in rows}
    for rid in a.rules.split(","):
        for sym in a.symbols.split(","):
            if (rid, sym) in done:
                continue
            r = anatomy(rid, sym)
            rows.append(r)
            out_path.write_text(json.dumps(rows, indent=1), encoding="utf-8")
            if r["trades"]:
                v = r["by_prev_day_volatility"]
                print(f"{rid} {sym}: gross/trade {r['mean_gross_pct']}% = {r['gross_over_cost']}x cost, hit {r['hit_rate_gross']}, "
                      f"long {r['by_side'].get('long', {}).get('mean_gross_pct')} short {r['by_side'].get('short', {}).get('mean_gross_pct')} | "
                      f"prev-day vol calm {v.get('calm', {}).get('mean_gross_pct')} normal {v.get('normal', {}).get('mean_gross_pct')} "
                      f"volatile {v.get('volatile', {}).get('mean_gross_pct')}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
