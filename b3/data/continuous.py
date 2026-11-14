"""Continuous series from individual contracts, additively back-adjusted (plan, F1.5).

Each trading day uses ONE contract, the active one under the ex-ante roll rule (b3/contracts.py).
At each roll, the price difference between the new and the old contract at their last common bar on
the old contract's last active day is added to ALL earlier bars, so the series has no artificial jump
and the most recent contract keeps its raw prices. Because the adjustment is additive and constant
within a day, and no position is held overnight, PnL in points is identical in raw and adjusted
prices; `adj_offset` gives raw = adjusted - adj_offset for reports.
"""

from __future__ import annotations

import pandas as pd

from b3.calendar import SP_TZ
from b3.contracts import RollSegment

PRICE_COLUMNS = ("open", "high", "low", "close")


def back_adjust(per_contract: dict[str, pd.DataFrame], schedule: list[RollSegment]) -> tuple[pd.DataFrame, list[dict]]:
    pieces, rolls = [], []
    for seg in schedule:
        code = seg.contract.code
        if code not in per_contract:
            raise KeyError(f"no bars for {code}, active {seg.first_day}..{seg.last_day}")
        df = per_contract[code]
        day = df["time"].dt.tz_convert(SP_TZ).dt.date
        part = df[(day >= seg.first_day) & (day <= seg.last_day)].copy()
        part["contract"] = code
        pieces.append(part)
    offsets = [0.0] * len(schedule)
    for i in range(len(schedule) - 1):
        old, new = schedule[i], schedule[i + 1]
        a, b = per_contract[old.contract.code], per_contract[new.contract.code]
        day_a = a["time"].dt.tz_convert(SP_TZ).dt.date
        on_last = a[day_a == old.last_day][["time", "close"]]
        common = on_last.merge(b[["time", "close"]], on="time", suffixes=("_old", "_new"))
        if common.empty:
            raise ValueError(f"roll {old.contract.code} -> {new.contract.code}: no common bar on {old.last_day}")
        last = common.iloc[-1]
        diff = float(last["close_new"] - last["close_old"])
        rolls.append({"from": old.contract.code, "to": new.contract.code, "at": str(last["time"]),
                      "old_close": float(last["close_old"]), "new_close": float(last["close_new"]), "diff": diff})
        offsets[i] = diff
    cumulative, running = [0.0] * len(schedule), 0.0
    for i in range(len(schedule) - 1, -1, -1):
        cumulative[i] = running
        running += offsets[i - 1] if i > 0 else 0.0
    out = []
    for part, adj in zip(pieces, cumulative):
        p = part.copy()
        for c in PRICE_COLUMNS:
            p[c] = p[c] + adj
        p["adj_offset"] = adj
        out.append(p)
    series = pd.concat(out, ignore_index=True).sort_values("time").reset_index(drop=True)
    if series["time"].duplicated().any():
        raise ValueError("overlapping segments produced duplicated bar times")
    return series, rolls
