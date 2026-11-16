"""WIN pattern search (owner 2026-11-16, paths A+B): the pre-registration is intact and the gate is strict."""

import json

import numpy as np

from b3 import pattern_search as ps


def test_preregistration_is_approved_and_has_552_variants():
    cfg = ps.load_config()
    assert cfg["approved_by_owner"] is True and cfg["market"] == "WIN"
    settings = ps.signal_settings(cfg)
    grid = cfg["execution"]["exit_grid"]
    assert len(settings) == 46
    assert len(settings) * len(cfg["data"]["timeframes_min"]) * len(grid["hold_min"]) * len(grid["stop_frac"]) == 552
    assert cfg["gate_search"]["min_trades_per_year"] == 500 and cfg["gate_search"]["deflated_sharpe_min"] == 0.95


def test_the_final_test_stays_locked():
    import pytest
    with pytest.raises(PermissionError):
        ps.split_bounds("final_test")


def test_gate_needs_every_condition():
    g = ps.load_config()["gate_search"]
    good = {"trades_per_year": 800, "net_return_pct": 5.0, "net_without_best_pct": 3.0, "max_drawdown_pct": 8.0,
            "positive_years_share": 1.0}
    assert ps.gate(good, good, 0.97, 0.1, g) == []
    assert ps.gate({**good, "trades_per_year": 499}, good, 0.97, 0.1, g) == ["trades_per_year"]
    assert ps.gate(good, {**good, "net_return_pct": -0.1}, 0.97, 0.1, g) == ["net_conservative"]
    assert "pbo" in ps.gate(good, good, 0.97, 0.31, g) and "deflated_sharpe" in ps.gate(good, good, 0.9, 0.1, g)


def test_cross_fires_once_per_crossing_and_never_on_the_previous_session():
    cond = np.array([True, True, False, True, True, True])
    day = np.array([0, 0, 0, 0, 1, 1])
    assert ps._cross(cond, day).tolist() == [True, False, False, True, True, False]


def test_recorded_fidelity_was_exact():
    f = json.loads((ps.OUT / "fidelity.json").read_text(encoding="utf-8"))
    assert all(v["identical_share"] == 1.0 and v["official_trades"] > 500 for v in f["variants"])


def test_path_c_has_288_variants_per_market():
    cfg = ps.load_config()
    settings = ps.signal_settings({"families": cfg["path_c"]["families"]})
    assert len(settings) == 24 and len(settings) * 2 * 6 == 288
    assert cfg["path_c"]["gate"]["min_trades_per_year"] == 50


def test_path_c_signals_are_causal():
    """A bar's signal must not change when later data is added (no look-ahead)."""
    import pandas as pd
    cfg = ps.load_config()
    short = ps.load_frame(5, pd.Timestamp("2022-09-01", tz="UTC"), cfg)
    long = ps.load_frame(5, pd.Timestamp("2022-11-01", tz="UTC"), cfg)
    n = len(short.df)
    assert (long.df["time"].iloc[:n].to_numpy() == short.df["time"].to_numpy()).all()
    s1, s2 = ps.Signals(short), ps.Signals(long)
    for fam, p in ps.signal_settings({"families": cfg["path_c"]["families"]}):
        a, b = s1.direction(fam, p), s2.direction(fam, p)[:n]
        assert (a == b).all(), fam
        assert np.abs(b).sum() > 0 or fam.startswith(("C01", "C02", "C07", "C08", "C09")), fam
