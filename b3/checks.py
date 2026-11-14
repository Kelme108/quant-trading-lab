"""Checks every B3 strategy must pass before a result is read (plan, F2.6 and F2.7).

1. static screen of the source file (b3/strategy_check.py);
2. causality of `prepare()` (session features + indicators): prefix invariance and future
   corruption from lab/causality.py;
3. window parity: the decision the live engine would take from its window of `warmup + 4` closed
   bars equals the backtester's decision from the full history, on a sample of bars and for each
   position state. A failure means the warm-up is too short (a recursive indicator that has not
   converged, a lookback longer than declared, or a session feature without the whole session).
"""

from __future__ import annotations

import random

import pandas as pd

from b3.strategy import B3Strategy
from lab.causality import future_corruption, prefix_invariance
from live.core.models import Position


def causality_problems(strategy: B3Strategy, frame: pd.DataFrame, n_cuts: int = 8, seed: int = 1) -> list[str]:
    def compute(df: pd.DataFrame) -> pd.DataFrame:
        out = strategy.prepare(df)
        return out.select_dtypes(include="number")

    n = len(frame)
    if n < 10:
        return ["frame too short for the causality check"]
    rng = random.Random(seed)
    cuts = sorted({rng.randrange(max(2, strategy.warmup), n) for _ in range(n_cuts)})
    problems = [f"prefix: {p}" for p in prefix_invariance(compute, frame, cuts)]
    problems += [f"corruption: {p}" for p in future_corruption(compute, frame, cuts[len(cuts) // 2])]
    return problems


def _same(a, b) -> bool:
    return (a.action, a.stop_price) == (b.action, b.stop_price)


def window_parity_problems(strategy: B3Strategy, frame: pd.DataFrame, samples: int = 200,
                           seed: int = 1) -> list[str]:
    """Compare full-history decisions with live-window decisions at `samples` random bars."""
    full = strategy.prepare(frame.reset_index(drop=True))
    rows = list(full.itertuples(index=False, name="Row"))
    window = strategy.warmup + 4             # what the engine passes: warmup + 5 fetched, minus the forming bar
    rng = random.Random(seed)
    candidates = list(range(window - 1, len(rows)))
    picks = sorted(rng.sample(candidates, min(samples, len(candidates))))
    problems = []
    for k in picks:
        part = frame.iloc[k - window + 1:k + 1].reset_index(drop=True)
        last = next(strategy.prepare(part).tail(1).itertuples(index=False, name="Row"))
        price = rows[k].close
        for position in (None, Position("X", 1.0, price, None), Position("X", -1.0, price, None)):
            a, b = strategy.decide(rows[k], position), strategy.decide(last, position)
            if not _same(a, b):
                state = "flat" if position is None else ("long" if position.volume > 0 else "short")
                problems.append(f"bar {k} ({frame['time'].iloc[k]}), {state}: full history -> {a.action} "
                                f"{a.stop_price}, live window -> {b.action} {b.stop_price}")
                break
        if len(problems) >= 10:
            problems.append("... stopped after 10 mismatches")
            break
    return problems
