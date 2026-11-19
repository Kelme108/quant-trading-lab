"""b3/esteira_live.py: entries carry the server stop and target in V; S4 trails; time exit (synthetic frames)."""

from datetime import date

import pandas as pd
import pytest

from b3.esteira_live import build
from live.core.models import Position

T = pd.Timestamp("2026-11-04 15:00", tz="UTC")


def frame(bars, side=1, v=0.001):
    return pd.DataFrame([{"time": T + pd.Timedelta(minutes=i), "open": c, "high": h, "low": lo, "close": c, "volume": 1.0,
                          "local_date": date(2026, 11, 4), "em_side": side if i == 0 else 0, "em_v": v}
                         for i, (h, lo, c) in enumerate(bars)])


def test_s3_entry_has_stop_1v_and_target_2v_on_the_server():
    r = build("E-156", "WIN", 1, {"k": 1.25, "win_min": 60}, "S3")()
    s = r.decide_frame(frame([(100000, 100000, 100000)], side=-1), None)
    assert s.action == "enter_short" and s.stop_price == pytest.approx(100100) and s.take_profit == pytest.approx(99800)
    f = frame([(100000, 100000, 100000), (100050, 99900, 99950)], side=-1)
    assert r.decide_frame(f, Position("WINZ26", -1, 100000.0, 100100.0)).action == "hold"   # no management in S3


def test_s4_moves_to_breakeven_then_trails_and_exits_on_time():
    r = build("E-040", "WIN", 1, {"k": 4}, "S4")()
    s = r.decide_frame(frame([(100000, 100000, 100000)]), None)
    assert s.action == "enter" and s.take_profit is None and s.stop_price == pytest.approx(99900)
    f = frame([(100000, 100000, 100000), (100130, 100000, 100120)])
    s = r.decide_frame(f, Position("WINZ26", 1, 100000.0, 99900.0))
    assert (s.action, s.stop_price) == ("move_stop", 100030.0)
    f = frame([(100000, 100000, 100000)] * 61)
    assert r.decide_frame(f, Position("WINZ26", 1, 100000.0, 99900.0)).action == "exit"


def test_only_grid_variants_are_accepted():
    with pytest.raises(SystemExit):
        build("E-040", "WIN", 1, {"k": 7}, "S2")
