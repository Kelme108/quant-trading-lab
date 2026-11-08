"""Time Machine for crypto day trades: the honest odds of a plan before it is traded.

Ported from the method of trader-timemachine in github.com/jakeschincariol/day-trader-skill (MIT, Jake Schincariol,
2026), adapted to this lab: Binance spot 15m candles from user_data/data, UTC sessions (crypto never closes), the
lab's cost model, long only.

Two answers for one plan (pair, date, entry bar, entry, stop, target, flat-by time):
1. Monte Carlo: the rest of the session rebuilt `replays` times. For each bar left, a past bar from the same time of
   day (plus or minus `window` bars) is drawn at random from the previous `lookback` full sessions and scaled to the
   current price as open/high/low/close over the previous close. Stop first, then target; a bar touching both counts
   as the stop (conservative). Seeded (default 19), so a run repeats exactly.
2. History: the plan's own opening-range rule re-run on every one of those past sessions (what really happened).

R is +target_R at the target, -1 at the stop, else the distance at the flat-by time over the risk; `R_net` also
subtracts the round trip of the chosen cost scenario. It never places an order and its numbers are not a gate: it is
a research and monitoring aid. Plans dated inside the validation split or later are labelled monitoring (the
validation split is read once, by the gates).
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from lab import costs, runner

ROOT = Path(__file__).parents[1]
BAR_MINUTES = 15
COIN_FLIP, STRONG, MANY_NEITHER = 0.05, 0.15, 0.40
MONITORING = "monitoramento, não avaliação: o plano cai na validação ou depois, que só os gates leem"


class TMError(Exception):
    """A plan or data problem, said in one plain line."""


@dataclass(frozen=True)
class Session:
    start_hhmm: str = "00:00"   # UTC
    hours: float = 24.0

    @property
    def bars(self) -> int:
        return int(round(self.hours * 60 / BAR_MINUTES))

    def start_of(self, day: pd.Timestamp) -> pd.Timestamp:
        h, m = (int(x) for x in self.start_hhmm.split(":"))
        return day.normalize() + pd.Timedelta(hours=h, minutes=m)


def load_bars(pair: str, root: Path = ROOT) -> pd.DataFrame:
    path = root / "user_data" / "data" / "binance" / f"{pair.replace('/', '_')}-15m.feather"
    if not path.is_file():
        raise TMError(f"no 15m data for {pair} at {path}")
    frame = pd.read_feather(path)
    frame["date"] = pd.to_datetime(frame["date"], utc=True)
    return frame.set_index("date")[["open", "high", "low", "close"]].sort_index()


def sessions_before(bars: pd.DataFrame, day: pd.Timestamp, session: Session, lookback: int) -> list[tuple[str, list]]:
    """Up to `lookback` FULL sessions strictly before `day` (every bar present), oldest first, as lists of
    (o, h, l, c)."""
    out = []
    first_day = bars.index[0].normalize()
    d = day.normalize() - pd.Timedelta(days=1)
    while len(out) < lookback and d >= first_day:
        start = session.start_of(d)
        window = bars.loc[start:start + pd.Timedelta(minutes=BAR_MINUTES * (session.bars - 1))]
        if len(window) == session.bars:
            out.append((d.strftime("%Y-%m-%d"), [tuple(r) for r in window.itertuples(index=False, name=None)]))
        d -= pd.Timedelta(days=1)
    return list(reversed(out))


def build_pool(sessions: list[tuple[str, list]], n_bars: int) -> list[list[tuple]]:
    pool = [[] for _ in range(n_bars)]
    for _, rows in sessions:
        for i in range(1, n_bars):
            pc = rows[i - 1][3]
            o, h, l, c = rows[i]
            pool[i].append((o / pc, h / pc, l / pc, c / pc))
    return pool


def simulate(pool, entry: float, stop: float, target: float, k: int, last: int, *, replays: int = 10000,
             seed: int = 19, window: int = 2, cost_round_trip: float = 0.0) -> dict:
    """Replays of bars k+1..last from entry (long only)."""
    risk = entry - stop
    r_target = round((target - entry) / risk, 4)
    n_bars = len(pool)
    rng = random.Random(seed)
    outcomes, closes = [], []
    for _ in range(replays):
        p, outcome = entry, None
        for i in range(k + 1, last + 1):
            slot = i if window == 0 else min(n_bars - 1, max(1, i + rng.randint(-window, window)))
            o, h, l, c = rng.choice(pool[slot])
            if outcome is None:
                if p * l <= stop:
                    outcome = "stop"
                elif p * h >= target:
                    outcome = "target"
            p = p * c
        outcomes.append(outcome or "close")
        closes.append(p)
    cnt = {x: outcomes.count(x) for x in ("target", "stop", "close")}
    green = sum(1 for o, p in zip(outcomes, closes) if o == "target" or (o == "close" and p > entry))
    rs = [r_target if o == "target" else -1.0 if o == "stop" else (p - entry) / risk for o, p in zip(outcomes, closes)]
    cost_r = cost_round_trip * entry / risk
    srt = sorted(closes)
    q = lambda f: srt[min(len(srt) - 1, int(f * len(srt)))]  # noqa: E731
    return {
        "replays": replays, "seed": seed, "window": window, "bars_left": last - k,
        "p_target": round(cnt["target"] / replays, 4), "p_stop": round(cnt["stop"] / replays, 4),
        "p_neither": round(cnt["close"] / replays, 4), "p_green": round(green / replays, 4),
        "median_close": q(0.5), "p5_close": q(0.05), "p95_close": q(0.95),
        "avg_R": round(statistics.mean(rs), 3), "avg_R_net": round(statistics.mean(rs) - cost_r, 3),
        "cost_R": round(cost_r, 3), "r_at_target": r_target,
    }


def history(sessions, *, or_bars: int, stop_rule: str, target_r: float, last: int, stop_pct: float = 1.0,
            cost_round_trip: float = 0.0) -> dict:
    """The opening-range rule on every past session: entry at the close of the first bar after the range that closes
    above the range high (up to `last`), then stop first, then target, else out at the close of bar `last`."""
    trades = []
    for d, rows in sessions:
        oh = max(r[1] for r in rows[:or_bars])
        ol = min(r[2] for r in rows[:or_bars])
        kk = next((i for i in range(or_bars, last + 1) if rows[i][3] > oh), None)
        if kk is None or kk >= last:
            continue
        e = rows[kk][3]
        s = rule_stop(stop_rule, oh, ol, e, stop_pct)
        risk = e - s
        if risk <= 0:
            continue
        t = e + target_r * risk
        outcome = None
        for r in rows[kk + 1:last + 1]:
            if r[2] <= s:
                outcome = "stop"
                break
            if r[1] >= t:
                outcome = "target"
                break
        cl = rows[last][3]
        big_r = target_r if outcome == "target" else -1.0 if outcome == "stop" else (cl - e) / risk
        trades.append({"date": d, "bar": kk, "entry": e, "stop": s, "target": t, "outcome": outcome or "close",
                       "R": round(big_r, 3), "R_net": round(big_r - cost_round_trip * e / risk, 3)})
    mean = lambda key: round(statistics.mean(x[key] for x in trades), 3) if trades else None  # noqa: E731
    return {
        "sessions": len(sessions), "triggered": len(trades),
        "target": sum(x["outcome"] == "target" for x in trades), "stop": sum(x["outcome"] == "stop" for x in trades),
        "close": sum(x["outcome"] == "close" for x in trades), "avg_R": mean("R"), "avg_R_net": mean("R_net"),
        "trades": trades,
    }


def rule_stop(rule: str, oh: float, ol: float, entry: float, stop_pct: float = 1.0) -> float:
    if rule == "or_mid":
        return (oh + ol) / 2
    if rule == "or_low":
        return ol
    if rule == "pct":
        return entry * (1 - stop_pct / 100.0)
    raise TMError(f"unknown stop rule {rule!r} (or_mid, or_low, pct)")


def lean(mc: dict):
    pt, ps = mc["p_target"], mc["p_stop"]
    if pt + ps <= 0:
        return None
    r = mc.get("r_at_target") or 1.0
    share, even = pt / (pt + ps), 1.0 / (1.0 + r)
    return share - even, share, even


def verdict(mc: dict) -> str:
    lv = lean(mc)
    if lv is None:
        return "No replay reached the target or the stop by the flat-by time: the price then decides every one."
    d, share, even = lv
    r = mc.get("r_at_target") or 1.0
    one_r = abs(r - 1.0) < 0.005
    if abs(d) < COIN_FLIP:
        head = "Close to a coin flip" if one_r else "Close to break-even"
    elif abs(d) < STRONG:
        head = "Leans toward the target" if d > 0 else "Leans toward the stop"
    else:
        head = "Strongly toward the target" if d > 0 else "Strongly toward the stop"
    odds = f"target first {100 * mc['p_target']:.1f} % vs stop first {100 * mc['p_stop']:.1f} %"
    if one_r:
        return f"{head}: {odds}."
    return (f"{head}: at {round(r, 2):g}R the target has to come first in {100 * even:.0f} % of the replays that hit "
            f"one side; it did in {100 * share:.0f} % ({odds}).")


def verdict_notes(mc: dict) -> list[str]:
    notes = []
    lv = lean(mc)
    if mc.get("p_neither", 0) > MANY_NEITHER and lv is not None:
        notes.append(f"{100 * mc['p_neither']:.1f} % of the replays hit neither by the flat-by time; the price then "
                     f"decides those.")
    if lv and abs(lv[0]) >= COIN_FLIP and mc["avg_R"] and (mc["avg_R"] > 0) != (lv[0] > 0):
        notes.append(f"Average R is {mc['avg_R']:+.3f} all the same: the replays that hit neither pull it the other way.")
    if mc["avg_R"] > 0 >= mc["avg_R_net"]:
        notes.append(f"After costs ({mc['cost_R']:.3f} R a round trip) the average R is {mc['avg_R_net']:+.3f}: "
                     f"the cost eats the edge.")
    return notes


def run(pair: str, date: str, *, entry_time: str, entry: float, stop: float, target: float,
        session: Session = Session(), until: str | None = None, or_bars: int = 1, stop_rule: str = "or_mid",
        lookback: int = 60, replays: int = 10000, seed: int = 19, window: int = 2, cost: str = "base",
        root: Path = ROOT, bars: pd.DataFrame | None = None) -> dict:
    if not stop < entry < target:
        raise TMError(f"a long plan needs stop < entry < target (got {stop}, {entry}, {target})")
    bars = bars if bars is not None else load_bars(pair, root)
    day = pd.Timestamp(date, tz="UTC")
    start = session.start_of(day)
    entry_at = pd.Timestamp(f"{date} {entry_time}", tz="UTC")
    k = int((entry_at - start) / pd.Timedelta(minutes=BAR_MINUTES)) - 1   # the bar whose CLOSE is the entry time
    last = session.bars - 1
    if until:
        last = int((pd.Timestamp(f"{date} {until}", tz="UTC") - start) / pd.Timedelta(minutes=BAR_MINUTES)) - 1
    if not 0 <= k < last < session.bars:
        raise TMError(f"the entry time {entry_time} UTC is not inside the session before the flat-by time")
    past = sessions_before(bars, day, session, lookback)
    if len(past) < 20:
        raise TMError(f"only {len(past)} full sessions before {date}; at least 20 are needed")
    scenario = costs.get_scenario(cost)
    rt = 2 * scenario.effective_fee_per_side
    mc = simulate(build_pool(past, session.bars), entry, stop, target, k, last, replays=replays, seed=seed,
                  window=window, cost_round_trip=rt)
    target_r = round((target - entry) / (entry - stop), 4)
    hist = history(past, or_bars=or_bars, stop_rule=stop_rule, target_r=target_r, last=last, cost_round_trip=rt)
    doc = {"pair": pair, "date": date, "entry_time_utc": entry_time, "entry": entry, "stop": stop, "target": target,
           "session": {"start_utc": session.start_hhmm, "hours": session.hours}, "flat_by_bar": last,
           "lookback_sessions": len(past), "cost_scenario": cost, "round_trip_cost": rt,
           "mc": mc, "history": {k2: v for k2, v in hist.items() if k2 != "trades"},
           "verdict": verdict(mc), "notes": verdict_notes(mc)}
    try:
        validation_start = pd.Timestamp(runner.load_splits()["pairs"][pair]["validation"]["start_utc"])
        if day >= validation_start.normalize():
            doc["label"] = MONITORING
    except (KeyError, OSError, ValueError):
        pass
    return doc


def report(doc: dict) -> str:
    mc, h = doc["mc"], doc["history"]
    lines = [
        f"{doc['pair']} {doc['date']}: entry {doc['entry']:g} at {doc['entry_time_utc']} UTC, stop {doc['stop']:g}, "
        f"target {doc['target']:g} ({mc['r_at_target']:g}R).",
        f"{mc['replays']:,} replays of the rest of the session ({mc['bars_left']} bars of 15m), seed {mc['seed']}, "
        f"pool of {doc['lookback_sessions']} past sessions:",
        f"  target first   {100 * mc['p_target']:.1f} %",
        f"  stop first     {100 * mc['p_stop']:.1f} %",
        f"  neither        {100 * mc['p_neither']:.1f} %   still open at the flat-by time",
        f"  green          {100 * mc['p_green']:.1f} %",
        f"  Price at the flat-by time: median {mc['median_close']:.6g}, 90 % between {mc['p5_close']:.6g} and "
        f"{mc['p95_close']:.6g}.",
        f"  Average R {mc['avg_R']:+.3f}; after the {doc['cost_scenario']} cost ({100 * doc['round_trip_cost']:.2f} % a "
        f"round trip) {mc['avg_R_net']:+.3f}.",
        f"History: the same opening-range rule on those {h['sessions']} sessions fired {h['triggered']} times: "
        f"{h['target']} target, {h['stop']} stop, {h['close']} neither. Average R {h['avg_R']}, net {h['avg_R_net']}.",
        doc["verdict"], *doc["notes"],
        "Built from the pair's own recent 15m bars; not a prediction.",
    ]
    if doc.get("label"):
        lines.append(f"[{doc['label']}]")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m lab.timemachine", description=__doc__.split("\n")[0])
    p.add_argument("pair")
    p.add_argument("--date", required=True, help="UTC date of the plan, YYYY-MM-DD")
    p.add_argument("--entry-time", required=True, help="UTC close time of the entry bar, HH:MM")
    p.add_argument("--entry", type=float, required=True)
    p.add_argument("--stop", type=float, required=True)
    p.add_argument("--target", type=float, required=True)
    p.add_argument("--until", help="flat-by time UTC, HH:MM (default: the session end)")
    p.add_argument("--session-start", default="00:00")
    p.add_argument("--session-hours", type=float, default=24.0)
    p.add_argument("--or-bars", type=int, default=1, help="15m bars in the opening range (history replay)")
    p.add_argument("--stop-rule", default="or_mid", choices=("or_mid", "or_low", "pct"))
    p.add_argument("--lookback", type=int, default=60)
    p.add_argument("--replays", type=int, default=10000)
    p.add_argument("--seed", type=int, default=19)
    p.add_argument("--cost", default="base", choices=costs.REQUIRED_SCENARIO_NAMES)
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    try:
        doc = run(a.pair, a.date, entry_time=a.entry_time, entry=a.entry, stop=a.stop, target=a.target,
                  session=Session(a.session_start, a.session_hours), until=a.until, or_bars=a.or_bars,
                  stop_rule=a.stop_rule, lookback=a.lookback, replays=a.replays, seed=a.seed, cost=a.cost)
    except TMError as error:
        print(error)
        return 1
    print(json.dumps(doc, indent=2, default=float) if a.json else report(doc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
