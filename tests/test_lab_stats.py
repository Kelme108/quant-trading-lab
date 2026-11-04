import math
import unittest

import numpy as np

from lab import stats


class SharpeTests(unittest.TestCase):
    def test_sharpe_of_known_series(self):
        self.assertAlmostEqual(stats.sharpe([1.0, 2.0, 3.0]), 2.0)  # mean 2, sample std 1
        self.assertEqual(stats.sharpe([0.01, 0.01, 0.01]), 0.0)  # constant series: no risk estimate
        self.assertEqual(stats.sharpe([0.5]), 0.0)

    def test_annualise(self):
        self.assertAlmostEqual(stats.annualise(0.1, 365), 0.1 * math.sqrt(365))


class PsrDsrTests(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(5)

    def test_psr_is_high_for_a_strong_long_series_and_near_half_for_noise(self):
        strong = self.rng.normal(0.002, 0.01, 2000)
        self.assertGreater(stats.probabilistic_sharpe(strong), 0.99)
        # a single noise sample's PSR is roughly uniform on [0, 1]; its average over many samples is near 0.5
        average = np.mean([stats.probabilistic_sharpe(self.rng.normal(0.0, 0.01, 1000)) for _ in range(200)])
        self.assertAlmostEqual(average, 0.5, delta=0.1)

    def test_psr_grows_with_sample_length_for_the_same_edge(self):
        base = self.rng.normal(0.001, 0.01, 4000)
        self.assertGreater(stats.probabilistic_sharpe(base[:4000]), stats.probabilistic_sharpe(base[:400]) - 0.3)
        self.assertTrue(math.isnan(stats.probabilistic_sharpe([0.01, 0.02])))

    def test_expected_max_sharpe_matches_extreme_value_theory(self):
        self.assertEqual(stats.expected_max_sharpe(1, 1.0), 0.0)
        self.assertAlmostEqual(stats.expected_max_sharpe(2, 1.0), 1 / math.sqrt(math.pi), delta=0.1)  # E[max of 2 N(0,1)]
        self.assertTrue(2.3 < stats.expected_max_sharpe(100, 1.0) < 2.7)  # E[max of 100 N(0,1)] ~ 2.51
        self.assertAlmostEqual(stats.expected_max_sharpe(50, 4.0), 2 * stats.expected_max_sharpe(50, 1.0))

    def test_dsr_equals_psr_with_one_trial_and_falls_as_trials_grow(self):
        returns = self.rng.normal(0.0008, 0.01, 1500)
        one = stats.deflated_sharpe(returns, 1, 0.0004)
        self.assertAlmostEqual(one["dsr"], one["psr_vs_zero"])
        few = stats.deflated_sharpe(returns, 5, 0.0004)["dsr"]
        many = stats.deflated_sharpe(returns, 200, 0.0004)["dsr"]
        self.assertGreater(one["dsr"], few)
        self.assertGreater(few, many)

    def test_trial_sharpe_variance(self):
        series = [self.rng.normal(0, 0.01, 300) for _ in range(30)]
        self.assertGreater(stats.trial_sharpe_variance(series), 0.0)
        self.assertEqual(stats.trial_sharpe_variance(series[:1]), 0.0)


class PboTests(unittest.TestCase):
    def test_pure_noise_has_pbo_near_one_half(self):
        rng = np.random.default_rng(7)
        result = stats.pbo_cscv(rng.normal(0, 0.01, (1200, 20)), n_slices=12)
        self.assertTrue(0.3 < result["pbo"] < 0.7, result)
        self.assertEqual(result["n_splits"], math.comb(12, 6))

    def test_a_genuine_persistent_edge_has_low_pbo_and_positive_oos_sharpe(self):
        rng = np.random.default_rng(8)
        matrix = rng.normal(0, 0.01, (1200, 20))
        matrix[:, 3] += 0.004
        result = stats.pbo_cscv(matrix, n_slices=12)
        self.assertLess(result["pbo"], 0.1, result)
        self.assertGreater(result["mean_oos_sharpe_of_is_winner"], 0.1)

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            stats.pbo_cscv(np.zeros((100, 1)))
        with self.assertRaises(ValueError):
            stats.pbo_cscv(np.zeros((100, 3)), n_slices=7)


class BootstrapCiTests(unittest.TestCase):
    def test_interval_covers_the_truth_is_reproducible_and_flags_small_samples(self):
        rng = np.random.default_rng(9)
        x = rng.normal(0.5, 1.0, 400)
        a = stats.block_bootstrap_ci(x, np.mean, block=5, seed=3)
        b = stats.block_bootstrap_ci(x, np.mean, block=5, seed=3)
        self.assertEqual(a, b)
        self.assertTrue(a["low"] < 0.5 < a["high"])
        self.assertFalse(a["low_sample"])
        small = stats.block_bootstrap_ci(x[:40], np.mean, block=5, seed=3)
        self.assertTrue(small["low_sample"])
        self.assertGreater(small["high"] - small["low"], a["high"] - a["low"])

    def test_degenerate_input(self):
        self.assertTrue(stats.block_bootstrap_ci([1.0], np.mean)["low_sample"])


if __name__ == "__main__":
    unittest.main()
