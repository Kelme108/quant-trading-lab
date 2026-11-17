"""Engine tests over a replayed WIN session (see live_helpers for the time map)."""

from datetime import timedelta

import pytest

from live.core.models import Signal
from live_helpers import (
    BASE, SCENARIO_A, SCENARIO_B, SYMBOL, TF, T0, Rig, RisingStrategy, make_bars, pad,
)


def test_round_trip_is_journalled_end_to_end(tmp_path):
    rig = Rig(tmp_path, SCENARIO_A)
    rig.engine.start()
    rig.run(2, 107)
    sent = rig.kinds("order_sent")
    assert [(e["side"], e["reduce_only"]) for e in sent] == [("buy", False), ("sell", True)]
    fills = rig.kinds("fill")
    assert [f["price"] for f in fills] == [130105.0, 130095.0]
    assert fills[1]["pnl"] == pytest.approx(-3.0)        # -2.0 points value - 0.5 - 0.5 costs
    assert rig.journal.net_volume(SYMBOL) == 0 and rig.broker.positions() == []
    assert all(e["strategy_hash"] == "abcdef123456" for e in rig.kinds("signal"))


def test_excursion_is_journalled_once_per_trade_and_never_trades(tmp_path):
    rig = Rig(tmp_path, SCENARIO_A)
    rig.engine.start()
    rig.run(2, 107)
    exc = rig.kinds("excursion")
    assert len(exc) == 1 and exc[0]["samples"] >= 1
    assert exc[0]["mfe_brl"] >= exc[0]["mae_brl"]
    assert [(e["side"], e["reduce_only"]) for e in rig.kinds("order_sent")] == [("buy", False), ("sell", True)]


def test_decisions_use_closed_bars_only(tmp_path):
    seen = []

    class Spy(RisingStrategy):
        def signal(self, bars, position):
            seen.append(bars[-1].time)
            return super().signal(bars, position)

    rig = Rig(tmp_path, SCENARIO_A, strategy=Spy())
    for k in range(2, 20):
        rig.after(k)
        assert seen[-1] + timedelta(minutes=TF) <= rig.clock.now()   # last bar already closed


def test_corrupting_the_forming_and_future_bars_does_not_change_signals(tmp_path):
    def signals(closes, sub):
        rig = Rig(tmp_path / sub, closes)
        rig.run(2, 8)                       # last step: bar 9 is still forming
        return [(e["key"], e["action"], e["stop"]) for e in rig.kinds("signal")]

    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    corrupted = SCENARIO_A[:9] + [BASE * 3] * (len(SCENARIO_A) - 9)
    assert signals(SCENARIO_A, "a") == signals(corrupted, "b")


def test_bar_is_processed_once_even_if_stepped_repeatedly(tmp_path):
    calls = []

    class Counting(RisingStrategy):
        def signal(self, bars, position):
            calls.append(bars[-1].time)
            return super().signal(bars, position)

    rig = Rig(tmp_path, SCENARIO_A, strategy=Counting())
    rig.run(2, 4)
    n = len(calls)
    for _ in range(3):
        rig.engine.step()
    assert len(calls) == n and len(set(calls)) == n      # no bar evaluated twice
    assert len(rig.kinds("order_sent")) == 1


def test_flatten_at_end_of_day(tmp_path):
    closes = pad([BASE] * 92 + [130050 + 50 * i for i in range(60)])   # rising into the close
    rig = Rig(tmp_path, closes)
    rig.run(2, 107)
    assert len(rig.kinds("order_sent")) == 1               # one entry, never exited by rule
    fills = rig.kinds("fill")
    assert fills[-1]["reason"] == "end_of_day_flatten"
    assert rig.broker.positions() == []
    assert rig.kinds("flatten")


def test_no_entries_outside_the_entry_window(tmp_path):
    # Rising closes at bars 94-95: the signal appears at 17:00, when entries are closed.
    rig = Rig(tmp_path, pad([BASE] * 94 + [130050, 130100]))
    rig.run(2, 107)
    veto = rig.kinds("veto")
    assert veto and "outside_entry_window:no_entry" in veto[0]["reasons"]
    assert rig.kinds("order_sent") == []


@pytest.mark.parametrize("limits,lock_key,reason", [
    ({"max_daily_loss": 20.0}, "day:", "daily_loss_limit"),
    ({"max_daily_loss": 1000.0, "max_weekly_loss": 20.0}, "week:", "weekly_loss_limit"),
])
def test_loss_lockout_persists_across_restart(tmp_path, limits, lock_key, reason):
    from live.brokers.paper import PaperConfig
    rig = Rig(tmp_path, SCENARIO_B, paper=PaperConfig(0.0, 1.0))
    rig.risk = type(rig.risk)(rig.with_risk(**limits))
    rig.engine = rig.new_engine()
    rig.run(2, 7)
    stop_fill = [f for f in rig.kinds("fill") if f["reason"] == "stop_loss"][0]
    assert stop_fill["pnl"] == pytest.approx(-22.0)
    assert any(e["key"].startswith(lock_key) for e in rig.kinds("lockout"))

    rig.engine = rig.new_engine()                  # process restart: lockout must survive
    rig.engine.start()
    rig.run(8, 20)
    vetoes = rig.kinds("veto")
    assert vetoes and all(reason in v["reasons"] for v in vetoes)
    assert len(rig.kinds("order_sent")) == 1       # only the original entry


def test_loss_limit_flattens_open_position(tmp_path):
    # Entry after bar 5, then price drifts down without touching the stop: unrealised loss
    # crosses the limit and the engine flattens.
    closes = pad([BASE] * 4 + [130050, 130100, 130050, 130030, 130020, 130010])
    rig = Rig(tmp_path, closes)
    rig.risk = type(rig.risk)(rig.with_risk(max_daily_loss=20.0))
    rig.engine = rig.new_engine()
    rig.run(2, 5)
    assert rig.broker.positions()
    # Entry fills at 130105. Replace the future with a slide to 129990 (mark-to-market
    # -23 BRL) and drop the stop so only the unrealised-loss path can trigger the exit.
    rig.broker.load_bars(SYMBOL, make_bars(pad([BASE] * 4 + [130050, 130100, 129990, 129990])), TF)
    rig.broker._pos[SYMBOL].stop = None
    acts = rig.after(6)
    assert "loss_limit_flatten" in acts and rig.broker.positions() == []


def test_max_entries_per_day(tmp_path):
    closes = pad([BASE] * 3 + [130050, 130100, 130050, 130000, 130050, 130100])
    rig = Rig(tmp_path, closes, risk=None)
    rig.risk = type(rig.risk)(rig.with_risk(max_entries_per_day=1))
    rig.engine = rig.new_engine()
    rig.run(2, 12)
    assert len(rig.kinds("order_sent")) == 2           # entry + exit
    assert any("max_entries_per_day" in v["reasons"] for v in rig.kinds("veto"))


def test_kill_switch_flattens_and_blocks_everything(tmp_path):
    rig = Rig(tmp_path, SCENARIO_A)
    rig.run(2, 4)
    assert rig.broker.positions()
    rig.ks.trigger("teste")
    assert rig.after(5) == ["killswitch"]
    assert rig.broker.positions() == [] and rig.kinds("killswitch")
    assert rig.kinds("fill")[-1]["reason"] == "killswitch"
    n = len(rig.kinds("order_sent"))
    assert all(a == ["killswitch"] for a in rig.run(6, 40))
    assert len(rig.kinds("order_sent")) == n


def test_restart_with_open_position_reconciles_and_does_not_duplicate(tmp_path):
    rig = Rig(tmp_path, SCENARIO_A)
    rig.run(2, 4)                                   # long position open
    rig.engine = rig.new_engine()                   # process dies and restarts
    rig.engine.start()
    assert not rig.engine.safe_mode and rig.alerts == []
    rig.engine.step()                               # same bar again: nothing happens
    rig.run(5, 107)
    sent = rig.kinds("order_sent")
    assert [(e["side"]) for e in sent] == ["buy", "sell"]
    assert rig.broker.positions() == [] and rig.journal.net_volume(SYMBOL) == 0


def test_mismatch_between_journal_and_broker_blocks_trading(tmp_path):
    from live.core.models import OrderRequest
    rig = Rig(tmp_path, SCENARIO_A)
    rig.run(2, 2)
    rig.clock.set(T0 + timedelta(minutes=15))
    rig.broker.send(OrderRequest("manual", SYMBOL, "buy", 1))     # position the journal never saw
    rig.engine = rig.new_engine()
    rig.engine.start()
    assert rig.alerts and "mismatch" in rig.alerts[0]
    out = rig.run(3, 20)
    assert all(a == ["safe_mode"] for a in out)
    assert rig.kinds("order_sent") == []
    rig.journal.log("adjust", SYMBOL, delta=1)                    # operator reconciles
    assert not rig.engine.safe_mode


def test_timeout_after_execution_is_recovered_without_duplicate(tmp_path):
    rig = Rig(tmp_path, SCENARIO_A)
    rig.broker.fail_next_send_after_fill = True
    rig.run(2, 4)
    assert rig.kinds("order_recovered") and not rig.engine.safe_mode
    assert rig.journal.net_volume(SYMBOL) == 1 == rig.broker.positions()[0].volume
    rig.run(5, 107)
    assert len(rig.kinds("order_sent")) == 2


def test_timeout_with_unknown_outcome_enters_safe_mode(tmp_path):
    rig = Rig(tmp_path, SCENARIO_A)
    rig.broker.fail_next_send_after_fill = True
    rig.broker.find_fill = lambda cid: None
    rig.run(2, 4)
    assert rig.engine.safe_mode and rig.kinds("order_unknown")
    assert rig.run(5, 10) and all(a == ["safe_mode"] for a in rig.run(5, 10))


def test_stale_data_vetoes_entries(tmp_path):
    rig = Rig(tmp_path, SCENARIO_A, n_bars=5)       # feed stopped after bar 4
    rig.clock.set(T0 + timedelta(minutes=5 * 5 + 15))     # 3 bars of silence
    rig.broker.sync()
    rig.engine.step()
    veto = rig.kinds("veto")
    assert veto and "stale_data" in veto[0]["reasons"]


def test_strategy_error_does_not_trade(tmp_path):
    class Broken(RisingStrategy):
        def signal(self, bars, position):
            raise RuntimeError("boom")

    rig = Rig(tmp_path, SCENARIO_A, strategy=Broken())
    rig.run(2, 20)
    assert rig.kinds("order_sent") == [] and any("strategy error" in a for a in rig.alerts)


def test_entry_without_stop_is_vetoed(tmp_path):
    class NoStop(RisingStrategy):
        def signal(self, bars, position):
            s = super().signal(bars, position)
            return Signal(s.action, None, s.reason)

    rig = Rig(tmp_path, SCENARIO_A, strategy=NoStop())
    rig.run(2, 6)
    assert any("no_stop" in v["reasons"] for v in rig.kinds("veto"))
    assert rig.broker.positions() == []
