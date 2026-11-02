import unittest

from lab.bootstrap import block_bootstrap, final_return, max_drawdown


class BootstrapTest(unittest.TestCase):
    def test_max_drawdown_of_known_sequence(self) -> None:
        # 1.0 -> 2.0 -> 1.0: a 50% fall from the peak.
        self.assertAlmostEqual(max_drawdown([1.0, -0.5]), 0.5)
        self.assertAlmostEqual(max_drawdown([0.1, 0.1]), 0.0)

    def test_final_return_compounds(self) -> None:
        self.assertAlmostEqual(final_return([0.1, 0.1]), 0.21)

    def test_same_seed_gives_same_result(self) -> None:
        ratios = [0.2, -0.05, -0.06, 0.4, -0.07, 0.1, -0.05, 0.3]
        self.assertEqual(block_bootstrap(ratios, n_resamples=200, seed=7), block_bootstrap(ratios, n_resamples=200, seed=7))

    def test_all_wins_never_breaches_the_limit(self) -> None:
        result = block_bootstrap([0.05] * 10, n_resamples=100)
        self.assertEqual(result["prob_drawdown_over_limit"], 0.0)
        self.assertEqual(result["prob_negative_return"], 0.0)

    def test_empty_input_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            block_bootstrap([])


if __name__ == "__main__":
    unittest.main()
