"""The owner's sha-pinned override that lets a b3_rule robot run on the REAL account (2026-11-17)."""

import hashlib
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from live import run as live_run

OVERRIDE = {"approved": True, "date": "2026-11-17", "reason": "owner decision"}


def real_cfg(tmp_path, **kw):
    cfg = {"mode": "live", "allow_real": True, "symbols": ["WINZ26"], "timeframe_min": 1, "volume": 1,
           "strategy": {"name": "b3_rule", "rule": "P-017", "market": "WIN"}, "broker": {"magic": 360017},
           "risk": {"long_only": False, "require_stop": True, "max_daily_loss": 50.0}, "owner_override": OVERRIDE,
           "sha_file": str(tmp_path / "x.sha256"), "feed_file": str(tmp_path / "feed-a.json")}
    cfg.update(kw)
    path = tmp_path / "live-b3-a.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    (tmp_path / "x.sha256").write_text(hashlib.sha256(path.read_bytes()).hexdigest(), encoding="utf-8")
    return path, cfg


def fake_broker(demo=False, account="777", hedging=False):
    return SimpleNamespace(account=lambda: SimpleNamespace(is_demo=demo, account_id=account), is_hedging=lambda: hedging,
                           mt5=SimpleNamespace(account_info=lambda: None))


STRAT = SimpleNamespace(name="b3_rule")


@pytest.fixture
def real_env(monkeypatch):
    monkeypatch.setenv("LIVE_MODE", "real")
    monkeypatch.setenv("LIVE_ACCOUNT_ID", "777")


def test_override_needs_every_field():
    assert live_run.owner_override({"owner_override": OVERRIDE})
    for bad in (None, {}, {**OVERRIDE, "approved": "yes"}, {**OVERRIDE, "reason": ""}, {**OVERRIDE, "date": ""}, "approved"):
        assert not live_run.owner_override({"owner_override": bad})


def test_a_real_b3_rule_without_the_override_is_still_refused(tmp_path, real_env):
    path, _ = real_cfg(tmp_path, owner_override=None)
    with pytest.raises(SystemExit, match="demonstration runs only with mode=demo"):
        live_run.load_config(path)


def test_the_override_loads_only_as_live_without_attach(tmp_path, real_env):
    path, cfg = real_cfg(tmp_path)
    assert live_run.load_config(path)["owner_override"] == OVERRIDE
    for patch in ({"mode": "demo"}, {"allow_real": False}, {"broker": {"magic": 1, "attach": "b3/config/broker_mt5.json"}}):
        path, _ = real_cfg(tmp_path, **patch)
        with pytest.raises(SystemExit, match="owner_override needs"):
            live_run.load_config(path)


def test_allow_real_still_needs_live_mode_real(tmp_path, monkeypatch):
    monkeypatch.delenv("LIVE_MODE", raising=False)
    path, _ = real_cfg(tmp_path)
    with pytest.raises(SystemExit, match="LIVE_MODE"):
        live_run.load_config(path)


def test_guard_allows_a_real_account_with_the_override_and_a_matching_pin(tmp_path, real_env):
    path, cfg = real_cfg(tmp_path)
    assert live_run.guard(cfg, path, fake_broker(), STRAT) == []


def test_guard_blocks_when_the_config_was_edited_after_the_pin(tmp_path, real_env):
    path, cfg = real_cfg(tmp_path)
    path.write_text(path.read_text(encoding="utf-8").replace('"max_daily_loss": 50.0', '"max_daily_loss": 5000.0'), encoding="utf-8")
    assert "config_sha_mismatch" in live_run.guard(cfg, path, fake_broker(), STRAT)


def test_guard_blocks_the_wrong_account_and_a_demo_account_in_real_mode(tmp_path, real_env):
    path, cfg = real_cfg(tmp_path)
    assert "account_id_mismatch" in live_run.guard(cfg, path, fake_broker(account="999"), STRAT)
    assert "account_is_demo_but_mode_real" in live_run.guard(cfg, path, fake_broker(demo=True), STRAT)


def test_guard_without_the_override_still_blocks_an_unapproved_rule_and_shorts(tmp_path, real_env):
    path, cfg = real_cfg(tmp_path, owner_override=None)
    why = live_run.guard(cfg, path, fake_broker(), STRAT)
    assert {"strategy_not_approved", "shorts_on_non_demo_account"} <= set(why)


def test_netting_account_blocks_a_second_robot_on_the_same_symbol(tmp_path, real_env):
    path, cfg = real_cfg(tmp_path)
    other = tmp_path / "live-b3-b.json"
    other.write_text(json.dumps({"symbols": ["WINZ26"], "feed_file": str(tmp_path / "feed-b.json")}), encoding="utf-8")
    (tmp_path / "feed-b.json").write_text(json.dumps({"updated_at": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
    assert "netting_account_symbol_in_use_by_live-b3-b" in live_run.guard(cfg, path, fake_broker(hedging=False), STRAT)
    assert live_run.guard(cfg, path, fake_broker(hedging=True), STRAT) == []            # hedging: separate tickets
    (tmp_path / "feed-b.json").write_text(json.dumps({"updated_at": "2020-01-01T00:00:00+00:00"}), encoding="utf-8")
    assert live_run.guard(cfg, path, fake_broker(hedging=False), STRAT) == []            # the other robot is not running
    other.write_text(json.dumps({"symbols": ["WDOZ26"], "feed_file": str(tmp_path / "feed-b.json")}), encoding="utf-8")
    assert live_run.other_real_robot_on_symbol(cfg, path) is None


def test_the_three_shipped_real_configs_are_valid_and_pinned():
    import os
    from pathlib import Path
    for n in ("017", "020", "026", "028"):
        path = Path(f"live/config/live-b3-p{n}-win.json")
        cfg = json.loads(path.read_text(encoding="utf-8"))
        assert cfg["mode"] == "live" and cfg["allow_real"] is True and live_run.owner_override(cfg)
        assert "attach" not in cfg["broker"] and cfg["env_file"] == "live/.env.real"
        assert cfg["risk"]["max_daily_loss"] == 50.0 and cfg["risk"]["max_weekly_loss"] == 150.0
        assert cfg["risk"]["require_stop"] is True and cfg["risk"]["max_contracts_per_symbol"] == 1 and cfg["volume"] == 1
        assert Path(cfg["sha_file"]).read_text(encoding="utf-8").strip() == hashlib.sha256(path.read_bytes()).hexdigest()
        assert cfg["killswitch_file"] == "live/STOP-live"
