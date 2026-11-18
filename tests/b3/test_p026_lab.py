"""b3/p026_lab.py exits on synthetic minutes (no market data)."""

from __future__ import annotations

import numpy as np
import pytest

from b3 import esteira as es
from b3 import p026_lab as lab
from tests.b3.test_esteira import EX, MIN, NO_COST, T0, WIN, flat, minutes


def run(prices, side, stop, target=np.inf, be=np.inf, trail=np.inf, hold=10, flatten_after=None):
    m = minutes(prices, flatten_after)
    d = {"stop": np.array([stop]), "target": np.array([target]), "be": np.array([be]), "trail": np.array([trail])}
    return lab.simulate(np.array([0]), np.array([side]), np.array([T0]), m, d, hold, WIN, NO_COST, 10)


def test_matches_the_conveyor_default_exit_on_the_same_cases():
    cases = []
    p = flat(20); p[5] = (100100, 100155, 100050, 100120); cases.append((p, 1))
    p = flat(20); p[2] = (100000, 100200, 99800, 100000); cases.append((p, 1))
    p = flat(20); p[4] = (99700, 99750, 99650, 99700); cases.append((p, 1))
    p = flat(20); p[3] = (100000, 100010, 99845, 99900); cases.append((p, -1))
    cases.append((flat(20), 1))
    for prices, side in cases:
        a = es.simulate(np.array([T0]), np.array([side]), minutes(prices), EX, WIN, NO_COST, 10)
        b = run(prices, side, 150.0, 150.0, hold=10)
        assert (a.loc[0, "reason"], a.loc[0, "exit"]) == (b.loc[0, "reason"], b.loc[0, "exit"])
        assert a.loc[0, "net_brl"] == pytest.approx(b.loc[0, "net_brl"])


def test_breakeven_moves_the_stop_from_the_next_minute():
    p = flat(20)
    p[2] = (100000, 100120, 99995, 100100)          # +120 >= be 100: stop to 100000 from minute 3
    p[3] = (100050, 100060, 99990, 100000)          # trades through 100000: stopped at breakeven
    t = run(p, 1, stop=200, be=100)
    assert t.loc[0, "reason"] == "stop_be_trail" and t.loc[0, "exit"] == 100000
    assert t.loc[0, "net_brl"] == pytest.approx(0.0)


def test_trailing_follows_the_best_price_of_earlier_minutes():
    p = flat(30)
    p[2] = (100000, 100300, 100000, 100250)         # best 100300 -> trail 100 -> stop 100200 from minute 3
    p[3] = (100250, 100260, 100150, 100160)
    t = run(p, 1, stop=200, trail=100, hold=20)
    assert t.loc[0, "exit"] == 100200 and t.loc[0, "reason"] == "stop_be_trail"


def test_short_trailing_mirrors():
    p = flat(30)
    p[2] = (100000, 100000, 99700, 99750)
    p[3] = (99750, 99850, 99740, 99840)
    t = run(p, -1, stop=200, trail=100, hold=20)
    assert t.loc[0, "exit"] == 99800 and t.loc[0, "net_brl"] == pytest.approx(40.0)


def test_box_mid_stop_is_clamped():
    E = np.array([100000.0, 100000.0])
    d = lab.distances({"stop": ["box_mid_clamped"]}, E, np.array([1.0, 1.0]), np.array([99990.0, 99000.0]),
                      np.array([0.001, 0.001]), 0.2, 5.0)
    assert list(d["stop"]) == [100.0, 300.0] and np.isinf(d["target"]).all()
