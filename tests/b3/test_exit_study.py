"""Exit study replay (b3/exit_study.py) on synthetic minutes: conservative fills, no look-ahead."""

from __future__ import annotations

from collections import namedtuple

import pandas as pd

from b3 import exit_study as es
from b3.instruments import instrument_for

T = namedtuple("T", "side entry_time exit_time stop_price exit_price exit_reason")
WIN = instrument_for("WIN")            # tick 5 points, BRL 0.2 per point: BRL 30 = 150 points
T0 = pd.Timestamp("2023-03-01T13:00:00Z")


def _mins(rows):
    """rows = [(open, high, low)] one per minute from T0."""
    tv = [(T0 + pd.Timedelta(minutes=k)).value for k in range(len(rows))]
    return {"time": tv, "open": [r[0] for r in rows], "high": [r[1] for r in rows], "low": [r[2] for r in rows],
            "pos": {v: k for k, v in enumerate(tv)}, "base_slip": 2.0}


def _trade(side="long", n=10, stop=None, reason="time_exit"):
    return T(side, T0, T0 + pd.Timedelta(minutes=n), stop, 0.0, reason)


TARGET30 = {"kind": "target", "target_brl": 30}


def test_target_needs_one_tick_through():
    flat = [(1000, 1000, 1000)] * 10
    touch = _mins([(1000, 1150, 995)] + flat[1:])            # exactly at the target: no fill
    E, X, why, _, _ = es.replay(_trade(), touch, TARGET30, WIN, 0.0)
    assert why == "time_exit" and E == 1000
    through = _mins([(1000, 1155, 995)] + flat[1:])
    E, X, why, _, _ = es.replay(_trade(), through, TARGET30, WIN, 0.0)
    assert why == "target" and X == 1150


def test_stop_first_when_one_minute_has_both():
    m = _mins([(1000, 1200, 900)] + [(1000, 1000, 1000)] * 9)
    E, X, why, _, _ = es.replay(_trade(stop=950.0), m, TARGET30, WIN, 0.0)
    assert why == "stop_loss" and X == 950


def test_short_is_symmetric():
    m = _mins([(1000, 1005, 845)] + [(1000, 1000, 1000)] * 9)
    E, X, why, _, _ = es.replay(_trade(side="short"), m, TARGET30, WIN, 0.0)
    assert why == "target" and X == 850


def test_trailing_uses_only_previous_minutes():
    # minute 0 runs to +200 points and back to -100 in the same minute: the trail is not armed yet -> no exit there
    m = _mins([(1000, 1200, 900), (1150, 1160, 1040), (1050, 1050, 1050)] + [(1050, 1050, 1050)] * 7)
    ex = {"kind": "trailing", "distance_brl": 20}            # 100 points
    E, X, why, t, _ = es.replay(_trade(), m, ex, WIN, 0.0)
    assert why == "trailing_stop" and X == 1100                # armed after minute 0 at 1200 - 100, hit in minute 1
    assert t == T0 + pd.Timedelta(minutes=2)


def test_breakeven_and_slippage():
    m = _mins([(1000, 1110, 1000), (1050, 1060, 990)] + [(1000, 1000, 1000)] * 8)
    ex = {"kind": "breakeven", "trigger_brl": 20}             # +100 points arms the stop at entry + 1 tick
    E, X, why, _, _ = es.replay(_trade(), m, ex, WIN, 1.0)
    assert why == "breakeven_stop" and X == 1005 - 5          # filled at 1005, minus 1 tick of slippage


def test_rule_exit_at_its_own_time():
    m = _mins([(1000, 1010, 990)] * 10 + [(1020, 1020, 1020)])
    E, X, why, t, fb = es.replay(_trade(n=10), m, {"kind": "rule"}, WIN, 0.0)
    assert (X, why, fb) == (1020, "time_exit", False) and t == T0 + pd.Timedelta(minutes=10)


def test_tighter_own_stop():
    m = _mins([(1000, 1000, 845)] + [(1000, 1000, 1000)] * 9)
    ex = {"kind": "target_stop", "target_brl": 30, "stop_brl": 30}
    E, X, why, _, _ = es.replay(_trade(stop=500.0), m, ex, WIN, 0.0)
    assert why == "target_stop_stop" and X == 850
