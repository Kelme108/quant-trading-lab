"""Integration tests built for the original three pairs pin runner.enabled_pairs() to them; the shipped
nine-pair universe (2026-11-06) is checked in test_lab_scenarios, and the breadth rule in test_lab_breadth."""

from unittest import mock

from lab import runner

THREE = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]


def module_fixtures():
    original = runner.enabled_pairs
    patcher = mock.patch.object(runner, "enabled_pairs",
                                side_effect=lambda scenarios=None: list(THREE) if scenarios is None else original(scenarios))
    return (lambda: patcher.start()), (lambda: patcher.stop())
