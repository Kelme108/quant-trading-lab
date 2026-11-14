"""Anatomy of 1-minute and 5-minute bars on the proxy markets, EXPLORATION period only.

For each market and bar size: the typical absolute move per bar and over the next 15/30/60 minutes,
compared with the market's base round-trip cost (b3/markets.py); the same by hour of the session; and
how the day's absolute movement splits between the first hour, the middle and the last hour.
Only regular-session bars (b3.markets.session_only) and only days with >= 90% of the session.

    python research/tools/intraday_anatomy.py [--out research/proxies/anatomy.json]
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

from b3.markets import MARKETS, load_bars, session_only  # noqa: E402

SPLITS = json.loads((ROOT / "b3/config/splits_proxies.json").read_text(encoding="utf-8"))
HORIZONS_MIN = (1, 5, 15, 30, 60)


def exploration_bars(symbol: str, tf: str) -> pd.DataFrame:
    m = MARKETS[symbol]
    s = SPLITS["symbols"][symbol]["exploration"]
    b = session_only(load_bars(symbol, tf), m)
    b = b[(b["time"] >= pd.Timestamp(s["start_utc"])) & (b["time"] < pd.Timestamp(s["end_utc"]))].copy()
    loc = b["time"].dt.tz_convert(m.zone)
    b["day"] = loc.dt.date
    b["minute"] = loc.dt.hour * 60 + loc.dt.minute
    full = (pd.Timestamp.combine(pd.Timestamp("2000-01-01"), m.close)
            - pd.Timestamp.combine(pd.Timestamp("2000-01-01"), m.open)).total_seconds() / 60 / int(tf[:-1])
    n = b.groupby("day")["close"].transform("size")
    return b[n >= 0.9 * full].reset_index(drop=True), int(full)


def forward_abs_moves(b: pd.DataFrame, tf_min: int) -> dict[int, pd.Series]:
    """|close(t+h) / close(t) - 1| inside the same day, in percent, for each horizon h (minutes)."""
    out = {}
    for h in HORIZONS_MIN:
        k = h // tf_min
        if k < 1:
            continue
        fwd = b.groupby("day")["close"].shift(-k)
        out[h] = (100 * (fwd / b["close"] - 1)).abs()
    return out


def analyse(symbol: str, tf: str) -> dict:
    m = MARKETS[symbol]
    cost = 100 * m.base_round_trip
    b, full = exploration_bars(symbol, tf)
    tf_min = int(tf[:-1])
    moves = forward_abs_moves(b, tf_min)
    res = {"symbol": symbol, "tf": tf, "cost_round_trip_base_pct": cost, "days": int(b["day"].nunique()),
           "bars_per_full_day": full, "horizons": {}}
    for h, s in moves.items():
        s = s.dropna()
        res["horizons"][h] = {"median_abs_pct": round(float(s.median()), 4), "mean_abs_pct": round(float(s.mean()), 4),
                              "median_over_cost": round(float(s.median() / cost), 2),
                              "share_over_3x_cost": round(float((s > 3 * cost).mean()), 3)}
    # by hour of the session, 30-minute forward move
    h30 = moves.get(30)
    if h30 is not None:
        hour = (b["minute"] // 60)
        g = pd.DataFrame({"hour": hour, "m": h30}).dropna().groupby("hour")["m"]
        res["by_hour_30min_median_over_cost"] = {int(k): round(float(v / cost), 2) for k, v in g.median().items()}
    # split of the day's absolute movement: first hour, middle, last hour
    r = (b.groupby("day")["close"].pct_change().abs())
    open_min = m.open.hour * 60 + m.open.minute
    close_min = m.close.hour * 60 + m.close.minute
    part = np.where(b["minute"] < open_min + 60, "first_hour", np.where(b["minute"] >= close_min - 60, "last_hour", "middle"))
    share = pd.Series(r.values, index=part).groupby(level=0).sum()
    res["share_of_abs_movement"] = {k: round(float(v / share.sum()), 3) for k, v in share.items()}
    # how concentrated is the movement across days: share of the total abs movement in the top 20% days
    day_move = r.groupby(b["day"]).sum().sort_values(ascending=False)
    res["top20pct_days_share_of_movement"] = round(float(day_move.head(max(1, len(day_move) // 5)).sum() / day_move.sum()), 3)
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "research/proxies/anatomy.json"))
    a = ap.parse_args()
    rows = []
    for sym in MARKETS:
        for tf in ("1m", "5m"):
            r = analyse(sym, tf)
            rows.append(r)
            hz = r["horizons"]
            print(f"{sym:<7} {tf} days {r['days']:>4} | median |move| / cost: "
                  + " ".join(f"{h}m={v['median_over_cost']}x" for h, v in hz.items())
                  + f" | >3x cost at 30m: {hz.get(30, {}).get('share_over_3x_cost')} | movement first/mid/last hour "
                  f"{r['share_of_abs_movement']} | top-20% days {r['top20pct_days_share_of_movement']}", flush=True)
    Path(a.out).write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
