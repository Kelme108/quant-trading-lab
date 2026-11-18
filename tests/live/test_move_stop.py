"""MOVE_STOP: the engine tightens the server stop (never loosens it); a refused move closes the position."""

from datetime import timedelta

from fake_mt5 import FakeMT5
from live.core.models import Position, Signal
from live_helpers import BASE, SYMBOL, Rig, pad
from test_mt5_adapter import SYM, broker, buy


def test_mt5_modify_stop_tightens_only_and_reports_refusals():
    fake = FakeMT5()
    b = broker(fake)
    b.send(buy(sl=95.0))
    ok, _ = b.modify_stop(SYM, 97.0)
    assert ok and b.positions()[0].stop_loss == 97.0
    n = len(fake.sent)
    ok, _ = b.modify_stop(SYM, 96.0)                  # looser: nothing is sent
    assert ok and len(fake.sent) == n and b.positions()[0].stop_loss == 97.0
    fake.send_retcodes = [10016]                      # INVALID_STOPS
    ok, msg = b.modify_stop(SYM, 98.0)
    assert not ok and ("10016" in msg or "INVALID" in msg)
    assert b.positions()[0].stop_loss == 97.0 and b.positions()[0].volume == 1.0


class EnterThenMove:
    """Enter long on the 4th bar (stop 100 below); then ask for the stop at `levels[k]` on later bars."""
    name, hash, timeframe_min, warmup = "mover", "fedcba654321", 5, 3

    def __init__(self, levels):
        self.levels, self.seen = levels, 0

    def signal(self, bars, position: Position | None) -> Signal:
        self.seen += 1
        if position is None:
            return Signal("enter", stop_price=bars[-1].close - 100, reason="t") if self.seen == 2 else Signal("hold")
        lv = self.levels.pop(0) if self.levels else None
        return Signal("move_stop", stop_price=lv, reason="trail") if lv is not None else Signal("hold")


def test_engine_moves_the_stop_up_ignores_a_looser_one_and_exits_when_refused(tmp_path):
    closes = pad([BASE] * 3 + [BASE + 50] * 10)
    rig = Rig(tmp_path, closes, strategy=EnterThenMove([BASE - 20, BASE - 60, BASE + 500]))
    rig.engine.start()
    rig.run(2, 3)                                     # entry after bar 3
    assert rig.broker.positions() and rig.broker.positions()[0].stop_loss == BASE - 50
    rig.run(4, 4)
    assert rig.broker.positions()[0].stop_loss == BASE - 20
    rig.run(5, 5)                                     # looser: kept
    assert rig.broker.positions()[0].stop_loss == BASE - 20
    rig.run(6, 6)                                     # above the price: refused -> market exit
    assert rig.broker.positions() == []
    moves = rig.kinds("stop_move")
    assert [m["done"] for m in moves] == [True, False, False]
    assert rig.kinds("order_sent")[-1]["reduce_only"] and "stop_move_refused" in rig.kinds("order_sent")[-1]["reason"]
