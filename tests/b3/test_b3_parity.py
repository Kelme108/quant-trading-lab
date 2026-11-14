"""Parity (plan F2.5): the backtester and the REAL live engine with a PaperBroker must produce the
same fills on the same bars: same times, sides, prices, PnL and reasons. Long-only, because the
live engine does not short yet (plan F3)."""

from datetime import timedelta

import pytest

from b3.backtest import BacktestConfig, run
from b3.costs import get_cost
from b3_helpers import TF, ChannelBreakout, random_walk_frame, to_bars
from live.brokers.paper import PaperBroker, PaperConfig
from live.core.clock import FakeClock
from live.core.engine import Engine
from live.core.journal import Journal
from live.core.killswitch import KillSwitch
from live.core.models import SymbolSpec
from live.core.risk import RiskConfig, RiskManager

SYMBOL = "WINZ26"
SPEC = SymbolSpec(SYMBOL, tick_size=5.0, tick_value=1.0)


def engine_fills(tmp_path, frame, strategy, cost, risk: RiskConfig):
    bars = to_bars(frame)
    clock = FakeClock(bars[0].time)
    broker = PaperBroker(clock, {SYMBOL: SPEC}, PaperConfig(cost.cash_per_side_brl, cost.slippage_ticks_per_side))
    broker.load_bars(SYMBOL, bars, TF)
    journal = Journal(":memory:", clock, strategy.name)
    engine = Engine(broker, strategy, clock, strategy.calendar, journal, RiskManager(risk),
                    KillSwitch(tmp_path / "STOP"), [SYMBOL], volume=1.0)
    engine.start()
    for b in bars:
        clock.set(b.time + timedelta(minutes=TF))
        broker.sync()
        engine.step()
    out = [(f["fill_time"], f["side"], f["volume"], f["price"], f["pnl"], f["reason"])
           for f in journal.events("fill")]
    journal.close()
    return out


def backtest_fills(frame, strategy, cost, cfg):
    res = run(frame.assign(contract=SYMBOL), strategy, cost, cfg)
    return res, [(f["time"].isoformat(), f["side"], f["volume"], f["price"], f["pnl"], f["reason"])
                 for f in res.fills]


def assert_same(a, b):
    assert len(a) == len(b), (len(a), len(b))
    for x, y in zip(a, b):
        assert x[0].replace("+00:00", "") == y[0].replace("+00:00", ""), (x, y)
        assert x[1:4] == y[1:4], (x, y)
        assert (x[4] is None) == (y[4] is None) and (x[4] is None or x[4] == pytest.approx(y[4])), (x, y)
        assert x[5] == y[5], (x, y)


@pytest.mark.parametrize("seed", [3, 7, 11])
def test_backtest_equals_live_engine_without_account_limits(tmp_path, seed):
    frame = random_walk_frame(seed=seed)
    strategy, cost = ChannelBreakout(), get_cost("WIN", "base")
    risk = RiskConfig(max_contracts_per_symbol=1, max_entries_per_day=10_000, max_daily_loss=1e12,
                      max_weekly_loss=1e12, require_stop=True, long_only=True, max_data_age_bars=2.0)
    live = engine_fills(tmp_path, frame, strategy, cost, risk)
    res, bt = backtest_fills(frame, strategy, cost, BacktestConfig(allow_short=False, max_contracts=1))
    assert len(res.trades) >= 10                      # the scenario really trades
    assert {t.exit_reason for t in res.trades} >= {"stop_loss", "below mean"}
    assert_same(live, bt)


class HoldToClose(ChannelBreakout):
    """Enters on the breakout with a wide stop and never exits by rule: the calendar flattens."""

    name = "test_hold_to_close"

    def decide(self, row, position):
        sig = super().decide(row, position)
        if sig.action == "enter":
            return type(sig)("enter", stop_price=sig.stop_price - 400 * 5.0, reason="hold")
        return type(sig)("hold") if position is not None else sig


def test_backtest_equals_live_engine_through_the_end_of_day_flatten(tmp_path):
    frame = random_walk_frame(seed=9)
    strategy, cost = HoldToClose(), get_cost("WIN", "stress")
    risk = RiskConfig(max_contracts_per_symbol=1, max_entries_per_day=10_000, max_daily_loss=1e12,
                      max_weekly_loss=1e12, require_stop=True, long_only=True, max_data_age_bars=2.0)
    live = engine_fills(tmp_path, frame, strategy, cost, risk)
    res, bt = backtest_fills(frame, strategy, cost, BacktestConfig(allow_short=False, max_contracts=1))
    assert [t.exit_reason for t in res.trades].count("end_of_day_flatten") >= 4
    assert res.positions_held_overnight == 0
    assert_same(live, bt)


def test_backtest_equals_live_engine_with_loss_limits_and_entry_cap(tmp_path):
    frame = random_walk_frame(seed=5, max_ticks=14)
    strategy, cost = ChannelBreakout(), get_cost("WIN", "conservative")
    risk = RiskConfig(max_contracts_per_symbol=1, max_entries_per_day=6, max_daily_loss=40.0,
                      max_weekly_loss=90.0, require_stop=True, long_only=True, max_data_age_bars=2.0)
    live = engine_fills(tmp_path, frame, strategy, cost, risk)
    res, bt = backtest_fills(frame, strategy, cost, BacktestConfig(
        allow_short=False, max_contracts=1, max_entries_per_day=6, max_daily_loss_brl=40.0, max_weekly_loss_brl=90.0))
    assert res.vetoes["max_entries_per_day"] + res.vetoes["daily_loss_limit"] + res.vetoes["weekly_loss_limit"] > 0
    assert_same(live, bt)
