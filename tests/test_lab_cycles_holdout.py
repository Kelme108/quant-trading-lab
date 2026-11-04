import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from lab import cycles, walkforward

ROOT = Path(__file__).parents[1]


class HoldoutConfigTests(unittest.TestCase):
    def test_prospective_start_matches_the_final_test_in_splits(self):
        splits = json.loads((ROOT / "lab" / "config" / "splits.json").read_text(encoding="utf-8"))
        self.assertEqual(cycles.prospective_start(), pd.Timestamp(splits["final_test"]["start_utc"]))
        self.assertFalse(splits["final_test"]["final_test_unlocked"])

    def test_the_last_twelve_months_end_where_the_prospective_holdout_begins(self):
        start, end = cycles.semi_contaminated_window()
        self.assertEqual(end + pd.Timedelta(seconds=1), cycles.prospective_start())
        self.assertAlmostEqual((end - start).days, 365, delta=1)

    def test_no_historical_cycle_reaches_the_prospective_holdout(self):
        for name, (start, end) in cycles.cycles().items():
            self.assertLess(start, end, name)
            cycles.assert_before_holdout(end)
        with self.assertRaises(ValueError):
            cycles.assert_before_holdout(cycles.prospective_start())

    def test_cycles_are_ordered_and_named(self):
        self.assertEqual(list(cycles.cycles()), ["2018", "2019", "2020-21", "2022", "2023+"])

    def test_evaluation_rule_is_documented_in_the_config(self):
        rule = cycles.holdout_config()["prospective_holdout"]
        self.assertEqual(rule["earliest_evaluation_utc"], "2027-04-21T00:00:00Z")
        self.assertGreaterEqual(rule["min_closed_trades"], 30)

    def test_labelled_periods_use_the_per_pair_splits(self):
        splits = json.loads((ROOT / "lab" / "config" / "splits.json").read_text(encoding="utf-8"))
        periods = cycles.labelled_periods("BTC/USDT", splits)
        self.assertEqual(set(periods), {"IS (exploration)", "OOS (validation)", "last 12m (semi-contaminated)"})
        self.assertLess(periods["IS (exploration)"][1], periods["OOS (validation)"][0])


class WalkForwardTests(unittest.TestCase):
    def frame(self):
        index = pd.date_range("2018-01-01", "2022-12-31", freq="D", tz="UTC")
        rng = np.random.default_rng(1)
        data = {f"c{i}": rng.normal(0, 0.01, len(index)) for i in range(5)}
        data["good"] = rng.normal(0.003, 0.01, len(index))
        return pd.DataFrame(data, index=index)

    def test_folds_are_anchored_and_never_overlap_the_train_window(self):
        frame = self.frame()
        folds = walkforward.anchored_folds(frame.index, 2020, 2022)
        self.assertEqual(len(folds), 3)
        for train_start, train_end, test_start, test_end in folds:
            self.assertLess(train_end, test_start)
            self.assertEqual(train_start, frame.index.min())

    def test_selection_uses_only_the_train_window(self):
        frame = self.frame()
        # make a column look great only in the test years: it must not be chosen
        frame["future_hero"] = 0.0
        frame.loc["2020-01-01":, "future_hero"] = 0.05
        result = walkforward.walk_forward(frame, walkforward.anchored_folds(frame.index, 2020, 2022))
        self.assertEqual(result["folds"][0]["chosen"], "good")
        self.assertNotEqual(result["folds"][0]["chosen"], "future_hero")

    def test_the_stitched_series_covers_the_test_years_only(self):
        frame = self.frame()
        result = walkforward.walk_forward(frame, walkforward.anchored_folds(frame.index, 2021, 2022))
        self.assertEqual(result["oos_returns"].index.min(), pd.Timestamp("2021-01-01", tz="UTC"))
        self.assertEqual(len(result["folds"]), 2)


if __name__ == "__main__":
    unittest.main()
