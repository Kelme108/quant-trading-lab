"""MT5 adapter tests against an in-memory fake of the MetaTrader5 package (no terminal)."""

from datetime import datetime, timedelta, timezone

import pytest

from fake_mt5 import DEAL_REASON_SL, FakeMT5, SYMBOL_FILLING_FOK
from live.brokers.mt5 import MT5Broker, MT5Unavailable, comment_for
from live.core.clock import AlwaysOpenCalendar, FakeClock
from live.core.engine import Engine
from live.core.journal import Journal
from live.core.killswitch import KillSwitch
from live.core.models import OrderRequest, Signal
from live.core.risk import RiskConfig, RiskManager

UTC = timezone.utc
SYM = "BTCUSD"
MAGIC = 260611


def broker(fake: FakeMT5, **kw) -> MT5Broker:
    b = MT5Broker(fake, magic=MAGIC, server_utc_offset_hours=fake.server_offset_h,
                  sleep=lambda s: None, now=lambda: fake.now_utc, **kw)
    b.connect()
    return b


def buy(cid="c1", vol=1.0, sl=95.0):
    return OrderRequest(cid, SYM, "buy", vol, stop_loss=sl, reason="t")


def sell(cid="c2", vol=1.0):
    return OrderRequest(cid, SYM, "sell", vol, reduce_only=True, reason="t")


# ---------- specs, data, time ----------
def test_symbol_spec_is_read_from_the_server():
    s = broker(FakeMT5(tick_size=0.5, tick_value=2.0)).symbol_spec(SYM)
    assert (s.tick_size, s.tick_value, s.volume_min, s.volume_step, s.volume_max) == (0.5, 2.0, 0.01, 0.01, 100.0)


def test_bar_times_are_converted_from_server_time_to_utc():
    fake = FakeMT5(server_offset_h=2.0)
    open_utc = datetime(2026, 11, 6, 10, 0, tzinfo=UTC)
    server_epoch = int(open_utc.timestamp()) + 2 * 3600
    fake.rates[SYM] = [{"time": server_epoch, "open": 1, "high": 2, "low": 0.5, "close": 1.5, "tick_volume": 10}]
    bars = broker(fake).bars(SYM, 5, 10)
    assert bars[0].time == open_utc and bars[0].close == 1.5


def test_server_offset_estimate_from_last_tick():
    assert broker(FakeMT5(server_offset_h=3.0)).estimate_server_offset(SYM) == 3.0


def test_unsupported_timeframe_and_unknown_symbol():
    b = broker(FakeMT5())
    with pytest.raises(ValueError):
        b.bars(SYM, 7, 10)
    assert b.send(OrderRequest("x", "NOPE", "buy", 1.0, stop_loss=1.0)).retcode == "UNKNOWN_SYMBOL"


def test_account_reports_demo_and_login():
    a = broker(FakeMT5(login=777)).account()
    assert a.is_demo and a.account_id == "777"
    assert not broker(FakeMT5(trade_mode=2)).account().is_demo


# ---------- orders ----------
def test_entry_carries_server_side_stop_magic_comment_and_filling():
    fake = FakeMT5(filling_mode=SYMBOL_FILLING_FOK)
    res = broker(fake).send(buy("abc", sl=95.0))
    assert res.accepted and res.fill.side == "buy" and res.fill.price == pytest.approx(100.1)
    req = fake.sent[-1]
    assert req["sl"] == 95.0 and req["magic"] == MAGIC and req["comment"] == "abc"
    assert req["type_filling"] == 0  # FOK chosen from the symbol's filling_mode
    assert res.fill.cost == pytest.approx(0.5)


def test_entry_without_stop_is_refused_before_reaching_the_server():
    fake = FakeMT5()
    res = broker(fake).send(OrderRequest("n", SYM, "buy", 1.0))
    assert not res.accepted and res.retcode == "NO_STOP" and fake.sent == []


def test_send_is_idempotent_in_memory_and_after_restart():
    fake = FakeMT5()
    b = broker(fake)
    first = b.send(buy("same"))
    assert b.send(buy("same")) is first and len(fake.sent) == 1
    restarted = broker(fake)                      # new process, same terminal
    again = restarted.send(buy("same"))
    assert again.accepted and again.retcode == "ALREADY_FILLED" and len(fake.sent) == 1


@pytest.mark.parametrize("code,name", [(10019, "NO_MONEY"), (10018, "MARKET_CLOSED"),
                                       (10014, "INVALID_VOLUME"), (10006, "REJECT"),
                                       (10027, "CLIENT_DISABLES_AT")])
def test_rejections_are_mapped_and_not_retried(code, name):
    fake = FakeMT5(send_retcodes=[code])
    res = broker(fake).send(buy())
    assert not res.accepted and res.retcode == name and len(fake.sent) == 1


def test_order_check_failure_blocks_the_send():
    fake = FakeMT5(check_retcode=10014)
    res = broker(fake).send(buy())
    assert not res.accepted and res.retcode == "INVALID_VOLUME" and fake.sent == []


def test_requote_is_retried_with_a_fresh_price():
    fake = FakeMT5(send_retcodes=[10004, 10020, 10009])
    res = broker(fake).send(buy())
    assert res.accepted and len(fake.sent) == 3


def test_timeout_raises_so_the_engine_can_recover():
    fake = FakeMT5(send_retcodes=[10012])
    with pytest.raises(TimeoutError):
        broker(fake).send(buy())


def test_accepted_but_invisible_deal_raises_instead_of_guessing():
    fake = FakeMT5()
    b = broker(fake)
    fake.hide_deals = True
    with pytest.raises(TimeoutError):
        b._execute(buy("h"))


def test_long_client_ids_get_a_stable_short_comment():
    cid = "abcdef-SOMEVERYLONGSYMBOLNAME-1730000000-E"
    c = comment_for(cid)
    assert len(c) <= 31 and c == comment_for(cid) and c != comment_for(cid + "x")
    fake = FakeMT5()
    b = broker(fake)
    assert b.send(OrderRequest(cid, SYM, "buy", 1.0, stop_loss=95.0)).accepted
    assert b.find_fill(cid) is not None


# ---------- exits: never a short ----------
@pytest.mark.parametrize("hedging", [False, True])
def test_exit_closes_by_ticket_and_reports_pnl(hedging):
    fake = FakeMT5(hedging=hedging)
    b = broker(fake)
    b.send(buy("in"))
    fake.bid = 101.0
    res = b.send(sell("out"))
    assert res.accepted and res.fill.side == "sell" and res.fill.pnl is not None
    assert "position" in fake.sent[-1]
    assert b.positions() == [] and fake.positions_get() == ()


def test_hedging_tickets_are_aggregated_and_closed_one_by_one():
    fake = FakeMT5(hedging=True)
    b = broker(fake)
    b.send(buy("a", vol=1.0))
    b.send(buy("b", vol=1.0))
    pos = b.positions()
    assert len(pos) == 1 and pos[0].volume == 2.0 and pos[0].stop_loss == 95.0
    res = b.send(sell("x", vol=2.0))
    assert res.accepted and res.fill.volume == 2.0 and fake.positions_get() == ()


def test_sell_without_position_never_opens_a_short():
    fake = FakeMT5(hedging=True)
    res = broker(fake).send(sell("x"))
    assert not res.accepted and res.retcode == "NO_POSITION" and fake.sent == []


def test_foreign_positions_are_ignored():
    fake = FakeMT5()
    fake.add_foreign_position(SYM, 3.0)
    assert broker(fake).positions() == []


# ---------- server events ----------
def test_server_stop_is_drained_exactly_once():
    fake = FakeMT5()
    b = broker(fake)
    b.send(buy("in"))
    ticket = fake.positions_get()[0].ticket
    fake.trigger_stop(ticket, 95.0)
    fills = b.drain_fills()
    assert len(fills) == 1 and fills[0].reason == f"server:{DEAL_REASON_SL}"
    assert fills[0].client_id.startswith("deal-") and fills[0].pnl < 0
    assert b.drain_fills() == []
    # A restarted process sees it again, but under the same key (the journal de-duplicates).
    assert broker(fake).drain_fills()[0].client_id == fills[0].client_id


def test_close_all_queues_fills_for_drain():
    fake = FakeMT5(hedging=True)
    b = broker(fake)
    b.send(buy("a"))
    b.send(buy("b"))
    b.close_all("killswitch")
    fills = b.drain_fills()
    assert len(fills) == 2 and {f.reason for f in fills} == {"killswitch"}
    assert fake.positions_get() == ()


# ---------- connection ----------
def test_reconnects_with_backoff_then_gives_up():
    fake = FakeMT5()
    alerts = []
    b = broker(fake, alert=alerts.append, reconnect_attempts=3)
    fake.connected = False
    with pytest.raises(MT5Unavailable):
        b.positions()
    assert len(fake.initialize_calls) == 1 + 3 and "unreachable" in alerts[-1]
    fake.connected = True
    assert b.positions() == []


def test_credentials_are_passed_to_initialize():
    fake = FakeMT5()
    MT5Broker(fake, magic=1, server_utc_offset_hours=0, login="123", password="p", server="S",
              path="C:/mt5/terminal64.exe").connect()
    assert fake.initialize_calls[-1] == {"login": 123, "password": "p", "server": "S",
                                         "path": "C:/mt5/terminal64.exe"}


# ---------- engine integration ----------
class EveryBar:
    name, hash, timeframe_min, warmup = "everybar", "feed12345678", 5, 2

    def signal(self, bars, position):
        if position is None:
            return Signal("enter", stop_price=round(bars[-1].close - 5.0, 2), reason="smoke")
        return Signal("exit", reason="next bar")


def test_engine_round_trip_and_server_stop_through_the_adapter(tmp_path):
    fake = FakeMT5(server_offset_h=2.0, hedging=True)
    clock = FakeClock(fake.now_utc)
    b = MT5Broker(fake, magic=MAGIC, server_utc_offset_hours=2.0, sleep=lambda s: None, now=clock.now)
    b.connect()

    def set_bars(n_closed):
        start = datetime(2026, 11, 6, 11, 0, tzinfo=UTC)
        fake.rates[SYM] = [{"time": int((start + timedelta(minutes=5 * i)).timestamp()) + 7200,
                            "open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0, "tick_volume": 1}
                           for i in range(n_closed + 1)]  # + the forming bar
        clock.set(start + timedelta(minutes=5 * n_closed, seconds=2))
        fake.now_utc = clock.now()

    journal = Journal(tmp_path / "j.sqlite", clock, "everybar")
    engine = Engine(b, EveryBar(), clock, AlwaysOpenCalendar(), journal,
                    RiskManager(RiskConfig(max_contracts_per_symbol=1, max_daily_loss=1e9,
                                           max_weekly_loss=1e9)),
                    KillSwitch(tmp_path / "STOP"), [SYM], volume=1.0)
    engine.start()
    set_bars(3)
    assert engine.step() == ["enter"]
    set_bars(4)
    assert engine.step() == ["exit"]
    set_bars(5)
    assert engine.step() == ["enter"]
    fake.trigger_stop(fake.positions_get()[0].ticket, 95.0)       # server stop between steps
    set_bars(6)
    assert engine.step() == ["enter"]                              # stop drained first, so no mismatch
    assert not engine.safe_mode and journal.net_volume(SYM) == 1.0
    fills = journal.events("fill")
    assert [f["side"] for f in fills] == ["buy", "sell", "buy", "sell", "buy"]
    assert fills[3]["key"].startswith("deal-") and fills[3]["pnl"] < 0   # the server stop-out
