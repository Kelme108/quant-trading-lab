"""P-032 management on hand-made 1-minute frames (entries are checked against the lab on real bars separately)."""

from datetime import date

import pandas as pd
import pytest

from b3.proxy_rules import RULES
from live.core.models import Position

T = pd.Timestamp("2026-11-04 15:00", tz="UTC")             # 12:00 in Sao Paulo


def frame(bars, signal_at=0, side=-1, b=100.0):
    """bars: list of (high, low, close); bar 0 is the signal bar, the entry fills at bar 1's open."""
    rows = []
    for i, (h, lo, c) in enumerate(bars):
        rows.append({"time": T + pd.Timedelta(minutes=i), "open": c, "high": h, "low": lo, "close": c, "volume": 1.0,
                     "local_date": date(2026, 11, 4), "bf_side": side if i == signal_at else 0,
                     "bf_b": b if i == signal_at else float("nan")})
    return pd.DataFrame(rows)


def rule():
    return RULES["P-032"]()


def test_long_trails_one_b_behind_the_best_high_and_moves_to_breakeven():
    r = rule()
    f = frame([(100000, 100000, 100000), (100060, 99990, 100050)], side=1)
    assert r.decide_frame(f.iloc[:1], None).action == "enter"
    s = r.decide_frame(f, Position("WINZ26", 1, 100000.0, 99900.0))
    assert (s.action, s.stop_price) == ("move_stop", 99960.0)        # best 100060 - 100: trailing before breakeven
    f = frame([(100000, 100000, 100000), (100060, 99990, 100050), (100180, 100050, 100170)], side=1)
    s = r.decide_frame(f, Position("WINZ26", 1, 100000.0, 99960.0))
    assert (s.action, s.stop_price) == ("move_stop", 100080.0)       # above the entry: profit locked


def test_close_through_the_new_level_exits_and_looser_is_never_asked():
    r = rule()
    f = frame([(100000, 100000, 100000), (100200, 100000, 100090)], side=1)
    r.decide_frame(f.iloc[:1], None)
    assert r.decide_frame(f, Position("WINZ26", 1, 100000.0, 99900.0)).action == "exit"   # close 100090 <= 100100
    f = frame([(100000, 100000, 100000), (100010, 99950, 99960)], side=1)
    assert r.decide_frame(f, Position("WINZ26", 1, 100000.0, 99920.0)).action == "hold"  # 99910 is looser than 99920


def test_short_mirrors_and_time_exit_after_60_minutes():
    r = rule()
    f = frame([(100000, 100000, 100000), (100010, 99850, 99870)], side=-1)
    r.decide_frame(f.iloc[:1], None)
    s = r.decide_frame(f, Position("WINZ26", -1, 100000.0, 100100.0))
    assert (s.action, s.stop_price) == ("move_stop", 99950.0)
    flat = [(100000, 100000, 100000)] * 61
    f = frame(flat, side=-1)
    assert r.decide_frame(f.iloc[:60], Position("WINZ26", -1, 100000.0, 100100.0)).action == "hold"
    assert r.decide_frame(f, Position("WINZ26", -1, 100000.0, 100100.0)).action == "exit"


def test_after_a_restart_the_trade_is_recovered_from_the_signal_bar():
    f = frame([(100000, 100000, 100000), (100010, 99850, 99870)], side=-1, b=100.0)
    s = rule().decide_frame(f, Position("WINZ26", -1, 100000.0, 100100.0))   # a fresh instance: no memory
    assert (s.action, s.stop_price) == ("move_stop", 99950.0)


def test_entry_stop_is_one_b_from_the_close():
    s = rule().decide_frame(frame([(100000, 100000, 100000)], side=-1, b=85.0), None)
    assert s.action == "enter_short" and s.stop_price == pytest.approx(100085.0)
