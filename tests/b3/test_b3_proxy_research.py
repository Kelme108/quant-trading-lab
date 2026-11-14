"""b3/proxy_research.py: nothing is read before the owner approves, the final test is locked, validation is
read once, and the ledger counts variants. Synthetic data only."""

import json
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest

import b3.proxy_research as pr
from b3.markets import market

UTC = timezone.utc


def write_npy(path, symbol="US500", days=40):
    """Server-clock 5-minute bars over the New York session (server = New York + 7 h)."""
    m = market(symbol)
    dt = np.dtype([("time", "<i8"), ("open", "<f8"), ("high", "<f8"), ("low", "<f8"), ("close", "<f8"),
                   ("tick_volume", "<u8"), ("spread", "<i4"), ("real_volume", "<u8")])
    rng = np.random.default_rng(5)
    rows, d, price, n = [], date(2023, 12, 1), 5000.0, 0
    while n < days:
        if d.weekday() < 5:
            n += 1
            t = datetime.combine(d, m.open, m.zone).replace(tzinfo=None) + timedelta(hours=7)
            for k in range(78):
                o = price
                c = o + 0.5 * rng.integers(-6, 7)
                epoch = int((t + timedelta(minutes=5 * k)).replace(tzinfo=UTC).timestamp())
                rows.append((epoch, o, max(o, c) + 0.5, min(o, c) - 0.5, c, 100, 1, 0))
                price = c
        d += timedelta(days=1)
    np.save(path / f"{symbol}-5m.npy", np.array(rows, dtype=dt))


@pytest.fixture
def lab(tmp_path, monkeypatch):
    splits = {"approved_by_owner": True, "final_test_unlocked": False, "symbols": {"US500": {
        "exploration": {"start_utc": "2023-12-01T00:00:00Z", "end_utc": "2024-01-01T00:00:00Z"},
        "validation": {"start_utc": "2024-01-01T00:00:00Z", "end_utc": "2024-02-01T00:00:00Z"},
        "final_test": {"start_utc": "2024-02-01T00:00:00Z", "end_utc": None}}}}
    gates = json.loads((pr.ROOT / "b3/config/gates_proxies.json").read_text(encoding="utf-8")) | {"approved_by_owner": True}
    (tmp_path / "splits.json").write_text(json.dumps(splits), encoding="utf-8")
    (tmp_path / "gates.json").write_text(json.dumps(gates), encoding="utf-8")
    monkeypatch.setattr(pr, "SPLITS_PATH", tmp_path / "splits.json")
    monkeypatch.setattr(pr, "GATES_PATH", tmp_path / "gates.json")
    monkeypatch.setattr(pr, "OUT_DIR", tmp_path / "out")
    monkeypatch.setattr(pr, "LEDGER", tmp_path / "out" / "ledger.jsonl")
    write_npy(tmp_path)
    return tmp_path


def test_nothing_is_read_before_the_owner_approves(lab):
    s = json.loads((lab / "splits.json").read_text(encoding="utf-8")) | {"approved_by_owner": False}
    (lab / "splits.json").write_text(json.dumps(s), encoding="utf-8")
    with pytest.raises(pr.NotApproved):
        pr.evaluate("P-001", "US500", "exploration", data_dir=lab)


def test_the_real_config_files_record_the_owner_approval():
    for path in (pr.SPLITS_PATH, pr.GATES_PATH):
        cfg = json.loads(path.read_text(encoding="utf-8"))
        assert cfg["approved_by_owner"] is True and "2026-11-14" in cfg["_approved"]
    assert json.loads(pr.SPLITS_PATH.read_text(encoding="utf-8"))["final_test_unlocked"] is False


def test_final_test_is_locked(lab):
    with pytest.raises(pr.NotApproved):
        pr.evaluate("P-001", "US500", "final_test", data_dir=lab)


def test_exploration_then_validation_once_and_the_ledger_counts_variants(lab):
    out = pr.evaluate("P-001", "US500", "exploration", data_dir=lab)
    assert set(out["scenarios"]) == {"optimistic", "base", "conservative", "stress"}
    assert out["prior_variants"] == 0
    base = out["scenarios"]["base"]
    assert base["trades"] > 0 and base["positions_held_overnight"] == 0
    # costs only make it worse
    nets = [out["scenarios"][s]["net_return_pct"] for s in ("optimistic", "base", "conservative", "stress")]
    assert nets == sorted(nets, reverse=True)
    out2 = pr.evaluate("P-002", "US500", "exploration", data_dir=lab)
    assert out2["prior_variants"] == 1
    pr.evaluate("P-001", "US500", "validation", data_dir=lab)
    with pytest.raises(pr.AlreadyRead):
        pr.evaluate("P-001", "US500", "validation", data_dir=lab)
    rows = pr.ledger_rows(pr.LEDGER)
    assert [(r["rule"], r["split"]) for r in rows] == [("P-001", "exploration"), ("P-002", "exploration"),
                                                       ("P-001", "validation")]


def test_metrics_of_two_hand_made_trades():
    t = pd.DataFrame({"exit_time": pd.to_datetime(["2024-01-02 15:00", "2025-01-03 15:00"], utc=True),
                      "entry_time": pd.to_datetime(["2024-01-02 14:00", "2025-01-03 14:30"], utc=True),
                      "entry_price": [100.0, 100.0], "net_brl": [2.0, -1.0], "gross_brl": [2.1, -0.9],
                      "side": ["long", "short"], "exit_reason": ["x", "y"]})
    m = pr.metrics(t, pd.Timestamp("2024-01-01", tz="UTC"), pd.Timestamp("2026-01-01", tz="UTC"), market("US500").zone)
    assert m["trades"] == 2
    assert m["net_return_pct"] == pytest.approx(100 * (1.02 * 0.99 - 1))
    assert m["max_drawdown_pct"] == pytest.approx(1.0)
    assert m["positive_years_share"] == 0.5
    assert m["net_return_excl_best_pct"] == pytest.approx(-1.0)
