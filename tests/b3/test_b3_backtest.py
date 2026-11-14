"""Hand-built cases for b3/backtest.py. Day: Thu 2026-11-12, WIN 09:00-18:25, 5-minute bars.
Bar k opens at 09:00 + 5k; the decision after bar k happens at its close and fills at the open of
bar k+1. Base cost: BRL 0.25 per side + 1 tick (5 points) of slippage per side."""

from datetime import date

import pandas as pd
import pytest

from b3.backtest import BacktestConfig, run
from b3.calendar import SessionRules
from b3.costs import get_cost
from b3.strategy import ENTER_LONG, ENTER_SHORT, EXIT, HOLD, B3Strategy
from b3_helpers import frame_from_closes
from live.core.models import Signal

DAY = [date(2026, 11, 12)]
BASE = 172_000.0
COST = get_cost("WIN", "base")


class Scripted(B3Strategy):
    """Acts on chosen bars of the day: {bar_in_day: (action, stop offset in points or None)}."""

    name, root, timeframe_min, warmup = "scripted", "WIN", 5, 1
    rules = SessionRules(15, 30, 10)

    def __init__(self, script):
        super().__init__()
        self.script = script

    def decide(self, row, position):
        action, offset = self.script.get(row.bar_in_day, (HOLD, None))
        if action in (ENTER_LONG, ENTER_SHORT):
            stop = None if offset is None else row.close + offset
            return Signal(action, stop_price=stop, reason=f"bar{row.bar_in_day}")
        return Signal(action, reason=f"bar{row.bar_in_day}")


def flat(n=113, overrides=None):
    closes = [BASE] * n
    for k, v in (overrides or {}).items():
        closes[k] = v
    return frame_from_closes(closes, DAY, start=BASE)


def test_long_round_trip_prices_and_pnl():
    f = flat(overrides={4: BASE + 100, **{k: BASE + 100 for k in range(5, 113)}})
    r = run(f, Scripted({3: (ENTER_LONG, -500), 4: (EXIT, None)}), COST)
    (t,) = r.trades
    assert (t.side, t.entry_price, t.exit_price) == ("long", BASE + 5, BASE + 95)
    assert t.points == pytest.approx(90) and t.gross_brl == pytest.approx(18.0)
    assert t.cost_brl == pytest.approx(0.5) and t.net_brl == pytest.approx(17.5)
    assert t.entry_time == f["time"][4] and t.exit_time == f["time"][5]
    assert r.positions_held_overnight == 0


def test_short_round_trip_is_the_mirror():
    f = flat(overrides={k: BASE + 100 for k in range(4, 113)})
    r = run(f, Scripted({3: (ENTER_SHORT, +500), 4: (EXIT, None)}), COST)
    (t,) = r.trades
    assert (t.side, t.entry_price, t.exit_price) == ("short", BASE - 5, BASE + 105)
    assert t.points == pytest.approx(-110) and t.net_brl == pytest.approx(-22.5)


def test_stop_fills_at_the_stop_or_at_a_gapped_open():
    f = flat()
    f.loc[6, ["open", "high", "low", "close"]] = [BASE - 50, BASE - 45, BASE - 300, BASE - 250]   # trades through stop
    r = run(f, Scripted({3: (ENTER_LONG, -200)}), COST)
    assert r.trades[0].exit_reason == "stop_loss"
    assert r.trades[0].exit_price == BASE - 200 - 5
    assert r.trades[0].exit_time == f["time"][6] + pd.Timedelta(minutes=5)

    g = flat()
    g.loc[6, ["open", "high", "low", "close"]] = [BASE - 400, BASE - 395, BASE - 450, BASE - 420]  # gaps below
    r = run(g, Scripted({3: (ENTER_LONG, -200)}), COST)
    assert r.trades[0].exit_price == BASE - 400 - 5


def test_short_stop_above():
    f = flat()
    f.loc[7, ["open", "high", "low", "close"]] = [BASE, BASE + 260, BASE - 5, BASE + 10]
    r = run(f, Scripted({3: (ENTER_SHORT, +250)}), COST)
    assert r.trades[0].exit_reason == "stop_loss" and r.trades[0].exit_price == BASE + 250 + 5


def test_end_of_day_flatten():
    f = flat()
    r = run(f, Scripted({3: (ENTER_LONG, -500)}), COST)
    (t,) = r.trades
    assert t.exit_reason == "end_of_day_flatten"
    # flatten_at = 18:25 - 10 min = 18:15 -> fills at the open of the 18:15 bar
    assert t.exit_time.tz_convert("America/Sao_Paulo").strftime("%H:%M") == "18:15"
    assert r.positions_held_overnight == 0


def test_vetoes_follow_the_live_risk_rules():
    f = flat()
    script = {0: (ENTER_LONG, -100),        # decided at 09:05: before the entry window
              3: (ENTER_LONG, +100),        # stop above the price
              4: (ENTER_LONG, -102),        # stop off the 5-point grid
              5: (ENTER_LONG, None)}        # no stop
    r = run(f, Scripted(script), COST)
    assert r.trades == []
    assert r.vetoes == {"outside_entry_window:no_entry": 1, "stop_wrong_side": 1, "stop_not_on_tick": 1, "no_stop": 1}
    r = run(f, Scripted({3: (ENTER_SHORT, +100)}), COST, BacktestConfig(allow_short=False))
    assert r.trades == [] and r.vetoes["long_only"] == 1


def test_max_entries_per_day():
    f = flat()
    script = {k: (ENTER_LONG, -100) if k % 2 else (EXIT, None) for k in range(3, 20)}
    r = run(f, Scripted(script), COST, BacktestConfig(max_entries_per_day=2))
    assert len(r.trades) == 2 and r.vetoes["max_entries_per_day"] > 0


def test_daily_loss_limit_flattens_and_locks_the_day():
    closes = [BASE] * 113
    for k in range(5, 113):
        closes[k] = BASE - 100                    # falls 100 points after the entry
    f = frame_from_closes(closes, DAY, start=BASE, wick=0.0)
    r = run(f, Scripted({3: (ENTER_LONG, -1000), 10: (ENTER_LONG, -1000)}), COST,
            BacktestConfig(max_daily_loss_brl=15.0))
    assert [t.exit_reason for t in r.trades] == ["loss_limit"]
    assert r.vetoes["daily_loss_limit"] == 1


def test_open_position_at_the_end_of_data_is_closed_and_flagged():
    f = flat(n=20)
    r = run(f, Scripted({3: (ENTER_LONG, -500)}), COST)
    assert r.trades[-1].exit_reason == "end_of_data"


def test_contract_column_is_carried_into_trades_and_bad_frames_are_refused():
    f = flat()
    f["contract"] = "WINZ26"
    r = run(f, Scripted({3: (ENTER_LONG, -500), 5: (EXIT, None)}), COST)
    assert r.trades[0].symbol == "WINZ26"
    with pytest.raises(ValueError):
        run(pd.concat([f, f.tail(1)]), Scripted({}), COST)
