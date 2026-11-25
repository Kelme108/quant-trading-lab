"""B3 demonstration on the Clear demo (owner 2026-11-16): shorts only on demo, a research rule run unchanged by the
live engine, and the attached terminal never reads live/.env."""

import json
from datetime import datetime, timedelta, timezone

import pytest

from live import run as live_run
from live.brokers.paper import PaperBroker, PaperConfig
from live.core.clock import FakeClock
from live.core.engine import Engine
from live.core.journal import Journal
from live.core.killswitch import KillSwitch
from live.core.models import Bar, OrderRequest, SymbolSpec
from live.core.risk import RiskConfig, RiskContext, RiskManager
from live.strategies.b3_rule import B3RuleStrategy

UTC = timezone.utc
SYM = "WINZ26"
SPEC = SymbolSpec(SYM, tick_size=5.0, tick_value=1.0, volume_min=1.0, volume_step=1.0)
DEMO_CFG = "live/config/demo-b3-p004-win.json"


def session_bars(day: datetime, start: float, step: float) -> list[Bar]:
    """5-minute bars of one WIN session 09:00-18:25 Sao Paulo (UTC-3), plus an off-session bar at 08:55."""
    t0 = day.replace(hour=12, minute=0, tzinfo=UTC)
    out, p = [Bar(t0 - timedelta(minutes=5), start, start + 5, start - 5, start, 1.0)], start
    for k in range(113):
        o, c = p, p + step
        out.append(Bar(t0 + timedelta(minutes=5 * k), o, max(o, c) + 5, min(o, c) - 5, c, 100.0))
        p = c
    return out


def test_risk_allows_a_short_only_when_not_long_only():
    ctx = RiskContext(now=datetime(2026, 11, 13, 20, 55, tzinfo=UTC), phase="entry", spec=SPEC, ref_price=130000.0,
                      position_volume=0.0, entries_today=0, lockout_day=False, lockout_week=False,
                      killswitch_active=False, safe_mode=False, data_age_bars=0.0)
    short = OrderRequest("s", SYM, "sell", 1, stop_loss=131300.0)
    assert "long_only" in RiskManager(RiskConfig()).check(short, ctx).reasons
    assert RiskManager(RiskConfig(long_only=False)).check(short, ctx).approved
    below = OrderRequest("s2", SYM, "sell", 1, stop_loss=129000.0)
    assert "stop_wrong_side" in RiskManager(RiskConfig(long_only=False)).check(below, ctx).reasons
    cover = OrderRequest("c", SYM, "buy", 1, reduce_only=True)
    held = RiskContext(**{**ctx.__dict__, "position_volume": -1.0})
    assert RiskManager(RiskConfig()).check(cover, held).approved                # exits are never blocked
    assert "exit_wrong_side" in RiskManager(RiskConfig()).check(OrderRequest("x", SYM, "sell", 1, reduce_only=True), held).reasons


def test_paper_short_round_trip_and_stop():
    clock = FakeClock(datetime(2026, 11, 13, 12, 0, tzinfo=UTC))
    b = PaperBroker(clock, {SYM: SPEC}, PaperConfig(0.0, 0.0), allow_short=True)
    bars = [Bar(clock.now() + timedelta(minutes=5 * k), 130000 - 50 * k, 130010 - 50 * k + (600 if k == 3 else 0),
                129940 - 50 * k, 129950 - 50 * k) for k in range(6)]
    b.load_bars(SYM, bars, 5)
    clock.advance(minutes=5)
    assert b.send(OrderRequest("e", SYM, "sell", 1, stop_loss=130400.0)).accepted
    assert b.positions()[0].volume == -1.0
    clock.advance(minutes=15)
    b.sync()                                    # bar 3 spikes to 130460 >= the stop
    f = b.drain_fills()
    assert len(f) == 1 and f[0].side == "buy" and f[0].price == 130400.0 and f[0].pnl < 0 and b.positions() == []


def test_p004_runs_unchanged_in_the_engine_and_shorts_a_down_day(tmp_path):
    bars = []                                                        # Mon-Thu up, Friday down: 5 regular sessions
    for i, day in enumerate(range(9, 13)):                           # (P-004 needs 400 bars of warm-up)
        bars += session_bars(datetime(2026, 11, day), 130000.0 + 600 * i, 5.0)
    bars += session_bars(datetime(2026, 11, 13), 132500.0, -10.0)
    clock = FakeClock(datetime(2026, 11, 13, 12, 0, tzinfo=UTC))
    broker = PaperBroker(clock, {SYM: SPEC}, PaperConfig(0.25, 1.0), allow_short=True)
    broker.load_bars(SYM, bars, 5)
    st = B3RuleStrategy("P-004", "WIN")
    assert st.hash == "1a24fd953697"                                 # the hash in research/b3/ledger.jsonl
    assert all(b.time.hour >= 12 for b in st.session_bars(bars[:5]))  # the 08:55 bar is dropped
    journal = Journal(tmp_path / "j.sqlite", clock, st.name)
    eng = Engine(broker, st, clock, st.calendar, journal, RiskManager(RiskConfig(long_only=False, max_contracts_per_symbol=1)),
                 KillSwitch(tmp_path / "STOP"), [SYM], volume=1.0)
    eng.start()
    while clock.now() < datetime(2026, 11, 13, 21, 30, tzinfo=UTC):
        clock.advance(minutes=5)
        broker.sync()
        eng.step()
    sent = journal.events("order_sent")
    fills = journal.events("fill")
    assert [(e["side"], e["reduce_only"]) for e in sent] == [("sell", False)]       # one short, 30 min before close
    entry = [e for e in fills if e["side"] == "sell"][0]
    assert entry["fill_time"].startswith("2026-11-13T20:55")                        # 17:55 Sao Paulo
    assert [e for e in fills if e["side"] == "buy"][0]["reason"] == "end_of_day_flatten"   # flat at 18:20
    assert broker.positions() == []


def test_the_demo_config_attaches_without_credentials_and_only_on_demo(tmp_path, monkeypatch):
    cfg = live_run.load_config(DEMO_CFG)
    assert cfg["mode"] == "demo" and cfg["allow_real"] is False and cfg["risk"]["long_only"] is False
    att = live_run.attach_config(cfg)
    assert att["server"] == "XPMT5-DEMO" and "PRD" not in att["server"].upper()
    monkeypatch.setenv("MT5_LOGIN", "123")
    monkeypatch.setenv("MT5_PASSWORD", "secret")
    broker = live_run.build_broker(cfg, object())
    assert broker._creds == {"path": att["terminal_path"], "login": None, "password": None, "server": None}
    assert broker.allow_short is True
    for bad in ({"mode": "real"}, {"allow_real": True}):
        p = tmp_path / "bad.json"
        p.write_text(json.dumps({**cfg, **bad}), encoding="utf-8")
        with pytest.raises(SystemExit):
            live_run.load_config(p)
    p = tmp_path / "short.json"
    p.write_text(json.dumps({**json.loads(open("live/config/live.smoke.example.json", encoding="utf-8").read()),
                             "mode": "x", "risk": {"long_only": False}}), encoding="utf-8")
    with pytest.raises(SystemExit):
        live_run.load_config(p)


def test_main_never_reads_the_env_file_for_an_attached_terminal(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("MT5_LOGIN=999\nMT5_PASSWORD=x\nMT5_SERVER=XPMT5-PRD\n", encoding="utf-8")
    for k in ("MT5_LOGIN", "MT5_PASSWORD", "MT5_SERVER", "MT5_PATH"):
        monkeypatch.delenv(k, raising=False)
    seen = {}

    def fake_build(cfg, mod, **kw):
        seen.update({k: live_run.os.environ.get(k) for k in ("MT5_LOGIN", "MT5_SERVER")})
        raise SystemExit(0)

    monkeypatch.setattr(live_run, "build_broker", fake_build)
    monkeypatch.setattr(live_run, "setup_logging", lambda path: None)      # never write the real demo log
    with pytest.raises(SystemExit):
        live_run.main(["--config", DEMO_CFG, "--env", str(env), "--check"], mt5_module=object())
    assert seen == {"MT5_LOGIN": None, "MT5_SERVER": None}


def test_mt5_adapter_opens_and_covers_a_short_only_with_allow_short():
    import sys
    sys.path.insert(0, "tests/live")
    from fake_mt5 import FakeMT5
    from live.brokers.mt5 import MT5Broker
    fake = FakeMT5()
    sym = "BTCUSD"                                  # the fake's symbol (tests/live/test_mt5_adapter.py)

    def mk(**kw):
        b = MT5Broker(fake, magic=7, server_utc_offset_hours=fake.server_offset_h, sleep=lambda s: None,
                      now=lambda: fake.now_utc, **kw)
        b.connect()
        return b

    long_only = mk()
    assert long_only.send(OrderRequest("s0", sym, "sell", 1.0)).retcode == "NO_POSITION"   # never opens a short
    b = mk(allow_short=True)
    tick = fake.symbol_info_tick(sym)
    assert b.send(OrderRequest("s1", sym, "sell", 1.0)).retcode == "NO_STOP"
    res = b.send(OrderRequest("s2", sym, "sell", 1.0, stop_loss=float(tick.ask) + 10))
    assert res.accepted and res.fill.side == "sell" and b.positions()[0].volume < 0
    assert b.send(OrderRequest("s3", sym, "sell", 1.0, stop_loss=float(tick.ask) + 10)).retcode == "ALREADY_OPEN"
    cov = b.send(OrderRequest("c1", sym, "buy", 1.0, reduce_only=True))
    assert cov.accepted and cov.fill.side == "buy" and cov.fill.pnl is not None and b.positions() == []


def test_live_feed_keeps_today_session_bars_with_the_forming_one_and_the_open_result():
    from types import SimpleNamespace
    from live.core.models import Position
    from live.feed import build_feed
    st = B3RuleStrategy("P-004", "WIN")
    t0 = datetime(2026, 11, 13, 12, 0, tzinfo=UTC)                 # 09:00 Sao Paulo
    bars = [Bar(t0 - timedelta(minutes=2), 1, 1, 1, 1)] + [Bar(t0 + timedelta(minutes=k), 130000 + 5 * k, 130010 + 5 * k, 129995 + 5 * k, 130005 + 5 * k, 10) for k in range(30)]

    class B:
        mt5 = SimpleNamespace(symbol_info_tick=lambda s: SimpleNamespace(bid=130200.0, ask=130205.0, last=130200.0))
        def bars(self, symbol, tf, n): assert tf == 1; return bars
        def positions(self): return [Position(SYM, -1.0, 130100.0, 131400.0)]
        def symbol_spec(self, symbol): return SPEC

    f = build_feed(B(), st, SYM, t0 + timedelta(minutes=29, seconds=30))
    assert f["day"] == "2026-11-13" and len(f["bars_1m"]) == 30          # the 08:58 bar is not in the session
    assert f["position"]["open_result_brl"] == -21.0                      # short 1 at 130100, marked at the ask 130205


def test_demo_state_pairs_fills_into_trades(tmp_path):
    from lab import demo_b3
    from live.core.clock import FakeClock
    clock = FakeClock(datetime(2026, 11, 13, 20, 55, tzinfo=UTC))
    j = Journal(tmp_path / "j.sqlite", clock, "demo")
    j.log("fill", SYM, key="e1", side="sell", volume=1.0, price=170000.0, cost=0.5, pnl=None, reason="day_down_so_far", fill_time="2026-11-13T20:55:01+00:00")
    j.log("fill", SYM, key="x1", side="buy", volume=1.0, price=169800.0, cost=0.5, pnl=39.5, reason="end_of_day_flatten", fill_time="2026-11-13T21:20:02+00:00")
    j.close()
    t = demo_b3.round_trips([e for e in demo_b3._journal(tmp_path / "j.sqlite") if e["kind"] == "fill"])
    assert len(t) == 1 and t[0]["side"] == "venda" and t[0]["points"] == 200.0 and t[0]["pnl_brl"] == 39.5
    state = demo_b3.demo_state()
    assert {i["market"] for i in state["items"] if "error" not in i} >= {"WIN", "WDO"}
