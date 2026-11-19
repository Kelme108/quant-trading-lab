"""b3/exit_menu.py imports and its config is the approved exploration-only menu (the cycle runs it after each batch)."""

from b3 import exit_menu


def test_module_and_config_load():
    cfg = exit_menu.load_config()
    assert set(cfg["exits"]) == {"S1", "S2", "S3", "S4"} and cfg["split"] == "exploration"
