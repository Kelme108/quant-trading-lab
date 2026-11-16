"""Exploration-only anatomy of WIN and WDO for the research agent (research/b3/anatomy.json): how far the price
moves over 5 / 15 / 30 / 60 minutes compared with the round-trip cost, by part of the session, and the share of the
day's range made in each hour. EXPLORATION split only (b3/config/splits_b3.json); no rule is evaluated here.

    python research/tools/b3_anatomy.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from b3 import b3_data  # noqa: E402
from b3.calendar import SP_TZ, SessionRules  # noqa: E402
from b3.markets import market  # noqa: E402

OUT = ROOT / "research" / "b3" / "anatomy.json"


def anatomy(root: str) -> dict:
    splits = json.loads((ROOT / "b3/config/splits_b3.json").read_text(encoding="utf-8"))
    ex = splits["symbols"][root]["exploration"]
    start, end = pd.Timestamp(ex["start_utc"]), pd.Timestamp(ex["end_utc"])
    m = market(root)
    inst = m.instrument()
    bars = b3_data.load_b3_bars(root, "5m")
    cal = b3_data.history_calendar(root, bars, SessionRules(0, 0, 0))
    bars = b3_data.session_only_b3(bars, cal, 5)
    bars = bars[(bars["time"] >= start) & (bars["time"] < end)].reset_index(drop=True)
    skip = b3_data.incomplete_days(bars, cal, 5, 0.9)
    local = bars["time"].dt.tz_convert(SP_TZ)
    bars["day"], bars["hour"] = local.dt.date, local.dt.hour
    bars = bars[~bars["day"].isin(skip)].reset_index(drop=True)
    price = float(bars["close"].median())
    cost_pct = {s: 100 * m.cost(s).round_trip_brl(inst) / (price * inst.point_value_brl) for s in ("base", "conservative")}
    out = {"root": root, "data_symbol": m.data_symbol, "split": "exploration", "start_utc": str(start), "end_utc": str(end),
           "sessions": int(bars["day"].nunique()), "median_price_points": price,
           "round_trip_cost_pct": cost_pct, "stop_extra_ticks_base": m.stop_extra_ticks_base,
           "tick_size_points": inst.tick_size, "tick_pct_of_price": 100 * inst.tick_size / price, "moves": {}, "by_hour": {}}
    for minutes in (5, 15, 30, 60, 120):
        k = minutes // 5
        mv = (bars.groupby("day")["close"].shift(-k) / bars["close"] - 1).abs() * 100
        mv = mv.dropna()
        out["moves"][f"{minutes}m"] = {"median_abs_pct": round(float(mv.median()), 4),
                                       "p75_abs_pct": round(float(mv.quantile(0.75)), 4),
                                       "median_over_base_cost": round(float(mv.median()) / cost_pct["base"], 2)}
    day = bars.groupby("day").agg(o=("open", "first"), c=("close", "last"), hi=("high", "max"), lo=("low", "min"))
    out["day_range_median_pct"] = round(float(((day["hi"] - day["lo"]) / day["o"]).median() * 100), 3)
    out["open_to_close_abs_median_pct"] = round(float(((day["c"] / day["o"] - 1).abs()).median() * 100), 3)
    rng = (bars["high"] - bars["low"]) / bars["close"] * 100
    for hour, v in rng.groupby(bars["hour"]):
        out["by_hour"][f"{hour:02d}h"] = {"median_5m_range_pct": round(float(v.median()), 4)}
    return out


def main() -> int:
    data = {"generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "note": "EXPLORATION split only. Moves are |close(t+h)/close(t) - 1| inside one session (no overnight).",
            "markets": {r: anatomy(r) for r in ("WIN", "WDO")}}
    OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")
    for r, a in data["markets"].items():
        print(r, "cost base %.4f%%" % a["round_trip_cost_pct"]["base"], {k: v["median_over_base_cost"] for k, v in a["moves"].items()},
              "day range", a["day_range_median_pct"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
