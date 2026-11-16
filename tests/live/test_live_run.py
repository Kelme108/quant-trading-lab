"""live/run.py with the fake MT5: --check sends nothing, the guards refuse real accounts,
and a short run goes through connect -> order -> journal."""

import json
from datetime import datetime, timedelta, timezone

import pytest

from fake_mt5 import FakeMT5
from live import run as live_run
from live.core.clock import FakeClock
from live.strategies.smoke import SmokeStrategy

UTC = timezone.utc


def write_cfg(tmp_path, **over):
    cfg = json.loads(open("live/config/live.smoke.example.json", encoding="utf-8").read())
    cfg.update({"journal_db": str(tmp_path / "j.sqlite"), "log_file": str(tmp_path / "live.log"),
                "killswitch_file": str(tmp_path / "STOP"), "sha_file": str(tmp_path / "live.sha256")})
    cfg["broker"]["server_utc_offset_hours"] = 2.0
    cfg["risk"]["max_contracts_per_symbol"] = 1.0
    cfg.update(over)
    path = tmp_path / "live.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path, cfg


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for k in ("LIVE_MODE", "LIVE_ACCOUNT_ID", "MT5_LOGIN", "MT5_PASSWORD", "MT5_SERVER", "MT5_PATH"):
        monkeypatch.delenv(k, raising=False)


def test_check_sends_nothing_and_passes_on_demo(tmp_path, capsys):
    path, _ = write_cfg(tmp_path)
    fake = FakeMT5()
    assert live_run.main(["--config", str(path), "--check", "--env", str(tmp_path / "none")], mt5_module=fake) == 0
    out = capsys.readouterr().out
    assert "DEMO" in out and "OK para operar em demo" in out and fake.sent == []


def test_check_blocks_a_real_account(tmp_path, capsys):
    path, _ = write_cfg(tmp_path)
    fake = FakeMT5(trade_mode=2)
    assert live_run.main(["--config", str(path), "--check", "--env", str(tmp_path / "none")], mt5_module=fake) == 3
    assert "BLOQUEADO" in capsys.readouterr().out and fake.sent == []


def test_run_requires_the_server_offset(tmp_path):
    path, cfg = write_cfg(tmp_path)
    cfg["broker"]["server_utc_offset_hours"] = None
    path.write_text(json.dumps(cfg), encoding="utf-8")
    with pytest.raises(SystemExit):
        live_run.main(["--config", str(path), "--env", str(tmp_path / "none")], mt5_module=FakeMT5())


def test_allow_real_without_live_mode_real_is_refused(tmp_path):
    path, _ = write_cfg(tmp_path, allow_real=True)
    with pytest.raises(SystemExit):
        live_run.main(["--config", str(path), "--env", str(tmp_path / "none")], mt5_module=FakeMT5())


def test_only_the_smoke_strategy_is_wired(tmp_path):
    path, cfg = write_cfg(tmp_path, strategy={"name": "H-009"})
    broker = live_run.build_broker(cfg, FakeMT5())
    broker.connect()
    with pytest.raises(SystemExit):
        live_run.build_strategy(cfg, broker)


def test_env_file_fills_credentials_without_overriding(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("MT5_LOGIN=42\nMT5_PASSWORD='s3cr3t'\n# comment\nMT5_SERVER=Demo\n", encoding="utf-8")
    monkeypatch.setenv("MT5_SERVER", "Already")
    live_run.load_env_file(env)
    import os
    assert os.environ["MT5_LOGIN"] == "42" and os.environ["MT5_PASSWORD"] == "s3cr3t"
    assert os.environ["MT5_SERVER"] == "Already"


def test_short_run_trades_the_smoke_round_trip(tmp_path):
    path, cfg = write_cfg(tmp_path)
    fake = FakeMT5(server_offset_h=2.0, bid=70000.0, tick_size=0.01)
    start = datetime(2026, 11, 6, 11, 0, tzinfo=UTC)
    clock = FakeClock(start)
    state = {"n": 3}

    def tick(_seconds):
        state["n"] += 1
        n = state["n"]
        fake.rates["BTCUSD"] = [{"time": int((start + timedelta(minutes=5 * i)).timestamp()) + 7200,
                                 "open": 70000.0, "high": 70010.0, "low": 69990.0, "close": 70000.0,
                                 "tick_volume": 1} for i in range(n + 1)]
        clock.set(start + timedelta(minutes=5 * n, seconds=2))
        fake.now_utc = clock.now()

    tick(0)
    broker = live_run.build_broker(cfg, fake, now=clock.now)
    broker.connect()
    assert live_run.run(cfg, path, broker, clock=clock, max_steps=3, sleep=tick) == 0
    from live.core.journal import Journal
    j = Journal(cfg["journal_db"], clock)
    fills = j.events("fill")
    assert [f["side"] for f in fills] == ["buy", "sell", "buy"]
    assert fake.sent[0]["sl"] == pytest.approx(69950.0)   # 5000 ticks below the last close, on the server
    assert fake.sent[0]["volume"] == 0.01


def test_smoke_stop_is_on_the_tick_grid():
    s = SmokeStrategy(5, tick_size=5.0, stop_ticks=20)
    assert s.stop_for(130_003.0) == 129_900.0
    assert SmokeStrategy(5, 0.01, 10).stop_for(100.0) == pytest.approx(99.9)
