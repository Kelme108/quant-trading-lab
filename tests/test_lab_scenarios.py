import unittest

from lab import runner


class ScenarioLoaderTests(unittest.TestCase):
    def test_shipped_config_enables_the_three_pairs_on_1h_and_15m(self) -> None:
        """15m was enabled on 2026-11-05: the splits are dated (timeranges), so they cut 15m candles at the same
        instants as 1h. Any other timeframe still needs its own data first."""
        self.assertEqual(runner.enabled_pairs(), ["BTC/USDT", "ETH/USDT", "BNB/USDT"])
        self.assertEqual(runner.enabled_timeframes(), ["1h", "15m"])

    def test_gap_tolerance_is_a_documented_number(self) -> None:
        self.assertEqual(runner.max_gap_hours(), 48.0)

    def test_synthetic_resampling_is_not_enabled(self) -> None:
        self.assertFalse(runner.load_scenarios()["synthetic_resampling"]["enabled"])

    def test_disabled_and_unflagged_entries_are_skipped(self) -> None:
        scenarios = {
            "pairs": [
                {"pair": "A/USDT", "enabled": True},
                {"pair": "B/USDT", "enabled": False},
                {"pair": "C/USDT"},
            ],
            "timeframes": [{"timeframe": "1h", "enabled": True}],
        }
        self.assertEqual(runner.enabled_pairs(scenarios), ["A/USDT"])

    def test_no_enabled_pair_is_an_error_not_an_empty_run(self) -> None:
        scenarios = {"pairs": [{"pair": "A/USDT", "enabled": False}], "timeframes": []}
        with self.assertRaises(ValueError):
            runner.enabled_pairs(scenarios)
        with self.assertRaises(ValueError):
            runner.enabled_timeframes(scenarios)


if __name__ == "__main__":
    unittest.main()
