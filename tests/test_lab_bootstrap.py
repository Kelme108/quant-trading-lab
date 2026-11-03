import unittest

from lab.bootstrap import block_bootstrap, choose_exposure, final_return, max_drawdown


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

    def test_choose_exposure_is_full_when_the_risk_is_small(self) -> None:
        result = choose_exposure({"A": [0.02, -0.01, 0.03] * 10}, n_resamples=200)
        self.assertEqual(result["exposure"], 1.0)

    def test_choose_exposure_scales_down_for_a_risky_pair_and_uses_the_worst_pair(self) -> None:
        risky = [0.3, -0.25, -0.25, 0.4, -0.3, 0.2] * 6
        calm = [0.02, -0.01] * 20
        both = choose_exposure({"calm": calm, "risky": risky}, n_resamples=300)
        only_risky = choose_exposure({"risky": risky}, n_resamples=300)
        self.assertLess(both["exposure"], 1.0)
        self.assertEqual(both["exposure"], only_risky["exposure"])
        self.assertTrue(all(v <= 0.25 for v in both["p95_by_pair"].values()))

    def test_empty_input_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            block_bootstrap([])


if __name__ == "__main__":
    unittest.main()
