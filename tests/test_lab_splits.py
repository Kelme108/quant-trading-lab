import unittest
from datetime import datetime, timedelta, timezone

from lab import runner


def parse_utc(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def timerange_bounds(timerange: str) -> tuple[int, int | None]:
    start, _, stop = timerange.partition("-")
    return int(start), (int(stop) if stop else None)


class ShippedSplitsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.splits = runner.load_splits()
        self.cutoff = parse_utc(self.splits["historical_cutoff_utc_exclusive"])

    def test_every_enabled_pair_has_exploration_and_validation(self) -> None:
        for pair in runner.enabled_pairs():
            for split in ("exploration", "validation"):
                self.assertIn(split, self.splits["pairs"][pair], f"{pair} lacks {split}")

    def test_exploration_precedes_validation_with_no_overlap_and_no_hole(self) -> None:
        for pair, entry in self.splits["pairs"].items():
            exploration_end = parse_utc(entry["exploration"]["end_utc"])
            validation_start = parse_utc(entry["validation"]["start_utc"])
            self.assertEqual(validation_start - exploration_end, timedelta(hours=1), pair)

    def test_timeranges_are_exact_timestamps_matching_the_stated_utc_bounds(self) -> None:
        for pair, entry in self.splits["pairs"].items():
            for split in ("exploration", "validation"):
                start, stop = timerange_bounds(entry[split]["timerange"])
                self.assertEqual(start, int(parse_utc(entry[split]["start_utc"]).timestamp()), pair)
                self.assertEqual(stop, int(parse_utc(entry[split]["end_utc"]).timestamp()), pair)

    def test_all_historical_data_ends_before_the_final_test_starts(self) -> None:
        final_start = parse_utc(self.splits["final_test"]["start_utc"])
        self.assertEqual(final_start, self.cutoff)
        for pair, entry in self.splits["pairs"].items():
            self.assertLess(parse_utc(entry["validation"]["end_utc"]), self.cutoff, pair)
        start, stop = timerange_bounds(self.splits["final_test"]["timerange"])
        self.assertEqual(start, int(self.cutoff.timestamp()))
        self.assertIsNone(stop)

    def test_exploration_takes_about_the_stated_share_of_history(self) -> None:
        share = self.splits["exploration_share_of_history"]
        for pair, entry in self.splits["pairs"].items():
            if pair not in ("BTC/USDT", "ETH/USDT", "BNB/USDT"):
                continue  # the 2026-11-06 pairs share the original calendar instead (test below)
            first = parse_utc(entry["exploration"]["start_utc"])
            explore_end = parse_utc(entry["exploration"]["end_utc"])
            valid_end = parse_utc(entry["validation"]["end_utc"])
            actual = (explore_end - first) / (valid_end - first)
            self.assertAlmostEqual(actual, share, delta=0.01, msg=pair)

    def test_pairs_added_in_2026_11_end_exploration_on_the_shared_calendar(self) -> None:
        for pair in ("XRP/USDT", "ADA/USDT", "LTC/USDT", "LINK/USDT", "DOGE/USDT", "SOL/USDT",
                     "AVAX/USDT", "DOT/USDT", "TRX/USDT", "NEAR/USDT", "UNI/USDT", "BCH/USDT", "XLM/USDT", "FIL/USDT", "AAVE/USDT", "INJ/USDT", "HBAR/USDT", "OP/USDT", "APT/USDT", "ARB/USDT", "SUI/USDT", "ATOM/USDT", "ETC/USDT"):
            entry = self.splits["pairs"][pair]
            self.assertEqual(entry["exploration"]["end_utc"], "2024-07-04T23:00:00Z", pair)
            self.assertEqual(entry["validation"]["start_utc"], "2024-07-05T00:00:00Z", pair)
            start, stop = timerange_bounds(entry["exploration"]["timerange"])
            self.assertEqual(stop + 3600, timerange_bounds(entry["validation"]["timerange"])[0], pair)
        for pair in ("BTC/USDT", "ETH/USDT", "BNB/USDT"):
            self.assertNotEqual(self.splits["pairs"][pair]["exploration"]["end_utc"], "2024-07-04T23:00:00Z")

    def test_final_test_ships_locked(self) -> None:
        self.assertIs(self.splits["final_test"]["final_test_unlocked"], False)


class ResolveSplitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.splits = runner.load_splits()

    def test_resolves_the_per_pair_timerange(self) -> None:
        timerange = runner.resolve_split_timerange("exploration", self.splits, pair="ETH/USDT")
        self.assertEqual(timerange, self.splits["pairs"]["ETH/USDT"]["exploration"]["timerange"])

    def test_pairs_get_their_own_boundaries(self) -> None:
        btc = runner.resolve_split_timerange("validation", self.splits, pair="BTC/USDT")
        bnb = runner.resolve_split_timerange("validation", self.splits, pair="BNB/USDT")
        self.assertNotEqual(btc, bnb)

    def test_exploration_without_a_pair_is_an_error(self) -> None:
        with self.assertRaises(ValueError):
            runner.resolve_split_timerange("exploration", self.splits)

    def test_unknown_pair_is_an_error(self) -> None:
        with self.assertRaises(KeyError):
            runner.resolve_split_timerange("exploration", self.splits, pair="XYZ/USDT")

    def test_unknown_split_is_an_error(self) -> None:
        with self.assertRaises(ValueError):
            runner.resolve_split_timerange("holdout", self.splits, pair="BTC/USDT")

    def test_final_test_is_refused_while_locked(self) -> None:
        with self.assertRaises(runner.FinalTestLockedError):
            runner.resolve_split_timerange("final_test", self.splits)
        with self.assertRaises(runner.FinalTestLockedError):
            runner.resolve_split_timerange("final_test", self.splits, pair="BTC/USDT")

    def test_final_test_resolves_only_once_unlocked(self) -> None:
        unlocked = {"final_test": {"final_test_unlocked": True, "timerange": "100-"}}
        self.assertEqual(runner.resolve_split_timerange("final_test", unlocked), "100-")


if __name__ == "__main__":
    unittest.main()
