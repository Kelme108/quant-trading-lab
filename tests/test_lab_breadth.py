import unittest

from lab import bootstrap, breadth, forward


class BreadthRuleTests(unittest.TestCase):
    def test_k_of_n_with_the_shipped_config(self) -> None:
        self.assertEqual(breadth.exploration_min_pairs(3), 3)
        self.assertEqual(breadth.exploration_min_pairs(9), 6)
        self.assertEqual(breadth.exploration_min_pairs(26), 16)   # same pre-registered 0.6 fraction on the 26-pair universe
        self.assertEqual(breadth.exploration_min_pairs(2), 2)
        self.assertEqual(breadth.validation_min_pairs(), 2)

    def test_causality_checks_run_on_the_three_longest_histories(self) -> None:
        nine = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "XRP/USDT", "ADA/USDT", "LTC/USDT", "LINK/USDT", "DOGE/USDT", "SOL/USDT"]
        self.assertEqual(breadth.causality_check_pairs(nine), ["BTC/USDT", "ETH/USDT", "BNB/USDT"])
        self.assertEqual(breadth.causality_check_pairs(["SOL/USDT"]), ["SOL/USDT"])

    def test_exposure_needs_k_pairs_not_the_worst_one(self) -> None:
        calm = [0.01, -0.005, 0.012, -0.004] * 15
        risky = [0.10, -0.12, -0.11, 0.05] * 15
        every = bootstrap.choose_exposure({"a": calm, "b": calm, "c": risky}, n_resamples=300)
        two = bootstrap.choose_exposure({"a": calm, "b": calm, "c": risky}, n_resamples=300, min_pairs=2)
        self.assertGreater(two["exposure"], every["exposure"] or 0)

    def test_every_pair_has_a_forward_key_and_old_freezes_keep_three(self) -> None:
        self.assertEqual(len(forward.PAIR_KEYS), 26)
        self.assertEqual(forward.pair_keys("H-999"), ["btc", "eth", "bnb"])


if __name__ == "__main__":
    unittest.main()
