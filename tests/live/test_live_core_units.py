"""Unit tests: calendar, journal, risk vetoes, paper broker, real-mode gate, kill switch."""

import json
import sqlite3
from dataclasses import replace
from datetime import date, datetime, timedelta

import pytest

from live.brokers.paper import PaperBroker, PaperConfig
from live.core.clock import UTC, B3Calendar, FakeClock, SessionConfig
from live.core.journal import Journal
from live.core.killswitch import KillSwitch
from live.core.models import OrderRequest
from live.core.realguard import file_sha256, trading_blockers
from live.core.risk import RiskConfig, RiskContext, RiskManager
from live_helpers import SPEC, SYMBOL, T0, make_bars


# ---------------- calendar ----------------
def brt(h, m, day=4):  # 2026-11-04 is a Wednesday
    return datetime(2026, 11, day, h + 3, m, tzinfo=UTC)


@pytest.mark.parametrize("h,m,phase", [
    (8, 59, "closed"), (9, 0, "no_entry"), (9, 14, "no_entry"), (9, 15, "entry"),
    (16, 59, "entry"), (17, 0, "no_entry"), (17, 45, "flatten"), (17, 59, "flatten"),
    (18, 0, "closed")])
def test_phases(h, m, phase):
    assert B3Calendar().phase(brt(h, m)) == phase


def test_weekend_and_holiday_closed():
    assert B3Calendar().phase(brt(10, 0, day=7)) == "closed"  # Saturday
    cal = B3Calendar(SessionConfig(holidays=frozenset({date(2026, 11, 4)})))
    assert cal.phase(brt(10, 0)) == "closed"


def test_day_and_week_boundaries_are_local_midnight():
    cal = B3Calendar()
    assert cal.day_start_utc(brt(10, 0)) == datetime(2026, 11, 4, 3, 0, tzinfo=UTC)
    assert cal.week_start_utc(brt(10, 0)) == datetime(2026, 11, 2, 3, 0, tzinfo=UTC)  # Monday


# ---------------- journal ----------------
def test_journal_is_append_only(tmp_path):
    j = Journal(tmp_path / "j.sqlite", FakeClock(T0))
    j.log("x", key="1", a=1)
    with pytest.raises(sqlite3.DatabaseError):
        j.db.execute("UPDATE events SET kind='y'")
    with pytest.raises(sqlite3.DatabaseError):
        j.db.execute("DELETE FROM events")


def test_journal_key_is_idempotent_and_net_volume(tmp_path):
    clock = FakeClock(T0)
    j = Journal(tmp_path / "j.sqlite", clock)
    assert j.log("fill", "A", key="c1", side="buy", volume=2, pnl=None)
    assert not j.log("fill", "A", key="c1", side="buy", volume=2, pnl=None)  # duplicate
    j.log("fill", "A", key="c2", side="sell", volume=1, pnl=-5.0)
    assert j.net_volume("A") == 1
    j.log("adjust", "A", delta=-1)
    assert j.net_volume("A") == 0


def test_realized_pnl_since(tmp_path):
    clock = FakeClock(T0)
    j = Journal(tmp_path / "j.sqlite", clock)
    j.log("fill", "A", key="old", side="sell", volume=1, pnl=-10.0)
    clock.advance(days=1)
    j.log("fill", "A", key="new", side="sell", volume=1, pnl=-4.0)
    assert j.realized_pnl(T0 + timedelta(hours=1)) == -4.0
    assert j.realized_pnl(T0 - timedelta(hours=1)) == -14.0


# ---------------- risk ----------------
def good_ctx(**kw):
    base = dict(now=T0, phase="entry", spec=SPEC, ref_price=130100.0, position_volume=0.0,
                entries_today=0, lockout_day=False, lockout_week=False,
                killswitch_active=False, safe_mode=False, data_age_bars=0.0)
    return RiskContext(**{**base, **kw})


def entry(**kw):
    base = dict(client_id="c", symbol=SYMBOL, side="buy", volume=1.0, stop_loss=130000.0)
    return OrderRequest(**{**base, **kw})


def test_risk_approves_a_clean_entry():
    assert RiskManager().check(entry(), good_ctx()).approved


@pytest.mark.parametrize("req_kw,ctx_kw,reason", [
    ({"side": "sell"}, {}, "long_only"),
    ({}, {"killswitch_active": True}, "killswitch"),
    ({}, {"safe_mode": True}, "safe_mode"),
    ({}, {"phase": "no_entry"}, "outside_entry_window:no_entry"),
    ({}, {"phase": "flatten"}, "outside_entry_window:flatten"),
    ({}, {"phase": "closed"}, "outside_entry_window:closed"),
    ({}, {"lockout_day": True}, "daily_loss_limit"),
    ({}, {"lockout_week": True}, "weekly_loss_limit"),
    ({"volume": 3.0}, {}, "max_contracts"),
    ({}, {"position_volume": 2.0}, "max_contracts"),
    ({}, {"entries_today": 10}, "max_entries_per_day"),
    ({}, {"data_age_bars": 2.5}, "stale_data"),
    ({"stop_loss": None}, {}, "no_stop"),
    ({"stop_loss": 130002.0}, {}, "stop_not_on_tick"),
    ({"stop_loss": 130100.0}, {}, "stop_wrong_side"),
    ({"stop_loss": 130200.0}, {}, "stop_wrong_side"),
    ({"volume": 0.5}, {}, "volume_out_of_range"),
    ({"volume": 1.5}, {}, "volume_step"),
])
def test_risk_vetoes(req_kw, ctx_kw, reason):
    dec = RiskManager().check(entry(**req_kw), good_ctx(**ctx_kw))
    assert not dec.approved and reason in dec.reasons


def test_exits_are_never_blocked_by_limits():
    ctx = good_ctx(phase="closed", killswitch_active=True, lockout_day=True,
                   lockout_week=True, safe_mode=True, position_volume=1.0, data_age_bars=9)
    ex = entry(side="sell", reduce_only=True, stop_loss=None)
    assert RiskManager().check(ex, ctx).approved


def test_exit_larger_than_position_is_rejected():
    ex = entry(side="sell", reduce_only=True, volume=2.0, stop_loss=None)
    dec = RiskManager().check(ex, good_ctx(position_volume=1.0))
    assert "exit_larger_than_position" in dec.reasons


# ---------------- paper broker ----------------
def paper(closes, cfg=None):
    clock = FakeClock(T0)
    b = PaperBroker(clock, {SYMBOL: SPEC}, cfg or PaperConfig(0.5, 1.0))
    b.load_bars(SYMBOL, make_bars(closes), 5)
    return clock, b


def test_paper_fills_at_next_open_with_slippage_and_costs():
    clock, b = paper([130000, 130100, 130200, 130300])
    clock.set(T0 + timedelta(minutes=10))          # bar 1 closed; bar 2 opens at 130100
    r = b.send(OrderRequest("e1", SYMBOL, "buy", 1, stop_loss=129000.0))
    assert r.fill.price == 130105.0 and r.fill.cost == 0.5       # +1 tick slippage
    clock.set(T0 + timedelta(minutes=15))          # bar 3 opens at 130200
    x = b.send(OrderRequest("x1", SYMBOL, "sell", 1, reduce_only=True))
    assert x.fill.price == 130195.0
    assert x.fill.pnl == pytest.approx((130195 - 130105) / 5 * 1.0 - 0.5 - 0.5)


def test_paper_resend_same_client_id_does_not_duplicate():
    clock, b = paper([130000, 130100, 130200])
    clock.set(T0 + timedelta(minutes=10))
    req = OrderRequest("same", SYMBOL, "buy", 1, stop_loss=129000.0)
    assert b.send(req) == b.send(req)
    assert b.positions()[0].volume == 1


def test_paper_rejects_bad_orders():
    clock, b = paper([130000, 130100, 130200])
    clock.set(T0 + timedelta(minutes=10))
    assert b.send(OrderRequest("a", SYMBOL, "buy", 0)).retcode == "INVALID_VOLUME"
    assert b.send(OrderRequest("b", SYMBOL, "sell", 1)).retcode == "NO_POSITION"
    assert b.send(OrderRequest("c", "NOPE", "buy", 1)).retcode == "UNKNOWN_SYMBOL"
    b.send(OrderRequest("d", SYMBOL, "buy", 1))
    assert b.send(OrderRequest("e", SYMBOL, "buy", 1)).retcode == "ALREADY_OPEN"


def test_paper_stop_fills_at_stop_or_gap_open():
    # bar 2 opens 130100, gaps down to 129000 (below the 129500 stop)
    clock, b = paper([130000, 130100, 129000, 129000])
    clock.set(T0 + timedelta(minutes=10))
    b.send(OrderRequest("e", SYMBOL, "buy", 1, stop_loss=129500.0))
    clock.set(T0 + timedelta(minutes=15))          # bar 2 closed
    b.sync()
    (f,) = b.drain_fills()
    assert f.reason == "stop_loss" and f.price == 129500.0 - 5.0   # stop, not the gap open
    assert b.positions() == [] and b.drain_fills() == []


def test_paper_bars_include_the_forming_bar():
    clock, b = paper([130000, 130100, 130200])
    clock.set(T0 + timedelta(minutes=10))
    assert b.bars(SYMBOL, 5, 10)[-1].time == T0 + timedelta(minutes=10)   # forming


# ---------------- real-mode gate ----------------
def real_setup(tmp_path, allow=True, record_sha=True):
    cfg = tmp_path / "live.json"
    cfg.write_text(json.dumps({"allow_real": allow}))
    sha = tmp_path / "live.sha256"
    if record_sha:
        sha.write_text(file_sha256(cfg))
    return cfg, sha


ENV_REAL = {"LIVE_MODE": "real", "LIVE_ACCOUNT_ID": "123"}


def test_gate_allows_real_only_when_everything_holds(tmp_path):
    cfg, sha = real_setup(tmp_path)
    assert trading_blockers(ENV_REAL, cfg, sha, False, "123", True) == []


@pytest.mark.parametrize("kw,reason", [
    ({"env": {"LIVE_MODE": "demo"}}, "real_account_in_non_real_mode"),
    ({"env": {"LIVE_MODE": "real"}}, "account_id_mismatch"),
    ({"account_id": "999"}, "account_id_mismatch"),
    ({"is_demo": True}, "account_is_demo_but_mode_real"),
    ({"approved": False}, "strategy_not_approved"),
    ({"allow": False}, "config_allow_real_false"),
    ({"record": False}, "config_sha_missing"),
])
def test_gate_blocks(tmp_path, kw, reason):
    cfg, sha = real_setup(tmp_path, allow=kw.get("allow", True), record_sha=kw.get("record", True))
    out = trading_blockers(kw.get("env", ENV_REAL), cfg, sha, kw.get("is_demo", False),
                           kw.get("account_id", "123"), kw.get("approved", True))
    assert reason in out


def test_gate_blocks_when_config_changed_after_hash_recorded(tmp_path):
    cfg, sha = real_setup(tmp_path)
    cfg.write_text(json.dumps({"allow_real": True, "tampered": 1}))
    assert "config_sha_mismatch" in trading_blockers(ENV_REAL, cfg, sha, False, "123", True)


def test_demo_mode_with_demo_account_is_allowed(tmp_path):
    cfg, sha = real_setup(tmp_path)
    assert trading_blockers({"LIVE_MODE": "demo"}, cfg, sha, True, "x", False) == []


# ---------------- kill switch ----------------
def test_killswitch_file(tmp_path):
    ks = KillSwitch(tmp_path / "STOP")
    assert not ks.active() and ks.token() == ""
    ks.trigger("teste")
    assert ks.active() and ks.reason() == "teste" and ks.token() != ""
