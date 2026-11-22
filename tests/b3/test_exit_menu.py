"""b3/exit_menu.py imports and its config is the approved exploration-only menu (the cycle runs it after each batch)."""

from b3 import exit_menu


def test_module_and_config_load():
    cfg = exit_menu.load_config()
    assert set(cfg["exits"]) == {"S1", "S2", "S3", "S4"} and cfg["split"] == "exploration"


def test_fixed_brl_menu_config():
    """The owner's R$ 35 target / R$ 90 stop menu (b3/config/exit_brl.json) loads, is exploration-only and converts to
    WIN points (R$ 0.20 per point, tick 5): target 175, stop 450."""
    from pathlib import Path

    import numpy as np

    from b3 import p026_lab as lab

    cfg = exit_menu.load_config(Path(__file__).resolve().parents[2] / "b3" / "config" / "exit_brl.json")
    assert cfg["split"] == "exploration" and cfg["markets"] == ["WIN"]
    assert set(cfg["exits"]) == {"B1", "B2", "B3", "B4", "B5"}
    assert cfg["exit_neighbours"]["B1"] == ["B2", "B3", "B4", "B5"]
    d = lab.distances(cfg["exits"]["B1"], np.array([170000.0]), None, None, np.array([0.001]), 0.2, 5.0)
    assert float(d["target"][0]) == 175.0 and float(d["stop"][0]) == 450.0
