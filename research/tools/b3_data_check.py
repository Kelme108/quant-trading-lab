"""Data check of the WIN/WDO export from the Clear demo (b3/b3_data.py). Bar times and counts only, plus the roll
days (dates and gap in points): no return or price statistic of any rule.

    python research/tools/b3_data_check.py      -> research/b3/data_quality.json
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from b3 import b3_data  # noqa: E402
from b3.calendar import SP_TZ, Holidays, SessionRules  # noqa: E402
from b3.data.quality import check_bars  # noqa: E402

OUT = ROOT / "research" / "b3" / "data_quality.json"
MIN_COVERAGE = 0.9


def check(root: str, timeframe: str) -> dict:
    tf = {"1m": 1, "5m": 5, "15m": 15}[timeframe]
    bars = b3_data.load_b3_bars(root, timeframe)
    cal = b3_data.history_calendar(root, bars, SessionRules(0, 0, 0))
    inside = b3_data.session_only_b3(bars, cal, tf)
    cov = b3_data.session_coverage(bars, cal, tf)
    skipped = b3_data.incomplete_days(bars, cal, tf, MIN_COVERAGE)
    rep = check_bars(bars, tf)
    by_year = {}
    for y in sorted({d.year for d in cov.index}):
        c = cov[[d.year == y for d in cov.index]]
        by_year[y] = {"days_with_bars": int(len(c)), "days_ge_90pct": int((c >= MIN_COVERAGE).sum()),
                      "median_coverage": round(float(c.median()), 4)}
    return {"root": root, "data_symbol": f"{root}$N", "timeframe": timeframe, "bars": len(bars),
            "bars_outside_session": len(bars) - len(inside), "first": rep.get("first"), "last": rep.get("last"),
            "duplicated_times": rep["duplicated_times"], "ohlc_inconsistent": rep["ohlc_inconsistent"],
            "zero_volume_bars": rep["zero_volume"], "first_bar_local_time": rep["first_bar_local_time"],
            "days_skipped_under_90pct": len(skipped), "skipped_days": sorted(str(d) for d in skipped),
            "coverage_by_year": by_year}


def main() -> int:
    official = Holidays.from_file()
    out = {"generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "source": "Clear demo (ClearInvestimentos-DEMO), b3/config/broker_mt5.json; server clock = Sao Paulo",
           "min_session_coverage": MIN_COVERAGE, "markets": {}}
    for root in ("WIN", "WDO"):
        d5 = b3_data.load_b3_bars(root, "5m")
        days = set(d5["time"].dt.tz_convert(SP_TZ).dt.date)
        h = b3_data.holidays_for(d5)
        inferred = sorted(d for d in h.closed if d.year not in official.known_years and d.weekday() < 5
                          and min(days) <= d <= max(days))
        on_official = sorted(str(d) for d in days if d in official.closed)
        rolls = b3_data.roll_days(root)
        out["markets"][root] = {
            "timeframes": [check(root, tf) for tf in ("1m", "5m", "15m")],
            "inferred_closed_weekdays_by_year": dict(Counter(d.year for d in inferred)),
            "inferred_closed_weekdays": [str(d) for d in inferred],
            "bars_on_official_2026_holidays": on_official,
            "rolls": [{"day": str(r["day"]), "gap_points": r["gap_points"]} for r in rolls],
        }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    for root, m in out["markets"].items():
        for t in m["timeframes"]:
            print(root, t["timeframe"], t["bars"], "outside", t["bars_outside_session"], "skipped",
                  t["days_skipped_under_90pct"], {y: v["days_ge_90pct"] for y, v in t["coverage_by_year"].items()})
        print(root, "closed by year", m["inferred_closed_weekdays_by_year"], "rolls", len(m["rolls"]),
              "bars on 2026 holidays", m["bars_on_official_2026_holidays"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
